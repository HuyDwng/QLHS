import os
from functools import wraps


from flask_login import current_user, login_manager, login_user
from flask_login import LoginManager
from sqlalchemy import func

from QLHS import create_app, db, mail
from flask import render_template, Flask, jsonify, request, flash, redirect, url_for, session
from datetime import datetime, date
from QLHS.models import Subject, Year, Semester, Class, Point, Student, StudentRule, ClassRule, PhoneNumber, Email, User, Study, Teacher, Teach, PointType 
from werkzeug.security import generate_password_hash
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer as Serializer
from QLHS.forms import StudentForm


app = create_app()

# Tạo một serializer để tạo và xác minh token
s = Serializer(app.config['SECRET_KEY'])

def login_required(role=None):
    def decorator(func):
        @wraps(func)
        def wrapped_func(*args, **kwargs):
            if 'username' not in session:
                flash('Bạn cần đăng nhập trước khi truy cập trang này!', 'danger')
                return redirect(url_for('login'))

            if role and session['role'] != role:
                flash('Bạn không có quyền truy cập trang này!', 'danger')
                return redirect(url_for('login'))

            return func(*args, **kwargs)

        return wrapped_func

    return decorator

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
            login_user(user)  # Đăng nhập người dùng

            print("id gv: ", user.userID)
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
### Resetpassword end ###
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
                students = Student.query.join(Study).filter(Study.classID == cls.classID).all()
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
@login_required(role='teacher')
def teacher_page():
    return render_template('teacher.html')
