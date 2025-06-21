import datetime
from flask import Flask, request, render_template, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
from models import MensajeContacto, Pedido, db, Usuario, Producto, Sucursal
import os
from urllib.parse import quote_plus

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL').replace('postgres://', 'postgresql://')
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
        'precio_normal': float(p.precio), 
        'dscto': float(p.dscto) if p.dscto else 0,
        'descuento': float(p.dscto) if p.dscto else 0,  
        'precio_anterior': float(p.precio_anterior) if p.precio_anterior else None,
        'descripcion': p.descripcion,
        'descripcion_larga': p.descripcion,
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


@app.route('/categorias')
@login_required
def categorias():
    categorias = db.session.query(Producto.categoria).filter_by(
        sucursal_id=current_user.sucursal_id
    ).distinct().all()
    categorias = [c[0] for c in categorias]
    
    productos_por_categoria = []
    for categoria in categorias:
        count = Producto.query.filter_by(
            sucursal_id=current_user.sucursal_id,
            categoria=categoria
        ).count()
        productos_por_categoria.append({
            'nombre': categoria,
            'cantidad': count
        })
    
    return render_template('categorias.html', 
                         categorias=productos_por_categoria,
                         sucursal=current_user.sucursal)

@app.route('/stock')
@login_required
def stock():
    stock_bajo = Producto.query.filter(
        Producto.sucursal_id == current_user.sucursal_id,
        Producto.stock <= 5
    ).order_by(Producto.stock.asc()).all()
    
    stock_normal = Producto.query.filter(
        Producto.sucursal_id == current_user.sucursal_id,
        Producto.stock > 5
    ).order_by(Producto.nombre.asc()).all()
    
    return render_template('stock.html',
                         stock_bajo=stock_bajo,
                         stock_normal=stock_normal,
                         sucursal=current_user.sucursal)
    
@app.route('/pedidos', methods=['GET', 'POST'])
@login_required
def pedidos():
    if request.method == 'POST':
        try:
            producto_id = request.form.get('producto_id')
            if not producto_id:
                return render_template('pedidos.html', 
                                    error="Debes seleccionar un producto",
                                    productos=Producto.query.filter_by(sucursal_id=current_user.sucursal_id).all(),
                                    sucursales=Sucursal.query.filter(Sucursal.id != current_user.sucursal_id).all(),
                                    sucursal=current_user.sucursal)
            
            cantidad = int(request.form.get('cantidad', 0))
            sucursal_destino_id = int(request.form.get('sucursal_destino', 0))
            
            if cantidad <= 0:
                return render_template('pedidos.html', 
                                    error="La cantidad debe ser mayor a cero",
                                    productos=Producto.query.filter_by(sucursal_id=current_user.sucursal_id).all(),
                                    sucursales=Sucursal.query.filter(Sucursal.id != current_user.sucursal_id).all(),
                                    sucursal=current_user.sucursal)
            
            producto = Producto.query.filter_by(codigo_producto=producto_id, sucursal_id=current_user.sucursal_id).first()
            if not producto:
                return render_template('pedidos.html', 
                                    error="Producto no encontrado",
                                    productos=Producto.query.filter_by(sucursal_id=current_user.sucursal_id).all(),
                                    sucursales=Sucursal.query.filter(Sucursal.id != current_user.sucursal_id).all(),
                                    sucursal=current_user.sucursal)
            
            if producto.stock < cantidad:
                return render_template('pedidos.html', 
                                    error="No hay suficiente stock disponible",
                                    productos=Producto.query.filter_by(sucursal_id=current_user.sucursal_id).all(),
                                    sucursales=Sucursal.query.filter(Sucursal.id != current_user.sucursal_id).all(),
                                    sucursal=current_user.sucursal)
            
            nuevo_pedido = Pedido(
                producto_id=producto.codigo_producto,
                cantidad=cantidad,
                sucursal_origen_id=current_user.sucursal_id,
                sucursal_destino_id=sucursal_destino_id,
                usuario_id=current_user.id,
                estado='pendiente'
            )
            
            producto.stock -= cantidad
            
            db.session.add(nuevo_pedido)
            db.session.commit()
            
            return redirect('/pedidos?exito=1&pedido_id=' + str(nuevo_pedido.id))
        
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error al procesar pedido: {str(e)}")
            return render_template('pedidos.html', 
                                error=f"Error al procesar el pedido: {str(e)}",
                                productos=Producto.query.filter_by(sucursal_id=current_user.sucursal_id).all(),
                                sucursales=Sucursal.query.filter(Sucursal.id != current_user.sucursal_id).all(),
                                sucursal=current_user.sucursal)
    
    productos = Producto.query.filter_by(sucursal_id=current_user.sucursal_id).all()
    sucursales = Sucursal.query.filter(Sucursal.id != current_user.sucursal_id).all()
    exito = request.args.get('exito')
    pedido_id = request.args.get('pedido_id')
    
    return render_template('pedidos.html', 
                        productos=productos, 
                        sucursales=sucursales,
                        sucursal=current_user.sucursal,
                        exito=exito,
                        last_pedido_id=pedido_id)



