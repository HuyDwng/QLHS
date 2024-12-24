from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from . import db
from enum import Enum as PyEnum
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app

# Enum cho UserRole
class UserRole(PyEnum):
    ADMIN = 1
    TEACHER = 2
    STAFF = 3

# Model User
class User(db.Model, UserMixin):
    __tablename__ = 'User'

    userID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False)  # Sử dụng Enum cho role
    name = db.Column(db.String(255), nullable=True)
    dateOfBirth = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(10), nullable=True)

    def check_password(self, password):
        return check_password_hash(self.password, password)  # Kiểm tra mật khẩu

# Model PhoneNumber
class PhoneNumber(db.Model):
    __tablename__ = 'PhoneNumber'

    phoneID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userID = db.Column(db.Integer, db.ForeignKey('User.userID'), nullable=False)
    phoneNumber = db.Column(db.String(15), unique=True, nullable=False)
    user = db.relationship('User', backref=db.backref('phone_numbers', lazy=True))

# Model Email
class Email(db.Model):
    __tablename__ = 'Email'

    emailID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userID = db.Column(db.Integer, db.ForeignKey('User.userID'), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    user = db.relationship('User', backref=db.backref('emails', lazy=True))

# Model Admin (Kế thừa từ User)
class Admin(db.Model):
    __tablename__ = 'Admin'

    adminID = db.Column(db.Integer, db.ForeignKey('User.userID'), primary_key=True)
    user = db.relationship('User', backref=db.backref('admin', uselist=False))

# Model Staff (Kế thừa từ User)
class Staff(db.Model):
    __tablename__ = 'Staff'

    staffID = db.Column(db.Integer, db.ForeignKey('User.userID'), primary_key=True)
    user = db.relationship('User', backref=db.backref('staff', uselist=False))

# Model Teacher (Kế thừa từ User)
class Teacher(db.Model):
    __tablename__ = 'Teacher'

    teacherID = db.Column(db.Integer, db.ForeignKey('User.userID'), primary_key=True)
    user = db.relationship('User', backref=db.backref('teacher', uselist=False))

# Các model khác giữ nguyên

# Model ClassRule
class ClassRule(db.Model):
    __tablename__ = 'ClassRule'

    classRuleID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    maxNumber = db.Column(db.Integer, nullable=False)

# Model Class
class Class(db.Model):
    __tablename__ = 'Class'

    classID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    number = db.Column(db.Integer, nullable=False)
    grade = db.Column(db.Enum('grade10', 'grade11', 'grade12'), nullable=False)
    class_name = db.Column(db.String(255), nullable=False)
    classRuleID = db.Column(db.Integer, db.ForeignKey('ClassRule.classRuleID'), nullable=False)
    classRule = db.relationship('ClassRule', backref=db.backref('classes', lazy=True))

# Model StudentRule
class StudentRule(db.Model):
    __tablename__ = 'StudentRule'

    stuRuleID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    minAge = db.Column(db.Integer, nullable=False)
    maxAge = db.Column(db.Integer, nullable=False)

# Model Student
class Student(db.Model):
    __tablename__ = 'Student'

    studentID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    gender = db.Column(db.String(10), nullable=True)
    dateOfBirth = db.Column(db.Date, nullable=True)
    address = db.Column(db.String(255), nullable=True)
    classID = db.Column(db.Integer, db.ForeignKey('Class.classID'), nullable=False)
    class_ = db.relationship('Class', backref=db.backref('students', lazy=True))

# Model Year
class Year(db.Model):
    __tablename__ = 'Year'

    yearID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    yearName = db.Column(db.String(50), nullable=False)

# Model Semester
class Semester(db.Model):
    __tablename__ = 'Semester'

    semesterID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    semesterName = db.Column(db.String(50), nullable=False)
    yearID = db.Column(db.Integer, db.ForeignKey('Year.yearID'), nullable=False)
    year = db.relationship('Year', backref=db.backref('semesters', lazy=True))

# Model Subject
class Subject(db.Model):
    __tablename__ = 'Subject'

    subjectID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    subjectName = db.Column(db.String(255), nullable=False)
    grade = db.Column(db.Enum('grade10', 'grade11', 'grade12'), nullable=False)

# Model PointType
class PointType(db.Model):
    __tablename__ = 'PointType'

    pointTypeID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pointTypeName = db.Column(db.String(255), nullable=False)

# Model Point
class Point(db.Model):
    __tablename__ = 'Point'

    pointID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    subjectID = db.Column(db.Integer, db.ForeignKey('Subject.subjectID'), nullable=False)
    studentID = db.Column(db.Integer, db.ForeignKey('Student.studentID'), nullable=False)
    semesterID = db.Column(db.Integer, db.ForeignKey('Semester.semesterID'), nullable=False)
    value = db.Column(db.Float, nullable=False)
    pointTypeID = db.Column(db.Integer, db.ForeignKey('PointType.pointTypeID'), nullable=False)

    subject = db.relationship('Subject', backref=db.backref('points', lazy=True))
    student = db.relationship('Student', backref=db.backref('points', lazy=True))
    semester = db.relationship('Semester', backref=db.backref('points', lazy=True))
    pointType = db.relationship('PointType', backref=db.backref('points', lazy=True))

# Model Teach (Nhiều giáo viên có thể dạy nhiều lớp)
class Teach(db.Model):
    __tablename__ = 'Teach'

    teacherID = db.Column(db.Integer, db.ForeignKey('Teacher.teacherID'), primary_key=True)
    classID = db.Column(db.Integer, db.ForeignKey('Class.classID'), primary_key=True)

    teacher = db.relationship('Teacher', backref=db.backref('teaches', lazy=True))
    class_ = db.relationship('Class', backref=db.backref('teaches', lazy=True))

# Model Study (Nhiều học sinh có thể học nhiều lớp)
class Study(db.Model):
    __tablename__ = 'Study'

    studentID = db.Column(db.Integer, db.ForeignKey('Student.studentID'), primary_key=True)
    classID = db.Column(db.Integer, db.ForeignKey('Class.classID'), primary_key=True)

    student = db.relationship('Student', backref=db.backref('studies', lazy=True))
    class_ = db.relationship('Class', backref=db.backref('studies', lazy=True))
