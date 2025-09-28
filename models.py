from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class Categoria(db.Model):
    __tablename__ = "categorias"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)

class Proveedor(db.Model):
    __tablename__ = "proveedores"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    telefono = db.Column(db.String(50))
    email = db.Column(db.String(150))

class Producto(db.Model):
    __tablename__ = "productos"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False, default=0)
    precio = db.Column(db.Numeric(10,2), nullable=False, default=0.00)
    activo = db.Column(db.Boolean, nullable=False, default=True)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'), nullable=True)
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedores.id'), nullable=True)
    categoria = db.relationship('Categoria', backref=db.backref('productos', lazy=True))
    proveedor = db.relationship('Proveedor', backref=db.backref('productos', lazy=True))

class Usuario(UserMixin, db.Model):
    __tablename__ = "usuarios"
    id_usuario = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    activo = db.Column(db.Boolean, nullable=False, default=True)
    
    def get_id(self):
        return str(self.id_usuario)

class Venta(db.Model):
    __tablename__ = "ventas"
    id = db.Column(db.Integer, primary_key=True)
    # 🚨 CORRECCIÓN 1/3: Usamos 'fecha' para coincidir con tu tabla MySQL y plantillas corregidas.
    fecha = db.Column(db.DateTime, default=datetime.utcnow, nullable=False) 
    
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=True)
    total = db.Column(db.Numeric(10,2), default=0.00)
    
    # Relaciones
    usuario = db.relationship('Usuario', backref=db.backref('ventas', lazy=True))
    detalles = db.relationship('DetalleVenta', backref='venta', lazy=True)

class DetalleVenta(db.Model):
    __tablename__ = "detalle_ventas"
    id = db.Column(db.Integer, primary_key=True)
    venta_id = db.Column(db.Integer, db.ForeignKey('ventas.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Numeric(10,2), nullable=False)
    subtotal = db.Column(db.Numeric(10,2), nullable=False)
    
    producto = db.relationship('Producto')