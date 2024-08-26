#Esta es la ultima versión funcional.


#El programa funciona por frames, cada frame es analizado y mostrado con sus descripciones al instante.
# Para obtener la información total es necesario generar los reportes.
# Un estudio es un analisis de un frame y el analisis es mostrado en la tabla de contador y en la tabla de descripción.
# Todas las camaras son agregadas a una lista, donde esta lista es recorrida secuencialmente obteniendo los frames.

#Libraries used
import time
import cv2
from ultralytics import YOLO
import torch
from flask import Flask, jsonify, render_template, Response, request, session, flash
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask import url_for, redirect
from flask_wtf import FlaskForm

from wtforms import StringField, PasswordField, EmailField, SelectField, SubmitField, validators
from wtforms.validators import InputRequired, Length, ValidationError

from flask_bcrypt import Bcrypt
from ultralytics.utils.plotting import Annotator
from collections import deque
from flask_sqlalchemy import SQLAlchemy
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from datetime import datetime
from imutils import paths
from PIL import Image as im
import time
import sqlite3
import json
import random
import numpy as np
import tensorflow as tf
from datetime import date
import os
from libraries.validate_User import validate_User
from fpdf import FPDF
from libraries.mailer import mailer
import logging 

# Configure the logger
logging.basicConfig(filename='register.log', level=logging.ERROR)

# Global variables
image_size = 1000#1080#72
patch_size = 1000#1080#84#6
half_patch = patch_size // 2


objects = []
iSList = []
global crowdName
global nameCam
global saveToDB
global id_Crowd
global chickCounting
crowdName = ""
nameCam = ""
saveToDB = True
id_Crowd=None
chickCounting = 0
#headings = ("ID","CATEGORIA","PRECISION")

def crop_shift_pad(images, mode):
    try:
        # Build the diagonally shifted images
        if mode == "left-up":
            crop_height = half_patch
            crop_width = half_patch
            shift_height = 0
            shift_width = 0
        elif mode == "left-down":
            crop_height = 0
            crop_width = half_patch
            shift_height = half_patch
            shift_width = 0
        elif mode == "right-up":
            crop_height = half_patch
            crop_width = 0
            shift_height = 0
            shift_width = half_patch
        else:
            crop_height = 0
            crop_width = 0
            shift_height = half_patch
            shift_width = half_patch

        # Crop the shifted images and pad them
        crop = tf.image.crop_to_bounding_box(
            images,
            offset_height=crop_height,
            offset_width=crop_width,
            target_height=image_size - half_patch,
            target_width=image_size - half_patch,
        )

        shift_pad = tf.image.pad_to_bounding_box(
            crop,
            offset_height=shift_height,
            offset_width=shift_width,
            target_height=image_size,
            target_width=image_size,
        )
        return shift_pad
    except Exception as e:
        logging.error('Error:' + str(e))
        flash('Error:'+str(e))

def getSegmentedImages(image):
    try:
        image = cv2.resize(image, (image_size, image_size))
        return [np.array(crop_shift_pad(image, mode="left-down")), np.array(crop_shift_pad(image, mode="right-up")), np.array(crop_shift_pad(image, mode="right-down")), np.array(crop_shift_pad(image, mode="left-up"))]
    except Exception as e:
        logging.error('Error:' + str(e))
        flash('Error:'+str(e))

#Loading the database 
def getJSONValues():
    try:
        dataValues = []
        with open('data.json', 'r') as jsonDataF:
            load_file = json.load(jsonDataF)
            dataValues.append({"ltModel":load_file["ltModel"], "dbConn":load_file["dbConn"]})
        return dataValues
    except Exception as e:
        logging.error('Error:' + str(e))
        flash('Error:'+str(e))

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] =\
        'sqlite:///' + os.path.join(basedir, getJSONValues()[0]["dbConn"])
app.config['SECRET_KEY'] = 'thisisasecretkey'
#app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    userType = db.Column(db.String(25), nullable=False)

class LoginForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Nombre de usuario"})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Contraseña"})

    submit = SubmitField('Iniciar sesión')


@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except Exception as e:
        flash()
        logging.error('Error:'+str(e))
        flash('Error: '+str(e))

