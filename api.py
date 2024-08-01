from datetime import datetime
import random
from flask import Flask, jsonify, abort, make_response, request
from flask_cors import CORS
from pymongo import MongoClient

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


#####           Tiendas

###crear
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

        # Imprimir los datos recibidos
        print('Request.form:', request.form)
        print('Request.files:', request.files)
        
        # Contenido de los archivos
        logoConte = logo.read().decode('utf-8')
        pemConte = pem.read().decode('utf-8')

        
        tkn1 = token()
        conex = contextDB()

        tienda = {
            "_id": tkn1,
            'nombreEmpresa': request.form['nombreEmpresa'],
            'propietarioEmpresa': request.form['propietarioEmpresa'],
            'cedulaEmpresa': request.form['cedulaEmpresa'],
            'categoria': request.form['categoria'],
            'datoFirmaDigital': pemConte,  ##cifrar
            'email': request.form['email'],
            'passwd': request.form['passwd'], ##cifrar
            'logoTienda': logoConte
        }

        # Intentar insertar el documento en la base de datos
        conex.tienda.insert_one(tienda)
        tienda2 = {
            'token': tkn1,
            'nombreEmpresa': request.form['nombreEmpresa'],
            'propietarioEmpresa': request.form['propietarioEmpresa'],
            'cedulaEmpresa': request.form['cedulaEmpresa'],
            'categoria': request.form['categoria'],
            'datoFirmaDigital': pemConte,
            'email': request.form['email'],
            'passwd': request.form['passwd'],
            'logoTienda': logoConte
        }
        data = {
            "status_code": 201,
            "status_message": "Data was created",
            "data": {'tienda': tienda2}
        }
    except Exception as expc:
        # Imprimir la excepción completa
        print('Exception:', str(expc))
        abort(500)
    
    return jsonify(data), 201



#Logg in
@app.route('/loginEmpresa/<string:email>/<string:passwd>', methods=['GET'])
def get_enterprise_login(email, passwd):
    conex = contextDB()
    try:
        tienda = conex.tienda.find_one({"email": email, "passwd": passwd})
        if tienda is None:
            return jsonify({
                "status_code": 404,
                "status_message": "Not Found",
                "data": "Enterprise not found"
            }), 404
        data = {
                    "status_code": 200,
                    "status_message": "Ok",
                    "token": str(tienda['_id']),
                    "data": {
                        "enterprise": {
                            "email": tienda['email'],
                            "passwd": tienda['passwd'],
                            "token": str(tienda['_id'])
                        }
                    }
                }
    except Exception as expc:
        abort(500)
    return jsonify(data), 200




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

    tkn1 = token()
    usuario = {
        "_id": tkn1,
        'nombre': request.json['nombre'],
        'apellidos': request.json['apellidos'],
        'email': request.json['email'],
        'passwd': request.json['passwd'],
        'lugarResidencia': request.json['lugarResidencia']
    }
    try:
        conex = contextDB()
        conex.user.insert_one(usuario)
        usuario2 = {
            'token': tkn1,
            'nombre': request.json['nombre'],
            'apellidos': request.json['apellidos'],
            'email': request.json['email'],
            'passwd': request.json['passwd'],
            'lugarResidencia': request.json['lugarResidencia']
            }
        data = {
            "status_code": 201,
            "status_message": "Data was created",
            "data": {'usuario': usuario2}
        }
    except Exception as expc:
        print(expc)
        abort(500)
    return jsonify(data), 201



@app.route('/loginUsuario/<string:email>/<string:passwd>', methods=['GET'])
def get_user_login(email, passwd):
    conex = contextDB()
    try:
        usuario = conex.user.find_one({"email": email, "passwd": passwd})
        if usuario is None:
            return jsonify({
                "status_code": 404,
                "status_message": "Not Found",
                "data": "User not found"
            }), 404
        data = {
            "status_code": 200,
            "status_message": "Ok",
            "token": str(usuario['_id']),
            "data": {
                "user": {
                    "email": usuario['email'],
                    "passwd": usuario['passwd'],
                    "token": str(usuario['_id'])
                }
            }
        }
    except Exception as expc:
        print(expc)
        abort(500)
    return jsonify(data), 200

##Productos


if __name__ == '__main__':
    HOST = '0.0.0.0'
    PORT = 5000
    app.run(HOST, PORT)
