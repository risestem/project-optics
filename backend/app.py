from fastapi import FastAPI, Request, HTTPException
from utils.llm import call_llm
from utils.helpers import animate_scene

if __name__ == "__main__":
    response = call_llm("dfs on a graph")
    animate_scene(response)