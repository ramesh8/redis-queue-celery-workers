import datetime
import os
import random
import time
import uuid
from pymongo import MongoClient


from celery import Celery, Task

# celery = Celery(__name__)
# celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379")
# celery.conf.result_backend = os.environ.get(
#     "CELERY_RESULT_BACKEND", "redis://localhost:6379"
# )


celery = Celery(__name__)
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://redis:6379")
celery.conf.result_backend = os.environ.get(
    "CELERY_RESULT_BACKEND", "redis://redis:6379"
)


class CallbackTask(Task):
    def on_success(self, retval, task_id, args, kwargs):
        """
        retval – The return value of the task.
        task_id – Unique id of the executed task.
        args – Original arguments for the executed task.
        kwargs – Original keyword arguments for the executed task.
        """
        print(retval, task_id, args, kwargs, "==[V]==")
        pass

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """
        exc – The exception raised by the task.
        task_id – Unique id of the failed task.
        args – Original arguments for the task that failed.
        kwargs – Original keyword arguments for the task that failed.
        """
        print(exc, task_id, args, kwargs, einfo, "---[#]--")
        pass


# it is from mq
def process_mail(mailid, sender, filecount):
    # mailreferenceid = uuid.uuid4()
    # fpath = f"{sender}-{filecount}-{id}.txt"
    for findex in range(filecount):
        # create celery task for each file
        print(f"creating celery task for {sender} file {findex}")
        process_file.delay(mailid, sender, findex)


@celery.task(name="create_task", base=CallbackTask)
def process_file(mailid, sender, findex):
    myjob = MyJob(mailid, sender, findex)
    myjob.run_stages()
    pass


class MyJob:
    def __init__(self, mailid, sender, findex):
        self.mailid = mailid
        self.sender = sender
        self.findex = findex
        mongo = MongoClient("mongodb://mongodbserver:27017/")
        db = mongo["asyncdemo"]
        self.mails = db["mails"]
        self.files = db["files"]
        self.stages = [
            {
                "name": "SE",
                "description": "Save Email",
                "time_min": 1,
                "time_max": 10,
                "order": 1,
            },
            {
                "name": "SA",
                "description": "Save Attachment",
                "time_min": 10,
                "time_max": 100,
                "order": 2,
            },
            {
                "name": "Conv",
                "description": "Conversion",
                "time_min": 0,
                "time_max": 100,
                "order": 3,
            },
            {
                "name": "Ext",
                "description": "Extraction",
                "time_min": 10,
                "time_max": 200,
                "order": 4,
            },
            {
                "name": "GBO",
                "description": "Generate Bill Object",
                "time_min": 10,
                "time_max": 20,
                "order": 5,
            },
        ]

    def run_stages(self):
        fileid = str(uuid.uuid4())
        # we can use message queue here instead of loop
        for stage in self.stages:
            fileobj = {
                "fileid": fileid,
                "sender": self.sender,
                "index": self.findex,
                "stage": stage,
                "timestamp": datetime.datetime.utcnow(),
                "mail_id": self.mailid,
            }
            print(fileobj)
            self.files.update_one({"fileid": fileid}, {"$set": fileobj}, upsert=True)
            waittime = random.randint(stage["time_min"], stage["time_max"])
            time.sleep(waittime)

    # def print_number(self, start, end, sender, message):
    #     print("----------------[starting job]----------------")
    #     id = uuid.uuid4()
    #     fpath = f"{sender}-{message}-{id}.txt"
    #     with open(fpath, "w+", encoding="utf-8") as f:
    #         f.write(f"sent by {sender}\n message : {message}\n")
    #         for i in range(start, end):
    #             f.write("*" * i)
    #             f.write("\n")
    #             time.sleep(1)
    #     print("----------------[finished job]----------------")
