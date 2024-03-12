import asyncio
from fastapi import FastAPI, Request


# FastAPI 사용(
app = FastAPI()

@app.get("/hello_world/{id}")
async def hello_world(request: Request, id: int, abcd:int = 0):
    await asyncio.sleep(2)
    return {
        id:abcd
    }