from datetime import datetime  # Cambia esta línea
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import uuid

db = SQLAlchemy()

class Sucursal(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    apikey = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    nombre = db.Column(db.String(160), nullable=False)
    #conexión con productos (varios productos por sucursal)
    productos = db.relationship('Producto', backref='sucursal', lazy=True)
    #conexion con usuarios x sucursal
    usuarios = db.relationship('Usuario', backref='sucursal', lazy=True)
    
class Producto(db.Model):
    codigo_producto = db.Column(db.Integer, primary_key=True)
    categoria = db.Column(db.String(100), nullable=False)
    marca = db.Column(db.String(100), nullable=False)
    codigo = db.Column(db.String(100), nullable=False)
    nombre = db.Column(db.String(160), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    dscto = db.Column(db.Integer, nullable=True)
    stock = db.Column(db.Integer, nullable=True)
    precio_anterior = db.Column(db.Integer, nullable=True)
    imagen = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.String(160), nullable=False)
    sucursal_id = db.Column(db.Integer, db.ForeignKey('sucursal.id'), nullable=False)
    
class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    sucursal_id = db.Column(db.Integer, db.ForeignKey('sucursal.id'), nullable=False)
    
class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.codigo_producto'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    sucursal_origen_id = db.Column(db.Integer, db.ForeignKey('sucursal.id'), nullable=False)
    sucursal_destino_id = db.Column(db.Integer, db.ForeignKey('sucursal.id'), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)  # Ahora funcionará correctamente
    estado = db.Column(db.String(20), default='pendiente')
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    
    producto = db.relationship('Producto', backref='pedidos')
    sucursal_origen = db.relationship('Sucursal', foreign_keys=[sucursal_origen_id])
    sucursal_destino = db.relationship('Sucursal', foreign_keys=[sucursal_destino_id])
    usuario = db.relationship('Usuario', backref='pedidos')
    
class MensajeContacto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    mensaje = db.Column(db.Text, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow) 
    leido = db.Column(db.Boolean, default=False)