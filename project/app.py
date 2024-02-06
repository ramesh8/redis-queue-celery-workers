import uuid
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from rq import Queue
from redis import Redis
from pymongo import MongoClient
from worker import process_mail
import os

app = FastAPI()
mq_conn = Redis(host="redis", port=6379, db=0)
task_queue = Queue("task_queue", connection=mq_conn)
# jobs = ProcessStages()
# celery = Celery(__name__)
# celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379")
# celery.conf.result_backend = os.environ.get(
#     "CELERY_RESULT_BACKEND", "redis://localhost:6379"
# )


mongo = MongoClient("mongodb://mongodbserver:27017/")
db = mongo["asyncdemo"]
mails = db["mails"]


@app.get("/", response_class=JSONResponse)
def index(request: Request):
    return {"success": True, "message": "hello world"}


class JobData(BaseModel):
    # start: int = 0
    # end: int = 10
    sender: str = "Ramesh"
    # message: str = "Hello"
    filecount: int = 1


@app.post("/job", response_class=JSONResponse)
def post_job(request: Request, jobdata: JobData):
    # jobid = str(uuid.uuid4())
    # start = jobdata.start
    # end = jobdata.end
    sender = jobdata.sender
    # message = jobdata.message
    filecount = jobdata.filecount
    # print_number
    # job = task_queue.enqueue(jobs.print_number, start, end, sender, message)
    job = task_queue.enqueue(process_mail, sender, filecount)
    # job = process_mail(sender, filecount)
    mailobj = {"mail_job_id": job.id, "sender": sender, "filecount": filecount}
    mails.insert_one(mailobj)
    return {"success": True, "message": "job placed on queue", "id": job.id}