def getNativeTracking(model, image, name, visDefault, tracker, nEstudio, confW=0.1, saveToDB=False):
    try:
        for result in model.track(source=image, show=visDefault, stream=False, persist=False, verbose=False, tracker=tracker):#, conf=0.7): # Si persist es igual a false, no podrá reconocer en todos los segmentos de la imagen.|
            start = time.perf_counter()
            annotator = None
            for res in result:
                annotator = Annotator(image)
                boxes = res.boxes.cpu()
                for box in boxes:
                    b = box.xyxy[0]
                    c = box.cls
                    id = box.id
                    if id != None: 
                        id = int(id)
                        conf = round(float(box.conf[0]), 1)
                        if(conf>confW):
                            annotator.box_label(b, str(id))
                            if(saveToDB):
                                try:
                                    conn = sqlite3.connect(getJSONValues()[0]["dbConn"])
                                    con = conn.cursor()
                                    con.execute('select MAX(numDet) from deteccion;')
                                    numDet = con.fetchall()
                                    con.execute('select MAX(numEstudio) from estudio;')
                                    nEstudio = con.fetchall()
                                    nDet = int(numDet[0][0]+1) if(numDet[0][0] != None) else 1
                                    con.execute('INSERT INTO deteccion VALUES (?, ?, ?, ?, ?); ', (str(nDet), str(int(id)), str(model.names[int(c)]), str(conf), str(nEstudio[0][0])))
                                    conn.commit()
                                    conn.close()
                                    #flash('Registro guardado exitosamente.')
                                except Exception as e:
                                    logging.error('Error: %s, Error.  No se pudo insertar los datos a la base de datos.', str(e))
                                    flash('Error:'+str(e)+', Error.  No se pudo insertar los datos a la base de datos.')
            if(annotator != None):
                image = annotator.result() # El problema está en que no me graba nada, porque el id es None
            end = time.perf_counter()
            totalTime = end - start
            fps = 1 / totalTime
            return image
    except Exception as e:
        logging.error('Error: '+str(e)+', Error. No se pudieron procesar las imágenes.')
        flash('Error: '+str(e)+', Error. No se pudieron procesar las imágenes.')
def getCameraList(crowd):
    try:
        conn = sqlite3.connect(getJSONValues()[0]["dbConn"])
        con = conn.cursor()
        con.execute('select crowdCameras from crowd where crowdName ="'+crowd+'";')
        crowdCameras = con.fetchall()
        conn.close()
        #Setting cameras
        image_source = str(crowdCameras[0][0])
        image_source = image_source.strip()
        image_source = image_source.split(",")
        global iSList
        global sourceList
        iSList = []
        sourceList = []
        for iSou in image_source:
            iSou = iSou.strip()
            iSList.append(cv2.VideoCapture(iSou))
            sourceList.append(iSou)
    except Exception as e:
        logging.error('Error: ' +str(e))
        flash('Error: ' +str(e))      

def gen_frame():
    try:
        lmodelTrained = getJSONValues()[0]["ltModel"]
        model = YOLO(lmodelTrained)
        detector = model
        count = 0
        img = []
        global iSList
        global sourceList
        global nameCam
        global id_Crowd
        while True:
            frame = None
            for imgSource in iSList:
                success, frame = imgSource.read()
                nameCam = str(sourceList[iSList.index(imgSource)])
                frame = np.array(frame)
                if frame.all() != None:
                    frame = cv2.resize(frame, (540, 300))#(1080, 600))
                if not success and frame.all() == None:
                    logging.error('Error: ----------------------------- Error en la cámara #%s+" -----------------------------.', str(numCam))
                    pass
                else:
                    frameAux = frame
                    saveToDB = True
                    if(saveToDB):
                        try:
                            global crowdName
                            conn = sqlite3.connect(getJSONValues()[0]["dbConn"])
                            con = conn.cursor()
                            con.execute('select idCrowd from crowd where crowdName = ?;', (crowdName, ))
                            idCrowd = con.fetchall()
                            id_Crowd = int(idCrowd[0][0])
                            con.execute('select MAX(numEstudio) from estudio;')
                            numEstudio = con.fetchall()
                            nEstudio = int(numEstudio[0][0]+1) if(numEstudio[0][0] != None) else 1
                            con.execute('INSERT INTO estudio VALUES (?, ?, ?, ?, ?);', (str(nEstudio), str(nameCam), str(date.today()), str(time.time()), str(idCrowd[0][0])))
                            conn.commit()
                            conn.close()
                        except Exception as e:
                            logging.error("Error: No se pudo insertar los datos a la base de datos. "+ str(e))
                    image = getSegmentedImages(frame)
                    for segImage in image:
                        saveToDB = True
                        segImage = getNativeTracking(model, segImage, "1", False, "bytetrack.yaml", nEstudio, saveToDB=saveToDB)
                        suc, encode = cv2.imencode('.jpg', segImage)
                        segImage = encode.tobytes()
                        yield(b'--frame\r\n'
                                b'content-Type: image/jpeg\r\n\r\n'+ segImage + b'\r\n')
                    evalImage = False
                    if(evalImage):
                        saveToDB = False
                        frameAux = getNativeTracking(model, frameAux, "1", False, "bytetrack.yaml", nEstudio, saveToDB=saveToDB)
                        suc, encode = cv2.imencode('.jpg', frameAux)
                        frameAux = encode.tobytes()
                        yield(b'--frame\r\n'
                                b'content-Type: image/jpeg\r\n\r\n'+ frameAux + b'\r\n')
    except Exception as e:
        logging.error('Error:'+str(e)+'. Error al procesar las imágenes.')
        flash('Error: '+str(e)+'. Error al procesar las imágenes.')
            

@app.route('/', methods=['GET', 'POST'])
def login():
    try:
        #Login
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            if user:
                if bcrypt.check_password_hash(user.password, form.password.data):
                    login_user(user)
                    if(user.userType == "admin"):
                        return redirect(url_for('adminMenu', userName=form.username.data, userType=user.userType))
                    elif(user.userType == "commonUs"):
                        return redirect(url_for('userMenu', userName=form.username.data))
        return render_template('login.html', form=form)
    except Exception as e:
        logging.error('Error: ' +str(e))
        flash('Error: ' +str(e))
        return render_template('login.html', form=form)
        

