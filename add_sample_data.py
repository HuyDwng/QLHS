from datetime import date
import random
from QLHS import create_app, db  
from QLHS.models import User, UserRole, PhoneNumber, Email, Admin, Staff, Teacher, Class, Student, Year, Semester, Subject, PointType, Point, Teach, Study, ClassRule, StudentRule
from werkzeug.security import generate_password_hash

app = create_app()

def add_sample_data():
    with app.app_context():
        # Thêm người dùng
        admin_user = User(
            username='admin',
            password=generate_password_hash('123'),
            role=UserRole.ADMIN,
            name='Admin User',
            dateOfBirth=date(1985, 1, 1),
            gender='Male'
        )
        teacher_user_1 = User(
            username='teacher1',
            password=generate_password_hash('123'),
            role=UserRole.TEACHER,
            name='Teacher 1',
            dateOfBirth=date(1990, 5, 15),
            gender='Female'
        )
        teacher_user_2 = User(
            username='teacher2',
            password=generate_password_hash('456'),
            role=UserRole.TEACHER,
            name='Teacher 2',
            dateOfBirth=date(1992, 8, 25),
            gender='Male'
        )
        staff_user = User(
            username='staff',
            password=generate_password_hash('123'),
            role=UserRole.STAFF,
            name='Staff User',
            dateOfBirth=date(1988, 3, 12),
            gender='Female'
        )

        #   Thêm User vào cơ sở dữ liệu trước
        db.session.add(admin_user)
        db.session.add(teacher_user_1)
        db.session.add(teacher_user_2)
        db.session.add(staff_user)
        db.session.commit()  

        # Thêm PhoneNumber và Email
        admin_phone = PhoneNumber(phoneNumber='1234567890', userID=admin_user.userID)
        admin_email = Email(email='admin@example.com', userID=admin_user.userID)

        teacher1_phone = PhoneNumber(phoneNumber='0987654321', userID=teacher_user_1.userID)
        teacher1_email = Email(email='teacher1@example.com', userID=teacher_user_1.userID)

        teacher2_phone = PhoneNumber(phoneNumber='1122334455', userID=teacher_user_2.userID)
        teacher2_email = Email(email='teacher2@example.com', userID=teacher_user_2.userID)

        staff_phone = PhoneNumber(phoneNumber='5566778899', userID=staff_user.userID)
        staff_email = Email(email='staff@example.com', userID=staff_user.userID)

        # Thêm PhoneNumber và Email vào cơ sở dữ liệu
        db.session.add(admin_phone)
        db.session.add(admin_email)

        db.session.add(teacher1_phone)
        db.session.add(teacher1_email)

        db.session.add(teacher2_phone)
        db.session.add(teacher2_email)

        db.session.add(staff_phone)
        db.session.add(staff_email)

        # Ghi thay đổi cuối cùng vào cơ sở dữ liệu
        db.session.commit()

        # Thêm lớp học
        class_rule = ClassRule(maxNumber=30)
        db.session.add(class_rule)

        class1 = Class( grade='grade10', class_name='Lớp 10A', classRule=class_rule)
        class2 = Class( grade='grade11', class_name='Lớp 11A', classRule=class_rule)
        class3 = Class( grade='grade12', class_name='Lớp 12A', classRule=class_rule)
        db.session.add(class1)
        db.session.add(class2)
        db.session.add(class3)

        db.session.commit()

        # Tạo danh sách học sinh
        students = [
            Student(name='Nguyễn Văn A', gender='Male', dateOfBirth='2008-03-15', address='Hà Nội'),
            Student(name='Trần Thị B', gender='Female', dateOfBirth='2008-06-20', address='Hải Phòng'),
            Student(name='Lê Văn C', gender='Male', dateOfBirth='2007-09-10', address='Hà Nam'),
            Student(name='Phạm Văn D', gender='Male', dateOfBirth='2006-01-25', address='Hà Nội'),
            Student(name='Nguyễn Thị E', gender='Female', dateOfBirth='2008-11-10', address='Hải Dương'),
            Student(name='Đặng Văn F', gender='Male', dateOfBirth='2007-04-14', address='Hưng Yên'),
            Student(name='Phan Văn G', gender='Male', dateOfBirth='2006-07-01', address='Thái Bình'),
            Student(name='Trần Thị H', gender='Female', dateOfBirth='2008-02-22', address='Hà Nội'),
            Student(name='Lý Văn I', gender='Male', dateOfBirth='2007-05-13', address='Hà Nam'),
            Student(name='Phạm Thị J', gender='Female', dateOfBirth='2006-09-17', address='Hải Phòng'),
            Student(name='Nguyễn Văn K', gender='Male', dateOfBirth='2008-12-03', address='Hà Nội'),
            Student(name='Lê Văn L', gender='Male', dateOfBirth='2007-08-09', address='Hà Nam'),
            Student(name='Phạm Văn M', gender='Male', dateOfBirth='2008-06-22', address='Hải Phòng'),
            Student(name='Trần Thị N', gender='Female', dateOfBirth='2008-01-11', address='Hải Dương'),
            Student(name='Đặng Văn O', gender='Male', dateOfBirth='2007-03-18', address='Hưng Yên'),
            Student(name='Phan Văn P', gender='Male', dateOfBirth='2006-10-07', address='Thái Bình'),
            Student(name='Lý Văn Q', gender='Male', dateOfBirth='2008-05-19', address='Hà Nam'),
            Student(name='Phạm Thị R', gender='Female', dateOfBirth='2007-07-30', address='Hải Phòng '),
            Student(name='Nguyễn Văn S', gender='Male', dateOfBirth='2008-09-23', address='Hà Nội'),
            Student(name='Trần Thị T', gender='Female', dateOfBirth='2008-12-28', address='Hà Nội')
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
        semester1 = Semester(semesterName='Học kỳ 1', year=year1)
        semester2 = Semester(semesterName='Học kỳ 2', year=year1)
        semester3 = Semester(semesterName='Học kỳ 1', year=year2)
        semester4 = Semester(semesterName='Học kỳ 2', year=year2)
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

        # Thêm dữ liệu vào bảng study
        for student in students:
            study = Study(studentID=student.studentID, classID= round(random.uniform(1, 3), 2))

            db.session.add(study)

        db.session.commit()
        # Lưu vào bảng User


        # Tạo đối tượng Teacher liên kết với User
        teacher1_teacher = Teacher(teacherID=teacher_user_1.userID, subjectID=1)  # Liên kết với user ID
        teacher2_teacher = Teacher(teacherID=teacher_user_2.userID, subjectID=2)

        # Thêm vào bảng Teacher
        db.session.add(teacher1_teacher)
        db.session.add(teacher2_teacher)
        db.session.commit()

        # Giả sử bạn đã có giáo viên với ID = 1 và môn học với ID = 1
        teacher_id = teacher1_teacher.teacherID
        subject_id = teacher1_teacher.subjectID

        # Giả sử bạn có các lớp học với các classID
        class_ids = [1, 2]  # Ví dụ giáo viên dạy lớp 1 và lớp 2

        # Lặp qua danh sách các lớp để thêm dữ liệu liên kết
        for class_id in class_ids:
            # Tạo đối tượng Teach mới
            teach = Teach(teacherID=teacher_id, classID=class_id, subjectID=subject_id)
            db.session.add(teach)

            # Thêm đối tượng Teach vào cơ sở dữ liệu

        teach = Teach(teacherID=3, classID=3, subjectID=2)
        db.session.add(teach)

        # Commit để lưu các thay đổi vào cơ sở dữ liệu
        db.session.commit()

        print("Dữ liệu đã được thêm thành công!!!")

if __name__ == '__main__':
    add_sample_data()