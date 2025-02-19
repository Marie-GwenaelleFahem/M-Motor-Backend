from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from database import get_db_connection
from database import DATABASE_URL
import asyncpg
from pydantic import BaseModel, PositiveFloat
from auth import oauth2_scheme, create_access_token, verify_password, SECRET_KEY
import jwt
from jwt import PyJWTError

from datetime import datetime

router = APIRouter()

# Récupérer tous les véhicules
@router.get("/vehicles/")
async def get_vehicles():
    connection = await get_db_connection()
    try:
        vehicles = await connection.fetch("SELECT * FROM vehicles")
        return vehicles
    finally:
        await connection.close()

# Ajouter un véhicule
@router.post("/vehicles/")
async def add_vehicle(vehicle: VehicleCreate):
    connection = await get_db_connection()
    try:
        await connection.execute("""
            INSERT INTO vehicles (model, purchase_price, rental_price, is_sold)
            VALUES (%s, %s, %s, %s)
        """, vehicle.model, vehicle.purchase_price, vehicle.rental_price, vehicle.is_sold)
        return {"message": "Véhicule bien ajouté"}
    finally:
        await connection.close()

# Mettre à jour un véhicule
@router.put("/vehicles/{vehicle_id}")
async def update_vehicle(vehicle_id: int, vehicle: VehicleCreate):
    connection = await get_db_connection()
    try:
        existing_vehicle = await connection.fetchrow("SELECT * FROM vehicles WHERE id = $1", vehicle_id)
        if not existing_vehicle:
            raise HTTPException(status_code=404, detail="Véhicule non trouvé")
        
        await connection.execute("""
            UPDATE vehicles 
            SET model = %s, purchase_price = %s, rental_price = %s, is_sold = %s
            WHERE id = %s
        """, vehicle.model, vehicle.purchase_price, vehicle.rental_price, vehicle.is_sold, vehicle_id)
        
        return {"message": "Véhicule mis à jour avec succès"}
    finally:
        await connection.close()

# Supprimer un véhicule
@router.delete("/vehicles/{vehicle_id}")
async def delete_vehicle(vehicle_id: int):
    connection = await get_db_connection()
    try:
        existing_vehicle = await connection.fetchrow("SELECT * FROM vehicles WHERE id = $1", vehicle_id)
        if not existing_vehicle:
            raise HTTPException(status_code=404, detail="Véhicule non trouvé")

        await connection.execute("DELETE FROM vehicles WHERE id = $1", vehicle_id)
        return {"message": "Véhicule supprimé avec succès"}
    finally:
        await connection.close()

# Acheter un véhicule
@router.post("/purchase/")
async def purchase_vehicle(order: OrderCreate):
    connection = await get_db_connection()
    try:
        vehicle = await connection.fetchrow("SELECT is_sold FROM vehicles WHERE id = $1", order.vehicle_id)
        if not vehicle:
            raise HTTPException(status_code=404, detail="Véhicule non trouvé")
        if vehicle['is_sold']:
            raise HTTPException(status_code=400, detail="Ce véhicule est déjà vendu")

        await connection.execute("""
            INSERT INTO orders (user_id, vehicle_id, order_type, status, created_at)
            VALUES (%s, %s, 'purchase', 'pending', %s)
        """, order.user_id, order.vehicle_id, datetime.now())

        return {"message": "Commande d'achat créée, en attente d'approbation"}
    finally:
        await connection.close()

# Louer un véhicule
@router.post("/rental/")
async def rent_vehicle(rental: RentalCreate):
    connection = await get_db_connection()
    try:
        vehicle = await connection.fetchrow("SELECT id FROM vehicles WHERE id = $1", rental.vehicle_id)
        if not vehicle:
            raise HTTPException(status_code=404, detail="Véhicule non trouvé")

        await connection.execute("""
            INSERT INTO orders (user_id, vehicle_id, order_type, status, start_date, return_date, created_at)
            VALUES (%s, %s, 'rental', 'pending', %s, %s, %s)
        """, rental.user_id, rental.vehicle_id, rental.start_date, rental.return_date, datetime.now())

        return {"message": "Demande de location créée, en attente d'approbation"}
    finally:
        await connection.close()