@app.route('/adminMenu/', methods=['GET', 'POST'])
@login_required
def adminMenu():
    try:
        userName = request.args['userName']
        userType = request.args['userType']
        if(userType == "admin"):
            return render_template('adminMenu.html', userName=userName)
        return redirect(url_for('userMenu', userName=userName))
    except Exception as e:
        flash('Error: ' +str(e))
        logging.error('Error: ' +str(e))

@app.route('/userMenu/', methods=['GET', 'POST'])
@login_required
def userMenu():
    try:
        userName = request.args['userName']
        conn = sqlite3.connect(getJSONValues()[0]["dbConn"])
        con = conn.cursor()
        con.execute('select id, userType from user where username = "'+userName+'";')
        User = con.fetchall()
        if(User[0][1] == "commonUs"):
            con.execute('select crowdName from crowd where id = '+str(User[0][0])+';')
        elif(User[0][1] == "admin"):
            con.execute('select crowdName from crowd;')
        crowdsNames = con.fetchall()
        listCrowds = [list(x) for x in crowdsNames]
        conn.close()
        return render_template('userMenu.html', data=listCrowds, userName=userName)
    except Exception as e:
        flash('Error: ' +str(e))
        logging.error('Error: ' +str(e))

@app.errorhandler(404)
@login_required
def page_not_found(error):
    try:
        if not ('conectado' in session and request.method == 'GET'):
            return redirect(url_for('pagenotfound'))
    except Exception as e:
        flash('Error: ' +str(e))
        logging.error('Error: ' +str(e))

@app.route('/pagenotfound', methods=['GET', 'POST'])
@login_required
def pagenotfound():
    try:
        return render_template('pagenotfound.html'), 404
    except Exception as e:
        flash('Error: ' +str(e))
        logging.error('Error: ' +str(e))

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    try:
        return render_template('dashboard.html')
    except Exception as e:
        return jsonify({'error': str(e)})
        flash('Error: ' +str(e))
        logging.error('Error: ' +str(e))
        

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    try:
        logout_user()
        return redirect(url_for('login'))
    except Exception as e:
        flash('Error: ' +str(e))
        logging.error('Error: ' +str(e))
        

#Función para operar con los usuarios.
def getUsers():
    try:
        dataValues = getJSONValues()
        conn = sqlite3.connect(dataValues[0]["dbConn"])
        con = conn.cursor()
        con.execute('select * from user;')
        userDetails = con.fetchall()
        listUserDetails = [list(x) for x in userDetails]
        for user in listUserDetails:
            user[2]="OCULTO"
        userDetails = tuple(listUserDetails)
        insertObject = []
        columnNames = [column[0] for column in con.description]
        for record in userDetails:
            insertObject.append(dict(zip(columnNames, record)))
        con.close()
        return insertObject
    except Exception as e:
        flash('Error: ' +str(e))
        logging.error('Error: ' +str(e))
        

@app.route('/updateUser/<string:id>',  methods=['GET', 'POST'])
@login_required
def updateUser(id):
    try:
        if(request.method == 'POST'):
            dataValues = getJSONValues()
            validateU = validate_User(request.form.get('usernameedit'), request.form.get('passwordedit'), request.form.get('emailedit'), dataValues = dataValues, mode="")
            if(validateU.validate_User()):
                conn = sqlite3.connect(dataValues[0]["dbConn"])
                con = conn.cursor()
                hashed_password = bcrypt.generate_password_hash(request.form.get('passwordedit'))
                con.execute('UPDATE user SET username = ?, password = ?, email = ?, userType = ? WHERE id = ?', (request.form.get('usernameedit'), hashed_password, request.form.get('emailedit'), request.form.get('userTypeedit'), id))
                conn.commit()
                conn.close()
                flash('Registro actualizado exitosamente.')
        return redirect(url_for('register'))
    except ValidationError as e:
        flash('Error: ' +str(e))
        logging.error('Error: ' +str(e))
        return redirect(url_for('register'))

@app.route('/deleteUser/<string:id>')
@login_required
def deleteUser(id):
    try:
        dataValues = getJSONValues()
        conn = sqlite3.connect(dataValues[0]["dbConn"])
        con = conn.cursor()
        con.execute('delete from user where id='+id+';')
        conn.commit()
        conn.close()
        flash('Registro eliminado exitosamente.')
        return redirect(url_for('register'))
    except ValidationError as e:
        flash('Error: ' +str(e))
        logging.error('Error: ' +str(e))
        return redirect(url_for('register'))

