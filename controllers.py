from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from database import database
from database import DATABASE_URL
import asyncpg
from pydantic import BaseModel, PositiveFloat
from auth import oauth2_scheme, create_access_token, verify_password, SECRET_KEY
import jwt
import json
from jwt import PyJWTError
from models import VehicleCreate, OrderCreate
from datetime import datetime

router = APIRouter()

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# Récupérer tous les véhicules
@router.get("/vehicles/")
async def get_vehicles():
    try:
        vehicles = await database.fetch_all("SELECT * FROM vehicles WHERE is_sold = false")  
        return vehicles
    except Exception as e:
        return {"error": str(e)}



# Ajouter un véhicule
@router.post("/vehicles/")
async def add_vehicle(vehicle: VehicleCreate):
    try:
        # Connexion à la base de données (utilisation de `database` directement)
        connection = await database.connect()
        
        # Exécution de la requête avec des paramètres
        query = """
            INSERT INTO vehicles (model, purchase_price, rental_price, is_sold)
            VALUES (%s, , :rental_price, :is_sold)
        """
        values = {
            "model": vehicle.model,
            "purchase_price": vehicle.purchase_price,
            "rental_price": vehicle.rental_price,
            "is_sold": vehicle.is_sold
        }
        
        # Exécution de la requête avec un dictionnaire de paramètres
        await database.execute(query, values)

        return {"message": "Véhicule bien ajouté"}
    except Exception as e:
        return {"error": str(e)}
       

# Mettre à jour un véhicule
@router.put("/vehicles/{vehicle_id}")
async def update_vehicle(vehicle_id: int, vehicle: VehicleCreate):
    try:
        # Vérifier si le véhicule existe
        existing_vehicle = await database.fetch_one(
            "SELECT * FROM vehicles WHERE id = :id", {"id": vehicle_id}
        )
        if not existing_vehicle:
            raise HTTPException(status_code=404, detail="Véhicule non trouvé")
        
        # Mise à jour des données
        query = """
            UPDATE vehicles 
            SET model = :model, purchase_price = :purchase_price, rental_price = :rental_price, is_sold = :is_sold
            WHERE id = :id
        """
        values = {
            "model": vehicle.model,
            "purchase_price": vehicle.purchase_price,
            "rental_price": vehicle.rental_price,
            "is_sold": vehicle.is_sold,
            "id": vehicle_id
        }

        # Exécuter la requête d'update
        await database.execute(query, values)

        return {"message": "Véhicule mis à jour avec succès"}
    
    except Exception as e:
        return {"error": str(e)}


# Supprimer un véhicule
@router.delete("/vehicles/{vehicle_id}")
async def delete_vehicle(vehicle_id: int):
    try:
        existing_vehicle = await database.fetch_one(
            "SELECT * FROM vehicles WHERE id = :id", {"id": vehicle_id}
        )
        if not existing_vehicle:
            raise HTTPException(status_code=404, detail="Véhicule non trouvé")

        await database.execute("DELETE FROM vehicles WHERE id = :id", {"id": vehicle_id})
        return {"message": "Véhicule supprimé avec succès"}
    
    except Exception as e:
        return {"error": str(e)}


# Acheter un véhicule
@router.post("/purchase/")
async def purchase_vehicle(order: OrderCreate):
    try:
        # Vérifier si le véhicule existe et est disponible
        vehicle = await database.fetch_one(
            "SELECT is_sold FROM vehicles WHERE id = :vehicle_id",
            {"vehicle_id": order.vehicle_id}
        )

        if not vehicle:
            raise HTTPException(status_code=404, detail="Véhicule non trouvé")

        if vehicle["is_sold"]:
            raise HTTPException(status_code=400, detail="Ce véhicule est déjà vendu")

        # Créer une commande d'achat avec un statut 'pending'
        query = """
            INSERT INTO orders (user_id, vehicle_id, order_type, status, start_date, return_date, created_at)
            VALUES (:user_id, :vehicle_id, 'purchase', 'pending',:start_date, :return_date, :created_at)
        """
        values = {
            "user_id": order.user_id,
            "vehicle_id": order.vehicle_id,
            "start_date": order.start_date,
            "return_date": order.return_date,
            "created_at": datetime.now(),
        }

        await database.execute(query, values)

        return {"message": "Commande de voiture créée, en attente d'approbation"}

    except Exception as e:
        return {"error": str(e)}

# Louer un véhicule

@router.post("/rental/")
async def rent_vehicle(rental: OrderCreate):
    try:
        # Vérifier si le véhicule existe et est disponible
        vehicle = await database.fetch_one(
            "SELECT is_sold FROM vehicles WHERE id = :vehicle_id",
            {"vehicle_id": rental.vehicle_id}
        )

        if not vehicle:
            raise HTTPException(status_code=404, detail="Véhicule non trouvé")

        if vehicle["is_sold"]:
            raise HTTPException(status_code=400, detail="Ce véhicule est déjà vendu")

        # Vérifier que la date de retour est après la date de début
        if rental.return_date <= rental.start_date:
            raise HTTPException(status_code=400, detail="La date de retour doit être après la date de début")

        # Convertir les dates de chaîne en datetime
        start_date = datetime.strptime(rental.start_date, '%Y-%m-%d').date() if rental.start_date else None
        return_date = datetime.strptime(rental.return_date, '%Y-%m-%d').date() if rental.return_date else None

        # Convertir les options en JSON (chaîne)
        options_json = json.dumps(rental.options) if rental.options else None

        # Créer une commande de location avec un statut 'pending'
        query = """
            INSERT INTO orders (user_id, vehicle_id, order_type, status, subscription, options, start_date, return_date, created_at)
            VALUES (:user_id, :vehicle_id, 'rental', 'pending', :subscription, :options, :start_date, :return_date, NOW())
        """
        values = {
            "user_id": rental.user_id,
            "vehicle_id": rental.vehicle_id,
            "subscription": rental.subscription,  # Abonnement
            "options": options_json,  # Options sous forme de chaîne JSON
            "start_date": start_date,  # Date de début
            "return_date": return_date,  # Date de retour
        }

        print("Subscription:", rental)

        # Exécution de la requête pour insérer la commande dans la base de données
        await database.execute(query, values)

        return {"message": "Demande de location créée, en attente d'approbation"}

    except HTTPException as http_error:
        raise http_error  # Reraise HTTPException for fastapi to handle properly
    except Exception as e:
        return {"error": f"Une erreur s'est produite: {str(e)}"}


