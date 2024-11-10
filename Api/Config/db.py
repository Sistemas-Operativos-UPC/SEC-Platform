from motor.motor_asyncio import AsyncIOMotorGridFSBucket, AsyncIOMotorClient

uri = "mongodb+srv://SEC:FzOsXLbVGfKnpqcQ@cluster0.pixei.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = AsyncIOMotorClient(uri)
db = client.SEC

# Configurar GridFS
grid_fs_bucket = AsyncIOMotorGridFSBucket(db)

users_collection = db.get_collection("users")
educational_institutions_collection = db.get_collection("educational_institutions")