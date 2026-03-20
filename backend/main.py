
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager


app = FastAPI()


@app.get("/healthcheck")
async def healthcheck():
    return {"status": "alive"}
