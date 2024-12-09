import random
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

        db.session.commit()

        # Thêm lớp học
        class_rule = ClassRule(maxNumber=30)
        db.session.add(class_rule)

        class1 = Class(number=1, grade='grade10', class_name='Class 10A', classRule=class_rule)
        class2 = Class(number=2, grade='grade11', class_name='Class 11A', classRule=class_rule)
        class3 = Class(number=3, grade='grade12', class_name='Class 12A', classRule=class_rule)
        db.session.add(class1)
        db.session.add(class2)
        db.session.add(class3)

        db.session.commit()

        # Tạo danh sách học sinh
        students = [
            Student(name='Nguyễn Văn A', gender='Male', dateOfBirth='2008-03-15', address='Hà Nội', classID=1),
            Student(name='Trần Thị B', gender='Female', dateOfBirth='2008-06-20', address='Hải Phòng', classID=1),
            Student(name='Lê Văn C', gender='Male', dateOfBirth='2007-09-10', address='Hà Nam', classID=1),
            Student(name='Phạm Văn D', gender='Male', dateOfBirth='2006-01-25', address='Hà Nội', classID=1),
            Student(name='Nguyễn Thị E', gender='Female', dateOfBirth='2008-11-10', address='Hải Dương', classID=1),
            Student(name='Đặng Văn F', gender='Male', dateOfBirth='2007-04-14', address='Hưng Yên', classID=2),
            Student(name='Phan Văn G', gender='Male', dateOfBirth='2006-07-01', address='Thái Bình', classID=2),
            Student(name='Trần Thị H', gender='Female', dateOfBirth='2008-02-22', address='Hà Nội', classID=3),
            Student(name='Lý Văn I', gender='Male', dateOfBirth='2007-05-13', address='Hà Nam', classID=3),
            Student(name='Phạm Thị J', gender='Female', dateOfBirth='2006-09-17', address='Hải Phòng', classID=3),
            Student(name='Nguyễn Văn K', gender='Male', dateOfBirth='2008-12-03', address='Hà Nội', classID=1),
            Student(name='Lê Văn L', gender='Male', dateOfBirth='2007-08-09', address='Hà Nam', classID=2),
            Student(name='Phạm Văn M', gender='Male', dateOfBirth='2008-06-22', address='Hải Phòng', classID=2),
            Student(name='Trần Thị N', gender='Female', dateOfBirth='2008-01-11', address='Hải Dương', classID=1),
            Student(name='Đặng Văn O', gender='Male', dateOfBirth='2007-03-18', address='Hưng Yên', classID=2),
            Student(name='Phan Văn P', gender='Male', dateOfBirth='2006-10-07', address='Thái Bình', classID=3),
            Student(name='Lý Văn Q', gender='Male', dateOfBirth='2008-05-19', address='Hà Nam', classID=3),
            Student(name='Phạm Thị R', gender='Female', dateOfBirth='2007-07-30', address='Hải Phòng ', classID=3),
            Student(name='Nguyễn Văn S', gender='Male', dateOfBirth='2008-09-23', address='Hà Nội', classID=1),
            Student(name='Trần Thị T', gender='Female', dateOfBirth='2008-12-28', address='Hà Nội', classID=1)
        ]

        # Thêm từng học sinh vào phiên làm việc
        for student in students:
            db.session.add(student)


        db.session.commit()

        # Thêm năm học
        year1 = Year(yearName='2023-2024')
        year2 = Year(yearName='2024-2025')
        db.session.add(year1)
        db.session.add(year2)

        db.session.commit()

        # Thêm học kỳ
        semester1 = Semester(semesterName='Semester 1', year=year1)
        semester2 = Semester(semesterName='Semester 2', year=year1)
        semester3 = Semester(semesterName='Semester 1', year=year2)
        semester4 = Semester(semesterName='Semester 2', year=year2)
        db.session.add(semester1)
        db.session.add(semester2)
        db.session.add(semester3)
        db.session.add(semester4)

        db.session.commit()

        # Thêm môn học
        subject1 = Subject(subjectName='Lý', grade='grade10')
        subject2 = Subject(subjectName='Toán', grade='grade11')
        subject3 = Subject(subjectName='Hóa', grade='grade12')
        db.session.add(subject1)
        db.session.add(subject2)
        db.session.add(subject3)

        db.session.commit()

        # Thêm loại điểm
        point_type1 = PointType(pointTypeName='Kiểm tra 15 phút')
        point_type2 = PointType(pointTypeName='Kiểm tra 45 phút')
        point_type3 = PointType(pointTypeName='Kiểm tra Cuối Kỳ')
        db.session.add(point_type1)
        db.session.add(point_type2)
        db.session.add(point_type3)

        db.session.commit()

        # Lấy danh sách học sinh
        students = Student.query.all()

        # Lấy danh sách môn học và loại điểm
        subjects = Subject.query.all()
        point_types = PointType.query.all()
        semesters = Semester.query.all()

        # Tạo điểm cho mỗi học sinh
        for student in students:
            for subject in subjects:
                # Chọn một học kỳ ngẫu nhiên
                random_semester = random.choice(semesters)

                for point_type in point_types:
                    # Tạo điểm ngẫu nhiên từ 0 đến 10
                    value = round(random.uniform(3, 10), 2)

                    # Thêm điểm vào bảng `Point`
                    point = Point(
                        subjectID=subject.subjectID,
                        studentID=student.studentID,
                        semesterID=random_semester.semesterID,
                        pointTypeID=point_type.pointTypeID,
                        value=value
                    )
                    db.session.add(point)

        # Lưu thay đổi vào cơ sở dữ liệu    
        db.session.commit()

        # Thêm quan hệ học
        # Thêm dữ liệu vào bảng study
        for student in students:
            study = Study(studentID=student.studentID, classID=student.classID)
            db.session.add(study)

        db.session.commit()
        print("Dữ liệu đã được thêm thành công!!!")

if __name__ == '__main__':
    add_sample_data()