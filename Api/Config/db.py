import motor.motor_asyncio

uri = "mongodb+srv://SEC:FzOsXLbVGfKnpqcQ@cluster0.pixei.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = motor.motor_asyncio.AsyncIOMotorClient(uri)
db = client.SEC

users_collection = db.get_collection("users")
educational_institutions_collection = db.get_collection("educational_institutions")