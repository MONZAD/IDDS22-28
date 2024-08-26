import os
import sqlite3
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy


conn = sqlite3.connect('pryChick.db')
bcrypt = Bcrypt()#app)
#Connect to database
#Create a cursor
c = conn.cursor()
print("Creando la tabla de usuario")
#Create a Table
c.execute("""
    CREATE TABLE user (
        id INTEGER NOT NULL,
        username VARCHAR(20) NOT NULL,
        password VARCHAR(80) NOT NULL,
        email VARCHAR(100) NOT NULL,
        userType VARCHAR(25) NOT NULL,
        PRIMARY KEY (id)
    );
""")
print("Creando la tabla de galera")
#Create a Table
c.execute("""
    CREATE TABLE crowd (
        idCrowd INTEGER NOT NULL,
        crowdName VARCHAR(20) NOT NULL,
        crowdCameras VARCHAR(1000000000) NOT NULL,
        chickInitQuant INTEGER NOT NULL,
        id INTEGER NOT NULL,
        PRIMARY KEY (idCrowd),
        FOREIGN KEY (id) REFERENCES user (id)
    );
""")

print("Creando la tabla de estudio")
#Create a Table
c.execute("""
    CREATE TABLE estudio (
        numEstudio integer PRIMARY KEY,
        crowdCamera varchar(100),
        dateEst text,
        hourEst text,
        idCrowd INTEGER NOT NULL,
        FOREIGN KEY (idCrowd) REFERENCES crowd (idCrowd)
    );
""")

print("Creando la tabla de cantidad de pollos")
#Create a Table
c.execute("""
    CREATE TABLE cantPollos (
        numEstudio integer,
        cantPVivos integer,
        cantPMuertos integer,
        FOREIGN KEY (numEstudio) REFERENCES estudio (numEstudio)
    );
""")

print("Creando la tabla de deteccion")
#Create a Table
c.execute("""
    CREATE TABLE deteccion (
        numDet integer PRIMARY KEY,
        idChick integer,
        catChick text,
        confChick integer,
        numEstudio integer,
        FOREIGN KEY (numEstudio) REFERENCES estudio (numEstudio)
    );
""")

print("Creando usuarios por defecto")
hashed_password1 = bcrypt.generate_password_hash("admin123")
hashed_password = bcrypt.generate_password_hash("edgar123")
c.execute("""insert into user VALUES (?, ?, ?, ?, ?);""",(1, 'admin1', hashed_password1, 'fedgo5462@gmail.com', 'admin'))
c.execute("""insert into user VALUES (?, ?, ?, ?, ?);""",(2, 'edgar', hashed_password, 'fedgo5462@gmail.com', 'commonUs'))
conn.commit()
conn.close()

print("Proceso terminado.")