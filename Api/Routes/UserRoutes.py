from typing import List

from fastapi import FastAPI, Body, HTTPException, status, APIRouter
from fastapi.responses import Response
from bson import ObjectId
from pymongo import ReturnDocument

from Api.Config.db import users_collection
from Api.Model.User import UserModel, UserCollectionModel, UpdateUserModel

userRoutes = APIRouter()

def hash_password(password: str) -> str:
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

# Crear un nuevo usuario
@userRoutes.post(
    "/users/",
    response_description="Add new user",
    response_model=UserModel,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=False,
    tags=["users"],
)
async def create_user(user: UserModel = Body(...)):
    """
    Insertar un nuevo registro de usuario.

    Se creará un `id` único y se proporcionará en la respuesta.
    """
    # Hashear la contraseña antes de guardar
    user.password = hash_password(user.password)

    new_user = await users_collection.insert_one(
        user.model_dump(by_alias=True, exclude=["id"])
    )
    created_user = await users_collection.find_one(
        {"_id": new_user.inserted_id}
    )
    return created_user

# Obtener todos los usuarios
@userRoutes.get(
    "/users/",
    response_description="List all users",
    response_model=List[UserModel],
    response_model_by_alias=False,
    tags=["users"],
)
async def list_users():
    """
    Listar todos los datos de usuarios sin su contrasena
    """
    users = []
    async for user in users_collection.find():
        users.append(user)
    return users

# Obtener un usuario por ID
@userRoutes.get(
    "/users/{id}",
    response_description="Get a single user",
    response_model=UserModel,
    response_model_by_alias=False,
    tags=["users"],
)
async def show_user(id: str):
    """
    Obtener el registro de un usuario específico, buscado por `id`.
    """
    if (user := await users_collection.find_one({"_id": ObjectId(id)})) is not None:
        return user

    raise HTTPException(status_code=404, detail=f"User {id} not found")

# Actualizar un usuario
@userRoutes.put(
    "/users/{id}",
    response_description="Update a user",
    response_model=UserModel,
    response_model_by_alias=False,
    tags=["users"],
)
async def update_user(id: str, user: UpdateUserModel = Body(...)):
    """
    Actualizar campos individuales de un registro de usuario existente.

    Solo se actualizarán los campos proporcionados.
    Cualquier campo faltante o `null` será ignorado.
    """
    update_data = {k: v for k, v in user.dict(exclude_unset=True).items() if v is not None}

    if "password" in update_data:
        update_data["password"] = hash_password(update_data["password"])

    if len(update_data) >= 1:
        updated_user = await users_collection.find_one_and_update(
            {"_id": ObjectId(id)},
            {"$set": update_data},
            return_document=ReturnDocument.AFTER,
        )
        if updated_user is not None:
            return updated_user
        else:
            raise HTTPException(status_code=404, detail=f"User {id} not found")

    # La actualización está vacía, pero aún debemos devolver el documento coincidente
    if (existing_user := await users_collection.find_one({"_id": ObjectId(id)})) is not None:
        return existing_user

    raise HTTPException(status_code=404, detail=f"User {id} not found")

# Eliminar un usuario
@userRoutes.delete(
    "/users/{id}",
    response_description="Delete a user",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["users"],
)
async def delete_user(id: str):
    """
    Eliminar un solo registro de usuario de la base de datos.
    """
    delete_result = await users_collection.delete_one({"_id": ObjectId(id)})

    if delete_result.deleted_count == 1:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    raise HTTPException(status_code=404, detail=f"User {id} not found")