# Approuver une commande de location
@router.put("/rental/{order_id}/approve/")
async def approve_rental(order_id: int):
    try:
        # Vérifier si la commande existe et est en statut 'pending'
        order = await database.fetch_one(
            "SELECT * FROM orders WHERE id = :id AND order_type = 'rental' AND status = 'pending'", {"id": order_id}
        )
        if not order:
            raise HTTPException(status_code=404, detail="Commande de location non trouvée ou déjà traitée")
        query = """
            UPDATE orders
            SET status = 'approved'
            WHERE id = :id
        """
        values = {"id": order_id}
        await database.execute(query, values)
        return {"message": "Commande de location approuvée avec succès"}
    except Exception as e:
        return {"error": str(e)}
    
    
    # Approuver une commande de location
@router.put("/purchase/{order_id}/approve/")
async def approve_purchase(order_id: int):
    try:
        # Vérifier si la commande existe et est en statut 'pending'
        order = await database.fetch_one(
            "SELECT * FROM orders WHERE id = :id AND order_type = 'purchase' AND status = 'pending'", {"id": order_id}
        )
        if not order:
            raise HTTPException(status_code=404, detail="Commande  d'achat non trouvée ou déjà traitée")
        query = """
            UPDATE orders
            SET status = 'approved'
            WHERE id = :id
        """
        values = {"id": order_id}
        await database.execute(query, values)
        return {"message": "Commande d'achat approuvée avec succès"}
    except Exception as e:
        return {"error": str(e)}

# Rejeter une commande de location
@router.put("/rental/{order_id}/rejected/")
async def approve_rental(order_id: int):
    try:
        # Vérifier si la commande existe et est en statut 'pending'
        order = await database.fetch_one(
            "SELECT * FROM orders WHERE id = :id AND order_type = 'rental' AND status = 'pending'", {"id": order_id}
        )
        if not order:
            raise HTTPException(status_code=404, detail="Commande de location non trouvée ou déjà traitée")
        query = """
            UPDATE orders
            SET status = 'rejected'
            WHERE id = :id
        """
        values = {"id": order_id}
        await database.execute(query, values)
        return {"message": "Commande de location approuvée avec succès"}
    except Exception as e:
        return {"error": str(e)}
    
    
    # Rejeter une commande d'achat
@router.put("/purchase/{order_id}/rejected/")
async def approve_purchase(order_id: int):
    try:
        # Vérifier si la commande existe et est en statut 'pending'
        order = await database.fetch_one(
            "SELECT * FROM orders WHERE id = :id AND order_type = 'purchase' AND status = 'pending'", {"id": order_id}
        )
        if not order:
            raise HTTPException(status_code=404, detail="Commande  d'achat non trouvée ou déjà traitée")
        query = """
            UPDATE orders
            SET status = 'rejected'
            WHERE id = :id
        """
        values = {"id": order_id}
        await database.execute(query, values)
        return {"message": "Commande d'achat approuvée avec succès"}
    except Exception as e:
        return {"error": str(e)}


# Récupérer tous les véhicules réservés
@router.get("/vehicles/reserved")
async def get_reserved_vehicles():
    try:
        reserved_vehicles = await database.fetch_all("""
            SELECT v.id, v.model, o.order_type, o.status
            FROM vehicles v
            JOIN orders o ON v.id = o.vehicle_id
            WHERE o.status = 'pending' OR o.status = 'approved'
        """)
        return {"data": reserved_vehicles}
    except Exception as e:
        return {"error": str(e)}



# Récupérer toutes les commandes en attente
@router.get("/orders/pending")
async def get_pending_orders():
    try:
        orders = await database.fetch_all("""
            SELECT * FROM orders WHERE status = 'pending'
        """)
        return {"data": orders}
    except Exception as e:
        return {"error": str(e)}


# Récupérer une commande par son ID
@router.get("/orders/{order_id}")
async def get_order_by_id(order_id: int):
    try:
        order = await database.fetch_one("SELECT * FROM orders WHERE id = :id", {"id": order_id})
        if not order:
            raise HTTPException(status_code=404, detail="Commande non trouvée")
        return {"data": order}
    except Exception as e:
        return {"error": str(e)}
    
    
# Récupérer les revenus de tous les véhicules
@router.get("/vehicles/revenue")
async def get_vehicles_revenue():
    try:
        revenues = await database.fetch_all("""
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
    except Exception as e:
        return {"error": str(e)}
    
  
            
        
        
        
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
    