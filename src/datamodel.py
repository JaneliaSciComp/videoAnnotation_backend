from pydantic import BaseModel, BeforeValidator, Field
from typing import Union, List, Dict
from typing_extensions import Annotated
from enum import Enum


ObjectId = Annotated[str, BeforeValidator(str)]


class ProjectFromClient(BaseModel):
    projectId: ObjectId = Field(serialization_alias="_id")
    projectName: str = Field(max_length=200)
    description: Union[str, None] = Field(max_length=300, default=None)

class ProjectFromDB(ProjectFromClient):
    projectId: ObjectId = Field(validation_alias="_id")

class ProjectCollection(BaseModel):
    projects: List[ProjectFromDB]

class AdditionalField(BaseModel):
    name: str
    path: Union[str, None] = None
    # loadIn: Union[str, None] = None
    # value: Union[str, None] = None
    
class VideoFromClient(BaseModel):
    videoId: ObjectId = Field(serialization_alias="_id")
    projectId: Union[ObjectId, None] = None #if developer use VideoUploader solely to handle video, then no project
    name: str = Field(max_length=200)
    path: str
    additionalFields: List[AdditionalField] = []

class VideoFromDB(VideoFromClient):
    videoId: ObjectId = Field(validation_alias="_id")

class VideoCollectionFromDB(BaseModel):
    videos: List[VideoFromDB]

class VideoCollectionFromClient(BaseModel):
    videos: List[VideoFromClient]
    projectId: ObjectId

class BtnGroupType(str, Enum):
    shape = 'shape'
    category = 'category'
    skeleton = 'skeleton'
    brush = 'brush'

class BtnType(str, Enum):
    keyPoint = 'keyPoint'
    bbox = 'bbox'
    polygon = 'polygon'
    category = 'category'
    skeleton = 'skeleton'
    brush = 'brush'

class Btn(BaseModel):
    index: int = Field(ge=0)
    btnType: BtnType
    label: str = Field(min_length=1, max_length=100)
    color: str = Field(min_length=1) # TODO
    omitCrowdRadio: Union[bool, None] = Field(default=True)

class EdgeData(BaseModel):
    color: str = Field(min_length=1) # TODO
    edges: List[List[int]]

class BtnGroupFromClient(BaseModel):
    btnGroupId: ObjectId = Field(serialization_alias="_id")
    projectId: Union[ObjectId, None] = None #if developer use BtnGroupConroller solely to create btn, then no project
    groupType: BtnGroupType
    btnType: BtnType
    btnNum: int = Field(gt=0)
    childData: List[Btn] = Field(min_length=1)
    skeletonName: Union[str, None] = Field(max_length=100, default=None)
    edgeData: Union[EdgeData, None] = Field(default=None)

class BtnGroupFromDB(BtnGroupFromClient):
    btnGroupId: ObjectId = Field(validation_alias="_id")

class BtnGroupCollectionFromDB(BaseModel):
    btnGroups: List[BtnGroupFromDB]

class BtnGroupCollectionFromClient(BaseModel):
    btnGroups: List[BtnGroupFromClient]
    projectId: ObjectId     

class AnnotationFromClient(BaseModel):
    id: ObjectId = Field(serialization_alias="_id")
    videoId: ObjectId
    frameNum: int = Field(ge=0)
    type: BtnType
    label: str = Field(max_length=100)
    color: Union[str, None]  = Field(min_length=1, default=None) # TODO
    data: Union[None, List[int], List[List[float]], Dict[str, float], Dict[str, Dict[str, float]]] = None
    groupIndex: Union[None, ObjectId] = None
    isCrowd: Union[None, int] = None
    pathes: Union[None, List[str]] = None

class AnnotationCollectionFromClient(BaseModel):
    annotations: List[AnnotationFromClient]

class AnnotationFromDB(AnnotationFromClient):
    id: ObjectId = Field(validation_alias="_id")

class AnnotationCollectionFromDB(BaseModel):
    annotations: List[AnnotationFromDB]

class ProjectAnnotationCollectionFromDB(BaseModel):
    projectId: ObjectId
    videos: List[ObjectId]
    annotations: List[AnnotationFromDB]

class ProjectAnnotationCollectionFromClient(ProjectAnnotationCollectionFromDB):
    annotations: List[AnnotationFromClient]