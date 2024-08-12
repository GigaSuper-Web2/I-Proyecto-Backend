from datetime import datetime
import random
from flask import Flask, jsonify, abort, make_response, request
from werkzeug.utils import secure_filename # pa los documentos svg
from flask_cors import CORS
from pymongo import MongoClient
import bcrypt
import os

##encriptar y protocolo https

app = Flask(__name__)
CORS(app)

# Crear conexión con MongoDB
def contextDB():
    conex = MongoClient(host=['localhost:27017'])
    conexDB = conex.Proyecto
    return conexDB

# Generar token
def token():
    ahora = datetime.now()
    antes = datetime.strptime("1970-01-01", "%Y-%m-%d")
    XD = str(hex(abs((ahora - antes).seconds) * random.randrange(10000000)).split('x')[-1]).upper()
    return XD

# Manejadores de errores
@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({'error': 'Bad request....!'}), 400)

@app.errorhandler(401)
def unauthorized(error):
    return make_response(jsonify({'error': 'Unauthorized....!'}), 401)

@app.errorhandler(403)
def forbidden(error):
    return make_response(jsonify({'error': 'Forbidden....!'}), 403)

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found....!'}), 404)

@app.errorhandler(500)
def internal_error(error):
    return make_response(jsonify({'error': 'Internal Server Error....!'}), 500)




## Registrar tienda
@app.route('/registrarTienda', methods=['POST'])
def create_shop():
    try:
        # Verificar los datos del formulario
        if not request.form or \
                not all(key in request.form for key in (
                    'nombreEmpresa', 
                    'propietarioEmpresa', 
                    'cedulaEmpresa', 
                    'categoria',  
                    'email', 
                    'passwd'
                )):
            abort(400)

        if 'logoTienda' not in request.files or 'datoFirmaDigital' not in request.files:
            abort(400)

        logo = request.files['logoTienda']
        pem = request.files['datoFirmaDigital']

        # Contenido de los archivos
        logoConte = logo.read().decode('utf-8')
        pemConte = pem.read().decode('utf-8')

        # Encriptar la contraseña
        passs = request.form['passwd'].encode('utf-8')
        salt = bcrypt.gensalt()
        hasheada = bcrypt.hashpw(passs, salt)

        tkn1 = token()
        conex = contextDB()

        tienda = {
            "_id": tkn1,
            'nombreEmpresa': request.form['nombreEmpresa'],
            'propietarioEmpresa': request.form['propietarioEmpresa'],
            'cedulaEmpresa': request.form['cedulaEmpresa'],
            'categoria': request.form['categoria'],
            'datoFirmaDigital': pemConte,  # Se puede cifrar si es necesario
            'email': request.form['email'],
            'passwd': hasheada,  # Contraseña encriptada
            'logoTienda': logoConte
        }

        # Intentar insertar el documento en la base de datos
        conex.tienda.insert_one(tienda)
        data = {
            "status_code": 201,
            "status_message": "Data was created"
        }
    except Exception as expc:
        # Imprimir la excepción completa
        print('Exception:', str(expc))
        abort(500)
    
    return jsonify(data), 201

## Login Empresa
@app.route('/loginEmpresa/<string:email>/<string:passwd>', methods=['GET'])
def get_enterprise_login(email, passwd):
    conex = contextDB()
    try:
        # Buscar la tienda por email
        tienda = conex.tienda.find_one({"email": email})
        if tienda is None:
            return jsonify({
                "status_code": 404,
                "status_message": "Not Found",
                "data": "Enterprise not found"
            }), 404

        # Obtener la contraseña almacenada
        passstored = tienda.get('passwd')

        # Comparar la contraseña ingresada con la almacenada
        if not bcrypt.checkpw(passwd.encode('utf-8'), passstored):
            return jsonify({
                "status_code": 401,
                "status_message": "Unauthorized",
                "data": "Invalid password"
            }), 401

        data = {
            "status_code": 200,
            "status_message": "Ok",
            "token": str(tienda['_id']),
            "data": {
                "enterprise": {
                    "token": str(tienda['_id'])
                }
            }
        }
        return jsonify(data), 200

    except Exception as expc:
        print(f"Error during login: {expc}")  # Mejora el mensaje de error para depuración
        return jsonify({
            "status_code": 500,
            "status_message": "Internal Server Error",
            "data": str(expc)  # Esto enviará el mensaje de error en la respuesta (útil para depuración)
        }), 500



###                 Usuarios

@app.route('/registrarUsuario', methods=['POST'])
def registrarUsuario():
    if not request.json or \
            not 'nombre' in request.json or \
            not 'apellidos' in request.json or \
            not 'email' in request.json or \
            not 'passwd' in request.json or \
            not 'lugarResidencia' in request.json:
        abort(400)

    passs= request.json['passwd'].encode('utf-8')
    salt = bcrypt.gensalt()
    hasheada= bcrypt.hashpw(passs, salt)

    tkn1 = token()
    usuario = {
        "_id": tkn1,
        'nombre': request.json['nombre'],
        'apellidos': request.json['apellidos'],
        'email': request.json['email'],
        'passwd': hasheada, 
        'lugarResidencia': request.json['lugarResidencia']
    }
    try:
        conex = contextDB()
        conex.user.insert_one(usuario)
        data = {
            "status_code": 201,
            "status_message": "Data was created"
        }
    except Exception as expc:
        print(expc)
        abort(500)
    return jsonify(data), 201


