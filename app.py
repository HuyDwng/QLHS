from QLHS import create_app, db
from flask import render_template, Flask, jsonify, request, flash, redirect, url_for, session
from QLHS.models import userLogin, Subject, Year, Semester, Class, Point, Student
from werkzeug.security import generate_password_hash

app = create_app()

@app.route('/')
def index():
    return render_template('index.html')

###LOGIN start###
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        # Kiểm tra thông tin đăng nhập
        user = userLogin.query.filter_by(username=username).first()

        if user and user.check_password(password) and user.role.name == role.upper():  # Kiểm tra vai trò
            session['username'] = username
            session['role'] = role

            if role == 'admin':
                return redirect(url_for('admin_page'))
            elif role == 'teacher':
                return redirect(url_for('teacher_page'))
            elif role == 'staff':
                return redirect(url_for('staff_page'))
        else:
            flash('Tên đăng nhập, mật khẩu hoặc vai trò không đúng!', 'danger')

    return render_template('login.html')
###LOGIN end###

###LOGOUT start###
@app.route('/logout')
def logout():
    return redirect(url_for('index'))
###LOGOUT end###

###ADMIN start###
@app.route('/admin_page')
def admin_page():
    return render_template('admin.html')

###Thống kê báo cáo start###
@app.route('/report', methods=['GET', 'POST'])
def report():
    # Fetch data for dropdowns
    years = [(year.yearID, year.yearName) for year in Year.query.all()]
    subjects = [(subject.subjectID, subject.subjectName) for subject in Subject.query.all()]
    
    # Initialize variables for rendering
    report_data = None
    subject_name = None
    year_name = None
    semester_name = None
    show_chart = False

    if request.method == 'POST':
        # Get user input from form
        subject_id = int(request.form.get('subject'))
        year_id = int(request.form.get('year'))
        semester_id = int(request.form.get('semester'))
        show_chart = 'showChart' in request.form

        # Fetch selected subject, year, and semester names
        selected_subject = Subject.query.get(subject_id)
        selected_year = Year.query.get(year_id)
        selected_semester = Semester.query.get(semester_id)
        
        if selected_subject and selected_year and selected_semester:
            subject_name = selected_subject.subjectName
            year_name = selected_year.yearName
            semester_name = f"Học kỳ {semester_id}"

            # Fetch class data related to the selected year
            classes = Class.query.all()

            # Prepare report data
            report_data = []
            for cls in classes:
                # Get students in the class
                students = Student.query.filter(Student.classID == cls.classID).all()
                total_students = len(students)

                # Calculate the number of students who passed
                pass_students = 0
                for student in students:
                    # Calculate the average score for the selected subject and semester
                    points = Point.query.filter_by(
                        subjectID=subject_id,
                        studentID=student.studentID,
                        semesterID=selected_semester.semesterID
                    ).all()
                    if points:
                        average_score = sum(point.value for point in points) / len(points)
                        if average_score >= 5:  # Consider 5 as the passing mark
                            pass_students += 1

                # Calculate pass rate
                pass_rate = round((pass_students / total_students) * 100, 2) if total_students > 0 else 0

                # Add data for the class
                report_data.append({
                    'class_name': cls.class_name,
                    'total_students': total_students,
                    'pass_students': pass_students,
                    'pass_rate': pass_rate
                })

    return render_template(
        'report.html',
        subjects=subjects,
        years=years,
        report_data=report_data,
        subject_name=subject_name,
        year_name=year_name,
        semester_name=semester_name,
        subject_id=request.form.get('subject') if request.method == 'POST' else None,
        year_id=request.form.get('year') if request.method == 'POST' else None,
        semester_id=request.form.get('semester') if request.method == 'POST' else None,
        show_chart=show_chart
    )
###Thống kê báo cáo end###

###Tạo tài khoản start###
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        # Kiểm tra xem tên đăng nhập đã tồn tại chưa
        existing_user = userLogin.query.filter_by(username=username).first()
        if existing_user:
            flash('Tên đăng nhập đã tồn tại. Vui lòng chọn tên khác.', 'error')
            return redirect(url_for('register'))

        # Mã hóa mật khẩu trước khi lưu vào cơ sở dữ liệu
        hashed_password = generate_password_hash(password)

        # Tạo đối tượng UserLogin mới
        new_user = userLogin(username=username, password=hashed_password, role=role)

        # Thêm vào cơ sở dữ liệu
        db.session.add(new_user)
        db.session.commit()

        flash('Tài khoản đã được tạo thành công!', 'success')
        return redirect(url_for('register'))  # Chuyển hướng về trang đăng ký

    return render_template('register.html')
###Tạo tài khoản end###
###Thay đổi quy định start###
@app.route('/rule', methods=['GET', 'POST'])
def rule():
    return render_template('rule.html')

###Thay đổi quy định end###
###Quản lý môn học start###
@app.route('/manage', methods=['GET', 'POST'])
def manage():
    return render_template('manage.html')
###Quản lý môn học end###

###ADMIN end###

###Teacher start###
@app.route('/teacher_page')
def teacher_page():
    return render_template('teacher.html') 
###Teacher end###

###Staff start###
@app.route('/staff_page')
def staff_page():
    return render_template('staff.html')
###Staff end###

if __name__ == '__main__':
    app.run(debug=True)
