# models.py
from flask import Flask
from flask_mysql import MySQL

app = Flask(__name__)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'yourpassword'  # Đảm bảo đúng mật khẩu
app.config['MYSQL_DB'] = 'student_management'

mysql = MySQL(app)
