import os
from flask import Flask, request, render_template, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
from models import db, Usuario, Producto, Sucursal


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

@app.before_request
def crear_tablas():
    db.create_all()
    if not Sucursal.query.first():
        suc1 = Sucursal(nombre='Sucursal Viña')
        suc2 = Sucursal(nombre="Sucursal Santiago")
        db.session.add_all([suc1, suc2])
        db.session.commit()
        print("Sucursales creadas con API Keys:")
        for s in Sucursal.query.all():
            print(f"{s.nombre} - API Key: {s.apikey}")
        
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = Usuario.query.filter_by(email=request.form['email']).first()
        if user and bcrypt.check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect('/home')
        return "Credenciales incorrectas", 401
    return render_template('login.html')

@app.route('/home')
@login_required
def dashboard():
    productos = Producto.query.filter_by(sucursal_id=current_user.sucursal_id).all()
    sucursal = current_user.sucursal
    return render_template('index.html', productos =productos, sucursal=sucursal)

#agregar productos
@app.route('/producto/agregar', methods=['GET', 'POST'])
@login_required
def agregar_producto():
    if request.method == 'POST':
        nuevo = Producto(
            nombre=request.form['nombre'],
            marca=request.form['marca'],
            categoria=request.form['categoria'],
            codigo=request.form['codigo'],
            precio=float(request.form['precio']),
            dscto=float(request.form['dscto'] or 0),
            precio_anterior=float(request.form['precio_anterior'] or 0),
            descripcion=request.form['descripcion'],
            imagen=request.form['imagen'],
            stock = request.form.get('stock', 0),
            sucursal_id=current_user.sucursal_id
        )
        db.session.add(nuevo)
        db.session.commit()
        return redirect('/home')
    return render_template('agregar_producto.html')

#editar productos
@app.route('/producto/editar/<int:codigo_producto>', methods=['GET', 'POST'])
@login_required
def editar_producto(codigo_producto):
    producto = Producto.query.get_or_404(codigo_producto)
    if request.method == 'POST':
        producto.nombre = request.form['nombre']
        producto.marca = request.form['marca']
        producto.categoria = request.form['categoria']
        producto.codigo = request.form['codigo']
        producto.precio = float(request.form['precio'])
        producto.dscto = float(request.form['dscto'] or 0)
        producto.precio_anterior = float(request.form['precio_anterior'] or 0)
        producto.descripcion = request.form['descripcion']
        producto.imagen = request.form['imagen']
        producto.stock = request.form['stock']
        db.session.commit()
        return redirect('/home')
    return render_template('editar_producto.html', producto=producto)
#eliminar
@app.route('/producto/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_producto(id):
    producto = Producto.query.get_or_404(id)
    db.session.delete(producto)
    db.session.commit()
    return redirect('/home')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')
    
@app.route('/api/productos')
def api_productos():
    apikey = request.headers.get('Authorization')
    sucursal = Sucursal.query.filter_by(apikey=apikey.strip()).first() if apikey else None
    
    if not sucursal:
        return jsonify({"error": "API Key inválida"}), 403
    
    # Nuevo filtro por código
    codigo = request.args.get('codigo')
    categoria = request.args.get('categoria')
    
    query = Producto.query.filter_by(sucursal_id=sucursal.id)
    
    if codigo:
        query = query.filter_by(codigo=codigo)
    if categoria:
        query = query.filter_by(categoria=categoria)
    
    productos = query.all()
    
    return jsonify([{
        'nombre': p.nombre,
        'marca': p.marca,
        'categoria': p.categoria,
        'precio': float(p.precio),
        'precio_normal': float(p.precio),  # Añadido para compatibilidad
        'dscto': float(p.dscto) if p.dscto else 0,
        'descuento': float(p.dscto) if p.dscto else 0,  # Alias para compatibilidad
        'precio_anterior': float(p.precio_anterior) if p.precio_anterior else None,
        'descripcion': p.descripcion,
        'descripcion_larga': p.descripcion,  # Alias para compatibilidad
        'imagen': p.imagen,
        'codigo': p.codigo,
        'stock': p.stock if hasattr(p, 'stock') else 10, 
        'modelo': p.modelo if hasattr(p, 'modelo') else '',
        'garantia': p.garantia if hasattr(p, 'garantia') else ''
    } for p in productos])

@app.route('/registrar', methods=['POST'])
def registrar():
    data = request.json
    email = data['email']
    password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    sucursal_id = data['sucursal_id']
    if not Sucursal.query.get(sucursal_id):
        return jsonify({"error": "Sucursal no válida"}), 400
    if Usuario.query.filter_by(email=email).first():
        return jsonify({"error": "Email ya registrado"}), 400
    nuevo = Usuario(email=email, password=password, sucursal_id=sucursal_id)
    db.session.add(nuevo)
    db.session.commit()
    return jsonify({"mensaje": "Usuario creado correctamente"})


if __name__ == '__main__':
    app.run(debug=True)