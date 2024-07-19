import os
from sys import getsizeof
from datetime import datetime
import logging
from fastapi import FastAPI, Form, status, HTTPException
# from pydantic import BaseModel, BeforeValidator, Field
from fastapi.responses import FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import cv2 as cv
import json
# import psycopg
from motor import motor_asyncio
from pymongo import ReturnDocument
from configparser import ConfigParser
# from typing import Union, List
# from typing_extensions import Annotated
from contextlib import asynccontextmanager
from datamodel import ObjectId, ProjectFromClient, ProjectFromDB, ProjectCollection, BtnGroupFromClient, BtnGroupFromDB, BtnGroupCollectionFromDB, BtnGroupCollectionFromClient, VideoFromClient, VideoFromDB, VideoCollectionFromDB, VideoCollectionFromClient, AdditionalField, AnnotationFromClient, AnnotationCollectionFromClient, AnnotationCollectionFromDB, ProjectAnnotationCollectionFromDB, ProjectAnnotationCollectionFromClient
from customized import getAdditionalDataReader, getAdditionalData

#set up logger
logger = logging.getLogger('video_annotation')
logger.setLevel(logging.DEBUG)
log_handler = logging.StreamHandler()
# to print out source code location: %(pathname)s %(lineno)d:
log_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s: %(message)s'))
logger.addHandler(log_handler)




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

@app.post(
    "/api/project",
    response_description="Add new project",
    # response_model=VideoInfoObj,
    # status_code=status.HTTP_201_CREATED,
    # response_model_by_alias=False,
)
async def postProjectHandler(project_config_obj: ProjectFromClient):  #str= Form()):
    logger.debug("Post: /api/project")
    # logger.debug(video_config_obj)
    try:
        return await post_one_obj_mongo(project_config_obj, 'project')
    
    except Exception as e:
        print('error')
        return error_handler(e)

@app.put(
    "/api/project",
    response_description="Edit project",
    # response_model=VideoConfigObj,
    # response_model_by_alias=False,
)
async def editProjectHandler(new_project_obj: ProjectFromClient):  #str= Form()):
    logger.debug("Put: /api/project")
    # logger.debug(project_config_obj)
    try:
        # print(project_config_obj.model_dump(by_alias=True)) # {'_id': '...', 'projectId': 'testId', 'name': '/Users/pengxi/video/numbered.mp4', 'path': '/Users/pengxi/video/numbered.mp4', 'additionalFields': []}
        res = await edit_one_obj_mongo(new_project_obj, 'project')
        if res.get('error'): # possibly there is no existing project thus editing failed
            post_res = await post_one_obj_mongo(new_project_obj, 'project')
            return post_res
        return res
    except Exception as e:
        print('error')
        return error_handler(e)

@app.get("/api/projects",
         response_description="List all projects",
         response_model=ProjectCollection,
         response_model_by_alias=False)
async def getAllProjectsHandler():
    logger.debug("Get: /api/projects")
    try:
        res = await app.mongodb.project.find().to_list(None)
        print(res)
        # if res is None or len(res)==0:
        #     return {'error': 'No project is found.'}
        # else:
        return ProjectCollection(projects=res) 
    except Exception as e:
        print('error')
        return error_handler(e)

@app.get("/api/project",
         response_description="Find one project",
         response_model=ProjectFromDB,
         response_model_by_alias=False)
async def getProject(id: ObjectId):
    logger.debug(f"Get: /api/project?id={id}")
    try:
        res = await app.mongodb.project.find_one({"_id": id})
        print(res)
        if res is None:
            return {'error': 'No project is found'}
        return res
    except Exception as e:
        print('error')
        return error_handler(e)

@app.delete(
    "/api/project",
    response_description="Delete one project"
)
async def deleteProjectHandler(id: ObjectId):  
    logger.debug(f"Delete: /api/project?id={id}")
    # logger.debug(video_config_obj)
    try:
        # print(video_config_obj.model_dump(by_alias=True)) # {'_id': '...', 'projectId': 'testId', 'name': '/Users/pengxi/video/numbered.mp4', 'path': '/Users/pengxi/video/numbered.mp4', 'additionalFields': []}
        return await delete_one_obj_mongo(id, 'project')

    except Exception as e:
        print('error')
        return error_handler(e)


