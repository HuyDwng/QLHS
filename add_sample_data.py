from QLHS import create_app, db  
from QLHS.models import User, userLogin, UserRole, PhoneNumber, Email, Admin, Staff, Teacher, Class, Student, Year, Semester, Subject, PointType, Point, Teach, Study, ClassRule, StudentRule
from werkzeug.security import generate_password_hash

app = create_app()

def add_sample_data():
    with app.app_context():
        # Thêm người dùng
        admin_user = User(name='Admin User', userAccount='admin', password=generate_password_hash('123'))
        admin_login = userLogin(username='admin', password=generate_password_hash('123'), role=UserRole.ADMIN)  

        teacher_user_1 = User(name='Teacher 1', userAccount='teacher1', password=generate_password_hash('123'))
        teacher_login_1 = userLogin(username='teacher1', password=generate_password_hash('123'), role=UserRole.TEACHER)

        teacher_user_2 = User(name='Teacher 2', userAccount='teacher2', password=generate_password_hash('456'))
        teacher_login_2 = userLogin(username='teacher2', password=generate_password_hash('456'), role=UserRole.TEACHER)

        staff_user = User(name='Staff User', userAccount='staff', password=generate_password_hash('123'))
        staff_login = userLogin(username='staff', password=generate_password_hash('123'), role=UserRole.STAFF)

        # Thêm vào cơ sở dữ liệu
        db.session.add(admin_user)
        db.session.add(admin_login)

        db.session.add(teacher_user_1)
        db.session.add(teacher_login_1)

        db.session.add(teacher_user_2)
        db.session.add(teacher_login_2)

        db.session.add(staff_user)
        db.session.add(staff_login)

        # Commit các thay đổi
        db.session.commit()
        # Thêm lớp học
        class_rule = ClassRule(maxNumber=30)
        db.session.add(class_rule)

        class1 = Class(number=1, grade='grade10', class_name='Class 10A', classRule=class_rule)
        class2 = Class(number=2, grade='grade11', class_name='Class 11A', classRule=class_rule)
        db.session.add(class1)
        db.session.add(class2)

        # Thêm học sinh
        student1 = Student(name='Student One', gender='Male', dateOfBirth='2005-01-01', class_=class1)
        student2 = Student(name='Student Two', gender='Female', dateOfBirth='2005-02-01', class_=class1)
        student3 = Student(name='Student Three', gender='Male', dateOfBirth='2006-03-01', class_=class2)
        db.session.add(student1)
        db.session.add(student2)
        db.session.add(student3)

        # Thêm năm học
        year = Year(yearName='2023-2024')
        db.session.add(year)

        # Thêm học kỳ
        semester = Semester(semesterName='Semester 1', year=year)
        db.session.add(semester)

        # Thêm môn học
        subject1 = Subject(subjectName='Mathematics', grade='grade10')
        subject2 = Subject(subjectName='Literature', grade='grade11')
        db.session.add(subject1)
        db.session.add(subject2)

        # Thêm loại điểm
        point_type = PointType(pointTypeName='Midterm Exam')
        db.session.add(point_type)

        # Thêm điểm
        point1 = Point(subject=subject1, student=student1, semester=semester, value=8.5, pointType=point_type)
        point2 = Point(subject=subject2, student=student2, semester=semester, value=9.0, pointType=point_type)
        db.session.add(point1)
        db.session.add(point2)

        # # Thêm quan hệ dạy học
        # teach1 = Teach(teacher=teacher1, class_=class1)
        # teach2 = Teach(teacher=teacher2, class_=class2)
        # db.session.add(teach1)
        # db.session.add(teach2)

        # Thêm quan hệ học
        study1 = Study(student=student1, class_=class1)
        study2 = Study(student=student2, class_=class1)
        study3 = Study(student=student3, class_=class2)
        db.session.add(study1)
        db.session.add(study2)
        db.session.add(study3)

        # Commit tất cả các thay đổi
        db.session.commit()
        print('Sample data added successfully!')

if __name__ == '__main__':
    add_sample_data()