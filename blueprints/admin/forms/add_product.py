from flask_wtf import FlaskForm
from wtforms import Form, BooleanField, StringField, PasswordField, validators, SubmitField, RadioField, DecimalField, FileField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from wtforms.fields import html5 as h5fields
from wtforms.widgets import html5 as h5widgets
class AddProductForm(FlaskForm):

    
    product_name = StringField('Product Name',
                           validators=[DataRequired(), Length(min=1)])
    product_description = StringField('Product Description',
                           validators=[DataRequired(), Length(min=1)])
                           
    product_price = h5fields.DecimalField("Product Price", widget=h5widgets.NumberInput(step="any"))
    
    product_image = FileField("Product Image",validators=[DataRequired()])

        
    submit = SubmitField('Add Product')
