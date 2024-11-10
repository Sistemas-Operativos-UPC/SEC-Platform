from datetime import datetime
from typing import Optional, List

from pydantic import ConfigDict, BaseModel, Field, EmailStr
from pydantic.functional_validators import BeforeValidator

from typing_extensions import Annotated

from bson import ObjectId

# Represents an ObjectId field in the database.
# It will be represented as a `str` on the model so that it can be serialized to JSON.
PyObjectId = Annotated[str, BeforeValidator(str)]

class NameModel(BaseModel):
    """
    Modelo para representar el nombre de un usuario.
    """
    first_name: str = Field(...)
    last_name: str = Field(...)


class UserModel(BaseModel):
    """
    Contenedor para un solo registro de usuario.
    """

    # La clave primaria para UserModel, almacenada como `str` en la instancia.
    # Esto será alias como `_id` cuando se envíe a MongoDB,
    # pero se proporcionará como `id` en las solicitudes y respuestas de la API.
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: NameModel = Field(...)
    email: EmailStr = Field(...)
    password: str = Field(...)
    role: str = Field(..., enum=["teacher", "student", "parent"])
    birth_date: Optional[datetime] = None
    educational_institution_id: Optional[PyObjectId] = None

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "name": {
                    "first_name": "John",
                    "last_name": "Doe"
                },
                "email": "johndoe@example.com",
                "password": "securepassword123",
                "role": "student",
                "birth_date": "2000-01-01T00:00:00Z"
            }
        },
    )


class UpdateUserModel(BaseModel):
    """
    Un conjunto de actualizaciones opcionales para realizar en un documento de usuario en la base de datos.
    """

    name: Optional[NameModel] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[str] = Field(None, enum=["teacher", "student", "parent"])
    birth_date: Optional[datetime] = None
    educational_institution_id: Optional[PyObjectId] = None

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
        json_schema_extra={
            "example": {
                "name": {
                    "first_name": "Jane",
                    "last_name": "Smith"
                },
                "email": "janesmith@example.com",
                "password": "newsecurepassword456",
                "role": "teacher",
                "birth_date": "1990-05-15T00:00:00Z",
                "educational_institution_id": "507f1f77bcf86cd799439011"
            }
        },
    )


class UserCollectionModel(BaseModel):
    """
    Un contenedor que contiene una lista de instancias de `UserModel`.

    Esto existe porque proporcionar una matriz de nivel superior en una respuesta JSON puede ser una vulnerabilidad.
    """

    users: List[UserModel]