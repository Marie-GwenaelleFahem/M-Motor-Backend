from fastapi import APIRouter, HTTPException
from database import get_db_connection
from models import VehicleCreate

router = APIRouter()

@router.get("/vehicles/")
def get_vehicles():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM vehicles")
    vehicles = cursor.fetchall()
    cursor.close()
    connection.close()
    return vehicles
