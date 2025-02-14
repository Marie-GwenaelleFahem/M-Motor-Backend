from fastapi import APIRouter, HTTPException, Depends
from database import get_db_connection
from pydantic import BaseModel, PositiveFloat
from datetime import datetime
router = APIRouter()

# Modèle pour les données du véhicule
class VehicleCreate(BaseModel):
    model: str
    purchase_price: PositiveFloat
    rental_price: PositiveFloat
    is_sold: bool


# Modèle pour une commande
class OrderCreate(BaseModel):
    user_id: int
    vehicle_id: int
    
    
class SubscriptionCreate(BaseModel):
    user_id: int
    vehicle_id: int
    price: PositiveFloat
    start_date: datetime
    end_date: datetime
    

class RentedVehicle(BaseModel):
    vehicle_id: int
    model: str
    start_date: datetime
    return_date: datetime
    username: str


# Récupérer tous les véhicules
@router.get("/vehicles/")
def get_vehicles():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM vehicles")
    vehicles = cursor.fetchall()
    cursor.close()
    connection.close()
    return vehicles

# Ajouter un véhicule
@router.post("/vehicles/")
def add_vehicle(vehicle: VehicleCreate):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("""
        INSERT INTO vehicles (model, purchase_price, rental_price, is_sold)
        VALUES (%s, %s, %s, %s)
    """, (vehicle.model, vehicle.purchase_price, vehicle.rental_price, vehicle.is_sold))
    connection.commit()
    cursor.close()
    connection.close()
    return {"message": "Véhicule bien ajouté"}

# Mettre à jour un véhicule
@router.put("/vehicles/{vehicle_id}")
def update_vehicle(vehicle_id: int, vehicle: VehicleCreate):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM vehicles WHERE id = %s", (vehicle_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Véhicule non trouvé")
    cursor.execute("""
        UPDATE vehicles 
        SET model = %s, purchase_price = %s, rental_price = %s, is_sold = %s
        WHERE id = %s
    """, (vehicle.model, vehicle.purchase_price, vehicle.rental_price, vehicle.is_sold, vehicle_id))
    connection.commit()
    cursor.close()
    connection.close()
    return {"message": "Véhicule mis à jour avec succès"}

# Supprimer un véhicule
@router.delete("/vehicles/{vehicle_id}")
def delete_vehicle(vehicle_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM vehicles WHERE id = %s", (vehicle_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Véhicule non trouvé")
    cursor.execute("DELETE FROM vehicles WHERE id = %s", (vehicle_id,))
    connection.commit()
    cursor.close()
    connection.close()
    return {"message": "Véhicule supprimé avec succès"}

#Acheter un véhicule
@router.post("/purchase/")
def purchase_vehicle(order: OrderCreate):
    connection = get_db_connection()
    cursor = connection.cursor()

    # Vérifier si le véhicule est déjà vendu
    cursor.execute("SELECT is_sold FROM vehicles WHERE id = %s", (order.vehicle_id,))
    vehicle = cursor.fetchone()

    if not vehicle:
        raise HTTPException(status_code=404, detail="Véhicule non trouvé")
    
    if vehicle[0]:  # is_sold = 1
        raise HTTPException(status_code=400, detail="Ce véhicule est déjà vendu")

    # Insérer la commande dans la table `orders`
    cursor.execute("""
        INSERT INTO orders (user_id, vehicle_id, order_type, status, created_at)
        VALUES (%s, %s, 'purchase', 'pending', %s)
    """, (order.user_id, order.vehicle_id, datetime.now()))

    connection.commit()
    cursor.close()
    connection.close()

    return {"message": "Commande d'achat créée, en attente d'approbation"}


