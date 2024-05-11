import os
from sys import getsizeof
from datetime import datetime
import logging
from fastapi import FastAPI, Form, status, HTTPException
from pydantic import BaseModel, BeforeValidator, Field
from fastapi.responses import FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import cv2 as cv
import json
# import psycopg
from motor import motor_asyncio
from pymongo import ReturnDocument
from configparser import ConfigParser
from typing import Union, List
from typing_extensions import Annotated
from contextlib import asynccontextmanager


#set up logger
logger = logging.getLogger('video_annotation')
logger.setLevel(logging.DEBUG)
log_handler = logging.StreamHandler()
# to print out source code location: %(pathname)s %(lineno)d:
log_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s: %(message)s'))
logger.addHandler(log_handler)



######## data model ########
ObjectId = Annotated[str, BeforeValidator(str)]

class AdditionalField(BaseModel):
    name: str
    value: Union[str, None] = None
    
class VideoConfigObj(BaseModel):
    videoId: ObjectId = Field(serialization_alias="_id")
    projectId: ObjectId
    name: str = Field(max_length=200)
    path: str
    additionalFields: List[AdditionalField] = []




######### create connection to db ########
def config(section, filename='../database.ini'): 
    #section matches the section name, the first line, in database.int
    parser = ConfigParser()
    parser.read(filename)
    db_params = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db_params[param[0]] = param[1]
    else:
        raise Exception(f'Section {section} not found in the {filename} file')
    return db_params


@asynccontextmanager
async def lifespan(app: FastAPI):
    # connect to db
    try:
        # for postgreSQL
    #     params = config('postgresql')
    #     logger.info('Connecting to the PostgreSQL database...')
    #     conn = psycopg.connect(**params)
    #     cur = conn.cursor()
    #     cur.execute('SELECT current_schema()')
    #     schema = cur.fetchone()
    #     logger.info(f'Current schema: {schema}')
        
        # for mongodb
        settings = config('mongodb')
        url = f"mongodb://{settings['user']}:{settings['password']}@{settings['host']}"
        client = motor_asyncio.AsyncIOMotorClient(url)
        app.mongodb = client.get_database(settings['dbname'])
        app.mongodb.project_config = app.mongodb.get_collection("configuration")
        app.mongodb.video = app.mongodb.get_collection("video")
    
        yield
        # disconnect with db
        client.close()
    except Exception as e:
        logger.info('error', e)



######## launch api server ########
app = FastAPI(lifespan=lifespan)


# for CORS, backend server allow these origins to send request and access the response
origins = ['http://localhost:3000']
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)




######### routes ########

cap = None

@app.post(
    "/api/video",
    response_description="Add new video",
    # response_model=VideoInfoObj,
    status_code=status.HTTP_201_CREATED,
    # response_model_by_alias=False,
)
async def postVideoHandler(video_config_obj: VideoConfigObj):  #str= Form()):
    logger.debug("Post: /api/video")
    # logger.debug(video_config_obj)
    try:
        # print(video_config_obj.model_dump(by_alias=True)) # {'_id': '...', 'projectId': 'testId', 'name': '/Users/pengxi/video/numbered.mp4', 'path': '/Users/pengxi/video/numbered.mp4', 'additionalFields': []}
        videoId = video_config_obj.videoId
        existing_video = await app.mongodb.video.find_one({"_id": videoId})
        if existing_video is None:
            new_video = await app.mongodb.video.insert_one(
                video_config_obj.model_dump(by_alias=True)
                )
            check = await app.mongodb.video.find_one({"_id": new_video.inserted_id})
            print(check)
            # print(new_video) # InsertOneResult('1715271938193', acknowledged=True)
            return {'success': f'Inserted video {new_video.inserted_id}'}
        else:
            return {'info': 'Video already exists'}
        
        
    except Exception as e:
        print('error')
        return error_handler(e)


