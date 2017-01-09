import tweepy
import bs4
from urllib.request import urlopen
from html.parser import HTMLParser
import time
import json

class TwitterPublisher:
    def __init__(self, api = None):
        if api is None:
            self.api = self._get_api(self._get_cfg())
            print("Posting with Twitter name " + self.api.me().screen_name)
        else:
            self.api = api

    def publish_tweet(self, message):
        print("Tweeting: " + message)
        self.api.update_status(status=message)

    def _get_api(self, cfg):
        auth = tweepy.OAuthHandler(cfg['consumer_key'], cfg['consumer_secret'])
        auth.set_access_token(cfg['access_token'], cfg['access_token_secret'])
        return tweepy.API(auth)

    def _get_cfg(self):
        with open('auth.json', 'r') as authfile:
            return json.load(authfile)

class DriveSpreadsheetReader:
    def __init__(self, source_url = None, records = None):
        self.source_url = source_url
        if records is None:
            self.all_records = self.fetch_data()
        else:
            self.all_records = records

    def get_tables(self, htmldoc):
        soup = bs4.BeautifulSoup(htmldoc, "html.parser")
        return soup.findAll('table')

    def makelist(self, table):
        parser = HTMLParser()
        result = []
        allrows = table.findAll('tr')
        for row in allrows:
            result.append([])
            allcols = row.findAll('td')
            for col in allcols:
                thestrings = [parser.unescape(str(s))
                              for s in col.findAll(text=True)]
                thetext = ''.join(thestrings)
                result[-1].append(thetext)
        # gb: skip empty rows
        return [row for row in result if len(row) > 0]

    def fetch_data(self):
        url = self.source_url

        response = urlopen(url)
        pagecontent = response.read()

        tables = self.get_tables(pagecontent)
        content = self.makelist(tables[0])

        # Skip header row
        return content[1:]

    def new_records(self, df_old, df_new):
        old_set = set([tuple(l) for l in df_old])
        new_recs = []
        for row in df_new:
            if tuple(row) not in old_set:
                new_recs.append(row)
        return new_recs

    def fetch_new_records(self):
        print("Fetching data")
        updated_recs = self.fetch_data()
        only_new_recs = self.new_records(self.all_records, updated_recs)
        self.all_records = updated_recs
        return only_new_recs

class PublishHepRumors:
    def __init__(self, twitter_publisher = None, spreadsheet = None):
        rumors_url = 'https://docs.google.com/spreadsheets/d/1iMsLRnNNHFKmdq7ltrp9BR4jDd-Ots6UYDK2dgyRLZ0/htmlembed/sheet?headers=false&gid=0'
        self.sleep_interval_seconds = 30

        self.twitter_publisher = twitter_publisher or TwitterPublisher()
        self.spreadsheet = spreadsheet or DriveSpreadsheetReader(source_url = rumors_url)

    def make_message(self, record):
        name = record[0]
        inst = record[2]
        status = record[3]
        if "accepted" in status.lower():
            return name + " is going to " + inst + ". Good luck :)"
        if "offered" in status.lower():
            return name + " has an offer from " + inst + ". Congrats!"
        return None

    def publish_new_tweets(self, new_record_list):
        for record in reversed(new_record_list):
            message = self.make_message(record)
            if message is not None:
                self.twitter_publisher.publish_tweet(message)

    def poll_publish_loop(self):
        while True:
            new_tweets = self.spreadsheet.fetch_new_records()
            print("There are " + str(len(new_tweets)) + " updates.")
            self.publish_new_tweets(new_tweets)

            time.sleep(self.sleep_interval_seconds)

if __name__ == "__main__":
    rumor_publisher = PublishHepRumors()
    rumor_publisher.poll_publish_loop()