# Louer un véhicule
@router.post("/rental/")
def rent_vehicle(rental: RentalCreate):
    connection = get_db_connection()
    cursor = connection.cursor()

    # Vérifier si le véhicule existe
    cursor.execute("SELECT id FROM vehicles WHERE id = %s", (rental.vehicle_id,))
    vehicle = cursor.fetchone()

    if not vehicle:
        raise HTTPException(status_code=404, detail="Véhicule non trouvé")

    # Vérifier si le véhicule est déjà loué pendant cette période
    cursor.execute("""
        SELECT id FROM orders 
        WHERE vehicle_id = %s 
        AND order_type = 'rental' 
        AND status = 'approved'
        AND ((start_date BETWEEN %s AND %s) OR (return_date BETWEEN %s AND %s))
    """, (rental.vehicle_id, rental.start_date, rental.return_date, rental.start_date, rental.return_date))

    existing_rental = cursor.fetchone()
    if existing_rental:
        raise HTTPException(status_code=400, detail="Ce véhicule est déjà loué sur cette période")

    # Insérer la demande de location
    cursor.execute("""
        INSERT INTO orders (user_id, vehicle_id, order_type, status, start_date, return_date, created_at)
        VALUES (%s, %s, 'rental', 'pending', %s, %s, %s)
    """, (rental.user_id, rental.vehicle_id, rental.start_date, rental.return_date, datetime.now()))

    connection.commit()
    cursor.close()
    connection.close()

    return {"message": "Demande de location créée, en attente d'approbation"}


