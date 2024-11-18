import uuid

from fastapi import FastAPI, HTTPException, UploadFile
from typing import List
from fastapi.responses import StreamingResponse
from bson.objectid import ObjectId
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorGridFSBucket, AsyncIOMotorClient
from typing import Dict
from pydantic import BaseModel, Field
import hashlib


# import os
#
# uri = os.getenv("MONGO_URI")
#
# if not uri:
#     raise ValueError("MONGO_URI is not set")

uri = "mongodb+srv://SEC:EuFysgbX0pid5Rjq@cluster0.pixei.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

if not uri:
    raise ValueError("MONGO_URI is not set")

client = AsyncIOMotorClient(uri)
db = client.SEC

fs = AsyncIOMotorGridFSBucket(db, bucket_name="my-files")
app = FastAPI(
    title="SEC API",
    summary="API para el Sistema de Educación Continua",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todas las orígenes. Cámbialo a una lista específica de orígenes en producción.
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos (GET, POST, etc.).
    allow_headers=["*"],  # Permite todos los encabezados.
)

educational_institutions_collection = db.educational_institutions

class ClassSchema(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))  # Genera un id único
    name: str
    teacher_id: str
    resources: List[dict] = []
    comments: List[dict] = []

class EducationalInstitutionSchema(BaseModel):
    name: str
    address: str
    classes: List[ClassSchema] = []

class ResourceSchema(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))  # Genera un id único
    title: str
    description: str
    file_ids: List[str] = []

class CommentSchema(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))  # Genera un id único
    content: str
    author_id: str

# Helper para convertir ObjectId a str y agregar `id` en los elementos anidados
def add_ids(data):
    if "_id" in data:
        data["id"] = str(data.pop("_id"))  # Convierte `_id` a `id`

    # Asegúrate de que cada clase, recurso y comentario tenga su `id`
    for cls in data.get("classes", []):
        if "_id" in cls:
            cls["id"] = str(cls.pop("_id"))  # Convierte `_id` de la clase a `id`
        elif "id" not in cls:
            cls["id"] = str(uuid.uuid4())  # Asigna un nuevo `id` si no existe

        # Asegúrate de que cada recurso tenga un `id`
        for res in cls.get("resources", []):
            if "_id" in res:
                res["id"] = str(res.pop("_id"))  # Convierte `_id` del recurso a `id`
            elif "id" not in res:
                res["id"] = str(uuid.uuid4())  # Asigna un nuevo `id` si no existe

        # Asegúrate de que cada comentario tenga un `id`
        for com in cls.get("comments", []):
            if "_id" in com:
                com["id"] = str(com.pop("_id"))  # Convierte `_id` del comentario a `id`
            elif "id" not in com:
                com["id"] = str(uuid.uuid4())  # Asigna un nuevo `id` si no existe

    return data

# Endpoints para Educational Institutions
@app.post("/api/v1/educational-institutions/", tags=["Educational Institutions"])
async def create_educational_institution(institution: EducationalInstitutionSchema):
    result = await educational_institutions_collection.insert_one(institution.dict())
    return {"id": str(result.inserted_id), **institution.dict()}

@app.get("/api/v1/educational-institutions/", tags=["Educational Institutions"])
async def list_educational_institutions():
    institutions = await educational_institutions_collection.find().to_list(100)
    return [add_ids(inst) for inst in institutions]

@app.get("/api/v1/educational-institutions/{institution_id}", tags=["Educational Institutions"])
async def get_educational_institution(institution_id: str):
    institution = await educational_institutions_collection.find_one({"_id": ObjectId(institution_id)})
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")
    return add_ids(institution)

# Endpoints para Classes
@app.post("/api/v1/educational-institutions/{institution_id}/classes", tags=["Classes"])
async def create_class(institution_id: str, class_data: ClassSchema):
    institution = await educational_institutions_collection.find_one({"_id": ObjectId(institution_id)})
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")

    class_dict = class_data.dict()
    await educational_institutions_collection.update_one(
        {"_id": ObjectId(institution_id)},
        {"$push": {"classes": class_dict}}
    )
    return class_dict

@app.get("/api/v1/educational-institutions/{institution_id}/classes/{class_id}", tags=["Classes"])
async def get_class(institution_id: str, class_id: str):
    institution = await educational_institutions_collection.find_one({"_id": ObjectId(institution_id)})
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")

    class_item = next((cls for cls in institution.get("classes", []) if cls.get("id") == class_id), None)
    if not class_item:
        raise HTTPException(status_code=404, detail="Class not found")

    return class_item

# Endpoints para Resources
@app.post("/api/v1/educational-institutions/{institution_id}/classes/{class_id}/resources", tags=["Resources"])
async def create_resource(institution_id: str, class_id: str, resource: ResourceSchema):
    institution = await educational_institutions_collection.find_one({"_id": ObjectId(institution_id)})
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")

    class_list = institution.get("classes", [])
    class_item = next((cls for cls in class_list if cls.get("id") == class_id), None)
    if not class_item:
        raise HTTPException(status_code=404, detail="Class not found")

    resource_dict = resource.dict()
    class_item["resources"].append(resource_dict)
    await educational_institutions_collection.update_one(
        {"_id": ObjectId(institution_id)},
        {"$set": {"classes": class_list}}
    )
    return resource_dict

