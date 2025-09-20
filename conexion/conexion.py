# conexion/conexion.py
import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",        # ajusta si tienes otro usuario
        password="",        # tu contraseña MySQL
        database="supermercado"
    )