@router.post("/rental-with-subscription/")
def rent_vehicle_with_subscription(rental_subscription: SubscriptionCreate):
    connection = get_db_connection()
    cursor = connection.cursor()

    # Vérifier si le véhicule existe
    cursor.execute("SELECT id FROM vehicles WHERE id = %s", (rental_subscription.vehicle_id,))
    vehicle = cursor.fetchone()

    if not vehicle:
        raise HTTPException(status_code=404, detail="Véhicule non trouvé")

    # Vérifier si le véhicule est déjà loué pendant cette période
    cursor.execute("""
        SELECT id FROM orders 
        WHERE vehicle_id = %s 
        AND order_type = 'rental' 
        AND status = 'approved'
        AND ((start_date BETWEEN %s AND %s) OR (return_date BETWEEN %s AND %s))
    """, (rental_subscription.vehicle_id, rental_subscription.start_date, rental_subscription.end_date, rental_subscription.start_date, rental_subscription.end_date))

    existing_rental = cursor.fetchone()
    if existing_rental:
        raise HTTPException(status_code=400, detail="Ce véhicule est déjà loué sur cette période")

    # Insérer la demande de location
    cursor.execute("""
        INSERT INTO orders (user_id, vehicle_id, order_type, status, start_date, return_date, created_at)
        VALUES (%s, %s, 'rental', 'pending', %s, %s, %s)
    """, (rental_subscription.user_id, rental_subscription.vehicle_id, rental_subscription.start_date, rental_subscription.end_date, datetime.now()))

    # Créer l'abonnement
    cursor.execute("""
        INSERT INTO subscriptions (user_id, vehicle_id, plan, price, start_date, end_date)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (rental_subscription.user_id, rental_subscription.vehicle_id, rental_subscription.plan, rental_subscription.price, rental_subscription.start_date, rental_subscription.end_date))

    connection.commit()
    cursor.close()
    connection.close()

    return {"message": "Demande de location avec abonnement créée, en attente d'approbation"}



# Récupérer les revenus de tous les véhicules
@router.get("/vehicles/revenue")
def get_vehicles_revenue():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("""
        SELECT v.id, v.model, 
        COALESCE(SUM(
            CASE 
                WHEN o.order_type = 'purchase' THEN v.purchase_price
                WHEN o.order_type = 'rental' THEN v.rental_price * DATEDIFF(o.return_date, o.start_date)
                ELSE 0
            END), 0) AS total_revenue
        FROM vehicles v
        LEFT JOIN orders o ON v.id = o.vehicle_id AND o.status = 'approved'
        GROUP BY v.id, v.model
        ORDER BY total_revenue DESC
    """)
    revenues = cursor.fetchall()
    cursor.close()
    connection.close()
    return {"data": revenues}

# Récupérer les revenus d'un véhicule spécifique
@router.get("/vehicles/{vehicle_id}/revenue")
def get_vehicle_revenue(vehicle_id: int):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("""
        SELECT v.id, v.model, 
        COALESCE(SUM(
            CASE 
                WHEN o.order_type = 'purchase' THEN v.purchase_price
                WHEN o.order_type = 'rental' THEN v.rental_price * DATEDIFF(o.return_date, o.start_date)
                ELSE 0
            END), 0) AS total_revenue
        FROM vehicles v
        LEFT JOIN orders o ON v.id = o.vehicle_id AND o.status = 'approved'
        WHERE v.id = %s
        GROUP BY v.id, v.model
    """, (vehicle_id,))
    revenue = cursor.fetchone()
    cursor.close()
    connection.close()
    if not revenue:
        raise HTTPException(status_code=404, detail="Véhicule non trouvé")
    return revenue

@router.get("/rental-applications/")
def get_rental_applications(status: str = None):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    if status == "pending":
        cursor.execute("SELECT * FROM orders WHERE order_type = 'rental' AND status = %s", ("pending",))
    elif status == "processed":
        cursor.execute("SELECT * FROM orders WHERE order_type = 'rental' AND status IN (%s, %s)", ("approved", "rejected"))
    else:
        cursor.execute("SELECT * FROM orders WHERE order_type = 'rental'")

    applications = cursor.fetchall()

    cursor.close()
    connection.close()
    return {"data": applications}


@router.get("/purchase-applications/")
def get_purchase_applications(status: str = None):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    if status == "pending":
        cursor.execute("SELECT * FROM orders WHERE order_type = 'purchase' AND status = %s", ("pending",))
    elif status == "processed":
        cursor.execute("SELECT * FROM orders WHERE order_type = 'purchase' AND status IN (%s, %s)", ("approved", "rejected"))
    else:
        cursor.execute("SELECT * FROM orders WHERE order_type = 'purchase'")

    applications = cursor.fetchall()

    cursor.close()
    connection.close()
    return {"data": applications}


# Accepter une demande d'achat
@router.put("/purchase/{order_id}/approve/")
def approve_purchase(order_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()

    # Vérifier si la commande existe et est en attente
    cursor.execute("SELECT * FROM orders WHERE id = %s AND order_type = 'purchase' AND status = 'pending'", (order_id,))
    order = cursor.fetchone()

    if not order:
        raise HTTPException(status_code=404, detail="Commande d'achat non trouvée ou déjà traitée")

    # Mettre à jour le statut de la commande à "approved"
    cursor.execute("UPDATE orders SET status = 'approved' WHERE id = %s", (order_id,))
    connection.commit()

    cursor.close()
    connection.close()

    return {"message": "Commande d'achat approuvée avec succès"}

# Rejeter une demande d'achat
@router.put("/purchase/{order_id}/reject/")
def reject_purchase(order_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()

    # Vérifier si la commande existe et est en attente
    cursor.execute("SELECT * FROM orders WHERE id = %s AND order_type = 'purchase' AND status = 'pending'", (order_id,))
    order = cursor.fetchone()

    if not order:
        raise HTTPException(status_code=404, detail="Commande d'achat non trouvée ou déjà traitée")

    # Mettre à jour le statut de la commande à "rejected"
    cursor.execute("UPDATE orders SET status = 'rejected' WHERE id = %s", (order_id,))
    connection.commit()

    cursor.close()
    connection.close()

    return {"message": "Commande d'achat rejetée avec succès"}


# Approuver une demande de location
@router.put("/rental/{order_id}/approve/")
def approve_rental(order_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()

    # Vérifier si la commande existe et est en attente
    cursor.execute("SELECT * FROM orders WHERE id = %s AND order_type = 'rental' AND status = 'pending'", (order_id,))
    order = cursor.fetchone()

    if not order:
        raise HTTPException(status_code=404, detail="Demande de location non trouvée ou déjà traitée")

    # Mettre à jour le statut de la commande à "approved"
    cursor.execute("UPDATE orders SET status = 'approved' WHERE id = %s", (order_id,))
    connection.commit()

    cursor.close()
    connection.close()

    return {"message": "Demande de location approuvée avec succès"}

# Rejeter une demande de location
@router.put("/rental/{order_id}/reject/")
def reject_rental(order_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()

    # Vérifier si la commande existe et est en attente
    cursor.execute("SELECT * FROM orders WHERE id = %s AND order_type = 'rental' AND status = 'pending'", (order_id,))
    order = cursor.fetchone()

    if not order:
        raise HTTPException(status_code=404, detail="Demande de location non trouvée ou déjà traitée")

    # Mettre à jour le statut de la commande à "rejected"
    cursor.execute("UPDATE orders SET status = 'rejected' WHERE id = %s", (order_id,))
    connection.commit()

    cursor.close()
    connection.close()

    return {"message": "Demande de location rejetée avec succès"}