### Nhập điểm start ###
@app.route('/enter_scores', methods=['GET', 'POST'])
@login_required(role='teacher')
def enter_scores():
    # Kiểm tra quyền truy cập của giáo viên
    if current_user.is_authenticated:
        teacher = Teacher.query.filter_by(teacherID=current_user.userID).first()
        if not teacher:
            flash('Không tìm thấy giáo viên với tài khoản này!', 'danger')
            return redirect(url_for('login'))
    else:
        flash('Bạn cần đăng nhập để thực hiện thao tác này!', 'danger')
        return redirect(url_for('login'))

    semesters = Semester.query.order_by(Semester.yearID.desc(), Semester.semesterID.asc()).limit(2).all()
    subject = teacher.subjectID if teacher else None
    if subject is None:
        flash('Không tìm thấy môn học của giáo viên này!', 'danger')
        return redirect(url_for('some_page'))

    classes = db.session.query(Class).join(Teach).filter(Teach.teacherID == teacher.teacherID).all()
    students = None
    student_points = {}
    selected_semester = None
    selected_class = None
    points_columns = PointType.query.all()  # Lấy tất cả các loại điểm

    if request.method == 'POST':
        selected_semester = int(request.form.get('semester'))
        selected_class = int(request.form.get('class'))

        if selected_class not in [cls.classID for cls in classes]:
            flash('Bạn không có quyền nhập điểm cho lớp này.', 'danger')
            return redirect(url_for('enter_scores'))

        students = db.session.query(Student.studentID, Student.name).join(Study).filter(
            Study.classID == selected_class).all()

        if not students:
            flash('Không có học sinh nào trong lớp này.', 'danger')
            return redirect(url_for('enter_scores'))

        # Hàm lấy phần tên đầu (dùng cho trường hợp tên cuối giống nhau)
        def get_last_name(name):
            # Tách tên ra thành các từ và trả về từ cuối cùng
            parts = name.strip().split()
            return parts[-1] if parts else ''

        def get_first_name(name):
            # Tách tên ra thành các từ và trả về tất cả các từ trừ từ cuối cùng
            parts = name.strip().split()
            return ' '.join(parts[:-1]) if len(parts) > 1 else parts[0]

        # Sắp xếp học sinh theo tên cuối, nếu tên cuối giống nhau thì sắp xếp theo tên đầu
        students = sorted(students, key=lambda student: (
            get_last_name(student.name.lower()), get_first_name(student.name.lower())))

        # Khởi tạo student_points cho từng học sinh
        for student in students:
            student_points[student.studentID] = {}
            for column in points_columns:
                points = Point.query.filter_by(
                    studentID=student.studentID,
                    subjectID=subject,
                    semesterID=selected_semester,
                    pointTypeID=column.pointTypeID
                ).all()
                student_points[student.studentID][column.pointTypeID] = points  # Lưu cả đối tượng Point

        if 'submit_scores' in request.form:
            has_error = False  # Biến để theo dõi xem có lỗi nào xảy ra không
            is_updated = False  # Biến kiểm tra xem có điểm nào được cập nhật hay không

            for student in students:
                for column in points_columns:
                    num_scores = 5 if column.pointTypeID == 1 else (3 if column.pointTypeID == 2 else 1)

                    for idx in range(1, num_scores + 1):
                        score_name = f'score_{student.studentID}_{column.pointTypeID}_{idx}'
                        score = request.form.get(score_name)

                        if score:
                            try:
                                # Kiểm tra xem giá trị nhập vào có phải là số hay không
                                score_value = float(score)  # Chuyển điểm thành số

                                # Kiểm tra tính hợp lệ của điểm (phải trong khoảng từ 0 đến 10)
                                if score_value < 0 or score_value > 10:
                                    raise ValueError("Điểm phải nằm trong khoảng từ 0 đến 10.")
                            except ValueError as e:
                                # Thông báo lỗi nếu không phải số hoặc không hợp lệ
                                flash(f"Điểm không hợp lệ cho học sinh {student.name}: {e}", 'danger')
                                has_error = True
                                continue  # Tiếp tục với học sinh kế tiếp nếu có lỗi

                            # Kiểm tra xem có điểm nào đã tồn tại không
                            existing_points = Point.query.filter_by(
                                studentID=student.studentID,
                                subjectID=subject,
                                semesterID=selected_semester,
                                pointTypeID=column.pointTypeID
                            ).all()

                            # Nếu có điểm đã tồn tại và là điểm cần sửa
                            if idx <= len(existing_points):
                                existing_point = existing_points[idx - 1]  # Lấy điểm tương ứng
                                if existing_point.value != score_value:
                                    existing_point.value = score_value  # Cập nhật giá trị của điểm
                                    is_updated = True  # Đánh dấu là có sự thay đổi
                            else:
                                # Nếu không có điểm tương ứng, thêm điểm mới
                                new_point = Point(
                                    studentID=student.studentID,
                                    subjectID=subject,
                                    semesterID=selected_semester,
                                    pointTypeID=column.pointTypeID,
                                    value=score_value
                                )
                                db.session.add(new_point)  # Thêm điểm mới
                                is_updated = True  # Đánh dấu là có sự thay đổi

            if is_updated and not has_error:  # Chỉ commit và thông báo nếu có sự thay đổi và không có lỗi
                db.session.commit()
                flash('Điểm đã được cập nhật thành công!', 'success')
            elif not is_updated:  # Nếu không có sự thay đổi
                flash('Không có sự thay đổi nào để cập nhật.', 'warning')
            else:
                flash('Không thể cập nhật điểm do có lỗi!', 'danger')

            return redirect(url_for('enter_scores'))  # Đảm bảo luôn có return sau khi cập nhật

    # Nếu không phải là POST request, hoặc sau khi xử lý POST xong, luôn trả về render_template
    return render_template('enter_scores.html',
                           classes=classes,
                           semesters=semesters,
                           subjects=subject,
                           students=students,
                           selected_semester=selected_semester,
                           selected_class=selected_class,
                           points_columns=points_columns,
                           student_points=student_points)


### Nhập điểm end ###

### Xuất điểm start ###


