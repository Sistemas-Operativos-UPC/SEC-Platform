from typing import List

from fastapi import FastAPI, Body, HTTPException, status, APIRouter
from fastapi.responses import Response
from bson import ObjectId
from pymongo import ReturnDocument

from Api.Config.db import educational_institutions_collection
from Api.Model.EducationalInstitution import EducationalInstitutionModel, UpdateEducationalInstitutionModel, ClassModel, \
    UpdateClassModel
from Api.Model.Resource import ResourceModel, CommentModel

resourcesRoutes = APIRouter()


@resourcesRoutes.get(
    "/educationalInstitutions/{institution_id}/classes/{class_id}/resources",
    response_description="Get all resources of a class",
    response_model=List[ResourceModel],
    response_model_by_alias=False,
    tags=["educationalInstitutions"],
)
async def get_resources(institution_id: str, class_id: str):
    """
    Get all resources for a specific class in an educational institution.
    """
    institution = await educational_institutions_collection.find_one({"_id": ObjectId(institution_id)})

    if institution is None:
        raise HTTPException(status_code=404, detail=f"Institution {institution_id} not found")

    classes = institution.get("classes", [])
    for cls in classes:
        if str(cls.get("_id")) == class_id:
            resources = cls.get("resources", [])
            return [
                ResourceModel(
                    id=str(res.get("_id")),
                    title=res["title"],
                    type=res["type"],
                    files=res.get("files"),
                    comments=res.get("comments"),
                    created_at=res.get("created_at")
                )
                for res in resources
            ]

    raise HTTPException(status_code=404, detail=f"Class {class_id} not found in institution {institution_id}")

@resourcesRoutes.get(
    "/educationalInstitutions/{institution_id}/classes/{class_id}/resources/{resource_id}",
    response_description="Get a specific resource of a class",
    response_model=ResourceModel,
    response_model_by_alias=False,
    tags=["educationalInstitutions"],
)
async def get_resource(institution_id: str, class_id: str, resource_id: str):
    """
    Get a specific resource of a class in an educational institution.
    """
    institution = await educational_institutions_collection.find_one({"_id": ObjectId(institution_id)})

    if institution is None:
        raise HTTPException(status_code=404, detail=f"Institution {institution_id} not found")

    for cls in institution.get("classes", []):
        if str(cls.get("_id")) == class_id:
            for res in cls.get("resources", []):
                if str(res.get("_id")) == resource_id:
                    return ResourceModel(
                        id=str(res.get("_id")),
                        title=res["title"],
                        type=res["type"],
                        files=res.get("files"),
                        comments=res.get("comments"),
                        created_at=res.get("created_at")
                    )
            raise HTTPException(status_code=404, detail=f"Resource {resource_id} not found in class {class_id}")
    raise HTTPException(status_code=404, detail=f"Class {class_id} not found in institution {institution_id}")


@resourcesRoutes.post(
    "/educationalInstitutions/{institution_id}/classes/{class_id}/resources",
    response_description="Add a resource to a class",
    response_model=ResourceModel,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=False,
    tags=["educationalInstitutions"],
)
async def create_resource(
        institution_id: str, class_id: str, resource_data: ResourceModel = Body(...)
):
    """
    Add a new resource to a specific class in an educational institution.
    """
    # Asignar un nuevo ObjectId al recurso
    resource_id = ObjectId()
    resource_data.id = str(resource_id)
    resource_dict = resource_data.model_dump(by_alias=True, exclude_unset=True)

    # Convertir 'id' a ObjectId para almacenamiento
    resource_dict["_id"] = resource_id

    # Agregar el nuevo recurso al arreglo 'resources' de la clase
    result = await educational_institutions_collection.update_one(
        {
            "_id": ObjectId(institution_id),
            "classes._id": ObjectId(class_id)
        },
        {
            "$push": {"classes.$.resources": resource_dict}
        }
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail=f"Class {class_id} not found in institution {institution_id}")

    return resource_data


