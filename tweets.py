from auth import Auth
from datetime import datetime
import json
import time

from members import Member

from peewee import *

class Tweet(Model):
    member = ForeignKeyField(Member, related_name='tweets')
    twitter_id = BigIntegerField(unique=True)
    created_at = DateTimeField(default=datetime.now)
    text = CharField(max_length=300)
    in_reply_to_status_id = BigIntegerField(null=True)
    in_reply_to_user_id = BigIntegerField(null=True)
    retweet_count = IntegerField()
    favorite_count = IntegerField()

    class Meta:
        database = Auth.db

class Hashtag(Model):
    tweet = ForeignKeyField(Tweet, related_name='hashtags')
    text = CharField(max_length=300)

    class Meta:
        database = Auth.db

#creates tweets from JSON and returns the id
#of the last tweet added to the db
def create_tweets_from_json(db, tweet_json, member):
    max_id = None
    with db.atomic():
        for t in tweet_json:
            tweet_data = {
                "member": member,
                "twitter_id": t["id"],
                "text": t["text"],
                "created_at": t["created_at"],
                "in_reply_to_status_id": t["in_reply_to_status_id"],
                "in_reply_to_user_id": t["in_reply_to_user_id"],
                "retweet_count": t["retweet_count"],
                "favorite_count": t["favorite_count"],
            }
            tweet = Tweet.create(**tweet_data)
            create_hashtags_from_list(t["entities"]["hashtags"], tweet)
            max_id = tweet.twitter_id
    return max_id

def create_hashtags_from_list(hashtag_list, tweet):
    for hashtag_data in hashtag_list:
        Hashtag.create(tweet=tweet, text=hashtag_data["text"])

def collect_tweets(db, member, oldest_tweet):
    if member.twitter_account is None or member.twitter_account == "":
        return False
    if oldest_tweet != None:
        max_id = oldest_tweet.twitter_id
    else:
        max_id = None

    while True:
        retries = 0
        # Make 5 attempts to get a valid response from Twitter for this request
        while True:
            response = Auth.twitter.request('statuses/user_timeline',
                {'screen_name': member.twitter_account,
                    'count': 200,
                    'max_id': max_id
                })
            if response.status_code == 200:
                records = response.json()
                len_records = len(records)
                # If the only record we got back is the last one we processed,
                # we're done collecting tweets for this member
                if len_records == 1 and max_id == records[0]["id"]:
                   return
                records = filter(lambda x: x["id"] != max_id, records)
                max_id = create_tweets_from_json(db, records, member)
            elif response.status_code == 429:
                print("rate limit hit: waiting")
                time.sleep(200)
                continue
            else:
                retries += 1
                if retries < 5:
                    time.sleep(5)
                else:
                    assert False, "bad response %s" % response.text


def load_tweets(db):
    members = Member.select().order_by(fn.Random())
    for member in members:
        print("collecting tweets for", member.first_name, member.last_name, member.twitter_account)
        try:
            oldest_tweet = member.tweets.order_by(Tweet.twitter_id.asc()).limit(1).get()
        except Tweet.DoesNotExist:
            oldest_tweet = None
        collect_tweets(db, member, oldest_tweet)

if __name__ == "__main__":
    Auth.db.connect()
    Auth.db.create_tables([Tweet, Hashtag], safe=True)
    load_tweets(Auth.db)
