from typing import List

from fastapi import FastAPI, Body, HTTPException, status, APIRouter
from fastapi.responses import Response
from bson import ObjectId
from pymongo import ReturnDocument

from Api.Config.db import educational_institutions_collection
from Api.Model.EducationalInstitution import EducationalInstitutionModel, UpdateEducationalInstitutionModel, ClassModel, \
    UpdateClassModel

educationalInstitutionRoutes = APIRouter()

@educationalInstitutionRoutes.post(
    "/educationalInstitutions/",
    response_description="Add new educational institution",
    response_model=EducationalInstitutionModel,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=False,
    tags=["educationalInstitutions"],
)
async def create_educational_institution(
        institution: EducationalInstitutionModel = Body(...)
):
    """
    Insert a new educational institution record.

    A unique `id` will be created and provided in the response.
    """
    new_institution = await educational_institutions_collection.insert_one(
        institution.model_dump(by_alias=True, exclude={"id"})
    )
    created_institution = await educational_institutions_collection.find_one(
        {"_id": new_institution.inserted_id}
    )

    if created_institution is None:
        raise HTTPException(status_code=404, detail="Institution not found after creation")

    return EducationalInstitutionModel(
        id=str(created_institution["_id"]),
        name=created_institution["name"],
        address=created_institution["address"],
        location=created_institution.get("location")
    )


@educationalInstitutionRoutes.get(
    "/educationalInstitutions/",
    response_description="List all educational institutions",
    response_model=List[EducationalInstitutionModel],
    response_model_by_alias=False,
    tags=["educationalInstitutions"],
)
async def list_educational_institutions():
    """
    List all educational institutions in the database.

    The response is unpaginated and limited to 1000 results.
    """
    institutions = await educational_institutions_collection.find().to_list(1000)
    return [
        EducationalInstitutionModel(
            id=str(inst["_id"]),
            name=inst["name"],
            address=inst["address"],
            location=inst.get("location")
        )
        for inst in institutions
    ]

@educationalInstitutionRoutes.get(
    "/educationalInstitutions/{id}",
    response_description="Get a single educational institution",
    response_model=EducationalInstitutionModel,
    response_model_by_alias=False,
    tags=["educationalInstitutions"],
)
async def show_educational_institution(id: str):
    """
    Get the record for a specific educational institution, looked up by `id`.
    """
    institution = await educational_institutions_collection.find_one({"_id": ObjectId(id)})

    if institution is None:
        raise HTTPException(status_code=404, detail=f"Institution {id} not found")

    return EducationalInstitutionModel(
        id=str(institution["_id"]),
        name=institution["name"],
        address=institution["address"],
        location=institution.get("location")
    )

@educationalInstitutionRoutes.put(
    "/educationalInstitutions/{id}",
    response_description="Update an educational institution",
    response_model=EducationalInstitutionModel,
    response_model_by_alias=False,
    tags=["educationalInstitutions"],
)
async def update_educational_institution(
        id: str, institution: UpdateEducationalInstitutionModel = Body(...)
):
    """
    Update individual fields of an existing educational institution record.

    Only the provided fields will be updated.
    Any missing or `null` fields will be ignored.
    """
    update_data = {
        k: v for k, v in institution.model_dump(exclude_unset=True).items() if v is not None
    }

    if len(update_data) >= 1:
        updated_institution = await educational_institutions_collection.find_one_and_update(
            {"_id": ObjectId(id)},
            {"$set": update_data},
            return_document=ReturnDocument.AFTER,
        )
        if updated_institution is not None:
            return EducationalInstitutionModel(
                id=str(updated_institution["_id"]),
                name=updated_institution["name"],
                address=updated_institution["address"],
                location=updated_institution.get("location")
            )
        else:
            raise HTTPException(status_code=404, detail=f"Institution {id} not found")

    # The update is empty, but we should still return the matching document:
    existing_institution = await educational_institutions_collection.find_one({"_id": ObjectId(id)})
    if existing_institution is not None:
        return EducationalInstitutionModel(
            id=str(existing_institution["_id"]),
            name=existing_institution["name"],
            address=existing_institution["address"],
            location=existing_institution.get("location")
        )

    raise HTTPException(status_code=404, detail=f"Institution {id} not found")

@educationalInstitutionRoutes.delete(
    "/educationalInstitutions/{id}",
    response_description="Delete an educational institution",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["educationalInstitutions"],
)
async def delete_educational_institution(id: str):
    """
    Remove a single educational institution record from the database.
    """
    delete_result = await educational_institutions_collection.delete_one({"_id": ObjectId(id)})

    if delete_result.deleted_count == 1:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    raise HTTPException(status_code=404, detail=f"Institution {id} not found")


@educationalInstitutionRoutes.get(
    "/educationalInstitutions/{institution_id}/classes",
    response_description="Get all classes of an educational institution",
    response_model=List[ClassModel],
    response_model_by_alias=False,
    tags=["educationalInstitutions"],
)
async def get_classes(institution_id: str):
    """
    Get all classes for a specific educational institution.
    """
    institution = await educational_institutions_collection.find_one({"_id": ObjectId(institution_id)})

    if institution is None:
        raise HTTPException(status_code=404, detail=f"Institution {institution_id} not found")

    classes = institution.get("classes", [])

    # Convertir los datos a modelos ClassModel
    return [
        ClassModel(
            id=str(cls.get("_id")),
            name=cls["name"],
            teacher_id=str(cls["teacher_id"]),
            student_ids=[str(sid) for sid in cls.get("student_ids", [])]
        )
        for cls in classes
    ]