@app.route('/export_scores', methods=['GET', 'POST'])
@login_required(role='teacher')
def export_scores():
    # Xác thực người dùng và lấy thông tin giáo viên
    if not current_user.is_authenticated:
        flash('Bạn cần đăng nhập để thực hiện thao tác này!', 'danger')
        return redirect(url_for('login'))

    teacher = Teacher.query.filter_by(teacherID=current_user.userID).first()
    if not teacher:
        flash('Không tìm thấy giáo viên với tài khoản này!', 'danger')
        return redirect(url_for('login'))

    subjectID = teacher.subjectID
    subject=Subject.query.filter_by(subjectID=subjectID).first()
    teach_record = Teach.query.filter_by(teacherID=teacher.teacherID, subjectID=subjectID).first()

    if not teach_record:
        flash('Bạn không có quyền xuất điểm cho môn học này!', 'danger')
        return redirect(url_for('teacher_page'))

    classes = db.session.query(Class).join(Teach).filter(Teach.teacherID == teacher.teacherID,
                                                         Teach.subjectID == subjectID).all()

    selected_class = None
    students = None
    student_scores = {}

    semesters = Semester.query.order_by(Semester.yearID.desc(), Semester.semesterID.asc()).limit(2).all()
    year = None
    if semesters:
        year = Year.query.filter_by(yearID=semesters[0].yearID).first()

    if request.method == 'POST':
        selected_class_id = request.form.get('class')
        selected_class = db.session.get(Class, selected_class_id)

        if not selected_class:
            flash('Lớp không hợp lệ!', 'danger')
            return redirect(url_for('export_scores'))

        students = db.session.query(Student).join(Study).filter(Study.classID == selected_class_id).all()

        def get_last_name(name):
            # Tách tên ra thành các từ và trả về từ cuối cùng
            parts = name.strip().split()
            return parts[-1] if parts else ''

            # Hàm lấy phần tên đầu (dùng cho trường hợp tên cuối giống nhau)

        def get_first_name(name):
            # Tách tên ra thành các từ và trả về tất cả các từ trừ từ cuối cùng
            parts = name.strip().split()
            return ' '.join(parts[:-1]) if len(parts) > 1 else parts[0]

            # Sắp xếp học sinh theo tên cuối, nếu tên cuối giống nhau thì sắp xếp theo tên đầu

        students = sorted(students, key=lambda student: (
            get_last_name(student.name.lower()), get_first_name(student.name.lower())))

        # Truy xuất điểm học sinh
        for student in students:
            student_scores[student.studentID] = {
                'name': student.name,
                'class': [selected_class.class_name],
                'scores': {},
            }

            total_average_score = 0
            total_semesters = 0

            for semester in semesters:
                student_scores[student.studentID]['scores'][semester.semesterName] = {}

                if year:
                    student_scores[student.studentID]['year'] = year.yearName

                total_weighted_score = 0
                total_weighted_count = 0

                for point_type in PointType.query.all():
                    points = db.session.query(Point).filter_by(
                        studentID=student.studentID,
                        subjectID=subjectID,
                        semesterID=semester.semesterID,
                        pointTypeID=point_type.pointTypeID
                    ).all()

                    if points:
                        sum_points = sum(point.value for point in points if point.value is not None)
                        count_points = len([point for point in points if point.value is not None])

                        if count_points > 0:
                            weighted_score = (sum_points * point_type.pointTypeID)
                            total_weighted_score += weighted_score
                            total_weighted_count += count_points * point_type.pointTypeID

                if total_weighted_count > 0:
                    average_score = total_weighted_score / total_weighted_count
                    average_score = round(average_score, 2)
                else:
                    average_score = None

                student_scores[student.studentID]['scores'][semester.semesterName]['average'] = average_score

                if average_score is not None:
                    total_average_score += average_score
                    total_semesters += 1

            if total_semesters > 0:
                overall_average = round(total_average_score / total_semesters, 2)
                student_scores[student.studentID]['overall_average'] = overall_average
            else:
                student_scores[student.studentID]['overall_average'] = None

    # Render template cho việc hiển thị
    return render_template('export_scores.html',
                           classes=classes,
                           students=student_scores,
                           semesters=semesters,
                           year=year,
                           selected_class=selected_class,
                           subject=subject)


###Teacher end###


###Staff start###
@app.route('/staff_page')
@login_required(role='staff')
def staff_page():
    return render_template('staff.html')

