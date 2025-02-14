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

@router.get("/allusers")
def get_users():
    db = get_db_connection()
    if not db:
        return {"error": "Problème de connexion à la base de données"}

    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT id, username email, password, created_at FROM users")
    users = cursor.fetchall()
    cursor.close()
    db.close()

    return {"users": users}