import os
from TwitterAPI import TwitterAPI
from peewee import *

class Auth():
    times_base_uri = "http://api.nytimes.com/svc/politics/v3/us/legislative/congress"
    times_api_key = os.getenv("TIMES_API_KEY")
    congress_db = os.getenv("CONGRESS_DB")
    congress_db_user = os.getenv("CONGRESS_DB_USER")
    congress_db_password = os.getenv("CONGRESS_DB_PASSWORD")
    congress_db_host = os.getenv("CONGRESS_DB_HOST")
    twitter_access_token_key = os.getenv("TWITTER_ACCESS_TOKEN_KEY")
    twitter_access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
    twitter_api_key = os.getenv("TWITTER_API_KEY")
    twitter_api_secret = os.getenv("TWITTER_API_SECRET")

    db = PostgresqlDatabase(
        congress_db,
        user=congress_db_user,
        password=congress_db_password,
        host=congress_db_host
    )

    twitter = TwitterAPI(twitter_api_key,
        twitter_api_secret,
        twitter_access_token_key,
        twitter_access_token_secret)

    @classmethod
    def times_api_route(cls, congress, chamber):
        return "%s/%s/%s/members.json?api-key=%s" % (cls.times_base_uri,
            congress, chamber, cls.times_api_key)