@app.post(
    "/api/btn",
    response_description="Add new btn group",
    # response_model=VideoInfoObj,
    # status_code=status.HTTP_201_CREATED,
    # response_model_by_alias=False,
)
async def postBtnHandler(btn_group_obj: BtnGroupFromClient): 
    logger.debug("Post: /api/btn")
    # logger.debug(btn_group_obj)
    try:
        print(btn_group_obj)
        res = await post_one_obj_mongo(btn_group_obj, 'btn')
        print('post btn res: ', res)
        if res.get('info') == 'btn already exists':
            edit_res = await edit_one_obj_mongo(btn_group_obj, 'btn')
            return edit_res
        return res
    except Exception as e:
        print('error')
        return error_handler(e)

@app.delete(
    "/api/btn",
    response_description="Delete Btn Group"
)
async def deleteBtnGroupHandler(btnGroupId: ObjectId):  #str= Form()):
    logger.debug(f"Delete: /api/btn?btnGroupId={btnGroupId}")
    # logger.debug(video_config_obj)
    try:
        # print(video_config_obj.model_dump(by_alias=True)) # {'_id': '...', 'projectId': 'testId', 'name': '/Users/pengxi/video/numbered.mp4', 'path': '/Users/pengxi/video/numbered.mp4', 'additionalFields': []}
        return await delete_one_obj_mongo(btnGroupId, 'btn')
    except Exception as e:
        print('error')
        return error_handler(e)

@app.get("/api/btns",
         response_description="Find project btn configuration data",
         response_model=BtnGroupCollectionFromDB,
         response_model_by_alias=False)
async def getProjectBtn(projectId: ObjectId):
    logger.debug(f"Get: /api/btns?projectId={projectId}")
    try:
        res = await app.mongodb.btn.find({"projectId": projectId}).to_list(None)
        print(res)
        # if res is None or len(res)==0:
        #     return {'error': 'No btn group is found'}
        return BtnGroupCollectionFromDB(btnGroups=res)
    except Exception as e:
        print('error')
        return error_handler(e)

@app.delete(
    "/api/btns",
    response_description="Delete project btn configuration data"
)
async def deleteProjectBtnHandler(projectId: ObjectId):  #str= Form()):
    logger.debug(f"Delete: /api/btns?projectId={projectId}")
    # logger.debug(video_config_obj)
    try:
        # print(video_config_obj.model_dump(by_alias=True)) # {'_id': '...', 'projectId': 'testId', 'name': '/Users/pengxi/video/numbered.mp4', 'path': '/Users/pengxi/video/numbered.mp4', 'additionalFields': []}
        res = await delete_project_objs_mongo(projectId, 'btn')
        return {'info': f'deleted {res.deleted_count} btn groups'}
    except Exception as e:
        print('error')
        return error_handler(e)

@app.post("/api/btns",
         response_description="Post project btn configuration data",
         )
async def postProjectBtnHandler(btnGroupColletion: BtnGroupCollectionFromClient):
    logger.debug("Post: /api/btns")
    try:
        projectId = btnGroupColletion.projectId
        btnGroups = btnGroupColletion.btnGroups
        delete_res = await delete_project_objs_mongo(projectId, 'btn')
        print(delete_res, delete_res.deleted_count)
        insert_res = 0
        if len(btnGroups) > 0:
            insert_res = await post_project_objs_mongo(btnGroups, 'btn')
        if insert_res == len(btnGroups):
            return {'success': f'deleted {delete_res.deleted_count}, added {insert_res} btn groups'}
        else:
            return {'error': f'deleted {delete_res.deleted_count}, added {insert_res} btn groups, the uploaded data has {len(btnGroups)} btn groups'}
    except Exception as e:
        print('error')
        return error_handler(e)


cap = None

@app.post(
    "/api/video",
    response_description="Add new video",
    # response_model=VideoInfoObj,
    # status_code=status.HTTP_201_CREATED,
    # response_model_by_alias=False,
)
async def postVideoHandler(video_config_obj: VideoFromClient):  #str= Form()):
    logger.debug("Post: /api/video")
    # logger.debug(video_config_obj)
    try:
        # print(video_config_obj.model_dump(by_alias=True)) # {'_id': '...', 'projectId': 'testId', 'name': '/Users/pengxi/video/numbered.mp4', 'path': '/Users/pengxi/video/numbered.mp4', 'additionalFields': []}
       return await post_one_obj_mongo(video_config_obj, 'video')
    except Exception as e:
        print('error')
        return error_handler(e)