@resourcesRoutes.put(
    "/educationalInstitutions/{institution_id}/classes/{class_id}/resources/{resource_id}",
    response_description="Update a resource in a class",
    response_model=ResourceModel,
    response_model_by_alias=False,
    tags=["educationalInstitutions"],
)
async def update_resource(
        institution_id: str, class_id: str, resource_id: str, resource_data: ResourceModel = Body(...)
):
    """
    Update a resource in a specific class in an educational institution.
    """
    update_data = {
        k: v for k, v in resource_data.model_dump(exclude_unset=True).items() if v is not None
    }

    if len(update_data) == 0:
        raise HTTPException(status_code=400, detail="No update data provided")

    # Actualizar el recurso utilizando arrayFilters
    result = await educational_institutions_collection.update_one(
        {
            "_id": ObjectId(institution_id),
            "classes._id": ObjectId(class_id),
            "classes.resources._id": ObjectId(resource_id)
        },
        {
            "$set": {
                **{f"classes.$[class].resources.$[res].{key}": value for key, value in update_data.items()}
            }
        },
        array_filters=[
            {"class._id": ObjectId(class_id)},
            {"res._id": ObjectId(resource_id)}
        ]
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail=f"Resource {resource_id} not found in class {class_id}")

    # Devolver el recurso actualizado
    institution = await educational_institutions_collection.find_one({"_id": ObjectId(institution_id)})

    if institution is None:
        raise HTTPException(status_code=404, detail=f"Institution {institution_id} not found")

    for cls in institution.get("classes", []):
        if str(cls.get("_id")) == class_id:
            for res in cls.get("resources", []):
                if str(res.get("_id")) == resource_id:
                    return ResourceModel(
                        id=str(res.get("_id")),
                        title=res["title"],
                        type=res["type"],
                        files=res.get("files"),
                        comments=res.get("comments"),
                        created_at=res.get("created_at")
                    )
    raise HTTPException(status_code=404, detail=f"Resource {resource_id} not found after update")


@resourcesRoutes.delete(
    "/educationalInstitutions/{institution_id}/classes/{class_id}/resources/{resource_id}",
    response_description="Delete a resource from a class",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["educationalInstitutions"],
)
async def delete_resource(institution_id: str, class_id: str, resource_id: str):
    """
    Delete a resource from a specific class in an educational institution.
    """
    result = await educational_institutions_collection.update_one(
        {
            "_id": ObjectId(institution_id),
            "classes._id": ObjectId(class_id)
        },
        {
            "$pull": {"classes.$.resources": {"_id": ObjectId(resource_id)}}
        }
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail=f"Resource {resource_id} not found in class {class_id}")

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@resourcesRoutes.post(
    "/educationalInstitutions/{institution_id}/classes/{class_id}/resources/{resource_id}/comments",
    response_description="Add a comment to a resource",
    response_model=CommentModel,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=False,
    tags=["educationalInstitutions"],
)
async def create_comment(
        institution_id: str, class_id: str, resource_id: str, comment_data: CommentModel = Body(...)
):
    """
    Add a new comment to a specific resource in a class.
    """
    # Asignar un nuevo ObjectId al comentario
    comment_id = ObjectId()
    comment_data.id = str(comment_id)
    comment_dict = comment_data.model_dump(by_alias=True, exclude_unset=True)

    # Convertir 'id' y 'user_id' a ObjectId para almacenamiento
    comment_dict["_id"] = comment_id
    comment_dict["user_id"] = ObjectId(comment_dict["user_id"])

    # Agregar el nuevo comentario al arreglo 'comments' del recurso
    result = await educational_institutions_collection.update_one(
        {
            "_id": ObjectId(institution_id),
            "classes._id": ObjectId(class_id),
            "classes.resources._id": ObjectId(resource_id)
        },
        {
            "$push": {"classes.$[class].resources.$[res].comments": comment_dict}
        },
        array_filters=[
            {"class._id": ObjectId(class_id)},
            {"res._id": ObjectId(resource_id)}
        ]
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail=f"Resource {resource_id} not found in class {class_id}")

    return comment_data

