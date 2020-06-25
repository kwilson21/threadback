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
                "id": int(tweet.id),
                "conversation_id": int(tweet.conversation_id),
                "date": arrow.get(dt).format("YYYY-MM-DD HH:mm:ss"),
                "timezone": tweet.timezone,
                "tweet": tweet.tweet,
                "mentions": tweet.mentions,
                "urls": tweet.urls,
                "photos": tweet.photos,
                "username": tweet.username,
                "link": tweet.link,
                "nlikes": int(tweet.likes_count),
                "nreplies": int(tweet.replies_count),
                "nretweets": int(tweet.retweets_count),
                "video": tweet.video,
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
        tweet_config.Custom["tweet"] = [
            "id",
            "conversation_id",
            "date",
            "timezone",
            "tweet",
            "mentions",
            "urls",
            "photos",
            "username",
            "link",
            "nlikes",
            "nreplies",
            "nretweets",
        ]
        tweet_config.Filter_retweets = True

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
                thread_df = Tweets_df[
                    Tweets_df.conversation_id == conversation_id
                ].drop_duplicates("id")
                if (
                    len(thread_df) > 1
                    and not Tweets_df[Tweets_df.id == conversation_id].empty
                ):
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
                            video=row.video,
                            nlikes=row.nlikes,
                            nreplies=row.nreplies,
                            nretweets=row.nretweets,
                            user=user,
                        )

                        try:
                            tweet.save(cascade=True)
                        except (
                            pymongo.errors.DuplicateKeyError,
                            mongoengine.errors.NotUniqueError,
                        ):
                            pass

                        tweet_list.append(tweet)

                    thread = models.Thread.objects(
                        conversation_id=conversation_id,
                    ).first()

                    if thread:
                        thread.save(
                            push_all__tweets=[
                                tweet
                                for tweet in tweet_list
                                if tweet not in thread.tweets
                            ],
                            cascade=True,
                        )
                    elif not thread and not len(tweet_list) > 1:
                        continue
                    elif not thread:
                        thread = models.Thread(
                            conversation_id=conversation_id,
                            user=user,
                            tweets=tweet_list,
                        )
                        thread.save(cascade=True)

                    thread_list.append(thread)

            user.save(
                push_all__threads=[
                    thread for thread in thread_list if thread not in user.threads
                ],
            )
    finally:
        user.status = "None"
        user.save(cascade=True)