@app.put(
    "/api/video",
    response_description="Edit video",
    # response_model=VideoConfigObj,
    # response_model_by_alias=False,
)
async def editVideoHandler(new_video_obj: VideoFromClient):  #str= Form()):
    logger.debug("Put: /api/video")
    # logger.debug(video_config_obj)
    try:
        # print(video_config_obj.model_dump(by_alias=True)) # {'_id': '...', 'projectId': 'testId', 'name': '/Users/pengxi/video/numbered.mp4', 'path': '/Users/pengxi/video/numbered.mp4', 'additionalFields': []}
        res = await edit_one_obj_mongo(new_video_obj, 'video')
        if res.get('error'): # possibly there is no existing video thus editing failed
            post_res = await post_one_obj_mongo(new_video_obj, 'video')
            return post_res
        return res
    except Exception as e:
        print('error')
        return error_handler(e)


@app.delete(
    "/api/video",
    response_description="Delete video"
)
async def deleteVideoHandler(id: ObjectId):  #str= Form()):
    logger.debug(f"Delete: /api/video?id={id}")
    # logger.debug(video_config_obj)
    try:
        # print(video_config_obj.model_dump(by_alias=True)) # {'_id': '...', 'projectId': 'testId', 'name': '/Users/pengxi/video/numbered.mp4', 'path': '/Users/pengxi/video/numbered.mp4', 'additionalFields': []}
        return await delete_one_obj_mongo(id, 'video')

    except Exception as e:
        print('error')
        return error_handler(e)


@app.get("/api/videos",
         response_description="Find project video data",
         response_model=VideoCollectionFromDB,
         response_model_by_alias=False)
async def getProjectVideo(projectId: ObjectId):
    logger.debug(f"Get: /api/videos?projectId={projectId}")
    try:
        res = await app.mongodb.video.find({"projectId": projectId}).to_list(None)
        print(res) # if no doc found, res is []
        # if res is None or len(res)==0: # if return error msg, will fail in return model validation
        #     return {'error': 'No video is found'}
        return VideoCollectionFromDB(videos=res)
    except Exception as e:
        print('error')
        return error_handler(e)

@app.delete(
    "/api/videos",
    response_description="Delete project video data"
)
async def deleteProjectVideoHandler(projectId: ObjectId):  #str= Form()):
    logger.debug(f"Delete: /api/videos?projectId={projectId}")
    # logger.debug(video_config_obj)
    try:
        # print(video_config_obj.model_dump(by_alias=True)) # {'_id': '...', 'projectId': 'testId', 'name': '/Users/pengxi/video/numbered.mp4', 'path': '/Users/pengxi/video/numbered.mp4', 'additionalFields': []}
        res = await delete_project_objs_mongo(projectId, 'video')
        return {'info': f'deleted {res.deleted_count} videos'}
    except Exception as e:
        print('error')
        return error_handler(e)

@app.post("/api/videos",
         response_description="Post project video data",
         )
async def postProjectVideoHandler(videoColletion: VideoCollectionFromClient):
    logger.debug("Post: /api/videos")
    try:
        projectId = videoColletion.projectId
        videos = videoColletion.videos
        delete_res = await delete_project_objs_mongo(projectId, 'video')
        print(delete_res, delete_res.deleted_count)
        insert_res = 0
        if len(videos) > 0:
            insert_res = await post_project_objs_mongo(videos, 'video')
        if insert_res == len(videos):
            return {'success': f'deleted {delete_res.deleted_count}, added {insert_res} videos'}
        else:
            return {'error': f'deleted {delete_res.deleted_count}, added {insert_res} videos, the uploaded data has {len(videos)} videos'}
    except Exception as e:
        print('error')
        return error_handler(e)
    


@app.get("/api/videometa")
async def getVideoMetaHandler(id: ObjectId):
    logger.debug(f"Get: /api/videometa?id={id}")
    try:
        res = await app.mongodb.video.find_one({"_id": id}, { "_id": 0, "path": 1 })
        print(res, res['path'])
        if res is None:
            return {'error': 'No video is found'}
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



