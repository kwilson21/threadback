import datetime

import mongoengine


class Tweet(mongoengine.Document):
    tweet_id = mongoengine.LongField(required=True, unique=True)
    date = mongoengine.DateTimeField(default=datetime.datetime.utcnow, required=True)
    timezone = mongoengine.StringField(required=True)
    text = mongoengine.StringField(required=True)
    nlikes = mongoengine.IntField(required=True)
    nreplies = mongoengine.IntField(required=True)
    nretweets = mongoengine.IntField(required=True)
    user = mongoengine.ReferenceField("User")


class Thread(mongoengine.Document):
    conversation_id = mongoengine.LongField(required=True, unique=True)
    tweets = mongoengine.ListField(mongoengine.ReferenceField("Tweet"))
    user = mongoengine.ReferenceField("User")


class User(mongoengine.Document):
    user_id = mongoengine.LongField(unique=True)
    username = mongoengine.StringField(required=True, unique=True)
    threads = mongoengine.ListField(mongoengine.ReferenceField("Thread"))
    status = mongoengine.StringField(choices=("None", "Pending"), default="None")
