import elasticsearch
import unicodecsv

from auth import Auth

account_file = "data/twitter_accounts.csv"
es_index = "congress"
es_doc_type = "tweets"

def load_es():
    with open(account_file, 'r') as in_file:
        reader = unicodecsv.DictReader(in_file, encoding='utf-8')
        for member in reader:
            load_row(member)

def load_row(member):
    max_id = None
    response = Auth.twitter.request('statuses/user_timeline',
        {'screen_name': member['twitter_account'],
            'count': 200,
            'max_id': max_id
        }
    )
    assert response.status_code == 200
    if response.status_code == 200:
        tweets = response.json()
        if len(tweets) == 1 and max_id == tweets[0]["id"]:
            return
        # The max id, which we already have loaded, will appear in the
        # results set (the max ID is inclusive)
        tweets = filter(lambda x: x["id"] != max_id, tweets)
        max_id = load_result_set(tweets, member)
        # TODO: deal with rate limiting

def load_result_set(tweets, member):
    es = Auth.es
    member_name = "%s %s %s" % (member["first_name"] or "", \
            member["middle_name"] or "", member["last_name"] or "")
    indexes = []
    for tweet in tweets:
        index = {
            'member': member_name,
            'twitter_account': member['twitter_account'],
            'text': tweet['text'],
            'created_at': tweet['created_at'],
            'in_reply_to_status_id': tweet['in_reply_to_status_id'],
            'in_reply_to_user_id': tweet['in_reply_to_user_id'],
            'retweet_count': tweet['retweet_count'],
            'favorite_count': tweet['favorite_count'],
            'hashtags': []
        }
        for hashtag in tweet['entities']['hashtags']:
            index['hashtags'].append(hashtag['text'])
        #indexes.append(index)
        es.index(index=es_index, doc_type=es_doc_type, body=index)

if __name__ == '__main__':
    load_es()