@app.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    try:
        if request.method== "POST":
            dataValues = getJSONValues()
            conn = sqlite3.connect(dataValues[0]["dbConn"])
            con = conn.cursor()
            con.execute('select MAX(id) from user;')
            numId = con.fetchall()
            conn.close()
            numId = int(numId[0][0])+1
            validateU = validate_User(request.form.get('username'), request.form.get('password'), request.form.get('email'), dataValues = dataValues, mode="INSERT")
            if(validateU.validate_User()):
                hashed_password = bcrypt.generate_password_hash(request.form.get('password'))
                new_user = User(id=numId, username=request.form.get('username'), password=hashed_password, email=request.form.get('email'), userType=request.form.get('userType'))
                db.session.add(new_user)
                db.session.commit()
                flash('Registro guardado exitosamente.')
        userDetails = getUsers()
        return render_template('register.html', data=userDetails)
    except ValidationError as e:
        flash('Error: ' +str(e))
        logging.error('Error: ' +str(e))
        userDetails = getUsers()
        return render_template('register.html', data=userDetails)

def convert_tolist(listValues):
    try:
        listValues = [list(x) for x in listValues]
        return listValues
    except Exception as e:
        flash('Error: ' +str(e))
        logging.error('Error: ' +str(e))
        

def getCamerasLink(camerasLink):
    try:
        linkcameras = """"""
        for camera in camerasLink:
            if(camera == ""","""):
                camera += """\n"""
            linkcameras += camera
        return linkcameras
    except Exception as e:
        flash('Error: ' +str(e))
        logging.error('Error: ' +str(e))
        

#Funciones para ingresar una nueva galera.
def getCrowd():
    try:
        dataValues = getJSONValues()
        conn = sqlite3.connect(dataValues[0]["dbConn"])
        con = conn.cursor()
        con.execute('select * from user;')
        userDetails = con.fetchall()
        con.execute('select * from crowd;')
        crowdDetails = con.fetchall()
        insertObject = []
        columnNames = [column[0] for column in con.description]
        columnNames[4] = 'userName'
        listValues = convert_tolist(crowdDetails)
        for record in listValues:
            for user in userDetails:
                if(record[4] == user[0]):
                    record[4] = user[1]
                    record[2] = getCamerasLink(record[2])
                    record2 = tuple(record)
                    insertObject.append(dict(zip(columnNames, record2)))
        con.close()
        return insertObject 
    except Exception as e:
        flash('Error: ' +str(e))
        logging.error('Error: ' +str(e))
        

def validate_crowdName(name):
    try:
        if(name != '' or name != None):
            conn = sqlite3.connect(getJSONValues()[0]["dbConn"])
            con = conn.cursor()
            con.execute('select crowdName from crowd where crowdName = "'+name+'";')
            crowdName = con.fetchall()
            conn.close()
            if (len(crowdName) != 0):
                raise ValidationError('Este nombre ya existe en la base de datos. Por favor, introduzca un nombre único.')
                return False
            else:
                return True
        else:
            raise ValidationError('Por favor. Introduzca un nombre válido')
            return False
    except Exception as e:
        flash('Error: ' +str(e))
        logging.error('Error: ' +str(e))
        

def validate_crowdCameras(cameras):
    try:
        val = True
        if(cameras == '' or cameras == None):
            val = False 
            raise ValidationError('El enlace de cámaras, no debe estar vacío.')
        if('''"''' in cameras or """'""" in cameras):
            val = False
            raise ValidationError('El enlace de cámaras, no debe contener caracteres especiales como: " .')
        return val
    except Exception as e:
        flash('Error: ' +str(e))
        logging.error('Error: ' +str(e))
        

@app.route('/cregister', methods=['GET', 'POST'])
@login_required
def cregister():
    try:
        conn = sqlite3.connect(getJSONValues()[0]["dbConn"])
        con = conn.cursor()
        con.execute('select username from user;')
        userNameData = con.fetchall()
        conn.close()
        data2 = []
        for data in userNameData:
            data2.append(data[0])
        if request.method== "POST":
            conn = sqlite3.connect(getJSONValues()[0]["dbConn"])
            con = conn.cursor()
            con.execute('select MAX(idCrowd) from crowd;')
            numId = con.fetchall()
            conn.close()
            if(numId[0][0]!=None): 
                numId = int(numId[0][0])+1
            else:
                numId = 1
            if(validate_crowdName(request.form.get('crowdName')) and validate_crowdCameras(request.form.get('crowdCameras')) and request.form.get('chickInitQuant')!=0 and request.form.get('crowdUser')!=''):
                conn = sqlite3.connect(getJSONValues()[0]["dbConn"])
                con = conn.cursor()
                con.execute('select id from user where username = "'+request.form.get('crowdUser')+'";')
                userID = con.fetchall()
                con.execute('INSERT INTO crowd VALUES('+str(numId)+', "'+request.form.get('crowdName')+'", "'+str(request.form.get('crowdCameras'))+'", '+str(request.form.get('chickInitQuant'))+', '+str(userID[0][0])+')')
                conn.commit()
                conn.close()
                flash('Registro guardado exitosamente.')
        crowdDetails = getCrowd()
        return render_template('crowdRegister.html', crowdUser=data2, data=crowdDetails)
    except ValidationError as e:
        flash('Error: ' +str(e))
        logging.error('Error: ' +str(e))
        crowdDetails = getCrowd()
        #return render_template('crowdRegister.html', crowdUser=data2, data=crowdDetails, error=str(e))

