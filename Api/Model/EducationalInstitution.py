from datetime import datetime
from typing import Optional, List

from pydantic import ConfigDict, BaseModel, Field, EmailStr
from pydantic.functional_validators import BeforeValidator

from typing_extensions import Annotated

from bson import ObjectId

from Api.Model.Resource import ResourceModel

# Represents an ObjectId field in the database.
# It will be represented as a `str` on the model so that it can be serialized to JSON.
PyObjectId = Annotated[str, BeforeValidator(str)]

class CoordinatesModel(BaseModel):
    department: Optional[str] = None
    coordinates: List[float] = Field(..., min_items=2, max_items=2)

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
    )

class EducationalInstitutionModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str = Field(...)
    address: str = Field(...)
    location: Optional[CoordinatesModel] = None

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
        json_schema_extra={
            "example": {
                "name": "ABC University",
                "address": "123 University Ave",
                "location": {
                    "department": "Science",
                    "coordinates": [-123.456, 45.678]
                }
            }
        },
    )

class UpdateEducationalInstitutionModel(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    location: Optional[CoordinatesModel] = None

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
        json_schema_extra={
            "example": {
                "name": "XYZ University",
                "address": "456 College Rd",
                "location": {
                    "department": "Arts",
                    "coordinates": [-98.765, 54.321]
                }
            }
        },
    )

class ClassModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str = Field(...)
    teacher_id: PyObjectId = Field(...)
    student_ids: Optional[List[PyObjectId]] = None
    resources: Optional[List[ResourceModel]] = None

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
        json_schema_extra={
            "example": {
                "id": "60d5ec48f9bf5e0f57e4a5c1",
                "name": "Math 101",
                "teacher_id": "507f1f77bcf86cd799439011",
                "student_ids": ["507f1f77bcf86cd799439012", "507f1f77bcf86cd799439013"]
            }
        },
    )


class UpdateClassModel(BaseModel):
    name: Optional[str] = None
    teacher_id: Optional[PyObjectId] = None
    student_ids: Optional[List[PyObjectId]] = None

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
        json_schema_extra={
            "example": {
                "name": "Physics 201",
                "teacher_id": "507f1f77bcf86cd799439014",
                "student_ids": ["507f1f77bcf86cd799439015", "507f1f77bcf86cd799439016"]
            }
        },
    )