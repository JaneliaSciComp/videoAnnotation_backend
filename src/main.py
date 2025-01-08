import os
from sys import getsizeof
from datetime import datetime
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import cv2 as cv
from typing import List
from motor import motor_asyncio
from pymongo import ReturnDocument
from configparser import ConfigParser
from contextlib import asynccontextmanager
from datamodel import ObjectId, ProjectFromClient, ProjectFromDB, ProjectCollection, BtnGroupFromClient, BtnGroupFromDB, BtnGroupCollectionFromDB, BtnGroupCollectionFromClient, VideoFromClient, VideoFromDB, VideoCollectionFromDB, VideoCollectionFromClient, AdditionalField, AnnotationFromClient, AnnotationCollectionFromClient, AnnotationCollectionFromDB, ProjectAnnotationCollectionFromDB, ProjectAnnotationCollectionFromClient, VideoAnnotationCollectionFromDB, VideoAnnotationCollectionFromClient
from customized import getAdditionalData
import asyncio

logger = logging.getLogger('video_annotation')
logger.setLevel(logging.DEBUG)
log_handler = logging.StreamHandler()
log_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s: %(message)s'))
logger.addHandler(log_handler)




def config(section, filename='../database.ini'): 
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
    try:
        
        settings = config('mongodb')
        url = f"mongodb://{settings['user']}:{settings['password']}@{settings['host']}"
        client = motor_asyncio.AsyncIOMotorClient(url)
        app.mongodb = client.get_database(settings['dbname'])
        app.mongodb.project_config = app.mongodb.get_collection("configuration")
        app.mongodb.video = app.mongodb.get_collection("video")
    
        yield
        client.close()
    except Exception as e:
        logger.info('error', e)



app = FastAPI(lifespan=lifespan)


origins = ['http://localhost:3000']
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.get("/test")
async def testHandler():
    logger.debug("Get: /test")
    try:
        return 'I am ready!'
    except Exception as e:
        print('error')
        return error_handler(e)


@app.post(
    "/api/project",
    response_description="Add new project",
)
async def postProjectHandler(project_config_obj: ProjectFromClient):
    logger.debug("Post: /api/project")
    try:
        res = await post_one_obj_mongo(project_config_obj, 'project')
        if res.get('info') is not None:
            raise HTTPException(status_code=409, detail=f'project already exists')
        return res
    except Exception as e:
        print('error')
        return error_handler(e)

@app.put(
    "/api/project",
    response_description="Edit project",
)
async def editProjectHandler(new_project_obj: ProjectFromClient):
    logger.debug("Put: /api/project")
    try:
        res = await edit_one_obj_mongo(new_project_obj, 'project')
        if res.get('error'):
            post_res = await post_one_obj_mongo(new_project_obj, 'project')
            if res.get('info') is not None:
                raise HTTPException(status_code=409, detail=f'Editing project failed.')
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
        if res is None:
            raise HTTPException(status_code=404, detail='No project found')
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
    try:
        res = await delete_one_obj_mongo(id, 'project')
        if res.get('error') is not None:
            raise HTTPException(status_code=500, detail=f'Deleting project failed.')
        return res
    except Exception as e:
        print('error')
        return error_handler(e)


@app.post(
    "/api/btn",
    response_description="Add new btn group",
)
async def postBtnHandler(btn_group_obj: BtnGroupFromClient): 
    logger.debug("Post: /api/btn")
    try:
        res = await post_one_obj_mongo(btn_group_obj, 'btn')
        if res.get('info') == 'btn already exists':
            edit_res = await edit_one_obj_mongo(btn_group_obj, 'btn')
            if edit_res.get('error') is not None:
                raise HTTPException(status_code=500, detail=f'Editing btn group failed.')
            return edit_res
        return res
    except Exception as e:
        print('error')
        return error_handler(e)

@app.delete(
    "/api/btn",
    response_description="Delete Btn Group"
)
async def deleteBtnGroupHandler(btnGroupId: ObjectId):
    logger.debug(f"Delete: /api/btn?btnGroupId={btnGroupId}")
    try:
        res = await delete_one_obj_mongo(btnGroupId, 'btn')
        if res.get('error') is not None:
            raise HTTPException(status_code=500, detail=f'Deleting btn group failed.')
        return res
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
        return BtnGroupCollectionFromDB(btnGroups=res)
    except Exception as e:
        print('error')
        return error_handler(e)

