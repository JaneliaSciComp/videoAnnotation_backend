import os
from datetime import datetime
import logging
from fastapi import FastAPI, Form



#set up logger
logger = logging.getLogger('video_annotation')
logger.setLevel(logging.DEBUG)
log_handler = logging.StreamHandler()
# to print out source code location: %(pathname)s %(lineno)d:
log_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s: %(message)s'))
logger.addHandler(log_handler)

app = FastAPI()



#@app.post("/api/videopath")
#async def videopathHandler(videoPath: str=Form()):

