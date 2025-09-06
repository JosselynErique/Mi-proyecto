from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, DecimalField, SubmitField
from wtforms.validators import DataRequired, NumberRange

class ProductForm(FlaskForm):
    nombre = StringField("Nombre", validators=[DataRequired()])
    cantidad = IntegerField("Cantidad", validators=[DataRequired(), NumberRange(min=1)])
    precio = DecimalField("Precio", validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField("Agregar Producto")
