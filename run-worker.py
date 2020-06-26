from rq import Connection, Queue
from rq.worker import HerokuWorker as Worker

from threadback.app import conn

listen = ["high", "default", "low"]

if __name__ == "__main__":
    with Connection(conn):
        worker = Worker(map(Queue, listen))
        worker.work()
