from urllib.parse import quote

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    # app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:Admin@123@localhost/qlhs'
    app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:%s@localhost/student_manage?charset=utf8mb4" % quote('Admin@123')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'your_secret_key'  # Cần thiết cho session và các bảo mật khác
    db.init_app(app)
    # Khởi tạo LoginManager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "login"

    @login_manager.user_loader
    def load_user(user_id):
        return userLogin.query.get(int(user_id))
        ###Enter_scores start###
    # Import models để tạo bảng trong cơ sở dữ liệu
    with app.app_context():
        from .models import userLogin, User, PhoneNumber, Email, Admin, Staff, Teacher, ClassRule, Class, StudentRule, Student, Year, Semester, Subject, PointType, Point, Teach, Study
        db.create_all()

    return app