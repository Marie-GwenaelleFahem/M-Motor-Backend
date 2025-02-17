from fastapi import APIRouter, HTTPException
from database import database
from models import VehicleCreate

router = APIRouter()

@router.get("/vehicles/")
async def get_vehicles():
    query = "SELECT * FROM vehicles"
    vehicles = await database.fetch_all(query)
    return vehicles
