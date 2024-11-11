from motor.motor_asyncio import AsyncIOMotorGridFSBucket, AsyncIOMotorClient
import os

uri = os.getenv("MONGO_URI")

if not uri:
    raise ValueError("MONGO_URI is not set")

client = AsyncIOMotorClient(uri)
db = client.SEC

# Configurar GridFS
grid_fs_bucket = AsyncIOMotorGridFSBucket(db)

users_collection = db.get_collection("users")
educational_institutions_collection = db.get_collection("educational_institutions")