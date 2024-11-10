from fastapi import FastAPI

from Api.Routes.EducationalInstitutionRoutes import educationalInstitutionRoutes
from Api.Routes.ResourceRoutes import resourcesRoutes
from Api.Routes.StudentRoutes import studentRoutes
from Api.Config.db import student_collection, users_collection, educational_institutions_collection
from Api.Routes.UserRoutes import userRoutes

app = FastAPI(
    title="Student Course API",
    summary="A sample application showing how to use FastAPI to add a ReST API to a MongoDB collection.",
)
app.include_router(studentRoutes)
app.include_router(userRoutes)

app.include_router(educationalInstitutionRoutes)
app.include_router(resourcesRoutes)
