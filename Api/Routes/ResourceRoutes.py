from typing import List, Optional

from fastapi import FastAPI, Body, HTTPException, status, APIRouter, UploadFile, File, Form
from fastapi.responses import Response, FileResponse
from bson import ObjectId
from Api.Model.Resource import ResourceModel, CommentModel, FileModel

from Api.Config.db import educational_institutions_collection, db, grid_fs_bucket

resourcesRoutes = APIRouter()

@resourcesRoutes.post(
    "/educationalInstitutions/{institution_id}/classes/{class_id}/resources",
    response_description="Add a resource to a class",
    response_model=ResourceModel,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=False,
    tags=["educationalInstitutions"],
)
async def create_resource(
        institution_id: str,
        class_id: str,
        resource: ResourceModel = Body(...),
):
    """
    Agregar un nuevo recurso a una clase específica en una institución educativa.
    """
    resource_id = ObjectId()
    resource.id = str(resource_id)
    resource_data = resource.model_dump(by_alias=True, exclude_unset=True)
    resource_data["_id"] = resource_id

    # Agregar el nuevo recurso al arreglo 'resources' de la clase
    result = await educational_institutions_collection.update_one(
        {
            "_id": ObjectId(institution_id),
            "classes._id": ObjectId(class_id)
        },
        {
            "$push": {"classes.$.resources": resource_data}
        }
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail=f"Class {class_id} not found in institution {institution_id}")

    return resource


