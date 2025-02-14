from fastapi import FastAPI
from controllers import router

app = FastAPI()
app.include_router(router)

@app.get("/")
def read_root():
    return {"message": "API is running"}

@app.get("/generate-key")
def generate_key():
    key = secrets.token_hex(16)  # Clé de 32 caractères hexadécimaux
    return {"key": key}