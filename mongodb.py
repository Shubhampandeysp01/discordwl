import json
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
with open('config.json', 'r') as file:
    config = json.load(file)


MONGO_URI  = config["MongoURI"]

client = MongoClient(MONGO_URI )

db = client['dbone']
wlcollection = db['wlcollection']

def save_view(data):
    """Save the view data to MongoDB."""
    wlcollection.update_one(
        {"view_id": data['view_id']}, 
        {"$set": data}, 
        upsert=True
    )

def get_views():
    return list(wlcollection.find())

def delete_view(view_id):
    wlcollection.delete_one({"view_id": view_id})
