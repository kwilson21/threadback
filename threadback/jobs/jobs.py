import arrow
import mongoengine
import pymongo
import twint

from threadback.app import huey
from threadback.models import models


@huey.task()
def refresh_user_threads(username):
    user = models.User.objects(username=username).first()

    tweet_config = twint.Config()
    tweet_config.Username = username
    tweet_config.Pandas = True
    tweet_config.Hide_output = True

    latest_tweet = models.Tweet.objects(user=user).order_by("-date").first()

    if latest_tweet:
        since = (
            arrow.get(latest_tweet.date)
            .shift(days=-1)
            .replace(hour=0, minute=0, second=0)
            .format("YYYY-MM-DD HH:mm:ss")
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
                        link=row.link,
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
                    except (
                        pymongo.errors.DuplicateKeyError,
                        mongoengine.errors.NotUniqueError,
                    ):
                        pass
                    else:
                        tweet_list.append(tweet)

                thread = models.Thread.objects(conversation_id=conversation_id).first()

                if not thread:
                    thread = models.Thread(
                        conversation_id=conversation_id, user=user, tweets=tweet_list,
                    )
                else:
                    thread.tweets = list(set(thread.tweets + tweet_list))

                try:
                    thread.save()
                except (
                    pymongo.errors.DuplicateKeyError,
                    mongoengine.errors.NotUniqueError,
                ):
                    pass

                thread_list.append(thread)

                conversation_ids.append(conversation_id)

        user.threads = list(set(user.threads + thread_list))

        user.status = "None"

        user.save()
