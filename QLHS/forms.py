from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Email, Regexp  # Import Email từ wtforms.validators
import datetime

class StudentForm(FlaskForm):
    name = StringField('Tên Học Sinh', validators=[DataRequired(), Length(min=2, max=255)])
    dateOfBirth = StringField('Ngày Sinh', validators=[DataRequired()])  # Sử dụng StringField để người dùng nhập
    gender = SelectField('Giới Tính', choices=[('Male', 'Nam'), ('Female', 'Nữ')], validators=[DataRequired()])
    address = StringField('Địa Chỉ', validators=[Length(max=255)])
    phoneNumber = StringField('Số Điện Thoại', validators=[
        DataRequired(),
        Length(min=10, max=15),
        Regexp(r'^[0-9]+$', message="Số điện thoại chỉ được chứa các chữ số từ 0-9.")
    ])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=255)])
    submit = SubmitField('Thêm Học Sinh')

