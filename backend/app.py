from fastapi import FastAPI, Request, HTTPException
from utils.llm import call_llm
from utils.helpers import cloud_render
import uvicorn

app = FastAPI()

@app.get('/optics/{session_id}/{prompt}')
def get_optics(session_id : int, prompt: str):
    call = call_llm(prompt, {})
    response = cloud_render(call, session_id)
    return response

if __name__ == "__main__":
    response = call_llm("dfs on a graph")
    cloud_render(response)
    uivicorn.run(app, host="0.0.0", port=8000)

 