@app.delete(
    "/api/btns",
    response_description="Delete project btn configuration data"
)
async def deleteProjectBtnHandler(projectId: ObjectId):
    logger.debug(f"Delete: /api/btns?projectId={projectId}")
    try:
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
        print(delete_res.deleted_count)
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
)
async def postVideoHandler(video_config_obj: VideoFromClient):
    logger.debug("Post: /api/video")
    try:
        res = await post_one_obj_mongo(video_config_obj, 'video')
        if res.get('info') is not None:
            raise HTTPException(status_code=409, detail=f'Video already exists')
        return res
    except Exception as e:
        print('error')
        return error_handler(e)


@app.put(
    "/api/video",
    response_description="Edit video",
)
async def editVideoHandler(new_video_obj: VideoFromClient):
    logger.debug("Put: /api/video")
    try:
        res = await edit_one_obj_mongo(new_video_obj, 'video')
        if res.get('error') is not None:
            post_res = await post_one_obj_mongo(new_video_obj, 'video')
            if post_res.get('info') is not None:
                raise HTTPException(status_code=409, detail=f'Editing video failed.')
            return post_res
        return res
    except Exception as e:
        print('error')
        return error_handler(e)


@app.delete(
    "/api/video",
    response_description="Delete video"
)
async def deleteVideoHandler(id: ObjectId):
    logger.debug(f"Delete: /api/video?id={id}")
    try:
        deleteAnnotationRes = await delete_project_objs_mongo(None, 'annotation', [id])
        print(deleteAnnotationRes.deleted_count)
        deleteVideoRes = await delete_one_obj_mongo(id, 'video')
        print(deleteVideoRes, type(deleteVideoRes))
        if deleteVideoRes.get('error') is not None:
            raise HTTPException(status_code=500, detail=f'Deleting video failed.')
        return {'info': f'Deleted 1 video and {deleteAnnotationRes.deleted_count} annotations'}
    except Exception as e:
        print('error', e)
        return error_handler(e)


@app.get("/api/videos",
         response_description="Find project video data",
         response_model=VideoCollectionFromDB,
         response_model_by_alias=False)
async def getProjectVideo(projectId: ObjectId):
    logger.debug(f"Get: /api/videos?projectId={projectId}")
    try:
        res = await app.mongodb.video.find({"projectId": projectId}).to_list(None)
        return VideoCollectionFromDB(videos=res)
    except Exception as e:
        print('error')
        return error_handler(e)

@app.delete(
    "/api/videos",
    response_description="Delete project video data"
)
async def deleteProjectVideoHandler(projectId: ObjectId):
    logger.debug(f"Delete: /api/videos?projectId={projectId}")
    try:
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
        print(delete_res.deleted_count)
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
            raise HTTPException(status_code=404, detail='Video path not found')
        path = res['path']
        global cap
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail='Video file is not found')
        if cap:
            cap.release()
        cap = cv.VideoCapture(path)
        return {'frame_count': cap.get(cv.CAP_PROP_FRAME_COUNT), 'fps': cap.get(cv.CAP_PROP_FPS)}
    except Exception as e:
        print('error')
        return error_handler(e)
 

@app.get('/api/frame')
async def getFrame(num: int):
    logger.debug(f'api/frame?num={num}')
    try:
        if num < 0:
            raise HTTPException(status_code=416, detail='Frame number out of bound')
        cap.set(cv.CAP_PROP_POS_FRAMES, num)
        ret, frame = cap.read()
        if ret:
            ret, frame_1d = cv.imencode('.jpg', frame) 
            headers = {'Content-Disposition': f'inline; filename=f_{num}.jpg'}
            return Response(frame_1d.tobytes() , headers=headers, media_type='image/jpg')
        else:
            raise HTTPException(status_code=416, detail=f'Frame {num+1} reached video end')
    except Exception as e:
        print('error')
        return error_handler(e)


@app.post(
    "/api/projectannotation",
    response_description="Add new annotations of a project",
)
async def postProjectAnnotationHandler(annotationCollection: ProjectAnnotationCollectionFromClient): 
    logger.debug("Post: /api/projectannotation")
    try:
        projectId = annotationCollection.projectId
        videoIds = annotationCollection.videos
        annotations = annotationCollection.annotations
        delete_res = await delete_project_objs_mongo(projectId, 'annotation', videoIds)
        print(delete_res.deleted_count)
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
        videoList = await app.mongodb.video.find({"projectId": projectId}, {"_id": 1}).to_list(None)
        videoIdList = [v['_id'] for v in videoList]
        res = await app.mongodb.annotation.find({"videoId": {"$in": videoIdList}}).sort("frameNum", 1).to_list(None)
        print(len(res)) 
        return ProjectAnnotationCollectionFromDB(projectId=projectId, videos=videoIdList, annotations=res)
    except Exception as e:
        print('error')
        return error_handler(e)

