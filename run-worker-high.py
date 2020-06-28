from rq import Connection, Queue
from rq.worker import HerokuWorker as Worker

from threadback.app import conn

if __name__ == "__main__":
    with Connection(conn):
        worker = Worker(Queue("high"))
        worker.work()
