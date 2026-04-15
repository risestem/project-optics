import os
import subprocess
import tempfile
import requests
import json
import uuid

def clear_bucket(session_id):
    credentials = service_account.Credentials.from_service_account_file("key.json")
    storage_client = storage.Client(credentials=credentials)
    bucket = storage_client.bucket("manim-renders")
    blob = bucket.blob(f"{session_id}.mp4")
    blob.delete()

def fetch_history(session_id):
    with open("chat_history.json", "r") as f:
        history = json.load(f)
    return history.get(session_id, [])

def generate_session():
    return str(uuid.uuid4())
