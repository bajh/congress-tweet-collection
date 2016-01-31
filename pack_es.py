import requests
import json
import os
import datetime

import elasticsearch
import urllib3
import unicodecsv

from auth import Auth

account_file = "data/twitter_accounts.csv"
es_index = "congress"
es_doc_type = "tweets"

urllib3.disable_warnings()

def load_es():
    with open(account_file, 'r') as in_file:
        reader = unicodecsv.DictReader(in_file, encoding='utf-8')
        for member in reader:
            if member["twitter_account"] == None:
                continue
            print(member["twitter_account"])
            load_member_tweets(member)

def load_member_tweets(member):
    max_id = oldest_id(member['twitter_account'])
    print("Max id:", max_id)
    while True:
        response = Auth.twitter.request('statuses/user_timeline',
            {'screen_name': member['twitter_account'],
                'count': 200,
                'max_id': max_id
            }
        )
        status = response.status_code
        assert status == 200, "bad status %d" % status
        tweets = response.json()
        if len(tweets) == 1 and max_id == tweets[0]["id_str"]:
            return
        # The max id, which we already have loaded, will appear in the
        # results set (the max ID is inclusive)
        tweets = filter(lambda x: x["id"] != max_id, tweets)
        max_id = load_result_set(tweets, member)
        if max_id == None:
            return
        # TODO: deal with rate limiting

def load_result_set(tweets, member):
    es = Auth.es
    member_name = "%s %s %s" % (member["first_name"] or "", \
            member["middle_name"] or "", member["last_name"] or "")
    indexes = []
    oldest_id = None
    for tweet in tweets:
        dtime = datetime.datetime.strptime(tweet['created_at'] \
            .replace("+0000 ", ""), \
            "%a %b %d %H:%M:%S %Y") \
            .strftime("%s")
        index = {
            'member': member_name,
            'twitter_account': member['twitter_account'],
            'id': str(tweet['id_str']),
            'text': tweet['text'],
            'created_at': int(dtime),
            'in_reply_to_status_id': tweet['in_reply_to_status_id'],
            'in_reply_to_user_id': tweet['in_reply_to_user_id'],
            'retweet_count': tweet['retweet_count'],
            'favorite_count': tweet['favorite_count'],
            'hashtags': []
        }
        for hashtag in tweet['entities']['hashtags']:
            index['hashtags'].append(hashtag['text'])
        es.index(index=es_index, doc_type=es_doc_type, body=index)
        oldest_id = tweet['id_str']
    return oldest_id

def oldest_id(twitter_account):
    url = "%s/congress/tweets/_search" % Auth.es_host
    data = {
        "query": {
            "match": {
                "twitter_account": twitter_account
            }
        },
        "sort": [
            {
                "created_at": {
                    "order": "asc"
                }
            }
        ],
        "size": 1
    }
    resp = requests.get(url, data=json.dumps(data))
    status = resp.status_code
    # On creating the first record, we'll get a 404
    # TODO: fix this by creating index ahead of time
    if status == 404:
        return None
    assert status == 200, "bad status %d" % status
    result = json.loads(resp.text)
    if len(result['hits']) == 0 or len(result['hits']['hits']) == 0:
        return None
    return result['hits']['hits'][0]['_source']['id']

if __name__ == '__main__':
    load_es()
