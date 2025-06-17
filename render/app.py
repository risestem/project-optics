from fastapi import FastAPI, Request, HTTPException
from utils import animate_scene

app = FastAPI()
API_KEY = "super-secret-key"

@app.post("/render")
async def render(request: Request):
    if request.headers.get("X-API-Key") != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    data = await request.json()
    code = data.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Missing 'code'")

    output_path = animate_scene(code)
    return {"video_path": output_path}