@app.route('/updateCrowd/<string:idCrowd>',  methods=['GET', 'POST'])
@login_required
def updateCrowd(idCrowd):
    try:
        if(request.method == 'POST'):
            dataValues = getJSONValues()
            if(request.form.get('crowdNameedit') != '' and request.form.get('crowdCamerasedit') != '' and request.form.get('chickInitQuantedit') != None):
                conn = sqlite3.connect(dataValues[0]["dbConn"])
                con = conn.cursor()
                con.execute('UPDATE crowd SET crowdName = ?, crowdCameras = ?, chickInitQuant = ? WHERE idCrowd = ?', (request.form.get('crowdNameedit'), request.form.get('crowdCamerasedit'), request.form.get('chickInitQuantedit'), idCrowd))
                conn.commit()
                conn.close()
                flash('Registro actualizado exitosamente.')
        return redirect(url_for('cregister'))
    except ValidationError as e:
        flash('Error: ' +str(e))
        logging.error('Error: ' +str(e))
        return redirect(url_for('cregister'))

@app.route('/deleteCrowd/<string:id>')
@login_required
def deleteCrowd(id):
    try:
        dataValues = getJSONValues()
        conn = sqlite3.connect(dataValues[0]["dbConn"])
        con = conn.cursor()
        con.execute('delete from crowd where idCrowd='+id+';')
        conn.commit()
        conn.close()
        flash('Registro eliminado exitosamente.')
        return redirect(url_for('cregister'))
    except ValidationError as e:
        flash('Error: ' +str(e))
        logging.error('Error: ' +str(e))
        return redirect(url_for('cregister'))

@app.route('/index/<string:crowd>')
@login_required
def index(crowd):
    try:
        global crowdName
        crowdName = crowd
        getCameraList(crowd)
        return render_template('index.html', crowd=crowd)
    except Exception as e:
        flash('Error: ' +str(e))
        logging.error('Error: ' +str(e))
        return render_template('index.html', crowd=crowd)

@app.route('/get_NumCam', methods=['GET'])
def get_NumCam():
    try:
        global nameCam
        return jsonify({'numCam': str(nameCam)})
    except Exception as e:
        return jsonify({'numCam': str(0)})
        flash('Error:'+str(e)+'. No se pudo cargar el identificador de la cámara.')
        logging.error('Error:'+str(e)+'. No se pudo cargar el identificador de la cámara.')

@app.route('/configForm', methods=['GET', 'POST'])
@login_required
def configForm():
    try:
        if request.method == "POST":
            dictData = {
                "ltModel": request.form.get("ltModel"),
                "dbConn": request.form.get("dbConn")   
            }
            with open('data.json', 'w') as file_object:
                json.dump(dictData, file_object)
        dataValues = getJSONValues()
        return render_template('configForm.html', dataValuesltModel=dataValues[0]['ltModel'], dataValuesdbConn=dataValues[0]['dbConn']) #Por el momento solo retornará el index... #
    except:
        flash('Error: %s. No se pudieron guardar los datos.', str(e))
        logging.error('Error: %s. No se pudieron guardar los datos.', str(e))
        dataValues = getJSONValues()
        return render_template('configForm.html', dataValuesltModel=dataValues[0]['ltModel'], dataValuesdbConn=dataValues[0]['dbConn']) #Por el momento solo retornará el index... #

@app.route('/reports', methods=['GET', 'POST'])
@login_required
def reports():
    try:
        dataValues = getJSONValues()
        conn = sqlite3.connect(dataValues[0]["dbConn"])
        con = conn.cursor()
        con.execute('select idCrowd, crowdName, chickInitQuant from crowd;')
        crowd = con.fetchall()
        con.execute('select estudio.numEstudio, estudio.idCrowd, estudio.dateEst, cantPVivos, cantPMuertos from estudio inner join cantPollos on estudio.numEstudio = cantPollos.numEstudio group by estudio.dateEst;')# DESC;')#Limit 1;')#con.execute('select estudio.numEstudio, estudio.idCrowd, dateEst, cantPVivos, cantPMuertos from estudio inner join cantPollos on estudio.numEstudio = cantPollos.numEstudio order by estudio.dateEst DESC') #LIMIT 1;')
        estudio = con.fetchall()
        insertObject = []
        columnNames = [column[0] for column in con.description]
        columnNames[1] = 'Galera'
        columnNames.insert(2, "Cantidad")
        listValues = convert_tolist(estudio)
        for record in listValues:
            for crowdR in crowd:
                if(record[1] == crowdR[0]):
                    record[1] = crowdR[1]
                    record.insert(2, crowdR[2])
                    record2 = tuple(record)
                    insertObject.append(dict(zip(columnNames, record2)))
        con.close()
        return render_template('reports.html', data=insertObject)
    except Exception as e:
        flash('Error: ' +str(e))
        logging.error('Error: ' +str(e))

