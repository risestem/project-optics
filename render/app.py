from fastapi import FastAPI, Request, HTTPException
from utils import animate_scene, upload_to_gcs, clear_tmp

app = FastAPI()

@app.post("/render")
async def render(request: Request):
    data = await request.json()
    code = data.get("code")
    id = data.get("id")
    if not code:
        raise HTTPException(status_code=400, detail="Missing 'code'")
    if not id:
        raise HTTPException(status_code=400, detail="Missing 'id'") 

    output_path = animate_scene(code, id)
    video_url = upload_to_gcs(
        output_path,
        "manim-renders", 
        f"{id}.mp4"
    )

    clear_tmp(id)
    return {"video_url": video_url}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)