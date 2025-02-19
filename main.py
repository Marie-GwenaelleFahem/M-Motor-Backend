from fastapi import FastAPI
from database import database
from controllers import router
import logging

app = FastAPI()

@app.on_event("startup")
async def startup():
    if not database.is_connected:
        await database.connect()

@app.on_event("shutdown")
async def shutdown():
    if database.is_connected:
        await database.disconnect()

app.include_router(router)