@app.route('/genReport/<string:crowdName>/<string:dateEst>')
@login_required
def genReport(crowdName, dateEst):
    try:
        sumPV = 0
        sumPM = 0
        promPV = 0
        promPM = 0
        dataValues = getJSONValues()
        conn = sqlite3.connect(dataValues[0]["dbConn"])
        con = conn.cursor()
        con.execute('select idCrowd, chickInitQuant from crowd where crowdName = ?;', (crowdName, ))
        idCrowd = con.fetchall()
        con.execute('select estudio.numEstudio, dateEst, cantPVivos, cantPMuertos from estudio inner join cantPollos on estudio.numEstudio = cantPollos.numEstudio where estudio.dateEst= ? and estudio.idCrowd = ?;', (dateEst, idCrowd[0][0], ))
        estudio = con.fetchall()
        con.close() 
        pdf = FPDF()
        pdf.add_page()

        page_width = pdf.w -2 * pdf.l_margin

        pdf.set_font('Times', 'B', 14.0)
        pdf.cell(page_width, 0.0, crowdName, align='C')
        pdf.ln(10)
        pdf.cell(page_width, 0.0, 'Datos de los estudios', align='C')

        pdf.ln(10)
        pdf.set_font('Courier', '', 12)
        col_width = page_width/4
        pdf.ln(1)

        th = pdf.font_size

        pdf.cell(page_width/2, th, 'Cantidad de pollos iniciales', border=1)
        pdf.cell(page_width/2, th, str(idCrowd[0][1]), border=1)
        pdf.ln(10)
        
        pdf.cell(col_width, th, "# Estudio", border=1)
        pdf.cell(col_width, th, "Fecha", border=1)
        pdf.cell(col_width, th, "Detectados", border=1)
        pdf.cell(col_width, th, "No detectados", border=1)
        pdf.ln(th)
        for row in estudio:
            pdf.cell(col_width, th, str(row[0]), border=1)
            pdf.cell(col_width, th, str(row[1]), border=1)
            pdf.cell(col_width, th, str(row[2]), border=1)
            pdf.cell(col_width, th, str(row[3]), border=1)
            pdf.ln(th)
        
        pdf.ln(10)
        for est in estudio:
            sumPV += est[2]
            sumPM += est[3]
        
        promPV = sumPV/len(estudio)
        promPM = sumPM/len(estudio)
        
        pdf.cell(col_width, th, 'Promedios', border=1)
        pdf.ln(th)
        pdf.cell(col_width, th, "Detectados", border=1)
        pdf.cell(col_width, th, "No detectados", border=1)
        pdf.ln(th)
        pdf.cell(col_width, th, str(round(promPV, 0)), border=1)
        pdf.cell(col_width, th, str(round(promPM, 0)), border=1)
        pdf.ln(th)
        pdf.ln(th)
        pdf.set_font('Times', '', 10.0)
        pdf.cell(page_width, 0.0, '- Fin del reporte', align='C')
        return Response(pdf.output(dest='S').encode('latin-1'), mimetype='application/pdf', headers={'Content-Disposition':'attachment;filename=employee_report.pdf'})
    except Exception as e:
        flash('Error: ' +str(e))
        logging.error('Error: %s. ', str(e))

@app.route('/genReportUser/<string:crowd>')
@login_required
def genReportUser(crowd):
    try:
        sumPV = 0
        sumPM = 0
        promPV = 0
        promPM = 0
        global crowdName
        dataValues = getJSONValues()
        conn = sqlite3.connect(dataValues[0]["dbConn"])
        con = conn.cursor()
        con.execute('select idCrowd, chickInitQuant from crowd where crowdName = ?;', (crowdName, ))
        idCrowd = con.fetchall()
        conn = sqlite3.connect(dataValues[0]["dbConn"])
        con = conn.cursor()
        con.execute('select estudio.numEstudio, dateEst, cantPVivos, cantPMuertos from estudio inner join cantPollos on estudio.numEstudio = cantPollos.numEstudio where estudio.idCrowd= ?;', (str(idCrowd[0][0]), ))
        estudio = con.fetchall()
        con.close()
        pdf = FPDF()
        pdf.add_page()

        page_width = pdf.w -2 * pdf.l_margin

        pdf.set_font('Times', 'B', 14.0)
        pdf.cell(page_width, 0.0, crowdName, align='C')
        pdf.ln(10)
        pdf.cell(page_width, 0.0, 'Datos de los estudios', align='C')

        pdf.ln(10)
        pdf.set_font('Courier', '', 12)
        col_width = page_width/4
        pdf.ln(1)

        th = pdf.font_size

        pdf.cell(page_width/2, th, 'Cantidad de pollos iniciales', border=1)
        pdf.cell(page_width/2, th, str(idCrowd[0][1]), border=1)
        pdf.ln(10)
        
        pdf.cell(col_width, th, "# Estudio", border=1)
        pdf.cell(col_width, th, "Fecha", border=1)
        pdf.cell(col_width, th, "Detectados", border=1)
        pdf.cell(col_width, th, "No detectados", border=1)
        pdf.ln(th)
        for row in estudio:
            pdf.cell(col_width, th, str(row[0]), border=1)
            pdf.cell(col_width, th, str(row[1]), border=1)
            pdf.cell(col_width, th, str(row[2]), border=1)
            pdf.cell(col_width, th, str(row[3]), border=1)
            pdf.ln(th)
        
        pdf.ln(10)
        for est in estudio:
            sumPV += est[2]
            sumPM += est[3]
        
        promPV = sumPV/len(estudio)
        promPM = sumPM/len(estudio)
        
        pdf.cell(col_width, th, 'Promedios', border=1)
        pdf.ln(th)
        pdf.cell(col_width, th, "Detectados", border=1)
        pdf.cell(col_width, th, "No detectados", border=1)
        pdf.ln(th)
        pdf.cell(col_width, th, str(round(promPV, 0)), border=1)
        pdf.cell(col_width, th, str(round(promPM, 0)), border=1)
        pdf.ln(th)
        pdf.ln(th)
        pdf.set_font('Times', '', 10.0)
        pdf.cell(page_width, 0.0, '- Fin del reporte', align='C')
        return Response(pdf.output(dest='S').encode('latin-1'), mimetype='application/pdf', headers={'Content-Disposition':'attachment;filename=employee_report.pdf'})
    except Exception as e:
        flash('Error: ' +str(e))
        logging.error('Error: ' +str(e))

