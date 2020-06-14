import time
from typing import List, Union

import strawberry

from threadback.jobs import jobs
from threadback.models import models


@strawberry.type
class Tweet:
    tweet_id: strawberry.ID = None
    date: strawberry.DateTime = None
    timezone: str = None
    text: str = None
    nlikes: int = None
    nreplies: int = None
    nretweets: int = None


@strawberry.type
class Thread:
    conversation_id: strawberry.ID = None
    tweets: List[Tweet] = None


@strawberry.type
class User:
    user_id: strawberry.ID = None
    username: str = None
    threads: List[Thread] = None
    status: str = None


@strawberry.input
class TweetInput:
    tweet_ids: List[strawberry.ID] = None


@strawberry.type
class Query:
    @strawberry.field
    def get_users(
        self, info, usernames: List[str] = None, user_ids: List[strawberry.ID] = None,
    ) -> List[User]:
        if usernames and user_ids:
            raise ValueError("Cannot specify both names and user ids!")

        kwargs = {}

        if usernames:
            kwargs["username__in"] = usernames
        elif user_ids:
            kwargs["user_id__in"] = user_ids

        return models.User.objects(**kwargs)

    @strawberry.field
    def get_threads(self, info, conversation_ids: List[strawberry.ID]) -> List[Thread]:
        return models.Thread.objects(conversation_id__in=conversation_ids)

    @strawberry.field
    def get_tweets(self, info, input_field: TweetInput) -> Tweet:
        kwargs = {}

        if input_field.tweet_ids:
            kwargs["tweet_id__in"] = input_field.tweet_ids

        return models.Tweet.objects(**kwargs)


@strawberry.type
class Mutation:
    @strawberry.field
    def refresh_user_threads(
        self, info, username: str = None, user_id: strawberry.ID = None,
    ) -> User:
        if not username and not user_id or username and user_id:
            raise ValueError("You must specify either a username or user id!")

        kwargs = {}
        if username:
            kwargs["username"] = username
        elif user_id:
            kwargs["user_id"] = user_id

        user = models.User.objects(**kwargs).first()

        if not user:
            try:
                twitter_user = Profile(username)
            except IndexError:
                raise Exception("User does not exist!")
            else:
                user = models.User(username=username, user_id=twitter_user.user_id)

        if user.status != "Pending":
            user.status = "Pending"
            user.save()
            jobs.refresh_user_threads(username=username)

        return user


schema = strawberry.Schema(query=Query, mutation=Mutation)
