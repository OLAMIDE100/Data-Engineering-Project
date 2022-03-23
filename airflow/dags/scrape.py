#pyhon libraries
import snscrape.modules.twitter as sntwitter
import pandas as pd
from textblob import TextBlob
import re
from datetime import datetime,timedelta



def processed_tweet(tweet):
    return ' '.join(re.sub('(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)', ' ', tweet).split())

def sentimental_analysis(tweet):
    analysis = TextBlob(tweet)
    if analysis.sentiment.polarity > 0:
        return 'Positive'
    elif analysis.sentiment.polarity ==0:
        return 'Neutral'
    else:
        return 'Negative'





def scrape_tweet():

    today = datetime.today().strftime('%Y-%m-%d')

    yesterday = (datetime.today() + timedelta(days= -1)).strftime('%Y-%m-%d')
    
    maxTweets =30000

    columns = ['Datetime', 'Text', 'Username','location','verified','created','retweet','likes']

    tinubu = []
    atiku = []

    lists = [tinubu,atiku]
    political_aspiraant = ['tinubu','atiku']

    print("scraping in progress.................................................................................")

    for k,names in zip(lists,political_aspiraant):
        # Using TwitterSearchScraper to scrape data and append tweets to list
        for i,tweet in enumerate(sntwitter.TwitterSearchScraper('{} since:{} until:{}'.format(names,yesterday,today)).get_items()):
            if i>maxTweets:
                break
            k.append([tweet.date, tweet.content, tweet.user.username,tweet.user.location,tweet.user.verified,
            tweet.user.created,tweet.retweetCount,tweet.likeCount])

    print("scraping successfully completed from {} to {}".format(yesterday,today))



    tinubu_df = pd.DataFrame(tinubu, columns=columns)
    atiku_df = pd.DataFrame(atiku, columns=columns)
    atiku_df['category'] = "atiku"
    tinubu_df['category'] = "tinubu"
    
    

    print("Dataframe sucessfully created")


    data_set = pd.concat([tinubu_df, atiku_df])

    print("merging successful")

    data_set['Text'] = data_set['Text'].apply(lambda x: processed_tweet(x))

    print("tweets cleaning successful")

    data_set['Sentiment'] = data_set['Text'].apply(lambda x: sentimental_analysis(x))

    data_set['Date'] = pd.to_datetime(data_set['Datetime'],format="%d/%m/%Y")


    print("sentimental analysis successful")
    
    print("the length of the dataset is {}".format(len(data_set)))

    data_set.to_csv(f'/opt/airflow/tweets_{yesterday}.csv',index=False)

    return f"successfully converted to csv"


if __name__ == "__main__":
   scrape_tweet()

