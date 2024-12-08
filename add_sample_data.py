from QLHS import create_app, db  
from QLHS.models import User, userLogin, PhoneNumber, Email, Admin, Staff, Teacher, Class, Student, Year, Semester, Subject, PointType, Point, Teach, Study, ClassRule, StudentRule

app = create_app()

def add_sample_data():
    with app.app_context():
        # Thêm người dùng
        admin = Admin(user=User (name='Admin User', userAccount='admin', password='123'))
        teacher1 = Teacher(user=User (name='Teacher One', userAccount='teacher1', password='123'))
        teacher2 = Teacher(user=User (name='Teacher Two', userAccount='teacher2', password='456'))
        staff = Staff(user=User (name='Staff User', userAccount='staff', password='123'))

        db.session.add(admin)
        db.session.add(teacher1)
        db.session.add(teacher2)
        db.session.add(staff)

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

        # Thêm quan hệ dạy học
        teach1 = Teach(teacher=teacher1, class_=class1)
        teach2 = Teach(teacher=teacher2, class_=class2)
        db.session.add(teach1)
        db.session.add(teach2)

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