@app.post(
    "/api/frameannotation",
    response_description="Add new annotations of a frame",
    # response_model=VideoInfoObj,
    # status_code=status.HTTP_201_CREATED,
    # response_model_by_alias=False,
)
async def postFrameAnnotationHandler(annotation_objs: AnnotationCollectionFromClient): 
    logger.debug("Post: /api/frameannotation")
    # logger.debug(btn_group_obj)
    try:
        # print(annotation_objs)
        resList = []
        for obj in annotation_objs.annotations:
            res = await post_one_obj_mongo(obj, 'annotation')
            # print('post annotation res: ', res)
            if res.get('info') == 'annotation already exists':
                edit_res = await edit_one_obj_mongo(obj, 'annotation')
                resList.append(edit_res)
            else:
                resList.append(res)
        return resList
    except Exception as e:
        print('error')
        return error_handler(e)

@app.get("/api/frameannotation",
         response_description="Find all annotations of a frame",
         response_model=AnnotationCollectionFromDB,
         response_model_by_alias=False)
async def getFrameAnnotationHandler(frameNum: int, videoId: ObjectId):
    logger.debug(f"Get: /api/frameannotation?frameNum={frameNum}&videoId={videoId}")
    try:
        res = await app.mongodb.annotation.find({"frameNum": frameNum, "videoId": videoId}).to_list(None)
        print(res) # if no doc found, res is []
        # if res is None or len(res)==0: # if return error msg, will fail in return model validation
        #     return {'error': 'No video is found'}
        return AnnotationCollectionFromDB(annotations=res)
    except Exception as e:
        print('error')
        return error_handler(e)

@app.post(
    "/api/projectannotation",
    response_description="Add new annotations of a project",
    # response_model=VideoInfoObj,
    # status_code=status.HTTP_201_CREATED,
    # response_model_by_alias=False,
)
async def postProjectAnnotationHandler(annotationCollection: ProjectAnnotationCollectionFromClient): 
    logger.debug("Post: /api/projectannotation")
    # logger.debug(btn_group_obj)
    try:
        # print(annotationCollection)
        # resList = []
        # for obj in annotationCollection.annotations:
        #     res = await post_one_obj_mongo(obj, 'annotation')
        #     # print('post annotation res: ', res)
        #     if res.get('info') == 'annotation already exists':
        #         edit_res = await edit_one_obj_mongo(obj, 'annotation')
        #         resList.append(edit_res)
        #     else:
        #         resList.append(res)
        # return resList
        projectId = annotationCollection.projectId
        videoIds = annotationCollection.videos
        annotations = annotationCollection.annotations
        print(videoIds)
        delete_res = await delete_project_objs_mongo(projectId, 'annotation', videoIds)
        print(delete_res, delete_res.deleted_count)
        insert_res = 0
        if len(annotations) > 0:
            insert_res = await post_project_objs_mongo(annotations, 'annotation', videoIds)
        if insert_res == len(annotations):
            return {'success': f'deleted {delete_res.deleted_count}, added {insert_res} annotations'}
        else:
            return {'error': f'deleted {delete_res.deleted_count}, added {insert_res} annotations, the uploaded data has {len(annotations)} annotations'}
    except Exception as e:
        print('error')
        return error_handler(e)

@app.get("/api/projectannotation",
         response_description="Find all annotations of a project",
         response_model=ProjectAnnotationCollectionFromDB,
         response_model_by_alias=False)
async def getProjectAnnotationHandler(projectId: ObjectId):
    logger.debug(f"Get: /api/projectannotation?projectId={projectId}")
    try:
        videoList = await app.mongodb.video.find({"projectId": projectId}, {"_id": 1}).to_list(None) # if no doc found, return []
        videoIdList = [v['_id'] for v in videoList]
        print(videoIdList)
        res = await app.mongodb.annotation.find({"videoId": {"$in": videoIdList}}).to_list(None)
        print(len(res)) 
        # if res is None or len(res)==0: # if return error msg, will fail in return model validation
        #     return {'error': 'No video is found'}
        return ProjectAnnotationCollectionFromDB(projectId=projectId, videos=videoIdList, annotations=res)
    except Exception as e:
        print('error')
        return error_handler(e)

