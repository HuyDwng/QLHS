import os
from QLHS import create_app, db, mail
from flask import render_template, Flask, jsonify, request, flash, redirect, url_for, session
from QLHS.models import Subject, Year, Semester, Class, Point, Student, StudentRule, ClassRule, PhoneNumber, Email, User
from werkzeug.security import generate_password_hash
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer as Serializer


app = create_app()

# Tạo một serializer để tạo và xác minh token
s = Serializer(app.config['SECRET_KEY'])


@app.route('/')
def index():
    return render_template('index.html')

### LOGIN start###
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        # Kiểm tra thông tin đăng nhập
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password) and user.role.name == role.upper():  
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
### Forgotpassword start ###
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.join(Email).filter(Email.email == email).first()

        if user:
            # Tạo token
            token = s.dumps(email, salt='password-reset-salt')
            reset_link = url_for('reset_password', token=token, _external=True)

            # Gửi email chứa link đặt lại mật khẩu
            msg = Message("Yêu cầu đặt lại mật khẩu", recipients=[email])
            msg.body = f'Click vào link để đặt lại mật khẩu: {reset_link}'
            mail.send(msg)

            flash('Một email đặt lại mật khẩu đã được gửi đến bạn.', 'info')
            return redirect(url_for('login'))
        else:
            flash('Email không tồn tại trong hệ thống.', 'danger')

    return render_template('fpass.html')
### Forgotpassword end ###

### Resetpassword start ###
@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = s.loads(token, salt='password-reset-salt', max_age=3600)  
    except:
        flash('Link đặt lại mật khẩu đã hết hạn hoặc không hợp lệ.', 'danger')
        return redirect(url_for('login'))

    user = User.query.join(Email).filter(Email.email == email).first()

    if request.method == 'POST':
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Mật khẩu và xác nhận mật khẩu không khớp!', 'danger')
        else:
            user.password = generate_password_hash(password)
            db.session.commit()
            flash('Mật khẩu đã được cập nhật thành công!', 'success')
            return redirect(url_for('login'))

    return render_template('rpass.html', token=token)
###LOGIN end###

###LOGOUT start###
@app.route('/logout')
def logout():
    session.clear()
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
        # Lấy dữ liệu từ form
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        date_of_birth = request.form['dateofbirth']
        gender = request.form['gender']
        phone_number = request.form['phonenumber']
        email = request.form['email']

        # Kiểm tra xem tên đăng nhập đã tồn tại chưa
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Tên đăng nhập đã tồn tại. Vui lòng chọn tên khác.', 'error')
            return redirect(url_for('register'))

        # Kiểm tra xem số điện thoại đã tồn tại chưa
        existing_phone = PhoneNumber.query.filter_by(phoneNumber=phone_number).first()
        if existing_phone:
            flash('Số điện thoại đã tồn tại. Vui lòng sử dụng số khác.', 'error')
            return redirect(url_for('register'))

        # Kiểm tra xem email đã tồn tại chưa
        existing_email = Email.query.filter_by(email=email).first()
        if existing_email:
            flash('Email đã tồn tại. Vui lòng sử dụng email khác.', 'error')
            return redirect(url_for('register'))

        # Mã hóa mật khẩu trước khi lưu
        hashed_password = generate_password_hash(password)

        # Tạo đối tượng User mới
        new_user = User(
            name=None,  # Có thể cập nhật thêm nếu muốn lưu tên
            dateOfBirth=date_of_birth,
            gender=gender,
            username=username,
            password=hashed_password,
            role=role
        )

        # Lưu vào cơ sở dữ liệu
        db.session.add(new_user)
        db.session.commit()

        # Lấy ID của User mới tạo
        user_id = new_user.userID

        # Tạo đối tượng PhoneNumber và Email
        new_phone = PhoneNumber(userID=user_id, phoneNumber=phone_number)
        new_email = Email(userID=user_id, email=email)

        # Lưu vào cơ sở dữ liệu
        db.session.add(new_phone)
        db.session.add(new_email)
        db.session.commit()

        flash('Tài khoản đã được tạo thành công!', 'success')
        return redirect(url_for('register'))  # Chuyển hướng về trang đăng ký

    return render_template('register.html')
###Tạo tài khoản end###

