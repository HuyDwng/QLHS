from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:huyduong2004@localhost/qlhs'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'your_secret_key'  # Cần thiết cho session và các bảo mật khác
    db.init_app(app)

    # Import models để tạo bảng trong cơ sở dữ liệu
    with app.app_context():
        from .models import userLogin, User, PhoneNumber, Email, Admin, Staff, Teacher, ClassRule, Class, StudentRule, Student, Year, Semester, Subject, PointType, Point, Teach, Study
        db.create_all()

    return app