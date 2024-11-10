from datetime import datetime
from typing import Optional, List

from pydantic import ConfigDict, BaseModel, Field, EmailStr
from pydantic.functional_validators import BeforeValidator

from typing_extensions import Annotated

from bson import ObjectId

# Represents an ObjectId field in the database.
# It will be represented as a `str` on the model so that it can be serialized to JSON.
PyObjectId = Annotated[str, BeforeValidator(str)]

class CommentModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    user_id: PyObjectId = Field(...)
    content: str = Field(...)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
    )

class FileModel(BaseModel):
    file_name: str = Field(...)
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
    )


class ResourceModel(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)
    title: str = Field(...)
    type: str = Field(..., enum=["document", "video", "image"])
    file_ids: Optional[List[str]] = None  # Lista de IDs de archivos en GridFS
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
    )