@app.get("/api/video")
async def getVideoHandler(id: ObjectId):
    logger.debug(f"Get: /api/video?id={id}")
    try:
        res = await app.mongodb.video.find_one({"_id": id}, { "_id": 0, "path": 1 })
        print(res, res['path'])
        path = res['path']
        # res = readVideoMetaFromPath(res['path'])
        # return res
        global cap
        if not os.path.exists(path):
            return {'error': 'Video file does not exist'}
        if cap:
            cap.release()
        cap = cv.VideoCapture(path)
        return {'frame_count': cap.get(cv.CAP_PROP_FRAME_COUNT), 'fps': cap.get(cv.CAP_PROP_FPS)}
    except Exception as e:
        print('error')
        return error_handler(e)


@app.put(
    "/api/video",
    response_description="Edit video",
    # response_model=VideoConfigObj,
    # response_model_by_alias=False,
)
async def editVideoHandler(new_video_obj: VideoConfigObj):  #str= Form()):
    logger.debug("Put: /api/video")
    # logger.debug(video_config_obj)
    try:
        # print(video_config_obj.model_dump(by_alias=True)) # {'_id': '...', 'projectId': 'testId', 'name': '/Users/pengxi/video/numbered.mp4', 'path': '/Users/pengxi/video/numbered.mp4', 'additionalFields': []}
        new_data = new_video_obj.model_dump(by_alias=True)
        update_result = await app.mongodb.video.find_one_and_update(            
            {"_id": new_data['_id']},
            {"$set": new_data},
            return_document=ReturnDocument.AFTER,
        )
        print(update_result)
        if update_result is not None:
            return update_result
        else:
            return {'error': 'Editing failed'}

    except Exception as e:
        print('error')
        return error_handler(e)


@app.delete(
    "/api/video",
    response_description="Edit video",
    # response_model=VideoConfigObj,
    # response_model_by_alias=False,
)
async def deleteVideoHandler(id: ObjectId):  #str= Form()):
    logger.debug(f"Delete: /api/video?id={id}")
    # logger.debug(video_config_obj)
    try:
        # print(video_config_obj.model_dump(by_alias=True)) # {'_id': '...', 'projectId': 'testId', 'name': '/Users/pengxi/video/numbered.mp4', 'path': '/Users/pengxi/video/numbered.mp4', 'additionalFields': []}
        delete_result = await app.mongodb.video.delete_one({"_id": ObjectId(id)})
        print(delete_result, delete_result.deleted_count)
        if delete_result.deleted_count == 1:
            return {'success': f'Deleted video {id}'}
        else:
            return {'error': 'Deleting video failed.'}

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
    

@app.get('/api/additional-data/{name}')
async def getAdditionalData(name: str, videoId: str, num: int):
    # num in request already -1, so start from 0
    logger.debug(f'api/additional-data/{name}?videoId={videoId}&num={num}')
    try:
        # if num < 0 or num > frame_count-1:
        if num < 0:
            return {'error': 'Frame number out of bound'}
        #TODO: read and return data
        return 'currently no data'
        # else:
        #     return {'error': f'Frame {num+1} reached video end'}
    except Exception as e:
        print('error')
        return error_handler(e)



######## helper function ########

def error_handler(err):
    logger.error(err)
    # f = open('../log/log.txt','a')
    # traceback.print_exc(file=f)
    # f.close()
    return {'error': ', '.join(list(err.args))}


# def readVideoMetaFromPath(path):
#     # read meta info
#     try:
#         global cap
#         if not os.path.exists(path):
#             return {'error': 'Video file does not exist'}
#         if cap:
#             cap.release()
#         cap = cv.VideoCapture(path)
#         return {'frame_count': cap.get(cv.CAP_PROP_FRAME_COUNT), 'fps': cap.get(cv.CAP_PROP_FPS)}
#     except Exception as e:
#         print('error')
#         return error_handler(e)

