import os
from sys import getsizeof
from datetime import datetime
import logging
from fastapi import FastAPI, Form
from fastapi.responses import FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import cv2 as cv
import json
import psycopg
from configparser import ConfigParser


#set up logger
logger = logging.getLogger('video_annotation')
logger.setLevel(logging.DEBUG)
log_handler = logging.StreamHandler()
# to print out source code location: %(pathname)s %(lineno)d:
log_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s: %(message)s'))
logger.addHandler(log_handler)


######### create connection to db ########
def config(filename='../database.ini', section='postgresql'): #section matches the section name, the first line, in database.int
    # create a parser
    parser = ConfigParser()
    # read config file
    parser.read(filename)

    # get section, default to postgresql
    db_params = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db_params[param[0]] = param[1]
    else:
        raise Exception('Section {0} not found in the {1} file'.format(section, filename))

    return db_params


try:
    params = config()
    logger.info('Connecting to the PostgreSQL database...')
    conn = psycopg.connect(**params)
    cur = conn.cursor()
    cur.execute('SELECT current_schema()')
    schema = cur.fetchone()
    logger.info(f'Current schema: {schema}')
except (Exception, psycopg.DatabaseError) as error:
    logger.error(error)



######## launch api server ########
app = FastAPI()

cap = None

# for CORS, backend server allow these origins to send request and access the response
origins = ['http://localhost:3000']
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


def error_handler(err):
    logger.error(err)
    # f = open('../log/log.txt','a')
    # traceback.print_exc(file=f)
    # f.close()
    return {'error': ', '.join(list(err.args))}

@app.post("/api/videopath")
async def videopathHandler(video_path: str= Form()):
    logger.debug("/api/videopath")
    logger.debug(video_path)
    try:
        global cap
        if not os.path.exists(video_path):
            return {'error': 'Video file does not exist'}
        if cap:
            cap.release()
        cap = cv.VideoCapture(video_path)
        return {'frame_count': cap.get(cv.CAP_PROP_FRAME_COUNT), 'fps': cap.get(cv.CAP_PROP_FPS)}
    except Exception as e:
        print('error')
        return error_handler(e)
    


@app.get('/api/frame')
async def getFrame(num: int):
    # num in request already -1, so start from 0
    logger.debug(f'api/frame?num={num}')
    try:
        # if num < 0 or num > frame_count-1:
        if num < 0:
            return {'error': 'Frame number out of bound'}
        cap.set(cv.CAP_PROP_POS_FRAMES, num)
        # logger.debug(f'cursor1: {cap.get(cv.CAP_PROP_POS_FRAMES)}')
        ret, frame = cap.read()
        # logger.debug(f'cursor2: {cap.get(cv.CAP_PROP_POS_FRAMES)}')
        if ret:
            ret, frame_1d = cv.imencode('.jpg', frame) 
            # return Response(content=frame_1d, media_type='image/jpg')
            headers = {'Content-Disposition': f'inline; filename=f_{num}.jpg'}
            return Response(frame_1d.tobytes() , headers=headers, media_type='image/jpg')
        else:
            return {'error': f'Frame {num+1} reached video end'}
    except Exception as e:
        print('error')
        return error_handler(e)
    

