from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import json
import csv
import urllib.parse

# =============================
# CONFIGURACIÓN APP
# =============================
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "supermercado2025")  # usar var de entorno si existe

# Configuración de conexión MySQL
USER_DB = "root"
PASS_DB = ""
HOST_DB = "localhost"
NAME_DB = "supermercado"

# Construir URI con quote_plus para evitar problemas con caracteres
password_quoted = urllib.parse.quote_plus(PASS_DB)
app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+mysqlconnector://{USER_DB}:{password_quoted}@{HOST_DB}/{NAME_DB}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# =============================
# FLASK-LOGIN
# =============================
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# =============================
# MODELOS
# =============================
class Producto(db.Model):
    __tablename__ = "productos"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio = db.Column(db.Float, nullable=False)

class Usuario(UserMixin, db.Model):
    __tablename__ = "usuarios"
    id_usuario = db.Column(db.Integer, primary_key=True)  # <- usa id_usuario de tu tabla real
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    # Flask-Login requiere que get_id() devuelva un str
    def get_id(self):
        return str(self.id_usuario)

@login_manager.user_loader
def load_user(user_id):
    try:
        return Usuario.query.get(int(user_id))
    except Exception:
        return None

# =============================
# FUNCIONES AUXILIARES ARCHIVOS
# =============================
def guardar_txt():
    file_path = os.path.join(os.path.dirname(__file__), "datos", "datos.txt")
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    productos = Producto.query.all()
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("Inventario Supermercado\n-----------------------\n")
        for i, p in enumerate(productos, start=1):
            f.write(f"{i}. {p.nombre} - Cantidad: {p.cantidad} - Precio: {p.precio}\n")

def guardar_json():
    file_path = os.path.join(os.path.dirname(__file__), "datos", "datos.json")
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    productos = Producto.query.all()
    lista = [{"nombre": p.nombre, "cantidad": p.cantidad, "precio": p.precio} for p in productos]
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump({"productos": lista}, f, indent=4, ensure_ascii=False)

def guardar_csv():
    file_path = os.path.join(os.path.dirname(__file__), "datos", "datos.csv")
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    productos = Producto.query.all()
    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "nombre", "cantidad", "precio"])
        writer.writeheader()
        for i, p in enumerate(productos, start=1):
            writer.writerow({"id": i, "nombre": p.nombre, "cantidad": p.cantidad, "precio": p.precio})

# =============================
# RUTAS LOGIN / REGISTRO
# =============================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not nombre or not email or not password:
            flash("❌ Todos los campos son obligatorios", "danger")
            return redirect(url_for("register"))

        if Usuario.query.filter_by(email=email).first():
            flash("❌ El correo ya está registrado", "danger")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)

        nuevo = Usuario(nombre=nombre, email=email, password=hashed_password)
        db.session.add(nuevo)
        db.session.commit()

        flash("✅ Usuario registrado correctamente", "success")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("❌ Todos los campos son obligatorios", "danger")
            return redirect(url_for("login"))

        usuario = Usuario.query.filter_by(email=email).first()
        if usuario and check_password_hash(usuario.password, password):
            login_user(usuario)
            flash("✅ Bienvenido, login exitoso", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("dashboard"))
        else:
            flash("❌ Usuario o contraseña incorrectos", "danger")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("👋 Sesión cerrada", "info")
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", usuario=current_user)

# =============================
# RUTAS PRODUCTOS
# =============================
@app.route("/")
def index():
    return redirect(url_for('login'))

@app.route("/products")
@login_required
def list_products():
    productos = Producto.query.all()
    return render_template("products_list.html", productos=productos)

@app.route("/products/add", methods=["GET", "POST"])
@login_required
def add_product():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        cantidad_raw = request.form.get("cantidad", "").strip()
        precio_raw = request.form.get("precio", "").strip()

        if not nombre or not cantidad_raw or not precio_raw:
            flash("❌ Todos los campos son obligatorios", "danger")
            return redirect(url_for("add_product"))

        try:
            cantidad = int(cantidad_raw)
            precio = float(precio_raw)
        except ValueError:
            flash("❌ Cantidad debe ser un entero y precio un número válido", "danger")
            return redirect(url_for("add_product"))

        nuevo = Producto(nombre=nombre, cantidad=cantidad, precio=precio)
        db.session.add(nuevo)
        db.session.commit()

        guardar_txt()
        guardar_json()
        guardar_csv()

        flash("✅ Producto agregado correctamente", "success")
        return redirect(url_for("list_products"))
    return render_template("products_form.html")

@app.route("/products/delete/<int:id_producto>")
@login_required
def delete_product(id_producto):
    producto = Producto.query.get_or_404(id_producto)
    db.session.delete(producto)
    db.session.commit()

    guardar_txt()
    guardar_json()
    guardar_csv()

    flash("🗑 Producto eliminado", "warning")
    return redirect(url_for("list_products"))

# =============================
# RUTAS USUARIOS
# =============================
@app.route("/usuarios")
@login_required
def list_usuarios():
    usuarios = Usuario.query.all()
    return render_template("usuarios_list.html", usuarios=usuarios)

@app.route("/usuarios/delete/<int:id_usuario>")
@login_required
def delete_usuario(id_usuario):
    if current_user.id_usuario == id_usuario:
        flash("❌ No puedes eliminar tu propio usuario", "danger")
        return redirect(url_for("list_usuarios"))

    usuario = Usuario.query.get_or_404(id_usuario)
    db.session.delete(usuario)
    db.session.commit()
    flash("🗑 Usuario eliminado", "warning")
    return redirect(url_for("list_usuarios"))

# =============================
# MAIN
# =============================
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("✅ Tablas creadas (si no existían)")
    app.run(debug=True)
