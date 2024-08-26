from flask_wtf import FlaskForm
from wtforms.validators import InputRequired, Length, ValidationError
from wtforms import StringField, PasswordField, EmailField, SelectField, SubmitField, validators

class LoginForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Nombre de usuario"})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Contraseña"})

    submit = SubmitField('Iniciar sesión')