@app.delete(
    "/api/annotation",
    response_description="Delete an annotation"
)
async def deleteAnnotationHandler(id: ObjectId):  #str= Form()):
    logger.debug(f"Delete: /api/annotation?id={id}")
    # logger.debug(video_config_obj)
    try:
        # print(video_config_obj.model_dump(by_alias=True)) # {'_id': '...', 'projectId': 'testId', 'name': '/Users/pengxi/video/numbered.mp4', 'path': '/Users/pengxi/video/numbered.mp4', 'additionalFields': []}
        return await delete_one_obj_mongo(id, 'annotation')

    except Exception as e:
        print('error')
        return error_handler(e)

@app.delete(
    "/api/projectannotation",
    response_description="Delete project annotation data"
)
async def deleteProjectAnnotationHandler(projectId: ObjectId):  #str= Form()):
    logger.debug(f"Delete: /api/projectannotation?projectId={projectId}")
    # logger.debug(video_config_obj)
    try:
        # print(video_config_obj.model_dump(by_alias=True)) # {'_id': '...', 'projectId': 'testId', 'name': '/Users/pengxi/video/numbered.mp4', 'path': '/Users/pengxi/video/numbered.mp4', 'additionalFields': []}
        res = await delete_project_objs_mongo(projectId, 'annotation')
        return {'info': f'deleted {res.deleted_count} annotations'}
    except Exception as e:
        print('error')
        return error_handler(e)




additionalDataReaders = {} # {'trajectory': dataObj, ...}

#TODO: need videoId?
@app.get('/api/additionaldata/{name}')
async def getAdditionalDataHandler(name: str, frameNum: int, range: int): #videoId: str
    logger.debug(f'api/additionaldata/{name}?num={frameNum}&range={range}') #videoId={videoId}&
    try:
        if name not in additionalDataReaders:
            return {'error': f'{name} data not found'}
        
        dataObj = additionalDataReaders[name]
        res = getAdditionalData(dataObj, frameNum, range)
        # res['frameNum'] = frameNum
        # res['name'] = name
        print(res) # {range: , data: }
        return res
    except Exception as e:
        print('error')
        return error_handler(e)


@app.post("/api/additionaldataname")
async def postAdditionalNameToRetrieveHandler(obj: dict): 
    # find path for these names, and read data file to memory
    logger.debug("Post: /api/additionaldataname")
    # logger.debug(btn_group_obj)
    try:
        global additionalDataReaders
        videoId = obj['videoId']
        namesToRetrieve = obj['names']
        print(videoId, namesToRetrieve)
        if len(namesToRetrieve)==0:
            additionalDataReaders = {}
            return {'info': 'Requested no additional data.'}
        fieldsInfo = await app.mongodb.video.find_one({"_id": ObjectId(videoId)}, { "_id": 0, "additionalFields": 1 }) #{'addi...': [{}, {}]}
        # print(fieldsInfo, fieldsInfo['additionalFields'])
        if fieldsInfo is None:
            return {'error': f'No addtional data related to this video'}
        fieldList = list(filter(lambda x: x['name'] in namesToRetrieve, fieldsInfo['additionalFields'])) # return [] if no entry found
        # print(fieldList)
        if len(fieldList) == 0:
            return {'error': f'No addtional data matching the requested ones.'}
        elif len(fieldList) != len(namesToRetrieve):
            return {'error': 'The number of addtional data found in DB does not match the number of names to retrieve',
                    'inDB': fieldList,
                    'toRetrieve': namesToRetrieve}
        for field in fieldList:
            dataObj = getAdditionalDataReader(field['name'], field['path'])
            additionalDataReaders[field['name']] = dataObj
        print(additionalDataReaders)
        return {'info': f'{len(additionalDataReaders)} additional data readers ready'}
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


async def post_one_obj_mongo(obj, type):
    ''' type: 'project', 'video', 'btn', 'annotation' '''
    # obj = obj.model_dump(by_alias=False)
    # print(obj)
    if type=='project':
        id = obj.projectId
        collection = app.mongodb.project
    elif type=='video':
        id = obj.videoId
        collection = app.mongodb.video
    elif type=='btn':
        id = obj.btnGroupId
        collection = app.mongodb.btn
    elif type=='annotation':
        id = obj.id
        collection = app.mongodb.annotation

    existing_obj = await collection.find_one({"_id": id})
    # print('existing obj:', existing_obj)
    if existing_obj is None:
        new_obj = await collection.insert_one(
            obj.model_dump(by_alias=True)
            )
        # print(new_obj)
        check = await collection.find_one({"_id": new_obj.inserted_id})
        # print('post check', check)
        # print(new_video) # InsertOneResult('1715271938193', acknowledged=True)
        return {'success': f'Added {type} {new_obj.inserted_id}'}
    else:
        return {'info': f'{type} already exists'}


