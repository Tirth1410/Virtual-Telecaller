
from pymongo import MongoClient
import json
import os
from dotenv import load_dotenv
load_dotenv()


mongodb_uri = os.getenv("MONGODB_URI")

def save_data_to_mongo(business_name, business_data, system_prompt, source_Number, destination_Number):
    client = None
    try:
        client = MongoClient("mongodb://localhost:27017/")
        db = client["virtual_telecaller"]
        collection = db["user_data"]


        document = {
            "business_name": business_name,
            "business_data": business_data,
            "system_prompt": system_prompt,
            "source_number": source_Number,
            "destination_number": destination_Number
        }

        collection.insert_one(document)
        print("Data saved to MongoDB successfully.")
    except Exception as e:
        print(f"Error saving data to MongoDB: {e}")
    finally:
        if client:
            client.close()



def save_call_conversation(call_sid,call_text):
    client = None
    try:
        client = MongoClient(mongodb_uri)
        db = client["Virtual_tellecaller"]
        collection = db["call_conversations"]
        document = {
            "call_sid":call_sid,
            "call_text":call_text
        }


        collection.insert_one(document)
        print("Call conversation saved to MongoDB successfully.")
    except Exception as e:
        print(f"Error saving call conversation to MongoDB:{e}")
    finally:
        if client:
            client.close()



