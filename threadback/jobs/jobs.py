import arrow
import pandas as pd
import pymongo
import twint
from twitter_scraper import Profile

from threadback.app import huey
from threadback.models import models


@huey.task()
def refresh_user_threads(username):
    user = models.User.objects(username=username).first()

    if not user:
        try:
            twitter_user = Profile(username)
        except IndexError:
            raise Exception("User does not exist!")
        else:
            user = models.User(username=username)

    user.status = "Pending"
    user.save()

    tweet_config = twint.Config()
    tweet_config.Username = username
    tweet_config.Pandas = True
    tweet_config.Pandas_clean = True
    tweet_config.Pandas_au = True
    tweet_config.Hide_output = True

    try:
        latest_tweet = user.threads[-1].tweets[-1]
    except IndexError:
        pass
    else:
        since = (
            arrow.get(latest_tweet.date).shift(days=-1).format("YYYY-MM-DD HH:mm:ss")
        )
        tweet_config.Since = since

    twint.run.Search(tweet_config)

    Tweets_df = twint.storage.panda.Tweets_df.copy(deep=True)

    if not Tweets_df.empty:
        thread_list = []
        conversation_ids = []
        for conversation_id in Tweets_df.conversation_id:
            if (
                len(
                    (
                        thread_df := Tweets_df[
                            Tweets_df.conversation_id == conversation_id
                        ]
                    ),
                )
                > 1
                and conversation_id not in conversation_ids
            ):
                thread_df = thread_df.iloc[::-1]

                tweet_list = []
                for row in thread_df.itertuples():
                    tweet = models.Tweet(
                        tweet_id=row.id,
                        date=row.date,
                        timezone=row.timezone,
                        text=row.tweet,
                        nlikes=row.nlikes,
                        nreplies=row.nreplies,
                        nretweets=row.nretweets,
                        user=user,
                    )

                    try:
                        tweet.save()
                    except pymongo.errors.DuplicateKeyError:
                        pass
                    else:
                        tweet_list.append(tweet)

                thread = models.Thread(
                    conversation_id=conversation_id, user=user, tweets=tweet_list,
                )

                try:
                    thread.save()
                except pymongo.errors.DuplicateKeyError:
                    pass
                else:
                    thread_list.append(thread)

                conversation_ids.append(conversation_id)

        user.update(
            threads=thread_list, user_id=Tweets_df.iloc[0].user_id, status="None",
        )