### Tiếp nhận học sinh start###
@app.route('/add_student', methods=['GET', 'POST'])
@login_required(role='staff')
def add_student():
    form = StudentForm()

    # Kiểm tra khi form được submit
    if form.validate_on_submit():
        # Lấy thông tin từ form
        name = form.name.data
        dateOfBirth = form.dateOfBirth.data
        gender = form.gender.data
        address = form.address.data
        phone_number = form.phoneNumber.data
        email = form.email.data

        # Kiểm tra ngày sinh hợp lệ
        if isinstance(dateOfBirth, str):
            try:
                # Chuyển đổi ngày sinh từ chuỗi thành datetime.date
                dateOfBirth = datetime.strptime(dateOfBirth, "%Y-%m-%d").date()
            except ValueError:
                flash("Ngày sinh không hợp lệ. Vui lòng nhập lại ngày sinh.", "danger")
                return render_template('add_student.html', form=form)  # Giữ lại form và hiển thị lỗi

        if not isinstance(dateOfBirth, date):
            flash("Ngày sinh không hợp lệ. Vui lòng nhập lại ngày sinh.", "danger")
            return render_template('add_student.html', form=form)  # Giữ lại form và hiển thị lỗi

        today = datetime.today()
        age = today.year - dateOfBirth.year - ((today.month, today.day) < (dateOfBirth.month, dateOfBirth.day))

        # Kiểm tra quy định về độ tuổi học sinh
        student_rule = StudentRule.query.first()  # Lấy quy định học sinh (mặc định chỉ có một quy định)
        if not student_rule:
            flash('Quy định học sinh chưa được thiết lập.', 'danger')
            return render_template('add_student.html', form=form)  # Giữ lại form và hiển thị lỗi

        if age < student_rule.minAge or age > student_rule.maxAge:
            flash(f'Tuổi học sinh không hợp lệ! Tuổi phải trong khoảng {student_rule.minAge} - {student_rule.maxAge}.',
                  'danger')
            return render_template('add_student.html', form=form)  # Giữ lại form và hiển thị lỗi

        # Kiểm tra số điện thoại đã tồn tại
        existing_phone = PhoneNumber.query.filter_by(phoneNumber=phone_number).first()
        if existing_phone:
            flash(f"Số điện thoại {phone_number} đã được liên kết.", "danger")
            return render_template('add_student.html', form=form)  # Giữ lại form và hiển thị lỗi

        # Kiểm tra email đã tồn tại
        existing_email = Email.query.filter_by(email=email).first()
        if existing_email:
            flash(f"Email {email} đã được liên kết.", "danger")
            return render_template('add_student.html', form=form)  # Giữ lại form và hiển thị lỗi

        try:
            # Thêm học sinh vào cơ sở dữ liệu
            new_student = Student(name=name, dateOfBirth=dateOfBirth, gender=gender, address=address)
            db.session.add(new_student)
            db.session.commit()

            # Thêm email cho học sinh
            new_email = Email(studentID=new_student.studentID, email=email)
            db.session.add(new_email)

            # Thêm số điện thoại cho học sinh
            new_phone_number = PhoneNumber(studentID=new_student.studentID, phoneNumber=phone_number)
            db.session.add(new_phone_number)

            db.session.commit()

            flash('Thêm học sinh thành công!', 'success')
            return render_template('add_student.html', form=form)  # Giữ lại form và thông báo thành công

        except Exception as e:
            db.session.rollback()
            flash(f"Đã xảy ra lỗi khi thêm học sinh: {str(e)}", 'danger')
            return render_template('add_student.html', form=form)  # Giữ lại form và hiển thị lỗi

    # Nếu form không hợp lệ, trả về giao diện và hiển thị lỗi
    else:
        # Kiểm tra và thêm các thông báo lỗi vào flash message (có thể sử dụng để hiển thị ngoài form)
        for fieldName, errorMessages in form.errors.items():
            for errMsg in errorMessages:
                flash(f"{getattr(form, fieldName).label.text} Không Hợp Lệ: {errMsg}", 'danger')

    return render_template('add_student.html', form=form)
### Tiếp nhận học sinh end###