def generateDailyReport():
    try:
        sumPV = 0
        sumPM = 0
        promPV = 0
        promPM = 0
        global crowdName
        #Getting today date
        today = date.today()
        dataValues = getJSONValues()
        conn = sqlite3.connect(dataValues[0]["dbConn"])
        con = conn.cursor()
        con.execute('select idCrowd, chickInitQuant from crowd where crowdName = ?;', (crowdName, ))
        idCrowd = con.fetchall()
        conn = sqlite3.connect(dataValues[0]["dbConn"])
        con = conn.cursor()
        con.execute('select estudio.numEstudio, estudio.dateEst, cantPVivos, cantPMuertos from estudio inner join cantPollos on estudio.numEstudio = cantPollos.numEstudio where estudio.idCrowd= ? and estudio.dateEst = ?;', (str(idCrowd[0][0]), today, ))
        estudio = con.fetchall()
        con.close()
        pdf = FPDF()
        pdf.add_page()

        page_width = pdf.w -2 * pdf.l_margin

        pdf.set_font('Times', 'B', 14.0)
        pdf.cell(page_width, 0.0, crowdName, align='C')
        pdf.ln(10)
        pdf.cell(page_width, 0.0, 'Datos de los estudios', align='C')

        pdf.ln(10)
        pdf.set_font('Courier', '', 12)
        col_width = page_width/4
        pdf.ln(1)

        th = pdf.font_size

        pdf.cell(page_width/2, th, 'Cantidad de pollos iniciales', border=1)
        pdf.cell(page_width/2, th, str(idCrowd[0][1]), border=1)
        pdf.ln(10)
        
        pdf.cell(col_width, th, "# Estudio", border=1)
        pdf.cell(col_width, th, "Fecha", border=1)
        pdf.cell(col_width, th, "Detectados", border=1)
        pdf.cell(col_width, th, "No detectados", border=1)
        pdf.ln(th)
        for row in estudio:
            pdf.cell(col_width, th, str(row[0]), border=1)
            pdf.cell(col_width, th, str(row[1]), border=1)
            pdf.cell(col_width, th, str(row[2]), border=1)
            pdf.cell(col_width, th, str(row[3]), border=1)
            pdf.ln(th)
        
        pdf.ln(10)
        for est in estudio:
            sumPV += est[2]
            sumPM += est[3]
        
        promPV = sumPV/len(estudio)
        promPM = sumPM/len(estudio)
        
        pdf.cell(col_width, th, 'Promedios', border=1)
        pdf.ln(th)
        pdf.cell(col_width, th, "Detectados", border=1)
        pdf.cell(col_width, th, "No detectados", border=1)
        pdf.ln(th)
        pdf.cell(col_width, th, str(round(promPV, 0)), border=1)
        pdf.cell(col_width, th, str(round(promPM, 0)), border=1)
        pdf.ln(th)
        pdf.ln(th)
        pdf.set_font('Times', '', 10.0)
        pdf.cell(page_width, 0.0, '- Fin del reporte', align='C')
        pdf.output("reports/"+crowdName+".pdf", 'F')
    except Exception as e:
        flash('Error: ' +str(e))
        logging.error('Error: ' +str(e))

def sendMail(mailSystem=None, psswdSystem=None, emailUser=None):
    try:
        global crowdName
        now = datetime.now()
        current_hour = int(now.strftime("%H"))
        current_minutes = int(now.strftime("%M"))
        if(current_hour == 23):
            if(current_minutes >= 59 and current_minutes <= 59):
                generateDailyReport()
                mailer_sys = mailer(mailSystem, psswdSystem)
                mailer_sys.getBasicMail(emailUser, "reports/"+crowdName+".pdf")
    except Exception as e:
        flash('Error: ' +str(e))
        logging.error('Error: ' +str(e))

@app.route('/video')
def video():
    try:
        return Response(gen_frame(), mimetype='multipart/x-mixed-replace; boundary=frame')
    except Exception as e:
        flash('Error: ' +str(e))
        logging.error('Error: ' +str(e))

