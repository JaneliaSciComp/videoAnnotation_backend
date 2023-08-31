import os
from datetime import datetime
import logging
from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
import cv2 as cv
import json



#set up logger
logger = logging.getLogger('video_annotation')
logger.setLevel(logging.DEBUG)
log_handler = logging.StreamHandler()
# to print out source code location: %(pathname)s %(lineno)d:
log_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s: %(message)s'))
logger.addHandler(log_handler)

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
        print(cap.get(cv.CAP_PROP_FRAME_COUNT))
        #frame_count = cap.get(cv.CAP_PROP_FRAME_COUNT)
        # if num < 0 or num > frame_count-1:
        #     return {'error': 'Frame number out of bound'}
        cap.set(cv.CAP_PROP_POS_FRAMES, num)
        ret, frame = cap.read()
        cv.imwrite(f'../frames/f_{num}.jpg',frame)
        if ret:
            ret, frame_1d = cv.imencode('.jpg', frame)  
            frame_1d_int = map(lambda x: int(x), frame_1d)          
            # return Response(content=frame_1d, media_type='image/jpg')
            return {'res': json.dumps(list(frame_1d_int))}
        else:
            return {'error': f'Frame {num+1} reached video end'}
    except Exception as e:
        print('error')
        return error_handler(e)
    

