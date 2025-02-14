#Ce fichier permet en gros des shemas de validation, c'est avec fastAPI, ça permet de ne pas insérer n'imposte quoi en base et pour avoir une doc auss

from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class VehicleCreate(BaseModel):
    model: str
    purchase_price: Optional[int] = None
    rental_price: Optional[int] = None
    is_sold: bool = False

class OrderCreate(BaseModel):
    user_id: int
    vehicle_id: int
    order_type: str
    status: str = "pending"
    subscription: bool = False
    options: Optional[dict] = None
    start_date: Optional[str] = None
    return_date: Optional[str] = None

# Côté authentification
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

class UserCreate(BaseModel):
    username: str
    password: str