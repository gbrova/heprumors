import tweepy
import BeautifulSoup
import urllib2
import HTMLParser
import time
import json

SLEEP_INTERVAL_SECONDS = 30
SOURCE_URL = 'https://docs.google.com/spreadsheets/d/1iMsLRnNNHFKmdq7ltrp9BR4jDd-Ots6UYDK2dgyRLZ0/htmlembed/sheet?headers=false&gid=0'

def get_api(cfg):
    auth = tweepy.OAuthHandler(cfg['consumer_key'], cfg['consumer_secret'])
    auth.set_access_token(cfg['access_token'], cfg['access_token_secret'])
    return tweepy.API(auth)

def get_cfg():
    with open('auth.json', 'r') as authfile:
        return json.load(authfile)

def get_tables(htmldoc):
    soup = BeautifulSoup.BeautifulSoup(htmldoc)
    return soup.findAll('table')

def makelist(table):
    parser = HTMLParser.HTMLParser()
    result = []
    allrows = table.findAll('tr')
    for row in allrows:
        result.append([])
        allcols = row.findAll('td')
        for col in allcols:
            thestrings = [parser.unescape(unicode(s))
                          for s in col.findAll(text=True)]
            thetext = ''.join(thestrings)
            result[-1].append(thetext)
    # gb: skip empty rows
    return [row for row in result if len(row) > 0]

def fetch_data():
    url = SOURCE_URL

    response = urllib2.urlopen(url)
    pagecontent = response.read()

    tables = get_tables(pagecontent)
    content = makelist(tables[0])

    # Skip header row
    return content[1:]

def new_records(df_old, df_new):
    old_set = set([tuple(l) for l in df_old])
    new_recs = []
    for row in df_new:
        if tuple(row) not in old_set:
            new_recs.append(row)
    return new_recs

def make_message(record):
    name = record[0]
    inst = record[2]
    status = record[3]
    if "accepted" in status.lower():
        return name + " is going to " + inst + ". Good luck :)"
    if "offered" in status.lower():
        return name + " has an offer from " + inst + ". Congrats!"
    return None

def publish_tweet(api, message):
    print "Tweeting: " + message
    api.update_status(status=message)

def publish_new_tweets(api, new_record_list):
    for record in reversed(new_record_list):
        message = make_message(record)
        if message is not None:
            publish_tweet(api, message)

def main():
    api = get_api(get_cfg())

    print "Posting with Twitter name " + api.me().screen_name

    # Initial fetch
    df_new = fetch_data()

    while True:
        print "Fetching data"
        df_old = df_new
        df_new = fetch_data()
        new_ones = new_records(df_old, df_new)
        print "There are " + str(len(new_ones)) + " updates."
        publish_new_tweets(api, new_ones)

        time.sleep(SLEEP_INTERVAL_SECONDS)

if __name__ == "__main__":
    main()