### Thêm lớp start###
@app.route('/create_class', methods=['GET', 'POST'])
@login_required(role='staff')
def create_class():
    if request.method == 'POST':
        # Lấy thông tin lớp và quy định sĩ số
        class_name = request.form['class_name']
        grade = request.form['grade']
        class_rule_id = request.form['class_rule_id']  # Chọn quy định sĩ số từ danh sách đã có

        # Kiểm tra xem quy định sĩ số có hợp lệ không
        class_rule = ClassRule.query.get(class_rule_id)
        if not class_rule:
            flash('Quy định sĩ số không hợp lệ!', 'danger')
            return redirect(url_for('create_class'))

        # Kiểm tra tính duy nhất của tên lớp và khối
        existing_class = Class.query.filter_by(class_name=class_name, grade=grade).first()
        if existing_class:
            flash(f'Lớp "{class_name}" đã tồn tại trong khối {grade}!', 'danger')
            return redirect(url_for('create_class'))

        # Tạo lớp mới với quy định sĩ số đã có
        new_class = Class(
            class_name=class_name,
            grade=grade,
            classRuleID=class_rule_id
        )
        db.session.add(new_class)
        db.session.commit()

        # Thêm thông báo thành công
        flash(f'Lớp "{class_name}" đã được tạo thành công với sĩ số tối đa {class_rule.maxNumber}!', 'success')
        return redirect(url_for('create_class'))

    # Lấy các giá trị khối lớp (grade) từ bảng Class
    grades = db.session.query(Class.grade).distinct().all()

    # Lấy danh sách quy định sĩ số có sẵn
    class_rules = ClassRule.query.all()

    # Chuyển đổi kết quả grade thành danh sách dễ sử dụng trong template
    grades = [grade[0] for grade in grades]

    return render_template('create_class.html', class_rules=class_rules, grades=grades)

@app.route('/select_block', methods=['GET', 'POST'])
def select_block():
    if request.method == 'POST':
        # Lấy khối đã chọn
        block_id = request.form.get('block')
        return redirect(url_for('select_class', block_id=block_id))

    blocks = db.session.query(Class.grade).distinct().all()  # Lấy danh sách các khối
    return render_template('select_block.html', blocks=blocks)

@app.route('/select_class/<block_id>', methods=['GET', 'POST'])
def select_class(block_id):
    if request.method == 'POST':
        class_id = request.form.get('class')
        return redirect(url_for('manage_students', class_id=class_id))

    # Lấy danh sách các lớp theo khối
    classes = Class.query.filter_by(grade=block_id).all()
    return render_template('select_class.html', classes=classes)

@app.route('/remove_student_from_class/<int:class_id>/<int:student_id>', methods=['GET'])
def remove_student_from_class(class_id, student_id):
    # Lấy lớp theo class_id
    class_ = Class.query.filter_by(classID=class_id).first()

    # Lấy học sinh theo student_id
    student = Student.query.filter_by(studentID=student_id).first()

    # Kiểm tra xem học sinh có thuộc lớp này không
    study = Study.query.filter_by(studentID=student_id, classID=class_id).first()
    if study:
        db.session.delete(study)
        db.session.commit()
        flash('Học sinh đã xóa khỏi lớp.', 'success')

        return redirect(url_for('manage_students', class_id=class_id, success="Học sinh đã được xóa khỏi lớp thành công"))
    else:
        return redirect(url_for('manage_students', class_id=class_id, error="Học sinh không thuộc lớp này"))

@app.route('/add_student_to_class/<int:class_id>/<int:student_id>', methods=['GET'])
def add_student_to_class(class_id, student_id):
    # Lấy lớp theo class_id
    class_ = Class.query.filter_by(classID=class_id).first()

    # Lấy học sinh theo student_id
    student = Student.query.filter_by(studentID=student_id).first()

    # Kiểm tra xem học sinh đã thuộc lớp chưa
    existing_study = Study.query.filter_by(studentID=student_id, classID=class_id).first()
    if existing_study:
        return redirect(url_for('manage_students', class_id=class_id, error="Học sinh đã thuộc lớp này"))

    # Thêm học sinh vào lớp
    study = Study(studentID=student.studentID, classID=class_.classID)
    db.session.add(study)
    db.session.commit()
    flash('Học sinh đã được thêm vào lớp.', 'success')

    return redirect(url_for('manage_students', class_id=class_id, success="Học sinh đã được thêm vào lớp thành công"))


