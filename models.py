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
    categoria = db.Column(db.String(100), nullable=False )
    marca = db.Column(db.String(100), nullable=False )
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
    