from database import get_db_connection

try:
    connection = get_db_connection()
    cursor = connection.cursor()
    
    # Exécuter une requête simple pour tester la connexion
    cursor.execute("SELECT DATABASE();")
    db_name = cursor.fetchone()

    print(f"✅ Connexion réussie à la base de données : {db_name[0]}")

    cursor.close()
    connection.close()
except Exception as e:
    print(f"❌ Erreur de connexion : {e}")
