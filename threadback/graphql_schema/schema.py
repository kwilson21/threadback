from enum import Enum
from typing import Generic, List, Optional, Sequence, TypeVar

import strawberry
from rq import Queue
from twitter_scraper import Profile

from threadback.app import conn
from threadback.jobs import jobs
from threadback.models import models

T = TypeVar("T")


@strawberry.type
class Paginated(Generic[T]):
    items: List[T]
    count: Optional[int] = None

    @classmethod
    def paginate(cls, data: Sequence[T], offset: int, limit: Optional[int]):
        return Paginated(data.skip(offset).limit(limit), data.count())


@strawberry.type
class Connection(Generic[T]):
    items: List[T]
    count: Optional[int] = None

    @classmethod
    def paginate(cls, data: Sequence[T], offset: int, limit: Optional[int]):
        return Connection(data.skip(offset).limit(limit), data.count())


@strawberry.enum
class Direction(Enum):
    ASC = "asc"
    DESC = "desc"


@strawberry.enum
class Sort(Enum):
    TWEET_ID = "tweet_id"
    DATE = "date"
    CONVERSATION_ID = "conversation_id"
    USER_ID = "user_id"
    USERNAME = "username"
    STATUS = "status"


@strawberry.input
class Ordering:
    sort: Optional[Sort] = None
    direction: Optional[Direction] = None


@strawberry.type(description="A tweet by a Twitter user")
class Tweet:
    tweet_id: strawberry.ID = None
    link: str = None
    date: strawberry.DateTime = None
    timezone: str = None
    text: str = None
    mentions: List[str] = None
    urls: List[str] = None
    photos: List[str] = None
    video: bool = None
    nlikes: int = None
    nreplies: int = None
    nretweets: int = None
    user: "User" = None


@strawberry.type(
    description="Tweets with a string of replies to each other by a Twitter user",
)
class Thread:
    conversation_id: strawberry.ID = None
    user: "User" = None
    tweets: List[Tweet] = None


@strawberry.type(description="A Twitter user")
class User:
    user_id: strawberry.ID = None
    username: str = None
    bio: str = None
    profile_photo: str = None
    status: str = None

    @strawberry.field(description="Return twitter threads for a given user")
    def threads(
        self,
        info,
        conversation_ids: List[strawberry.ID] = None,
        offset: Optional[int] = 0,
        limit: Optional[int] = 5,
        order_by: Optional[Ordering] = None,
    ) -> Connection[Thread]:
        query_set = models.Thread.objects(user=self)

        if order_by:
            if order_by.direction is Direction.DESC:
                direction_str = "-"
            elif order_by.direction is Direction.ASC:
                direction_str = "+"

            order_by_str = "{dir}{sort}".format(
                dir=direction_str, sort=order_by.sort.value,
            )

            res = query_set.order_by(order_by_str)
        else:
            res = query_set.order_by("-conversation_id")

        return Connection.paginate(res, offset, limit)


