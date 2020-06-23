import arrow
import mongoengine
import pandas as pd
import pymongo
import twint

from threadback.app import huey
from threadback.models import models


def create_df(tweets):
    value_list = []
    for tweet in tweets:
        dt = f"{tweet.datestamp} {tweet.timestamp}"
        value_list.append(
            {
                "id": str(tweet.id),
                "conversation_id": tweet.conversation_id,
                "date": arrow.get(dt).format("YYYY-MM-DD HH:mm:ss"),
                "timezone": tweet.timezone,
                "place": tweet.place,
                "tweet": tweet.tweet,
                "mentions": tweet.mentions,
                "urls": tweet.urls,
                "photos": tweet.photos,
                "hashtags": tweet.hashtags,
                "cashtags": tweet.cashtags,
                "user_id": tweet.user_id,
                "user_id_str": tweet.user_id_str,
                "username": tweet.username,
                "name": tweet.name,
                "link": tweet.link,
                "retweet": tweet.retweet,
                "nlikes": int(tweet.likes_count),
                "nreplies": int(tweet.replies_count),
                "nretweets": int(tweet.retweets_count),
                "quote_url": tweet.quote_url,
                "near": tweet.near,
                "geo": tweet.geo,
                "source": tweet.source,
                "user_rt_id": tweet.user_rt_id,
                "user_rt": tweet.user_rt,
                "retweet_id": tweet.retweet_id,
                "reply_to": tweet.reply_to,
                "retweet_date": tweet.retweet_date,
                "translate": tweet.translate,
                "trans_src": tweet.trans_src,
                "trans_dest": tweet.trans_dest,
            },
        )

    return pd.DataFrame(value_list)


@huey.task()
def refresh_user_threads(username):
    try:
        user = models.User.objects(username=username).first()

        tweet_config = twint.Config()
        tweet_config.Username = username
        tweet_config.Store_object = True
        tweet_config.Hide_output = True

        latest_tweet = models.Tweet.objects(user=user).order_by("-tweet_id").first()

        if latest_tweet:
            since = (
                arrow.get(latest_tweet.date, tzinfo=latest_tweet.timezone)
                .shift(days=-2)
                .format("YYYY-MM-DD")
            )
            tweet_config.Since = since

        twint.run.Search(tweet_config)

        Tweets_df = create_df(set(twint.output.tweets_list))

        if not Tweets_df.empty:
            thread_list = []
            for conversation_id in Tweets_df.conversation_id.unique():
                thread_df = Tweets_df[Tweets_df.conversation_id == conversation_id]
                if len(thread_df) > 1:
                    thread_df = thread_df.iloc[::-1]

                    tweet_list = []
                    for row in thread_df.itertuples():
                        if not row.tweet and not row.tweet.strip():
                            continue

                        tweet = models.Tweet(
                            tweet_id=row.id,
                            link=row.link,
                            date=row.date,
                            timezone=row.timezone,
                            text=row.tweet,
                            mentions=row.mentions,
                            urls=row.urls,
                            photos=row.photos,
                            nlikes=row.nlikes,
                            nreplies=row.nreplies,
                            nretweets=row.nretweets,
                            user=user,
                        )

                        try:
                            tweet.save()
                        except (
                            pymongo.errors.DuplicateKeyError,
                            mongoengine.errors.NotUniqueError,
                        ):
                            pass
                        else:
                            tweet_list.append(tweet)

                    if not tweet_list:
                        continue

                    thread = models.Thread.objects(
                        conversation_id=conversation_id,
                    ).first()

                    if not thread and not len(tweet_list) > 1:
                        continue
                    elif not thread:
                        thread = models.Thread(
                            conversation_id=conversation_id,
                            user=user,
                            tweets=tweet_list,
                        )

                    thread.tweets = list(set(thread.tweets + tweet_list))

                    try:
                        thread.save()
                    except (
                        pymongo.errors.DuplicateKeyError,
                        mongoengine.errors.NotUniqueError,
                    ):
                        pass

                    thread_list.append(thread)

            user.threads = list(set(user.threads + thread_list))
    finally:
        user.status = "None"
        user.save()
