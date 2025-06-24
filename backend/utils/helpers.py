import requests
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google.cloud import storage
import json

def cloud_render(scene_code, id):
    service_account_file = 'key.json'
    target_audience = 'https://render-api-431158145985.us-east1.run.app'

    # Get ID token for Cloud Run
    credentials = service_account.IDTokenCredentials.from_service_account_file(
        service_account_file,
        target_audience=target_audience
    )

    # Refresh token
    request = Request()
    credentials.refresh(request)
    id_token_str = credentials.token

    url = f"{target_audience}/render"
    headers = {'Authorization': f'Bearer {id_token_str}'}
    data = {
        "code": scene_code,
        "id": id
    }

    response = requests.post(url, headers=headers, json=data)
    try:
        return response.json()
    except Exception:
        return {"error": f"Request failed with status {response.status_code}", "details": response.text}

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

    