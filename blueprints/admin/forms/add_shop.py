from flask_wtf import FlaskForm
from wtforms import Form, BooleanField, StringField, PasswordField, validators, SubmitField, RadioField, FileField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError

class AddShopForm(FlaskForm):
    shop_name = StringField('Shop Name',
                           validators=[DataRequired(), Length(min=1)])
    
    shop_address = StringField('Shop Address',
                           validators=[DataRequired(), Length(min=1)])

    shop_description = StringField('Shop Description',
                           validators=[DataRequired(), Length(min=1)])

    shop_image = FileField("Shop Image",validators=[DataRequired()])
    
    submit = SubmitField('Add Shop')