@educationalInstitutionRoutes.get(
    "/educationalInstitutions/{institution_id}/classes/{class_id}",
    response_description="Get a specific class of an educational institution",
    response_model=ClassModel,
    response_model_by_alias=False,
    tags=["educationalInstitutions"],
)
async def get_class(institution_id: str, class_id: str):
    """
    Get a specific class of a specific educational institution.
    """
    institution = await educational_institutions_collection.find_one({"_id": ObjectId(institution_id)})

    if institution is None:
        raise HTTPException(status_code=404, detail=f"Institution {institution_id} not found")

    classes = institution.get("classes", [])

    for cls in classes:
        if str(cls.get("_id")) == class_id:
            return ClassModel(
                id=str(cls.get("_id")),
                name=cls["name"],
                teacher_id=str(cls["teacher_id"]),
                student_ids=[str(sid) for sid in cls.get("student_ids", [])]
            )

    raise HTTPException(status_code=404, detail=f"Class {class_id} not found in institution {institution_id}")


@educationalInstitutionRoutes.post(
    "/educationalInstitutions/{institution_id}/classes",
    response_description="Add a class to an educational institution",
    response_model=ClassModel,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=False,
    tags=["educationalInstitutions"],
)
async def create_class(institution_id: str, class_data: ClassModel = Body(...)):
    """
    Add a new class to a specific educational institution.
    """
    # Asignar un nuevo ObjectId a la clase
    class_id = ObjectId()
    class_data.id = str(class_id)
    class_dict = class_data.model_dump(by_alias=True, exclude_unset=True)

    # Convertir 'id' y otros campos a ObjectId para almacenamiento
    class_dict["_id"] = class_id
    class_dict["teacher_id"] = ObjectId(class_dict["teacher_id"])
    class_dict["student_ids"] = [ObjectId(sid) for sid in class_dict.get("student_ids", [])]

    # Agregar la nueva clase al arreglo 'classes'
    result = await educational_institutions_collection.update_one(
        {"_id": ObjectId(institution_id)},
        {"$push": {"classes": class_dict}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail=f"Institution {institution_id} not found")

    return class_data


@educationalInstitutionRoutes.put(
    "/educationalInstitutions/{institution_id}/classes/{class_id}",
    response_description="Update a class of an educational institution",
    response_model=ClassModel,
    response_model_by_alias=False,
    tags=["educationalInstitutions"],
)
async def update_class(
        institution_id: str, class_id: str, class_data: UpdateClassModel = Body(...)
):
    """
    Update a class of a specific educational institution.
    """
    update_data = {
        k: v for k, v in class_data.model_dump(exclude_unset=True).items() if v is not None
    }

    if len(update_data) == 0:
        raise HTTPException(status_code=400, detail="No update data provided")

    # Convertir 'teacher_id' y 'student_ids' a ObjectId si están presentes
    if "teacher_id" in update_data:
        update_data["teacher_id"] = ObjectId(update_data["teacher_id"])
    if "student_ids" in update_data:
        update_data["student_ids"] = [ObjectId(sid) for sid in update_data["student_ids"]]

    # Actualizar la clase utilizando arrayFilters
    result = await educational_institutions_collection.update_one(
        {
            "_id": ObjectId(institution_id),
            "classes._id": ObjectId(class_id)
        },
        {
            "$set": {
                **{f"classes.$[elem].{key}": value for key, value in update_data.items()}
            }
        },
        array_filters=[{"elem._id": ObjectId(class_id)}]
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail=f"Class {class_id} not found in institution {institution_id}")

    # Devolver la clase actualizada
    institution = await educational_institutions_collection.find_one({"_id": ObjectId(institution_id)})

    if institution is None:
        raise HTTPException(status_code=404, detail=f"Institution {institution_id} not found")

    classes = institution.get("classes", [])
    for cls in classes:
        if str(cls.get("_id")) == class_id:
            return ClassModel(
                id=str(cls.get("_id")),
                name=cls["name"],
                teacher_id=str(cls["teacher_id"]),
                student_ids=[str(sid) for sid in cls.get("student_ids", [])]
            )

    raise HTTPException(status_code=404, detail=f"Class {class_id} not found after update")


@educationalInstitutionRoutes.delete(
    "/educationalInstitutions/{institution_id}/classes/{class_id}",
    response_description="Delete a class from an educational institution",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["educationalInstitutions"],
)
async def delete_class(institution_id: str, class_id: str):
    """
    Delete a class from a specific educational institution.
    """
    result = await educational_institutions_collection.update_one(
        {"_id": ObjectId(institution_id)},
        {"$pull": {"classes": {"_id": ObjectId(class_id)}}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail=f"Class {class_id} not found in institution {institution_id}")

    return Response(status_code=status.HTTP_204_NO_CONTENT)