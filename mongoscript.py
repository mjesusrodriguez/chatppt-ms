from pymongo import MongoClient

# Conexión al contenedor de MongoDB desde fuera de Docker
client = MongoClient("mongodb://localhost:27017/")
db = client["restaurants"]

# Intents a insertar
intents = [
    {"intent": "reserve_table"},
    {"intent": "get_menu"},
    {"intent": "cancel_reservation"}
]

# Colección de intents
intents_collection = db["intents"]

# Inserta si no están ya
for intent in intents:
    if not intents_collection.find_one({"intent": intent["intent"]}):
        intents_collection.insert_one(intent)

print("Intents insertados correctamente.")