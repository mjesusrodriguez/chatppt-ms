from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

# Leer MONGO_URI del entorno
#MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://host.docker.internal:27017/')

class MongoDB:
    def __init__(self, uri=None):
        if uri is None:
            uri = MONGO_URI  # Usar la URI del entorno si no se pasa otra
        self.client = MongoClient(uri)

    def get_collection(self, db_name, collection_name):
        db = self.client[db_name]
        return db[collection_name]

    def close_connection(self):
        self.client.close()