@app.get("/api/v1/educational-institutions/{institution_id}/classes/{class_id}/resources", tags=["Resources"])
async def list_resources(institution_id: str, class_id: str):
    institution = await educational_institutions_collection.find_one({"_id": ObjectId(institution_id)})
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")

    class_list = institution.get("classes", [])
    class_item = next((cls for cls in class_list if cls.get("id") == class_id), None)
    if not class_item:
        raise HTTPException(status_code=404, detail="Class not found")

    return class_item.get("resources", [])

@app.get("/api/v1/educational-institutions/{institution_id}/classes/{class_id}/resources/{resource_id}", tags=["Resources"])
async def get_resource(institution_id: str, class_id: str, resource_id: str):
    institution = await educational_institutions_collection.find_one({"_id": ObjectId(institution_id)})
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")

    class_list = institution.get("classes", [])
    class_item = next((cls for cls in class_list if cls.get("id") == class_id), None)
    if not class_item:
        raise HTTPException(status_code=404, detail="Class not found")

    resource = next((res for res in class_item.get("resources", []) if res.get("id") == resource_id), None)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    return resource

# Endpoints para Comments
@app.post("/api/v1/educational-institutions/{institution_id}/classes/{class_id}/comments", tags=["Comments"])
async def create_comment(institution_id: str, class_id: str, comment: CommentSchema):
    institution = await educational_institutions_collection.find_one({"_id": ObjectId(institution_id)})
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")

    class_list = institution.get("classes", [])
    class_item = next((cls for cls in class_list if cls.get("id") == class_id), None)
    if not class_item:
        raise HTTPException(status_code=404, detail="Class not found")

    comment_dict = comment.dict()
    class_item["comments"].append(comment_dict)
    await educational_institutions_collection.update_one(
        {"_id": ObjectId(institution_id)},
        {"$set": {"classes": class_list}}
    )
    return comment_dict

@app.get("/api/v1/educational-institutions/{institution_id}/classes/{class_id}/comments", tags=["Comments"])
async def list_comments(institution_id: str, class_id: str):
    institution = await educational_institutions_collection.find_one({"_id": ObjectId(institution_id)})
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")

    class_list = institution.get("classes", [])
    class_item = next((cls for cls in class_list if cls.get("id") == class_id), None)
    if not class_item:
        raise HTTPException(status_code=404, detail="Class not found")

    return class_item.get("comments", [])

@app.get("/api/v1/educational-institutions/{institution_id}/classes/{class_id}/comments/{comment_id}", tags=["Comments"])
async def get_comment(institution_id: str, class_id: str, comment_id: str):
    institution = await educational_institutions_collection.find_one({"_id": ObjectId(institution_id)})
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")

    class_list = institution.get("classes", [])
    class_item = next((cls for cls in class_list if cls.get("id") == class_id), None)
    if not class_item:
        raise HTTPException(status_code=404, detail="Class not found")

    comment = next((com for com in class_item.get("comments", []) if com.get("id") == comment_id), None)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    return comment




users_collection = db.users

# Esquemas Pydantic
class SignUpRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str  # Puede ser "principal", "teacher", "student", o "parent"

class SignInRequest(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str

# Helper para encriptar contraseñas
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# Endpoint de Sign-Up
@app.post("/api/v1/auth/sign-up", response_model=UserResponse, tags=["Authentication"])
async def sign_up(request: SignUpRequest):
    # Verificar si el email ya está registrado
    existing_user = await users_collection.find_one({"email": request.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = hash_password(request.password)
    user = {
        "name": request.name,
        "email": request.email,
        "password": hashed_password,  # Contraseña encriptada
        "role": request.role
    }
    result = await users_collection.insert_one(user)
    user_id = str(result.inserted_id)

    return {"id": user_id, "name": user["name"], "email": user["email"], "role": user["role"]}

# Endpoint de Sign-In
@app.post("/api/v1/auth/sign-in", tags=["Authentication"])
async def sign_in(request: SignInRequest):
    user = await users_collection.find_one({"email": request.email})
    if not user or user["password"] != hash_password(request.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return {"message": "Sign-in successful", "user_id": str(user["_id"]), "name": user["name"], "role": user["role"]}











# Endpoint para subir archivos
@app.post("/api/v1/files/upload", tags=["Files"], summary="Subir un archivo")
async def upload_file(file: UploadFile):
    try:
        file_id = await fs.upload_from_stream(file.filename, file.file, metadata={"contentType": file.content_type})
        return {"file_id": str(file_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint para descargar o mostrar archivos
@app.get("/api/v1/files/{file_id}", tags=["Files"], summary="Descargar o mostrar un archivo")
async def get_file(file_id: str):
    """
    Descarga o muestra un archivo desde la base de datos.

    - **file_id**: El identificador único del archivo.
    - El archivo se devuelve con el `Content-Type` correcto para que pueda ser mostrado en el navegador.
    """
    try:
        file_data = await fs.open_download_stream(ObjectId(file_id))
        if not file_data:
            raise HTTPException(status_code=404, detail="File not found")

        headers = {"Content-Type": file_data.metadata.get("contentType", "application/octet-stream")}
        return StreamingResponse(file_data, headers=headers)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))