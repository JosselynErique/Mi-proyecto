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
app.secret_key = os.environ.get("FLASK_SECRET", "supermercado2025")

USER_DB = "root"
PASS_DB = ""
HOST_DB = "localhost"
NAME_DB = "supermercado"
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
    id_usuario = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    def get_id(self):
        return str(self.id_usuario)

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# =============================
# RUTAS LOGIN / REGISTRO
# =============================
@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

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
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

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
            return redirect(url_for("dashboard"))
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
