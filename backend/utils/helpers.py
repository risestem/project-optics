import os
import subprocess
import tempfile
import requests
import json
import uuid

def clear_bucket(session_id):
    pass

def fetch_history(session_id):
    with open("chat_history.json", "r") as f:
        history = json.load(f)
    return history.get(session_id, [])

def generate_session():
    return str(uuid.uuid4())
