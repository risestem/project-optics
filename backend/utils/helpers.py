import os
import subprocess
import tempfile
import requests
import json

def animate_scene(scene_code, id):
    if "from manim import *" not in scene_code:
        scene_code = "from manim import *\n" + scene_code

    with tempfile.NamedTemporaryFile('w', prefix='manim_', suffix='.py', delete=False) as temp_file:
        temp_file.write(scene_code)
        temp_file_path = temp_file.name

    file_name = os.path.splitext(os.path.basename(temp_file_path))[0]
    try:
        cmd = [
            'manim',
            '-qh',
            temp_file_path,
            'LessonScene',
            '--media_dir', f'/tmp/{id}',
            '--output_file', f'{id}.mp4',
            '--disable_caching',
        ]
        subprocess.run(cmd, check=True)
    except Exception as e:
        print(f"Error: {e}")
        return None
    return f'/tmp/{id}/videos/{file_name}/1080p60/{id}.mp4'


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

def generate_session():
    #fetch latest session id
    with open("latest_session.txt", "r") as file:
        latest_session = int(file.read().strip())
    new_session = latest_session + 1
    with open("latest_session.txt", "w") as file:
        file.write(str(new_session))

    return new_session