@app.route('/_chickDesc', methods=['POST'])
def chickDesc(): 
    try:
        data = []
        global chickCounting
        conn = sqlite3.connect(getJSONValues()[0]["dbConn"])
        con = conn.cursor()
        con.execute('select MAX(numEstudio) from estudio;')
        numEstudio = con.fetchall()
        numEstudio = int(numEstudio[0][0])-1 if (numEstudio[0][0] != None) else 0
        con.execute('select * from deteccion where numEstudio = '+str(numEstudio)+' ORDER BY numDet ASC;')
        detections = con.fetchall()
        conn.close()
        for detection in detections:
            if(detection[2]=="pollo_vivo"):
                data.append({"ID": str(detection[1]), "CATEGORIA": "Pollo vivo", "PRECISION": detection[3]})
            else:
                data.append({"ID": str(detection[1]), "CATEGORIA": "Pollo muerto", "PRECISION": detection[3]})
        return jsonify(data)
    except Exception as e:
        flash('Error: '+ str(e)+'. No se pudieron cargar los datos.')
        logging.error('Error: '+ str(e)+'. No se pudieron cargar los datos.')
        data.append({"ID": str(0), "CATEGORIA": "Ninguna", "PRECISION": 0})
        return jsonify(data)

@app.route('/_chickCount', methods=['POST'])
def chickCount():
    try:
        global crowdName
        global id_Crowd
        dataCount = []
        countPV = 0
        countPM = 0
        countChickDetected = 0
        countingChick = 0
        #Getting the values of the table estudio
        """conn = sqlite3.connect(getJSONValues()[0]["dbConn"])
        con = conn.cursor()
        con.execute('select numEstudio from estudio where idCrowd='+str(id_Crowd)+' and crowdCamera='+sourceList[len(sourceList)-1]+';')
        estudioInfo = con.fetchall()
        for estudioIn in estudioInfo:
            conn = sqlite3.connect(getJSONValues()[0]["dbConn"])
            con = conn.cursor()
            con.execute('select catChick from deteccion where numEstudio = '+str(estudioIn[0])+' ORDER BY numDet ASC;')
            detections = con.fetchall()
            countingChick = countingChick + len(detections)
            conn.close()
        print(countingChick)"""
        #Extracting data from database
        conn = sqlite3.connect(getJSONValues()[0]["dbConn"])
        con = conn.cursor()
        con.execute('select MAX(numEstudio) from estudio;')
        numEstudio = con.fetchall()
        numEstudio = int(numEstudio[0][0])-1 if (numEstudio[0][0] != None) else 0
        con.execute('select catChick from deteccion where numEstudio = '+str(numEstudio)+' ORDER BY numDet ASC;')
        detections = con.fetchall()
        conn.close()
        countChickDetected = countChickDetected + len(detections)
        #Extracting initial data from database
        conn = sqlite3.connect(getJSONValues()[0]["dbConn"])
        con = conn.cursor()
        con.execute('select chickInitQuant from crowd where crowdName = "'+crowdName+'";')
        initialQuantity = con.fetchall() 
        conn.close()
        if(len(initialQuantity) != 0):
            if(initialQuantity[0][0] != None):
                initialQuantity = initialQuantity[0][0]
        else:
            initialQuantity = 0
        countChickNotDetected = int(initialQuantity) - countChickDetected #Por ahora se pone por código...
        #Appending data to send
        if(int(countChickDetected) < 0):
            countChickDetected = 0
        if(int(countChickNotDetected) < 0):
            countChickNotDetected = 0
        dataCount.append({"CCHICKDETECTED": str(countChickDetected), "CCHICKNOTDETECTED": countChickNotDetected})
        #Saving to db
        conn = sqlite3.connect(getJSONValues()[0]["dbConn"])
        con = conn.cursor()
        con.execute('select MAX(numEstudio) from estudio;')
        numEstudio = con.fetchall()
        nEstudio = int(numEstudio[0][0]+1) if(numEstudio[0][0] != None) else 1
        con.execute('INSERT INTO cantPollos VALUES (?, ?, ?); ', (str(nEstudio), str(int(countChickDetected)), str(int(countChickNotDetected))))
        conn.commit()
        conn.close()
        #flash('Registro guardado exitosamente.')

        #Sending mail
        crowd_Name = crowdName
        conn = sqlite3.connect(getJSONValues()[0]["dbConn"])
        con = conn.cursor()
        con.execute('select id from crowd where crowdName = ?;', (crowd_Name, ))
        idUser = con.fetchall()
        con.execute('select email from user where id = ?;', (str(idUser[0][0]), ))
        email = con.fetchall()
        conn.close()
        sendMail(mailSystem="monzad2023@outlook.com", psswdSystem="MonZ4d23", emailUser=email[0][0])
        return jsonify(dataCount)
    except Exception as e:
        dataCount = []
        dataCount.append({"CCHICKDETECTED": 0, "CCHICKNOTDETECTED": 0})
        return jsonify(dataCount)
        flash('Error: ' +str(e))
        logging.error('Error: ' +str(e))

@app.route('/_getDataValues', methods=['POST'])
def getDataValues():
    try:
        dataValues = getJSONValues()
        return jsonify(dataValues)
    except Exception as e:
        flash('Error: ' +str(e))
        logging.error('Error: ' +str(e))

def main():
    try:
        app.run(debug = True)
    except Exception as e:
        flash('Error: ' +str(e))
        logging.error('Error: ' +str(e))

if __name__ == "__main__":
    main()
   