@app.post("/api/videoannotation")
async def postVideoAnnotationHandler(annotationCollection: VideoAnnotationCollectionFromClient): 
    logger.debug("Post: /api/videoannotation")
    try:
        videoId = annotationCollection.videoId
        annotations = annotationCollection.annotations
        delete_res = await delete_video_annotation_mongo(videoId)
        insert_res = 0
        if len(annotations) > 0:
            insert_res = await post_video_annotations_mongo(annotations)
        if insert_res == len(annotations):
            return {'success': f'deleted {delete_res.deleted_count}, added {insert_res} annotations'}
        else:
            return {'error': f'deleted {delete_res.deleted_count}, added {insert_res} annotations, the uploaded data has {len(annotations)} annotations'}
    except Exception as e:
        print('error')
        return error_handler(e)

@app.get("/api/videoannotation",
         response_description="Find all annotations of a video",
         response_model=VideoAnnotationCollectionFromDB,
         response_model_by_alias=False)
async def getVideoAnnotationHandler(videoId: ObjectId):
    logger.debug(f"Get: /api/videoannotation?videoId={videoId}")
    try:
        res = await app.mongodb.annotation.find({"videoId": ObjectId(videoId)}).sort("frameNum", 1).to_list(None)
        print(len(res)) 
        return VideoAnnotationCollectionFromDB(videoId=videoId, annotations=res)
    except Exception as e:
        print('error')
        return error_handler(e)


@app.delete(
    "/api/projectannotation",
    response_description="Delete project annotation data"
)
async def deleteProjectAnnotationHandler(projectId: ObjectId):
    logger.debug(f"Delete: /api/projectannotation?projectId={projectId}")
    try:
        project_videos = await app.mongodb.video.find({"projectId": projectId}, {"_id": 1}).to_list(None)
        if len(project_videos) > 0:
            res = await delete_project_objs_mongo(projectId, 'annotation', project_videos)
            return {'info': f'deleted {res.deleted_count} annotations'}
        return {'info': 'no anntation found for this project'}
    except Exception as e:
        print('error')
        return error_handler(e)

@app.get("/api/annotationforchart",
         response_description="Find category annotations of a group of labels",
         )
async def getAnnotationForChartHandler(videoId: ObjectId, frameNum: int, labels: str, range: int):
    logger.debug(f"Get: /api/annotationforchart?videoId={videoId}&frameNum={frameNum}&labels={labels}&range={range}")
    try:
        labels_list = labels.split('@@')
        annotation_list = await app.mongodb.annotation.find( \
            {"videoId": videoId, \
             "frameNum": {"$gte": frameNum-range, "$lte": frameNum+range}, \
             "label": {"$in": labels_list}}, \
             {"data": 0, "groupIndex": 0, "isCrowd": 0, "pathes": 0}) \
            .sort({"frameNum": 1}) \
            .to_list(None)
        print(len(annotation_list))
        return annotation_list
    except Exception as e:
        print('error')
        return error_handler(e)



additionalDataReaders = {}

@app.get('/api/additionaldata/{videoId}')
async def getAdditionalDataHandler(videoId: ObjectId, names: str): 
    logger.debug(f'api/additionaldata/{videoId}?names={names}')
    try:
        namesToRetrieve = names.split('@@')
        if len(namesToRetrieve)==0:
            raise HTTPException(status_code=400, detail='No additional data name in the request')
        
        fieldsInfo = await app.mongodb.video.find_one({"_id": ObjectId(videoId)}, { "_id": 0, "additionalFields": 1 })
        if fieldsInfo is None:
            raise HTTPException(status_code=404, detail='No addtional data related to this video')
        fieldList = list(filter(lambda x: x['name'] in namesToRetrieve, fieldsInfo['additionalFields']))
        if len(fieldList) == 0:
            raise HTTPException(status_code=400, detail='No addtional data matching the requested ones.')
        elif len(fieldList) != len(namesToRetrieve):
            return {'error': 'The number of addtional data found in DB does not match the number of request data names',
                    'inDB': fieldList,
                    'toRetrieve': namesToRetrieve}
        data = {}
        for field in fieldList:
            res = getAdditionalData(field['name'], field['path'])
            data[field['name']] = res
        return data
    except Exception as e:
        print('error')
        return error_handler(e)





@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )

def error_handler(e):
    logger.error(e)
    if isinstance(e, HTTPException):
        raise e
    return JSONResponse(
        status_code=500,
        content={"error": ', '.join(list(e.args))}
    )




