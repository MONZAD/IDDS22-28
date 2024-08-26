from wtforms.validators import InputRequired, Length, ValidationError
import sqlite3

class validate_User():
    def __init__(self, username, passwd, email, dataValues, mode):
        self.username = username
        self.passwd = passwd
        self.email = email
        self.dataValues = dataValues
        self.mode = mode

    #Funciones para registrar usuarios
    def password_check(self, passwd):
        SpecialSym =['$', '@', '#', '%']
        val = True
        if len(passwd) < 6:
            raise ValidationError('La longitud debe ser al menos 6 caracteres')
            val = False

        if len(passwd) > 20:
            raise ValidationError('La longitud no debe ser más de 20 caracteres')
            val = False
            
        if not any(char.isdigit() for char in passwd):
            raise ValidationError('La contraseña debe tener al menos un numero')
            val = False
            
        if not any(char.isupper() for char in passwd):
            raise ValidationError('La contraseña debe tener al menos una letra mayuscula')
            val = False
            
        if not any(char.islower() for char in passwd):
            raise ValidationError('La contraseña debe tener al menos una letra minuscula')
            val = False
            
        if not any(char in SpecialSym for char in passwd):
            raise ValidationError('La contraseña debe tener al menos un simbolo $@#')
            val = False
        return val

    def validate_email(self, email):
        val = True
        if not("@" in email):
            raise ValidationError('El correo electrónico debe contener un @, por favor introduzca un correo válido.')
            val = False
        
        if not(".com" in email):
            raise ValidationError('El correo electrónico debe contener la extensión ".com", por favor introduzca un correo válido.')
            val = False
        
        if(self.mode == "INSERT"):
            conn = sqlite3.connect(self.dataValues[0]["dbConn"])
            con = conn.cursor()
            con.execute('select email from user where email = "'+email+'";')
            email = con.fetchall()

            if(len(email) != 0):
                raise ValidationError('Error: Ese correo electrónico ya existe. Por favor, introduzca uno diferente.')
                val = False
            conn.close()

        return val

    def validate_username(self, username):
        val = True
        if(username != None and username !=''):
            if(self.mode == "INSERT"):
                conn = sqlite3.connect(self.dataValues[0]["dbConn"])
                con = conn.cursor()
                if(len(username)>8 and len(username)<18):
                    con.execute('select username from user where username = "'+username+'";')
                    username = con.fetchall()
                    conn.close()
                    if (len(username) != 0):
                        raise ValidationError('Error: Ese nombre de usuario ya existe. Por favor, escoge uno diferente.')
                        val = False
        else:
            raise ValidationError('Error: El nombre de usuario no debe estar vacío. Por favor, rellene el campo.')
            val = False
        return val

    def validate_User(self):
        val = True
        val = self.validate_username(self.username)
        val = self.password_check(self.passwd)
        val = self.validate_email(self.email)
        return val