###Thay đổi quy định start###
@app.route('/rule', methods=['GET', 'POST'])
def rule():
    student_rule = StudentRule.query.first()
    class_rule = ClassRule.query.first()

    # Lấy dữ liệu từ database để hiển thị ban đầu
    min_age = student_rule.minAge if student_rule else None
    max_age = student_rule.maxAge if student_rule else None
    max_number = class_rule.maxNumber if class_rule else None

    success_message = None
    errors = {
        "minAge": None,
        "maxAge": None,
        "maxNumber": None
    }

    if request.method == 'POST':
        try:
            min_age_input = int(request.form.get('minAge', 0))
            max_age_input = int(request.form.get('maxAge', 0))
            max_number_input = int(request.form.get('maxNumber', 0))

            # Kiểm tra điều kiện hợp lệ
            if min_age_input <= 0:
                errors["minAge"] = "Tuổi nhỏ nhất phải lớn hơn 0."
            if max_age_input <= 0:
                errors["maxAge"] = "Tuổi lớn nhất phải lớn hơn 0."
            if max_number_input <= 0:
                errors["maxNumber"] = "Số học sinh tối đa phải lớn hơn 0."
            if max_age_input < min_age_input:
                errors["maxAge"] = "Tuổi lớn nhất không thể nhỏ hơn tuổi nhỏ nhất."
            if min_age_input > max_age_input:
                errors["minAge"] = "Tuổi nhỏ nhất không thể lớn hơn tuổi lớn nhất."

            # Nếu không có lỗi, lưu vào database
            if not any(errors.values()):
                if not student_rule:
                    student_rule = StudentRule(minAge=min_age_input, maxAge=max_age_input)
                    db.session.add(student_rule)
                else:
                    student_rule.minAge = min_age_input
                    student_rule.maxAge = max_age_input

                if not class_rule:
                    class_rule = ClassRule(maxNumber=max_number_input)
                    db.session.add(class_rule)
                else:
                    class_rule.maxNumber = max_number_input

                db.session.commit()
                success_message = "Lưu thay đổi thành công!"
                # Reset dữ liệu để hiển thị thành công
                min_age = min_age_input
                max_age = max_age_input
                max_number = max_number_input
        except ValueError:
            errors["minAge"] = "Vui lòng nhập số hợp lệ cho tuổi nhỏ nhất."
            errors["maxAge"] = "Vui lòng nhập số hợp lệ cho tuổi lớn nhất."
            errors["maxNumber"] = "Vui lòng nhập số hợp lệ cho số học sinh."

    return render_template(
        'rule.html',
        min_age=min_age,
        max_age=max_age,
        max_number=max_number,
        success_message=success_message,
        errors=errors
    )
###Thay đổi quy định end###
###Quản lý môn học start###
@app.route('/manage', methods=['GET'])
def manage():
    return render_template('manage.html')

@app.route('/add_subject', methods=['GET', 'POST'])
def add_subject():
    if request.method == 'POST':
        # Lấy dữ liệu từ form
        subject_name = request.form.get('subject_name')
        grade = request.form.get('grade')
        
        # Kiểm tra tính hợp lệ và thêm vào database
        if subject_name and grade:
            new_subject = Subject(subjectName=subject_name, grade=grade)
            try:
                db.session.add(new_subject)
                db.session.commit()
                flash('Thêm môn học thành công!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Lỗi khi thêm môn học: {str(e)}', 'danger')
            return redirect(url_for('add_subject'))
        else:
            flash('Vui lòng nhập đầy đủ thông tin!', 'warning')
    
    return render_template('add_subject.html')

@app.route('/update_subject', methods=['GET', 'POST'])
def update_subject():
    query = request.args.get('query')  # Lấy từ khóa tìm kiếm từ form
    subjects = Subject.query.all()  # Lấy toàn bộ môn học

    # Nếu có tìm kiếm, lọc danh sách môn học theo tên
    if query:
        subjects = Subject.query.filter(Subject.subjectName.like(f'%{query}%')).all()

    if request.method == 'POST':
        # Xử lý cập nhật môn học
        subject_id = request.form.get('subject_id')
        subject_name = request.form.get('subject_name')
        grade = request.form.get('grade')

        subject = Subject.query.get(subject_id)
        if subject:
            try:
                subject.subjectName = subject_name
                subject.grade = grade
                db.session.commit()
                flash('Cập nhật môn học thành công!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Lỗi khi cập nhật môn học: {str(e)}', 'danger')
        else:
            flash('Môn học không tồn tại!', 'warning')

        return redirect(url_for('update_subject'))
    
    return render_template('update_subject.html', subjects=subjects, query=query)

@app.route('/delete_subject', methods=['GET', 'POST'])
def delete_subject():
    # Lấy từ khóa tìm kiếm
    query = request.args.get('query')
    if query:
        # Lọc danh sách môn học theo từ khóa
        subjects = Subject.query.filter(Subject.subjectName.like(f'%{query}%')).all()
    else:
        # Hiển thị tất cả môn học nếu không có tìm kiếm
        subjects = Subject.query.all()

    if request.method == 'POST':
        # Lấy ID môn học từ form
        subject_id = request.form.get('subject_id')
        subject = Subject.query.get(subject_id)
        if subject:
            try:
                db.session.delete(subject)
                db.session.commit()
                flash('Xóa môn học thành công!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Lỗi khi xóa môn học: {str(e)}', 'danger')
        else:
            flash('Không tìm thấy môn học để xóa!', 'warning')
        return redirect(url_for('delete_subject'))

    return render_template('delete_subject.html', subjects=subjects)

@app.route('/search_subject', methods=['GET'])
def search_subject():
    query = request.args.get('query')
    subjects = []

    if query:
        subjects = Subject.query.filter(Subject.subjectName.like(f'%{query}%')).all()

    return render_template('search_subject.html', subjects=subjects, query=query)
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