# Récupérer les revenus de tous les véhicules
@router.get("/vehicles/revenue")
async def get_vehicles_revenue():
    connection = await get_db_connection()
    try:
        revenues = await connection.fetch("""
            SELECT v.id, v.model, 
            COALESCE(SUM(
                CASE 
                    WHEN o.order_type = 'purchase' THEN v.purchase_price
                    WHEN o.order_type = 'rental' THEN v.rental_price * (EXTRACT(day FROM (o.return_date - o.start_date)))
                    ELSE 0
                END), 0) AS total_revenue
            FROM vehicles v
            LEFT JOIN orders o ON v.id = o.vehicle_id AND o.status = 'approved'
            GROUP BY v.id, v.model
            ORDER BY total_revenue DESC
        """)
        return {"data": revenues}
    finally:
        await connection.close()

# Approuver une demande d'achat
@router.put("/purchase/{order_id}/approve/")
async def approve_purchase(order_id: int):
    connection = await get_db_connection()
    try:
        order = await connection.fetchrow("SELECT * FROM orders WHERE id = $1 AND order_type = 'purchase' AND status = 'pending'", order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Commande d'achat non trouvée ou déjà traitée")

        await connection.execute("UPDATE orders SET status = 'approved' WHERE id = $1", order_id)
        return {"message": "Commande d'achat approuvée avec succès"}
    finally:
        await connection.close()

# Rejeter une demande d'achat
@router.put("/purchase/{order_id}/reject/")
async def reject_purchase(order_id: int):
    connection = await get_db_connection()
    try:
        order = await connection.fetchrow("SELECT * FROM orders WHERE id = $1 AND order_type = 'purchase' AND status = 'pending'", order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Commande d'achat non trouvée ou déjà traitée")

        await connection.execute("UPDATE orders SET status = 'rejected' WHERE id = $1", order_id)
        return {"message": "Commande d'achat rejetée avec succès"}
    finally:
        await connection.close()

# Récupérer tous les véhicules réservés
@router.get("/vehicles/reserved")
async def get_reserved_vehicles():
    connection = await get_db_connection()
    try:
        reserved_vehicles = await connection.fetch("""
            SELECT v.id, v.model, o.order_type, o.status
            FROM vehicles v
            JOIN orders o ON v.id = o.vehicle_id
            WHERE o.status = 'pending' OR o.status = 'approved'
        """)
        return {"data": reserved_vehicles}
    finally:
        await connection.close()

# Récupérer toutes les commandes en attente
@router.get("/orders/pending")
async def get_pending_orders():
    connection = await get_db_connection()
    try:
        orders = await connection.fetch("""
            SELECT * FROM orders WHERE status = 'pending'
        """)
        return {"data": orders}
    finally:
        await connection.close()

# Récupérer une commande par son ID
@router.get("/orders/{order_id}")
async def get_order_by_id(order_id: int):
    connection = await get_db_connection()
    try:
        order = await connection.fetchrow("SELECT * FROM orders WHERE id = $1", order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Commande non trouvée")
        return {"data": order}
    finally:
        await connection.close()
        
        
@router.get("/allusers")
async def get_users():
    query = "SELECT id, username, email, password, created_at FROM users"
    users = await database.fetch_all(query)
    return users

@router.post("/addusers/")
async def create_user(user: UserCreate):
    query = "INSERT INTO users (username, email, password) VALUES (:username, :email, :password)"
    values = {"username": user.username, "email": user.email, "password": user.password}
    await database.execute(query, values)
    return {"message": "Utilisateur créé"}

@router.put("/updateusers/{id}")
async def update_user(id: int, user: UserCreate):
    query = "UPDATE users SET username=:username, email=:email, password=:password WHERE id=:id"
    values = {"id": id, "username": user.username, "email": user.email, "password": user.password}
    await database.execute(query, values)
    return {"message": "Utilisateur modifié"}

@router.delete("/deleteusers/{id}")
async def delete_user(id: int):
    query = "DELETE FROM users WHERE id=:id"
    await database.execute(query, {"id": id})
    return {"message": "Utilisateur supprimé"}

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    query = "SELECT * FROM users WHERE username=:username"
    user = await database.fetch_one(query, {"username": form_data.username})
    
    if user is None:
        raise HTTPException(status_code=400, detail="Nom d'utilisateur incorrect")
    if not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=400, detail="Mot de passe incorrect")
    
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me")
async def read_users_me(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Token invalide")
        return {"username": username}
    except PyJWTError:
        raise HTTPException(status_code=401, detail="Token invalide")