@strawberry.type
class Query:
    @strawberry.field(
        description="Return a list of twitter users with available threads",
    )
    def users(
        self,
        info,
        usernames: List[str] = None,
        user_ids: List[strawberry.ID] = None,
        offset: Optional[int] = 0,
        limit: Optional[int] = 5,
        order_by: Optional[Ordering] = None,
    ) -> Paginated[User]:
        if usernames and user_ids:
            raise ValueError("Cannot specify both names and user ids!")

        kwargs = {}

        if usernames:
            kwargs["username__in"] = usernames
        elif user_ids:
            kwargs["user_id__in"] = user_ids

        if order_by:
            if order_by.direction is Direction.DESC:
                direction_str = "-"
            elif order_by.direction is Direction.ASC:
                direction_str = "+"

            order_by_str = "{dir}{sort}".format(
                dir=direction_str, sort=order_by.sort.value,
            )

            res = models.User.objects(**kwargs).order_by(order_by_str)
        else:
            res = models.User.objects(**kwargs).order_by("-username")

        return Paginated.paginate(res, offset, limit)

    @strawberry.field(description="Return twitter threads")
    def threads(
        self,
        info,
        usernames: List[str] = None,
        user_ids: List[strawberry.ID] = None,
        conversation_ids: List[strawberry.ID] = None,
        offset: Optional[int] = 0,
        limit: Optional[int] = 5,
        order_by: Optional[Ordering] = None,
    ) -> Paginated[Thread]:
        # if (
        #     usernames
        #     and (user_ids or conversation_ids)
        #     or user_ids
        #     and (usernames or conversation_ids)
        # ):
        #     raise ValueError(
        #         "usernames, user_ids and conversation_ids are mutually exclusive!"
        #     )

        if usernames:
            user = models.User.objects(username__in=usernames).first()
            query_set = models.Thread.objects(user=user)
        elif user_ids:
            user = models.User.objects(user_id__in=user_ids).first()
            query_set = models.Thread.objects(user=user)
        elif conversation_ids:
            query_set = models.Thread.objects(conversation_id__in=conversation_ids)
        else:
            query_set = models.Thread.objects()

        if order_by:
            if order_by.direction is Direction.DESC:
                direction_str = "-"
            elif order_by.direction is Direction.ASC:
                direction_str = "+"

            order_by_str = "{dir}{sort}".format(
                dir=direction_str, sort=order_by.sort.value,
            )

            res = query_set.order_by(order_by_str)
        else:
            res = query_set.order_by("-conversation_id")

        return Paginated.paginate(res, offset, limit)

    @strawberry.field(description="Return tweets")
    def tweets(
        self,
        info,
        usernames: List[str] = None,
        user_ids: List[strawberry.ID] = None,
        tweet_ids: Optional[List[strawberry.ID]] = None,
        offset: Optional[int] = 0,
        limit: Optional[int] = 9999,
        order_by: Optional[Ordering] = None,
    ) -> Paginated[Tweet]:
        # if (
        #     usernames
        #     and (tweet_ids or tweet_ids)
        #     or tweet_ids
        #     and (usernames or tweet_ids)
        # ):
        #     raise ValueError(
        #         "usernames, tweet_ids and tweet_ids are mutually exclusive!"
        #     )

        if usernames:
            user = models.User.objects(username__in=usernames).first()
            query_set = models.Tweet.objects(user=user)
        elif user_ids:
            user = models.User.objects(user_id__in=user_ids).first()
            query_set = models.Tweet.objects(user=user)
        elif tweet_ids:
            query_set = models.Tweet.objects(tweet_id__in=tweet_ids)

        if order_by:
            if order_by.direction is Direction.DESC:
                direction_str = "-"
            elif order_by.direction is Direction.ASC:
                direction_str = "+"

            order_by_str = "{dir}{sort}".format(
                dir=direction_str, sort=order_by.sort.value,
            )

            res = query_set.order_by(order_by_str)
        else:
            res = query_set.order_by("-tweet_id")

        return Paginated.paginate(res, offset, limit)


@strawberry.type
class Mutation:
    @strawberry.field(description="Refresh tweets and threads for a given user")
    def refresh(
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
                user = models.User(
                    username=username,
                    user_id=twitter_user.user_id,
                    bio=twitter_user.biography,
                    profile_photo=twitter_user.profile_photo,
                )
        else:
            twitter_user = Profile(username)

        if user.threads:
            queue_type = "low"
        else:
            queue_type = "high"

        q = Queue(queue_type, connection=conn)

        user.status = "Pending"
        user.bio = twitter_user.biography
        user.profile_photo = twitter_user.profile_photo
        user.save()

        q.enqueue(jobs.refresh_user_threads, username, job_timeout="3h")

        return user


schema = strawberry.Schema(query=Query, mutation=Mutation)
