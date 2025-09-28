from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os, urllib.parse
from models import db, Usuario, Producto, Categoria, Proveedor, Venta, DetalleVenta 

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "supermercado2025_CLAVE_SECRETA_POR_DEFECTO")

# ------------------------
# CONFIGURACIÓN DB
# ------------------------
USER_DB = "root"
PASS_DB = "" 
HOST_DB = "localhost"
NAME_DB = "supermercado"
password_quoted = urllib.parse.quote_plus(PASS_DB)
app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+mysqlconnector://{USER_DB}:{password_quoted}@{HOST_DB}/{NAME_DB}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# ------------------------
# LOGIN MANAGER
# ------------------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id)) 

with app.app_context():
    db.create_all()

# ------------------------
# RUTAS PRINCIPALES
# ------------------------

@app.route("/")
def index():
    return redirect(url_for("dashboard")) if current_user.is_authenticated else redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", usuario=current_user)

# ------------------------
# LOGIN / REGISTER / LOGOUT
# ------------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        email = request.form.get("email","").strip().lower()
        password = request.form.get("password","")
        usuario = Usuario.query.filter_by(email=email, activo=True).first()
        
        if usuario and check_password_hash(usuario.password, password):
            # 🚨 CORRECCIÓN 2/3: Usamos remember=False para que la sesión no persista al reiniciar.
            login_user(usuario, remember=False) 
            flash("✅ ¡Bienvenido/a! Sesión iniciada.", "success")
            return redirect(request.args.get("next") or url_for("dashboard"))
        else:
            flash("❌ Correo o contraseña incorrectos.", "danger")
    return render_template("login.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        nombre = request.form.get("nombre").strip()
        email = request.form.get("email").strip().lower()
        password = request.form.get("password")
        
        if Usuario.query.filter_by(email=email).first():
            flash("❌ El correo electrónico ya está registrado.", "danger")
            return render_template("register.html")
            
        nuevo_usuario = Usuario(
            nombre=nombre,
            email=email,
            password=generate_password_hash(password),
            activo=True 
        )
        try:
            db.session.add(nuevo_usuario)
            db.session.commit()
            flash("✅ ¡Registro exitoso! Ya puedes iniciar sesión.", "success")
            return redirect(url_for("login"))
        except Exception as e:
            db.session.rollback()
            flash(f"❌ Error al registrar usuario: {e}", "danger")
            
    return render_template("register.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("👋 Sesión cerrada.", "info")
    return redirect(url_for("login"))

# ------------------------
# CRUD USUARIOS
# ------------------------
@app.route("/usuarios")
@login_required
def list_usuarios():
    usuarios = Usuario.query.all()
    return render_template("usuarios_list.html", usuarios=usuarios)

@app.route("/usuarios/nuevo", methods=["GET", "POST"])
@login_required
def add_usuario():
    if request.method == "POST":
        nombre = request.form.get("nombre").strip()
        email = request.form.get("email").strip().lower()
        password = request.form.get("password")
        
        if Usuario.query.filter_by(email=email).first():
            flash("❌ El correo electrónico ya está registrado.", "danger")
            return render_template("usuarios_form.html", usuario=None) 
            
        if not password:
            flash("❌ La contraseña no puede estar vacía.", "danger")
            return render_template("usuarios_form.html", usuario=None) 
            
        nuevo_usuario = Usuario(
            nombre=nombre,
            email=email,
            password=generate_password_hash(password),
            activo=True
        )
        try:
            db.session.add(nuevo_usuario)
            db.session.commit()
            flash("✅ Usuario creado exitosamente.", "success")
            return redirect(url_for("list_usuarios"))
        except Exception as e:
            db.session.rollback()
            flash(f"❌ Error al crear usuario: {e}", "danger")

    return render_template("usuarios_form.html", usuario=None) 

@app.route("/usuarios/editar/<int:id_usuario>", methods=["GET", "POST"])
@login_required
def edit_usuario(id_usuario):
    u = Usuario.query.get_or_404(id_usuario)
    
    if request.method == "POST":
        u.nombre = request.form.get("nombre").strip()
        
        nuevo_email = request.form.get("email").strip().lower()
        if nuevo_email != u.email and Usuario.query.filter_by(email=nuevo_email).first():
            flash("❌ El nuevo correo electrónico ya está registrado.", "danger")
            return render_template("usuarios_form.html", usuario=u) 
        u.email = nuevo_email
        
        password = request.form.get("password")
        if password:
            u.password = generate_password_hash(password)
            
        try:
            db.session.commit()
            flash(f"✅ Usuario {u.nombre} actualizado exitosamente.", "success")
            return redirect(url_for("list_usuarios"))
        except Exception as e:
            db.session.rollback()
            flash(f"❌ Error al actualizar usuario: {e}", "danger")
            
    return render_template("usuarios_form.html", usuario=u)

@app.route("/usuarios/eliminar/<int:id_usuario>", methods=["POST"])
@login_required
def delete_usuario(id_usuario):
    u = Usuario.query.get_or_404(id_usuario)
    if current_user.id_usuario != id_usuario: 
        u.activo = False
        db.session.commit()
        flash(f"🗑️ Usuario {u.nombre} marcado como inactivo.", "info")
    else:
        flash("❌ No puedes realizar esta acción en tu propia cuenta.", "danger")
    return redirect(url_for("list_usuarios"))

# ------------------------
# CRUD PRODUCTOS
# ------------------------

@app.route("/productos")
@login_required
def list_products():
    q = request.args.get("q","").strip()
    mostrar = request.args.get("mostrar","activos")
    query = Producto.query
    if mostrar=="activos":
        query = query.filter_by(activo=True)
    elif mostrar=="inactivos":
        query = query.filter_by(activo=False)
    if q:
        like = f"%{q}%"
        query = query.join(Categoria, isouter=True).join(Proveedor, isouter=True).filter(
            db.or_(Producto.nombre.ilike(like), Categoria.nombre.ilike(like), Proveedor.nombre.ilike(like))
        )
    productos = query.order_by(Producto.id.desc()).all()
    return render_template("products_list.html", productos=productos, q=q, mostrar=mostrar)

@app.route("/productos/nuevo", methods=["GET","POST"])
@login_required
def add_product(): # <--- ¡IMPORTANTE! El nombre de la función debe ser 'add_product'
    if request.method=="POST":
        nuevo = Producto(
            nombre=request.form.get("nombre").strip(),
            cantidad=int(request.form.get("cantidad") or 0),
            precio=float(request.form.get("precio") or 0),
            activo=True,
            categoria_id=int(request.form.get("categoria_id")) if request.form.get("categoria_id") else None,
            proveedor_id=int(request.form.get("proveedor_id")) if request.form.get("proveedor_id") else None
        )
        try:
            db.session.add(nuevo)
            db.session.commit()
            flash("✅ Producto creado", "success")
            return redirect(url_for("list_products"))
        except Exception as e:
            db.session.rollback()
            flash(f"❌ Error al crear producto: {e}", "danger")
            
    categorias = Categoria.query.all()
    proveedores = Proveedor.query.all()
    return render_template("products_form.html", producto=None, categorias=categorias, proveedores=proveedores)

@app.route("/productos/editar/<int:id>", methods=["GET","POST"])
@login_required
def edit_product(id):
    p = Producto.query.get_or_404(id)
    if request.method=="POST":
        p.nombre = request.form.get("nombre").strip()
        p.cantidad = int(request.form.get("cantidad") or 0)
        p.precio = float(request.form.get("precio") or 0)
        p.categoria_id = int(request.form.get("categoria_id")) if request.form.get("categoria_id") else None
        p.proveedor_id = int(request.form.get("proveedor_id")) if request.form.get("proveedor_id") else None
        db.session.commit()
        flash("✅ Producto actualizado", "success")
        return redirect(url_for("list_products"))
    categorias = Categoria.query.all()
    proveedores = Proveedor.query.all()
    return render_template("products_form.html", producto=p, categorias=categorias, proveedores=proveedores)

@app.route("/productos/eliminar/<int:id>", methods=["POST"])
@login_required
def delete_product(id):
    p = Producto.query.get_or_404(id)
    p.activo = False
    db.session.commit()
    flash("🗑️ Producto marcado como inactivo", "info")
    return redirect(url_for("list_products"))

@app.route("/productos/restaurar/<int:id>", methods=["POST"])
@login_required
def restore_product(id):
    p = Producto.query.get_or_404(id)
    p.activo = True
    db.session.commit()
    flash("✅ Producto restaurado", "success")
    return redirect(url_for("list_products", mostrar="inactivos"))

# ------------------------
# VENTAS Y HISTORIAL
# ------------------------

@app.route("/ventas/nueva", methods=["GET","POST"])
@login_required
def nueva_venta():
    if request.method=="POST":
        product_ids = request.form.getlist("product_id[]")
        cantidades = request.form.getlist("cantidad[]")
        if not product_ids:
            flash("❌ No hay productos seleccionados", "danger")
            return redirect(url_for("nueva_venta"))
            
        venta = Venta(usuario_id=current_user.id_usuario, total=0)
        db.session.add(venta)
        db.session.flush()
        
        total = 0
        try:
            for pid, cant in zip(product_ids, cantidades):
                pid, cant = int(pid), int(cant)
                prod = Producto.query.get(pid)
                
                if not prod or not prod.activo:
                    flash(f"❌ Producto (ID: {pid}) no encontrado o inactivo.", "danger")
                    db.session.rollback()
                    return redirect(url_for("nueva_venta"))
                
                if prod.cantidad < cant:
                    flash(f"❌ Stock insuficiente para {prod.nombre}. Disponible: {prod.cantidad}", "danger")
                    db.session.rollback()
                    return redirect(url_for("nueva_venta"))
                
                subtotal = float(prod.precio) * cant
                detalle = DetalleVenta(
                    venta_id=venta.id, 
                    producto_id=pid, 
                    cantidad=cant, 
                    precio_unitario=prod.precio, 
                    subtotal=subtotal
                )
                db.session.add(detalle)
                
                prod.cantidad -= cant
                total += subtotal
                
            venta.total = total
            db.session.commit()
            flash("✅ Venta registrada exitosamente.", "success")
            return redirect(url_for("list_ventas")) 
        except Exception as e:
            db.session.rollback()
            flash(f"❌ Error al procesar la venta: {e}", "danger")
            return redirect(url_for("nueva_venta"))
            
    productos = Producto.query.filter_by(activo=True).all()
    return render_template("venta_form.html", productos=productos)

# Ruta para ver el historial de ventas
@app.route("/ventas")
@login_required
def list_ventas():
    # 🚨 CORRECCIÓN 3/3: Ordenar por Venta.fecha para coincidir con el modelo.
    ventas = Venta.query.order_by(Venta.fecha.desc()).all()
    return render_template("ventas_list.html", ventas=ventas)

# Ruta para ver el detalle de una venta específica
@app.route("/ventas/<int:id_venta>")
@login_required
def view_venta(id_venta):
    venta = Venta.query.get_or_404(id_venta)
    return render_template("venta_detail.html", venta=venta)


# ------------------------
# API BUSQUEDA RÁPIDA
# ------------------------

@app.route("/api/productos/search")
@login_required
def api_search_products():
    q = request.args.get("q","").strip()
    query = Producto.query.filter_by(activo=True)
    if q:
        like = f"%{q}%"
        query = query.filter(Producto.nombre.ilike(like))
    productos = query.limit(20).all()
    results = [{"id": p.id, "nombre": p.nombre, "cantidad": p.cantidad, "precio": str(p.precio)} for p in productos]
    return jsonify(results)

# ------------------------
# RUN APP
# ------------------------
if __name__ == "__main__":
    app.run(debug=True)