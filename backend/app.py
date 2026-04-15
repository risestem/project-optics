from utils.llm import generate_plan, generate_manim_code
from utils.helpers import generate_session

import modal
from fastapi import FastAPI

app = FastAPI()

render_and_upload = modal.Function.from_name("manim-renderer", "render_and_upload")

@app.post("/lesson")
async def create_lesson(request: dict):
    topic = request["topic"]
    plan = generate_plan(topic)
    manim_result = generate_manim_code(plan)
    session_id = generate_session()
    video_url = render_and_upload.remote(manim_result["manim_code"], session_id)
    if not video_url:
        return {"error": "render failed"}

    return {
        "video_url": video_url,
        "topic": manim_result["topic"],
        "segments": manim_result["segments"],
        "total_duration": manim_result["total_duration_seconds"],
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
 
 
