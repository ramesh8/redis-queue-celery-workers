from pathlib import Path
import uuid
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from rq import Queue
from redis import Redis
from pymongo import MongoClient
from worker import process_mail
import os
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

BASE_PATH = Path(__file__).resolve().parent
TEMPLATES = Jinja2Templates(directory=str(BASE_PATH / "templates"))


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
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
files = db["files"]


@app.get("/", response_class=JSONResponse)
def index(request: Request):
    # return {"success": True, "message": "hello world"}
    ms = mails.find({}).sort("_id", -1)

    mslist = []
    for m in ms:
        fs = files.find({"mail_id": m["mail_id"]}).sort("_id", 1)
        if fs != None:
            m["files"] = list(fs)
            m["status"] = all(f["stage"]["name"] == "GBO" for f in m["files"])
        mslist.append(m)

    return TEMPLATES.TemplateResponse(
        "index.html",
        {"request": request, "mails": mslist},
    )


class JobData(BaseModel):
    # start: int = 0
    # end: int = 10
    sender: str = "Ramesh"
    # message: str = "Hello"
    filecount: int = 1


@app.post("/job", response_class=JSONResponse)
def post_job(request: Request, jobdata: JobData):
    mailid = str(uuid.uuid4())
    # start = jobdata.start
    # end = jobdata.end
    sender = jobdata.sender
    # message = jobdata.message
    filecount = jobdata.filecount
    # print_number
    # job = task_queue.enqueue(jobs.print_number, start, end, sender, message)
    job = task_queue.enqueue(process_mail, mailid, sender, filecount)
    # job = process_mail(sender, filecount)
    mailobj = {
        "mail_id": mailid,
        "sender": sender,
        "filecount": filecount,
        "status": False,
    }
    mails.insert_one(mailobj)
    return {"success": True, "message": "job placed on queue", "id": job.id}
