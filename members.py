import requests
import json

from peewee import *
from auth import Auth

class Member(Model):
    first_name = CharField(max_length=200, default="")
    middle_name = CharField(max_length=200, default="")
    last_name = CharField(max_length=200, default="")
    chamber = CharField(max_length=100)
    thomas_id = IntegerField(default=0, unique=True)
    party = CharField(max_length=10, default="")
    twitter_account = CharField(max_length=200, default="")
    dw_nominate = FloatField(default=0)
    ideal_point = FloatField(default=0)
    votes_with_party = FloatField(default=0)
    seniority = IntegerField(default=0)
    next_election = IntegerField(default=0)
    state = CharField(max_length=10, default="")

    class Meta:
        database = Auth.db


def load_members(congress):
    for chamber in ['house', 'senate']:
        resp = requests.get(Auth.times_api_route(congress, chamber))
        assert resp.status_code == 200, ('bad response getting list for %s: %d' % (chamber, resp.status_code))
        results = json.loads(resp.text)
        for member_json in results["results"][0]["members"]:
            member = create_new_member(congress, chamber, member_json)

def create_new_member(congress, chamber, member_json):
    attrs = ["first_name", "middle_name", "last_name", "thomas_id",
        "party", "twitter_account", "dw_nominate", "ideal_point",
        "votes_with_party", "seniority", "next_election", "state"]
    kwargs = {attr: member_json[attr] for attr in attrs if attr in member_json and
        member_json[attr] != "" and member_json[attr] is not None}
    kwargs["congress"] = congress
    kwargs["chamber"] = chamber
    Member.create(**kwargs)

if __name__ == '__main__':
    Auth.db.connect()
    Auth.db.create_tables([Member], safe=True)
    load_members(114)
