from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import os
import json
import csv

# =============================
# CONFIGURACIÓN APP
# =============================
app = Flask(__name__)
app.secret_key = "supermercado2025"

# Carpetas de datos y base
DATA_FOLDER = os.path.join(os.path.dirname(__file__), "datos")
DB_FOLDER = os.path.join(os.path.dirname(__file__), "database")
os.makedirs(DATA_FOLDER, exist_ok=True)
os.makedirs(DB_FOLDER, exist_ok=True)

DB_PATH = os.path.join(DB_FOLDER, "database.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# =============================
# MODELO DE PRODUCTO
# =============================
class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio = db.Column(db.Float, nullable=False)

# Crear tablas
with app.app_context():
    db.create_all()

# =============================
# FUNCIONES AUXILIARES PARA ARCHIVOS
# =============================
def guardar_txt():
    file_path = os.path.join(DATA_FOLDER, "datos.txt")
    productos = Producto.query.all()
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("Inventario Supermercado\n-----------------------\n")
        for i, p in enumerate(productos, start=1):
            f.write(f"{i}. {p.nombre} - Cantidad: {p.cantidad} - Precio: {p.precio}\n")

def guardar_json():
    file_path = os.path.join(DATA_FOLDER, "datos.json")
    productos = Producto.query.all()
    lista = [{"nombre": p.nombre, "cantidad": p.cantidad, "precio": p.precio} for p in productos]
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump({"productos": lista}, f, indent=4, ensure_ascii=False)

def guardar_csv():
    file_path = os.path.join(DATA_FOLDER, "datos.csv")
    productos = Producto.query.all()
    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "nombre", "cantidad", "precio"])
        writer.writeheader()
        for i, p in enumerate(productos, start=1):
            writer.writerow({"id": i, "nombre": p.nombre, "cantidad": p.cantidad, "precio": p.precio})

# =============================
# RUTAS
# =============================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/products")
def list_products():
    productos = Producto.query.all()
    return render_template("products_list.html", productos=productos)

@app.route("/products/add", methods=["GET", "POST"])
def add_product():
    if request.method == "POST":
        nombre = request.form.get("nombre")
        cantidad = request.form.get("cantidad", type=int)
        precio = request.form.get("precio", type=float)
        nuevo = Producto(nombre=nombre, cantidad=cantidad, precio=precio)
        
        db.session.add(nuevo)
        db.session.commit()  # ✅ Guardar en la DB

        # Guardar automáticamente en archivos
        guardar_txt()
        guardar_json()
        guardar_csv()

        flash("✅ Producto agregado y guardado correctamente", "success")
        return redirect(url_for("list_products"))
    return render_template("products_form.html")

@app.route("/products/delete/<int:id_producto>")
def delete_product(id_producto):
    producto = Producto.query.get_or_404(id_producto)
    db.session.delete(producto)
    db.session.commit()

    # Actualizar archivos
    guardar_txt()
    guardar_json()
    guardar_csv()

    flash("🗑 Producto eliminado", "warning")
    return redirect(url_for("list_products"))

# =============================
# MAIN
# =============================
if __name__ == "__main__":
    app.run(debug=True)