@app.route('/moneda/convertir', methods=['GET'])
def convertir_moneda():
    try:
        monto = request.args.get('monto', type=float)
        de_moneda = request.args.get('de', 'USD').upper() 
        a_moneda = request.args.get('a', 'CLP').upper()    
        
        if not monto or monto <= 0:
            return jsonify({"error": "Monto inválido"}), 400
        
        response = request.get('https://mindicador.cl/api')
        data = response.json()
        
        monedas_disponibles = {'USD', 'EUR', 'CLP'} 
        if de_moneda not in monedas_disponibles or a_moneda not in monedas_disponibles:
            return jsonify({"error": "Moneda no soportada"}), 400
        
        # Obtener tasas de conversión
        if de_moneda == 'CLP':
            valor_de = 1
        else:
            valor_de = data.get(de_moneda.lower(), {}).get('valor')
            if not valor_de:
                return jsonify({"error": f"No se pudo obtener valor para {de_moneda}"}), 400
        
        if a_moneda == 'CLP':
            valor_a = 1
        else:
            valor_a = data.get(a_moneda.lower(), {}).get('valor')
            if not valor_a:
                return jsonify({"error": f"No se pudo obtener valor para {a_moneda}"}), 400
        
        # Realizar conversión
        if de_moneda == 'CLP':
            resultado = monto / valor_a
        elif a_moneda == 'CLP':
            resultado = monto * valor_de
        else:
            # Conversión entre dos monedas extranjeras (primero a CLP y luego a la moneda destino)
            resultado = (monto * valor_de) / valor_a
        
        return jsonify({
            "monto_original": monto,
            "moneda_original": de_moneda,
            "monto_convertido": round(resultado, 2),
            "moneda_destino": a_moneda,
            "fecha_consulta": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "fuente": "mindicador.cl"
        })
        
    except request.RequestException as e:
        return jsonify({"error": f"Error al consultar API de monedas: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Error inesperado: {str(e)}"}), 500
    
    
@app.route('/contacto', methods=['GET', 'POST'])
def contacto():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        mensaje = request.form.get('mensaje')
        
        if not nombre or not email or not mensaje:
            return render_template('mensajes.html', error="Todos los campos son requeridos")
        
        try:
            nuevo_mensaje = MensajeContacto(
                nombre=nombre,
                email=email,
                mensaje=mensaje
            )
            
            db.session.add(nuevo_mensaje)
            db.session.commit()
            
            
            return render_template('mensajes.html', exito=True)
        
        except Exception as e:
            db.session.rollback()
            return render_template('mensajes.html', error=f"Error al enviar el mensaje: {str(e)}")
    
    return render_template('mensajes.html')
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)