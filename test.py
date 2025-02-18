import asyncio
from database import database

async def test_connection():
    try:
        await database.connect()
        print("✅ Connexion réussie !")
        await database.disconnect()
    except Exception as e:
        print("❌ Erreur de connexion :", e)

asyncio.run(test_connection())
