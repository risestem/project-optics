import requests
from google.auth.transport.requests import Request
from google.oauth2 import id_token
from google.oauth2 import service_account

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


def fetch_history(session_id):
    pass

if __name__ == "__main__":
    scene_code = """
from manim import *

class HelloWorld(Scene):
    def construct(self):
        text = Text("Hello, World!")
        self.play(Write(text))
        self.wait(1)
"""
    session_id = "test_hello_1a2b3c4d"
    result = cloud_render(scene_code, session_id)
    print(result)

    