import requests
import unicodecsv
import json

from auth import Auth

congress = 114
chambers = ('house', 'senate')
account_file = "data/twitter_accounts.csv"
field_names = [u'first_name', u'middle_name', u'last_name', u'thomas_id', \
    u'twitter_account', u'state', u'dw_nominate', u'ideal_point', u'party']

def save_csv():
    with open(account_file, 'w') as out_file:
        csv_writer = unicodecsv.DictWriter(out_file, fieldnames=field_names, encoding='utf-8')
        csv_writer.writeheader()
        for chamber in chambers:
            member_data = get_chamber_members(chamber, csv_writer)
            write_member_data(chamber, member_data, csv_writer)

def get_chamber_members(chamber, csv_writer):
    resp = requests.get(Auth.times_api_route(congress, chamber))
    assert resp.status_code == 200, ('bad response getting list for %s: %d' % (chamber, resp.status_code))
    return json.loads(resp.text)["results"][0]["members"]

def write_member_data(chamber, member_data, csv_writer):
    for member in member_data:
        row = {}
        for field in field_names:
            row[field] = member[field]
            if row[field] is not None:
                row[field] = row[field].encode('utf-8')
        csv_writer.writerow(row)

if __name__ == '__main__':
    save_csv()