async def edit_one_obj_mongo(obj, type):
    # print('edit obj called: ', obj)
    if type=='project':
        collection = app.mongodb.project
    elif type=='video':
        collection = app.mongodb.video
    elif type=='btn':
        collection = app.mongodb.btn
    elif type=='annotation':
        collection = app.mongodb.annotation
    
    new_data = obj.model_dump(by_alias=True)
    id = new_data['_id']
    update_result = await collection.find_one_and_update(            
        {"_id": id},
        {"$set": new_data},
        return_document=ReturnDocument.AFTER,
    )
    # print('update_result: ', update_result)
    if update_result is not None:
        return {'success': f'Edited {id}'} #update_result
    else:
        return {'error': f'Editing {type} failed'}
    

async def delete_one_obj_mongo(id, type):
    # print('delete obj called: ', obj)
    if type=='project':
        collection = app.mongodb.project
    elif type=='video':
        collection = app.mongodb.video
    elif type=='btn':
        collection = app.mongodb.btn
    elif type=='annotation':
        collection = app.mongodb.annotation
    
    delete_result = await collection.delete_one({"_id": ObjectId(id)})
    print(delete_result, delete_result.deleted_count)
    if delete_result.deleted_count == 1:
        return {'success': f'Deleted {type} {id}'}
    else:
        return {'error': f'Deleting {type} failed.'}


async def delete_project_objs_mongo(projectId, type, videoIds=None):
    # print('delete obj called: ', obj)
    if type=='video':
        collection = app.mongodb.video
    elif type=='btn':
        collection = app.mongodb.btn
    elif type=='annotation':
        collection = app.mongodb.annotation
    
    if type != 'annotation':
        delete_result = await collection.delete_many({"projectId": ObjectId(projectId)})
    else:
        delete_result = await collection.delete_many({"videoId": {"$in": videoIds}})
    # print(delete_result, delete_result.deleted_count)
    # if delete_result.deleted_count >= 1:
    #     return {'success': f'Deleted {delete_result.deleted_count} {type} for project'}
    # else:
    return delete_result


async def post_project_objs_mongo(objs, type, videoIds=None):
    ''' 
    This func should be called after deleting exsiting objs for the project in db, 
    thus does not check if each obj exists before insertion 
    
    type: 'video', 'btn', 'annotation' 
    '''
    # obj = obj.model_dump(by_alias=False)
    # print(obj)
    if len(objs) == 0:
        return {'success': f'Added 0 {type}'}
    
    if type=='project':
        collection = app.mongodb.project
    elif type=='video':
        collection = app.mongodb.video
    elif type=='btn':
        collection = app.mongodb.btn
    elif type=='annotation':
        collection = app.mongodb.annotation

    res = await collection.insert_many([obj.model_dump(by_alias=True) for obj in objs])
    # print(res)
    # print(objs)
    if type != 'annotation':
        check = await collection.find({"projectId": objs[0].projectId}).to_list(None)
    else:
        check = await collection.find({"videoId": {"$in": videoIds}}).to_list(None)
    # print('post check', check)
    # print(new_video) # InsertOneResult('1715271938193', acknowledged=True)
    return len(check)
    

# async def get_all_of_collection_mongo(type):
#     if type=='project':
#         collection = app.mongodb.project
#     elif type=='video':
#         collection = app.mongodb.video
#     elif type=='btn':
#         collection = app.mongodb.btn
#     elif type=='annotation':
#         collection = app.mongodb.annotation
    
#     new_data = obj.model_dump(by_alias=True)
#     update_result = await collection.find_one_and_update(            
#         {"_id": new_data['_id']},
#         {"$set": new_data},
#         return_document=ReturnDocument.AFTER,
#     )
#     print(update_result)
#     if update_result is not None:
#         return update_result
#     else:
#         return {'error': f'Editing {type} failed'}