## Logueo de usuario con contraseña encriptada
@app.route('/loginUsuario/<string:email>/<string:passwd>', methods=['GET'])
def get_user_login(email, passwd):
    conex = contextDB()
    try:
        usuario = conex.user.find_one({"email": email})
        if usuario is None:
            return jsonify({
                "status_code": 404,
                "status_message": "Not Found",
                "data": "User not found"
            }), 404
        
        passstored = usuario.get('passwd')
        if isinstance(passstored, str):  # Verifica si la contraseña almacenada es un string
            passstored = passstored.encode('utf-8')  # Si es un string, conviértelo a bytes

        if not bcrypt.checkpw(passwd.encode('utf-8'), passstored):
            return jsonify({
                "status_code": 401,
                "status_message": "Unauthorized",
                "data": "Invalid password"
            }), 401

        data = {
            "status_code": 200,
            "status_message": "Ok",
            "token": str(usuario['_id']),
            "data": {
                "user": {
                    "token": str(usuario['_id'])
                }
            }
        }
        return jsonify(data), 200

    except Exception as expc:
        print(f"Error during login: {expc}")  # Mejora el mensaje de error para depuración
        return jsonify({
            "status_code": 500,
            "status_message": "Internal Server Error",
            "data": str(expc)  # Esto enviará el mensaje de error en la respuesta (útil para depuración)
        }), 500

                                                        ##Productos

## Agregar un producto a una tienda
@app.route('/agregarProducto', methods=['POST'])
def agregar_producto():
    try:
        # Verificar los datos del formulario
        if not request.form or \
                not all(key in request.form for key in (
                    'tiendaId', 
                    'nombreProducto', 
                    'descripcion', 
                    'precio', 
                    'stock'
                )):
            abort(400)

        if 'logoProducto' not in request.files:
            abort(400)

        # Obtener el archivo
        logo = request.files['logoProducto']
        
        # Leer el contenido del archivo SVG
        logoConte = logo.read().decode('utf-8')

        # Crear un ID único para el producto
        tkn1 = token()
        conex = contextDB()

        # Crear el documento del producto
        producto = {
            "_id": tkn1,
            'tiendaId': request.form['tiendaId'],
            'nombreProducto': request.form['nombreProducto'],
            'descripcion': request.form['descripcion'],
            'precio': request.form['precio'],
            'stock': request.form['stock'],
            'logoProducto': logoConte
        }

        # Intentar insertar el documento en la base de datos
        conex.producto.insert_one(producto)
        data = {
            "status_code": 201,
            "status_message": "Producto agregado"
        }
    except Exception as expc:
        # Imprimir la excepción completa
        print('Exception:', str(expc))
        abort(500)
    
    return jsonify(data), 201

@app.route('/editarProducto/<string:producto_id>', methods=['PUT'])
def editar_producto(producto_id):
    try:
        # Verificar los datos del formulario
        if not request.form and 'logoProducto' not in request.files:
            abort(400)

        conex = contextDB()
        producto = conex.producto.find_one({"_id": producto_id})
        if producto is None:
            return jsonify({
                "status_code": 404,
                "status_message": "Producto no encontrado"
            }), 404

        # Datos a actualizar
        update_data = {}
        if 'nombreProducto' in request.form:
            update_data['nombreProducto'] = request.form['nombreProducto']
        if 'descripcion' in request.form:
            update_data['descripcion'] = request.form['descripcion']
        if 'precio' in request.form:
            update_data['precio'] = request.form['precio']
        if 'stock' in request.form:
            update_data['stock'] = request.form['stock']

        # Si se proporciona un nuevo archivo, actualizarlo
        if 'logoProducto' in request.files:
            logo = request.files['logoProducto']
            logoConte = logo.read().decode('utf-8')
            update_data['logoProducto'] = logoConte

        if update_data:
            conex.producto.update_one({'_id': producto_id}, {'$set': update_data})
            return jsonify({
                "status_code": 200,
                "status_message": "Producto actualizado"#,
                #"data": {'producto': update_data}
            }), 200
        else:
            return jsonify({
                "status_code": 400,
                "status_message": "No se proporcionaron datos para actualizar"
            }), 400

    except Exception as expc:
        # Imprimir la excepción completa
        print('Exception:', str(expc))
        abort(500)

## GET producto especifico
@app.route('/productoEspecifico/<string:producto_id>', methods=['GET'])
def get_producto(producto_id):
    conex = contextDB()
    try:
        producto = conex.producto.find_one({"_id": producto_id})
        if producto is None:
            return jsonify({
                "status_code": 404,
                "status_message": "Producto no encontrado"
            }), 404

        data = {
            "status_code": 200,
            "status_message": "Ok",
            "data": {
                "producto": {
                    "nombreProducto": producto['nombreProducto'],
                    "descripcion": producto['descripcion'],
                    "precio": producto['precio'],
                    "stock": producto['stock']#,
                    #"logoProducto": producto['logoProducto']
                }
            }
        }
    except Exception as expc:
        print('Exception:', str(expc))
        abort(500)
    
    return jsonify(data), 200

## Eliminar producto especifico
@app.route('/eliminarProducto/<string:producto_id>', methods=['DELETE'])
def eliminar_producto(producto_id):
    conex = contextDB()
    try:
        resultado = conex.producto.delete_one({"_id": producto_id})
        if resultado.deleted_count == 0:
            return jsonify({
                "status_code": 404,
                "status_message": "Producto no encontrado"
            }), 404
        
        return jsonify({
            "status_code": 200,
            "status_message": "Producto eliminado"
        }), 200
    except Exception as expc:
        print('Exception:', str(expc))
        abort(500)



if __name__ == '__main__':
    HOST = '0.0.0.0'
    PORT = 5000
    app.run(HOST, PORT)
