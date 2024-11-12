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

def get_views_by_type(view_type):
    """Fetch views from MongoDB based on view_type ('sell' or 'buy')."""
    return list(wlcollection.find({"view_type": view_type}))

def fetch_view_from_db(view_id):
    """Fetch a single view from MongoDB based on view_id."""
    return wlcollection.find_one({"view_id": view_id})

def delete_view_from_db(view_id):
    try:
        wlcollection.delete_one({"view_id": view_id})
        print(f"Successfully deleted view with ID {view_id} from the database.")
    except Exception as e:
        print(f"Failed to delete view with ID {view_id}: {e}")