async def post_one_obj_mongo(obj, type):
    ''' type: 'project', 'video', 'btn', 'annotation' '''
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
    if existing_obj is None:
        if type=='annotation' and obj.type == 'category':
            new_obj = await post_one_category_annotation_mongo(obj)
            if new_obj =='category annotation already exists':
                return {'success': f'{obj.label} already exists'}
        else:
            new_obj = await collection.insert_one(obj.model_dump(by_alias=True))
        return {'success': f'Added {type}: {new_obj.inserted_id}'}
    else:
        return {'info': f'{type} already exists'}


lock_annotation_tag = None

async def post_one_category_annotation_mongo(obj):
    collection = app.mongodb.annotation
    global lock_annotation_tag
    if lock_annotation_tag is None:
        lock_annotation_tag = {"createdAt": datetime.now()}
        
        existing_label = await collection.find_one({"videoId": ObjectId(obj.videoId), "type": 'category', "frameNum": obj.frameNum, "label": obj.label})
        if existing_label is None:
            new_obj = await collection.insert_one(obj.model_dump(by_alias=True))
            res = new_obj
        else:
            res = 'category annotation already exists'
        lock_annotation_tag = None
        return res
    elif (datetime.now() - lock_annotation_tag['createdAt']).total_seconds() > 3:
        lock_annotation_tag = {"createdAt": datetime.now()}
        
        existing_label = await collection.find_one({"videoId": ObjectId(obj.videoId), "type": 'category', "frameNum": obj.frameNum, "label": obj.label})
        if existing_label is None:
            new_obj = await collection.insert_one(obj.model_dump(by_alias=True))
            res = new_obj
        else:
            res = 'category annotation already exists'
        lock_annotation_tag = None
        return res
    else:
        await asyncio.sleep(0.1)
        return await post_one_category_annotation_mongo(obj)


async def edit_one_obj_mongo(obj, type):
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
    if update_result is not None:
        return {'success': f'Edited {id}'}
    else:
        return {'error': f'Editing {type} failed'}
    

async def delete_one_obj_mongo(id, type):
    if type=='project':
        collection = app.mongodb.project
    elif type=='video':
        collection = app.mongodb.video
    elif type=='btn':
        collection = app.mongodb.btn
    elif type=='annotation':
        collection = app.mongodb.annotation
    
    delete_result = await collection.delete_one({"_id": ObjectId(id)})
    print(delete_result.deleted_count)
    if delete_result.deleted_count == 1:
        return {'success': f'Deleted {type} {id}'}
    else:
        return {'error': f'Deleting {type} failed.'}

async def delete_multiple_obj_mongo(type, ids):
    if type=='project':
        collection = app.mongodb.project
    elif type=='video':
        collection = app.mongodb.video
    elif type=='btn':
        collection = app.mongodb.btn
    elif type=='annotation':
        collection = app.mongodb.annotation
    
    delete_result = await collection.delete_many({"_id": {"$in": ids}})
    print('delete mutiple obj called: ', delete_result, delete_result.deleted_count)
    return delete_result

async def delete_video_annotation_mongo(videoId):
    collection = app.mongodb.annotation
    delete_result = await collection.delete_many({"videoId": ObjectId(videoId)})
    return delete_result

async def post_video_annotations_mongo(annotations):
    ''' 
    This func should be called after deleting exsiting objs for the video in db, 
    thus does not check if each obj exists before insertion 
    '''
    if len(annotations) == 0:
        return {'success': f'Added 0 {type}'}
    
    collection = app.mongodb.annotation
    res = await collection.insert_many([anno.model_dump(by_alias=True) for anno in annotations])
    check = await collection.find({"videoId": ObjectId(annotations[0].videoId)}).to_list(None)
    return len(check)

async def delete_project_objs_mongo(projectId, type, videoIds=None):
    if type=='video':
        collection = app.mongodb.video
    elif type=='btn':
        collection = app.mongodb.btn
    elif type=='annotation':
        collection = app.mongodb.annotation
    
    if type != 'annotation':
        delete_result = await collection.delete_many({"projectId": ObjectId(projectId)})
    else:
        videoIds = [ObjectId(vid) for vid in videoIds]
        delete_result = await collection.delete_many({"videoId": {"$in": videoIds}})
    print(delete_result)
    return delete_result


async def post_project_objs_mongo(objs, type, videoIds=None):
    ''' 
    This func should be called after deleting exsiting objs for the project in db, 
    thus does not check if each obj exists before insertion 
    
    type: 'video', 'btn', 'annotation' 
    '''
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
    if type != 'annotation':
        check = await collection.find({"projectId": objs[0].projectId}).to_list(None)
    else:
        check = await collection.find({"videoId": {"$in": videoIds}}).to_list(None)
    return len(check)
    