@app.route('/manage_students/<class_id>', methods=['GET', 'POST'])
def manage_students(class_id):
    # Lấy thông tin lớp và quy định lớp
    class_ = Class.query.filter_by(classID=class_id).first()
    class_rule = ClassRule.query.filter_by(classRuleID=class_.classRuleID).first()

    # Lấy danh sách học sinh chưa thuộc lớp nào
    students_not_in_class = db.session.query(Student).outerjoin(Study).filter(Study.studentID == None).all()

    # Lấy danh sách học sinh trong lớp
    students_in_class = db.session.query(Student).join(Study).filter(Study.classID == class_id).all()

    # Kiểm tra và xử lý yêu cầu POST khi nhấn nút "Thêm tự động học sinh"
    if request.method == 'POST':
        print("POST request received.")  # In ra khi có POST request

        # Kiểm tra tất cả dữ liệu gửi từ form
        print(f"Form Data: {request.form}")  # In ra toàn bộ dữ liệu từ form

        # Kiểm tra xem nút 'auto_add_students' có được nhấn không
        if 'auto_add_students' in request.form:
            print("auto_add_students button clicked")  # In ra khi nút 'auto_add_students' được nhấn

            students_to_add = db.session.query(Student).outerjoin(Study).filter(Study.studentID == None).all()
            print(f"Number of students to add: {len(students_to_add)}")  # In ra số học sinh cần thêm

            # Lấy số lượng học sinh hiện có trong lớp
            current_students_count = len(students_in_class)
            max_students = class_rule.maxNumber

            # Biến để kiểm tra xem có học sinh nào được thêm không
            students_added = False

            for student in students_to_add:
                today = datetime.today()
                birthdate = student.dateOfBirth
                age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))

                # Debugging: In tuổi học sinh và ngày sinh
                print(f"Student: {student.name}, Birthdate: {birthdate}, Age: {age}")

                # Kiểm tra và thêm học sinh vào lớp nếu đủ điều kiện
                if current_students_count < max_students:
                    if age == 15 and class_.grade == 'grade10':
                        study = Study(studentID=student.studentID, classID=class_id)
                        db.session.add(study)
                        current_students_count += 1
                        students_added = True  # Đánh dấu là học sinh đã được thêm
                    elif age == 16 and class_.grade == 'grade11':
                        study = Study(studentID=student.studentID, classID=class_id)
                        db.session.add(study)
                        current_students_count += 1
                        students_added = True  # Đánh dấu là học sinh đã được thêm
                    elif age == 17 and class_.grade == 'grade12':
                        study = Study(studentID=student.studentID, classID=class_id)
                        db.session.add(study)
                        current_students_count += 1
                        students_added = True  # Đánh dấu là học sinh đã được thêm
                    else:
                        # Học sinh không phù hợp với lớp, thêm thông báo
                        flash(f'Học sinh {student.name} không phù hợp với lớp này.', 'warning')
                        continue
                else:
                    # Nếu lớp đã đủ học sinh, thêm thông báo
                    flash('Lớp đã đủ số lượng học sinh.', 'error')
                    return redirect(url_for('manage_students', class_id=class_id))

            # Nếu không có học sinh nào được thêm, không commit và không hiển thị thông báo thành công
            if students_added:
                db.session.commit()
                flash('Học sinh đã được thêm tự động vào lớp.', 'success')
            else:
                flash('Không có học sinh nào được thêm vào lớp vì không đủ điều kiện.', 'info')

            return redirect(url_for('manage_students', class_id=class_id))

    return render_template('manage_students.html',
                           students_not_in_class=students_not_in_class,
                           students_in_class=students_in_class,
                           class_id=class_id)
###Staff end###

if __name__ == '__main__':
    app.run(debug=True)
