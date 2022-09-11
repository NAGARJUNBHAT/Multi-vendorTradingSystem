from flask_wtf import FlaskForm
from wtforms import Form, BooleanField, StringField, PasswordField, validators, SubmitField, RadioField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError

class RegistrationForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
                        
    address = StringField('Address',
                        validators=[DataRequired()])

    password = PasswordField('Password', validators=[DataRequired()])
    
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])

    user_type = RadioField("User Type", validators=[DataRequired()], choices=[
        ("customer","Customer"),
        ("shopkeeper","Shopkeeper")
        ])
    submit = SubmitField('Sign Up')