@resourcesRoutes.post(
    "/educationalInstitutions/{institution_id}/classes/{class_id}/resources/{resource_id}/files",
    response_description="Upload files to a resource",
    status_code=status.HTTP_201_CREATED,
    tags=["educationalInstitutions"],
)
async def upload_files(
        institution_id: str,
        class_id: str,
        resource_id: str,
        files: List[UploadFile] = File(...)
):
    """
    Subir archivos a un recurso específico en una clase.
    """
    # Verificar que el recurso existe
    institution = await educational_institutions_collection.find_one({"_id": ObjectId(institution_id)})
    if not institution:
        raise HTTPException(status_code=404, detail=f"Institution {institution_id} not found")

    resource_found = False
    for cls in institution.get("classes", []):
        if str(cls.get("_id")) == class_id:
            for res in cls.get("resources", []):
                if str(res.get("_id")) == resource_id:
                    resource_found = True
                    file_ids = res.get("file_ids", [])
                    break
            break

    if not resource_found:
        raise HTTPException(status_code=404, detail=f"Resource {resource_id} not found in class {class_id}")

    # Subir archivos a GridFS y obtener sus IDs
    uploaded_file_ids = []
    for file in files:
        contents = await file.read()
        grid_in = grid_fs_bucket.open_upload_stream(
            file.filename,
            metadata={"contentType": file.content_type}
        )
        await grid_in.write(contents)
        await grid_in.close()
        uploaded_file_ids.append(grid_in._id)

    # Actualizar el recurso con los IDs de los archivos
    result = await educational_institutions_collection.update_one(
        {
            "_id": ObjectId(institution_id),
            "classes._id": ObjectId(class_id),
            "classes.resources._id": ObjectId(resource_id)
        },
        {
            "$push": {"classes.$[class].resources.$[res].file_ids": {"$each": uploaded_file_ids}}
        },
        array_filters=[
            {"class._id": ObjectId(class_id)},
            {"res._id": ObjectId(resource_id)}
        ]
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to update resource with file IDs")

    return {"file_ids": [str(file_id) for file_id in uploaded_file_ids]}


@resourcesRoutes.get(
    "/educationalInstitutions/{institution_id}/classes/{class_id}/resources/{resource_id}",
    response_description="Get a specific resource of a class",
    response_model=ResourceModel,
    response_model_by_alias=False,
    tags=["educationalInstitutions"],
)
async def get_resource(institution_id: str, class_id: str, resource_id: str):
    """
    Obtener un recurso específico de una clase en una institución educativa.
    """
    institution = await educational_institutions_collection.find_one(
        {
            "_id": ObjectId(institution_id),
            "classes._id": ObjectId(class_id),
            "classes.resources._id": ObjectId(resource_id)
        },
        {
            "classes.$": 1  # Solo devolver la clase que coincide
        }
    )

    if not institution or "classes" not in institution:
        raise HTTPException(status_code=404, detail=f"Resource {resource_id} not found")

    resource = None
    for res in institution["classes"][0]["resources"]:
        if str(res.get("_id")) == resource_id:
            resource = res
            break

    if resource is None:
        raise HTTPException(status_code=404, detail=f"Resource {resource_id} not found")

    return ResourceModel(
        id=str(resource["_id"]),
        title=resource["title"],
        type=resource["type"],
        file_ids=[str(fid) for fid in resource.get("file_ids", [])],
        created_at=resource.get("created_at")
    )

@resourcesRoutes.get(
    "/educationalInstitutions/{institution_id}/classes/{class_id}/resources/{resource_id}/files",
    response_description="Get all files of a resource",
    tags=["educationalInstitutions"],
)
async def get_files(institution_id: str, class_id: str, resource_id: str):
    """
    Obtener todos los archivos asociados a un recurso.
    """
    institution = await educational_institutions_collection.find_one(
        {
            "_id": ObjectId(institution_id),
            "classes._id": ObjectId(class_id),
            "classes.resources._id": ObjectId(resource_id)
        },
        {
            "classes.$": 1  # Solo devolver la clase que coincide
        }
    )

    if not institution or "classes" not in institution:
        raise HTTPException(status_code=404, detail=f"Resource {resource_id} not found")

    resource = None
    for res in institution["classes"][0]["resources"]:
        if str(res.get("_id")) == resource_id:
            resource = res
            break

    if resource is None:
        raise HTTPException(status_code=404, detail=f"Resource {resource_id} not found")

    file_ids = resource.get("file_ids", [])
    files_info = []

    for file_id in file_ids:
        grid_out = await grid_fs_bucket.open_download_stream(ObjectId(file_id))
        files_info.append({
            "file_id": str(file_id),
            "filename": grid_out.filename,
            "content_type": grid_out.metadata.get("contentType") if grid_out.metadata else None,
        })
        await grid_out.close()

    return files_info


@resourcesRoutes.get(
    "/educationalInstitutions/{institution_id}/classes/{class_id}/resources/{resource_id}/files/{file_id}",
    response_description="Download a specific file from a resource",
    tags=["educationalInstitutions"],
)
async def download_resource_file(
        institution_id: str,
        class_id: str,
        resource_id: str,
        file_id: str
):
    """
    Download a specific file associated with a resource in a class.
    """
    # Validate 'file_id' and retrieve 'file_id_obj'
    try:
        file_id_obj = ObjectId(file_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid file ID format")

    # Verify that the file belongs to the resource
    institution = await educational_institutions_collection.find_one(
        {
            "_id": ObjectId(institution_id),
            "classes._id": ObjectId(class_id),
            "classes.resources._id": ObjectId(resource_id)
        },
        {
            "classes.$": 1  # Only return the matching class
        }
    )

    if not institution or "classes" not in institution:
        raise HTTPException(status_code=404, detail=f"Resource {resource_id} not found")

    resource = None
    for res in institution["classes"][0]["resources"]:
        if str(res.get("_id")) == resource_id:
            resource = res
            break

    if resource is None:
        raise HTTPException(status_code=404, detail=f"Resource {resource_id} not found")

    # Ensure 'file_id' is associated with the resource
    resource_file_ids = [ObjectId(f_id) for f_id in resource.get("file_ids", []) if ObjectId.is_valid(f_id)]
    if file_id_obj not in resource_file_ids:
        raise HTTPException(status_code=404, detail="File not found for this resource")

    # Find the file using the cursor
    grid_out_cursor = grid_fs_bucket.find({"_id": file_id_obj})
    try:
        grid_out = await grid_out_cursor.next()
    except StopAsyncIteration:
        raise HTTPException(status_code=404, detail="File not found in GridFS")

    # Read the content
    content = grid_out.read()
    content_type = grid_out.metadata.get("contentType", 'application/octet-stream') if grid_out.metadata else 'application/octet-stream'
    filename = grid_out.filename

    # Close the grid_out if it is not None
    if grid_out:
        await grid_out.close()

    # Set 'Content-Disposition' to 'inline' to display in the browser
    return Response(
        content,
        media_type=content_type,
        headers={"Content-Disposition": f'inline; filename="{filename}"'}
    )



@resourcesRoutes.get(
    "/educationalInstitutions/{institution_id}/classes/{class_id}/resources/{resource_id}/comments",
    response_description="Get all comments of a resource",
    response_model=List[CommentModel],
    response_model_by_alias=False,
    tags=["educationalInstitutions"],
)
async def get_comments(institution_id: str, class_id: str, resource_id: str):
    """
    Obtener todos los comentarios de un recurso específico en una clase.
    """
    institution = await educational_institutions_collection.find_one({"_id": ObjectId(institution_id)})

    if not institution:
        raise HTTPException(status_code=404, detail=f"Institution {institution_id} not found")

    for cls in institution.get("classes", []):
        if str(cls.get("_id")) == class_id:
            for res in cls.get("resources", []):
                if str(res.get("_id")) == resource_id:
                    comments = res.get("comments", [])
                    # Convertir los comentarios a modelos
                    return [
                        CommentModel(
                            id=str(comment.get("_id")),
                            user_id=str(comment["user_id"]),
                            content=comment["content"],
                            created_at=comment.get("created_at")
                        ) for comment in comments
                    ]
            raise HTTPException(status_code=404, detail=f"Resource {resource_id} not found")
    raise HTTPException(status_code=404, detail=f"Class {class_id} not found")


@resourcesRoutes.post(
    "/educationalInstitutions/{institution_id}/classes/{class_id}/resources/{resource_id}/comments",
    response_description="Add a comment to a resource",
    response_model=CommentModel,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=False,
    tags=["educationalInstitutions"],
)
async def create_comment(
        institution_id: str,
        class_id: str,
        resource_id: str,
        comment_data: CommentModel = Body(...)
):
    """
    Agregar un nuevo comentario a un recurso específico en una clase.
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
        raise HTTPException(status_code=404, detail=f"Resource {resource_id} not found")

    return comment_data


