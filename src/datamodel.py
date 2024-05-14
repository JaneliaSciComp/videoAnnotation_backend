from pydantic import BaseModel, BeforeValidator, Field
from typing import Union, List
from typing_extensions import Annotated


ObjectId = Annotated[str, BeforeValidator(str)]


class ProjectConfigObj(BaseModel):
    projectId: Union[ObjectId, None] = Field(serialization_alias="_id")
    projectName: str = Field(max_length=200)
    description: Union[str, None] = Field(max_length=300, default=None)

class ProjectCollection(BaseModel):
    projects: List[ProjectConfigObj]

class AdditionalField(BaseModel):
    name: str
    value: Union[str, None] = None
    
class VideoConfigObj(BaseModel):
    videoId: Union[ObjectId, None] = Field(serialization_alias="_id")
    projectId: ObjectId
    name: str = Field(max_length=200)
    path: str
    additionalFields: List[AdditionalField] = []

# class BtnObj(BaseModel):

