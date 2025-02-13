from fastapi import FastAPI
from controllers import router

app = FastAPI()
app.include_router(router)

@app.get("/")
def read_root():
    return {"message": "API is running"}