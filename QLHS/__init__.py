from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_login import LoginManager
from urllib.parse import quote

db = SQLAlchemy()
mail = Mail()

def create_app():
    app = Flask(__name__)
    
    # Cấu hình cơ sở dữ liệu
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:huyduong2004@localhost/qlhs'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'your_secret_key'  # Cần thiết cho session và các bảo mật khác
    
    # Cấu hình email
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 465
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USE_SSL'] = True
    app.config['MAIL_USERNAME'] = 'dnmhuy@gmail.com'
    app.config['MAIL_PASSWORD'] = 'taaesdqdnjufapiw'
    app.config['MAIL_DEFAULT_SENDER'] = 'dnmhuy@gmail.com'
    
    db.init_app(app)
    mail.init_app(app)

    # Khởi tạo LoginManager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "login"

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
        ###Enter_scores start###

    # Import models để tạo bảng trong cơ sở dữ liệu
    with app.app_context():
        from .models import User, PhoneNumber, Email, Admin, Staff, Teacher, ClassRule, Class, StudentRule, Student, Year, Semester, Subject, PointType, Point, Teach, Study
        db.create_all()

    return app
