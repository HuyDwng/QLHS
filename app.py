import os
from functools import wraps
from flask_login import current_user, login_manager, login_user
from flask_login import LoginManager
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
@login_required(role='teacher')
def teacher_page():
    return render_template('teacher.html')

    ###Teacher end###

@app.route('/enter_scores', methods=['GET', 'POST'])
@login_required(role='teacher')
def enter_scores():
    # Kiểm tra quyền truy cập của giáo viên
    if current_user.is_authenticated:
        teacher = Teacher.query.filter_by(teacherID=current_user.id).first()
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

            for student in students:
                for column in points_columns:
                    num_scores = 5 if column.pointTypeID == 1 else (3 if column.pointTypeID == 2 else 1)

                    for idx in range(1, num_scores + 1):
                        score_name = f'score_{student.studentID}_{column.pointTypeID}_{idx}'
                        score = request.form.get(score_name)

                        if score:
                            try:
                                score_value = float(score)
                                # Kiểm tra tính hợp lệ của điểm
                                if score_value < 0 or score_value > 10:
                                    raise ValueError("Điểm phải nằm trong khoảng từ 0 đến 10.")
                            except ValueError as e:
                                flash(f"Điểm không hợp lệ cho học sinh {student.name}: {e}", 'danger')
                                has_error = True
                                continue

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
                                existing_point.value = score_value  # Cập nhật giá trị của điểm
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

            if not has_error:  # Chỉ commit nếu không có lỗi
                db.session.commit()
                flash('Điểm đã được cập nhật thành công!', 'success')
            else:
                flash('Không thể cập nhật điểm do có lỗi!', 'danger')

            return redirect(url_for('enter_scores'))

    return render_template('enter_scores.html',
                           classes=classes,
                           semesters=semesters,
                           subjects=subject,
                           students=students,
                           selected_semester=selected_semester,
                           selected_class=selected_class,
                           points_columns=points_columns,
                           student_points=student_points)




@app.route('/export_scores', methods=['GET', 'POST'])
@login_required(role='teacher')
def export_scores():
    # Xác thực người dùng và lấy thông tin giáo viên
    if current_user.is_authenticated:
        teacher = Teacher.query.filter_by(teacherID=current_user.id).first()
        if not teacher:
            flash('Không tìm thấy giáo viên với tài khoản này!', 'danger')
            return redirect(url_for('login'))
    else:
        flash('Bạn cần đăng nhập để thực hiện thao tác này!', 'danger')
        return redirect(url_for('login'))

    # Lấy môn học mà giáo viên dạy từ trường subjectID của giáo viên đã đăng nhập
    subjectID = teacher.subjectID if teacher else None
    teach_record = Teach.query.filter_by(teacherID=teacher.teacherID, subjectID=subjectID).first()

    if not teach_record:
        flash('Bạn không có quyền xuất điểm cho môn học này!', 'danger')
        return redirect(url_for('some_page'))

    # Lấy các lớp mà giáo viên dạy môn này
    classes = db.session.query(Class).join(Teach).filter(Teach.teacherID == teacher.teacherID,
                                                         Teach.subjectID == subjectID).all()

    selected_class = None
    students = None
    student_scores = {}

    semesters = Semester.query.order_by(Semester.yearID.desc(), Semester.semesterID.asc()).limit(2).all()
    year = None
    if semesters:
        # Lấy năm học từ học kỳ mới nhất
        year = Year.query.filter_by(yearID=semesters[0].yearID).first()

    if request.method == 'POST':
        selected_class_id = request.form.get('class')  # Lấy ID lớp mà giáo viên chọn
        selected_class = db.session.get(Class, selected_class_id)

        if not selected_class:
            flash('Lớp không hợp lệ!', 'danger')
            return redirect(url_for('export_scores'))

        # Lấy danh sách học sinh trong lớp đã chọn
        students = db.session.query(Student).join(Study).filter(Study.classID == selected_class_id).all()

        # Lấy điểm của học sinh trong lớp này theo môn học, học kỳ và các loại điểm
        for student in students:
            student_scores[student.studentID] = {
                'name': student.name,
                'class': [selected_class.class_name],
                'scores': {},
            }

            for semester in semesters:
                student_scores[student.studentID]['scores'][semester.semesterName] = {}

                # Lấy thông tin năm học từ Semester
                if year:
                    student_scores[student.studentID]['year'] = year.yearName

                total_weighted_score = 0
                total_weighted_count = 0

                # Duyệt qua từng loại điểm
                for point_type in PointType.query.all():
                    points = db.session.query(Point).filter_by(
                        studentID=student.studentID,
                        subjectID=subjectID,
                        semesterID=semester.semesterID,
                        pointTypeID=point_type.pointTypeID
                    ).all()  # Lấy tất cả điểm cho loại điểm này

                    # Tính tổng điểm và tổng số lượng điểm
                    if points:
                        sum_points = sum(point.value for point in points if point.value is not None)
                        count_points = len([point for point in points if point.value is not None])

                        if count_points > 0:
                            # Tính điểm theo hệ số
                            weighted_score = (sum_points * point_type.pointTypeID)  # Nhân tổng điểm với hệ số
                            total_weighted_score += weighted_score
                            total_weighted_count += count_points * point_type.pointTypeID  # Cộng số lượng đã nhân với hệ số

                # Tính điểm trung bình học kỳ
                if total_weighted_count > 0:
                    average_score = total_weighted_score / total_weighted_count
                    average_score = round(average_score, 2)
                else:
                    average_score = None

                # Lưu điểm trung bình vào cấu trúc dữ liệu
                student_scores[student.studentID]['scores'][semester.semesterName]['average'] = average_score

    return render_template('export_scores.html',
                           classes=classes,
                           students=student_scores,
                           semesters=semesters,
                           year=year,
                           selected_class=selected_class)


###Enter_scores end###

###Add student start###
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

        print(f"Ngày sinh nhận được từ form: {dateOfBirth}")
        print(f"dateOfBirth: {dateOfBirth}, type: {type(dateOfBirth)}")

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
            flash(f"Số điện thoại {phone_number} đã được sử dụng bởi học sinh khác.", "danger")
            return render_template('add_student.html', form=form)  # Giữ lại form và hiển thị lỗi

        # Kiểm tra email đã tồn tại
        existing_email = Email.query.filter_by(email=email).first()
        if existing_email:
            flash(f"Email {email} đã được sử dụng bởi học sinh khác.", "danger")
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

            flash('Thông báo thành công!', 'success')
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


@app.route('/get_classes_by_grade/<string:grade>', methods=['GET'])
def get_classes_by_grade(grade):
    classes = Class.query.filter_by(grade=grade).all()
    class_list = [{'classID': class_room.classID, 'class_name': class_room.class_name} for class_room in classes]

    # In ra lớp để kiểm tra
    print("Classes for grade", grade, class_list)

    return jsonify({'classes': class_list})


@app.route('/get_students_by_class/<class_id>', methods=['GET'])
@login_required(role='staff')
def get_students_by_class(class_id):
    students_in_class = Study.query.join(Student).filter(Study.classID == class_id).add_columns(
        Student.studentID, Student.name).all()

    return jsonify(
        {'students': [{'studentID': student.studentID, 'name': student.name} for student in students_in_class]})


@app.route('/add_student_to_class', methods=['GET', 'POST'])
@login_required(role='staff')
def add_student_to_class():
    students_in_class = []  # Khởi tạo danh sách học sinh trong lớp
    selected_class_id = None

    if request.method == 'POST':
        # Thêm học sinh thủ công
        if 'add_student' in request.form:
            student_id = request.form['student_id']
            class_id = request.form['class_id']

            # Tìm học sinh theo student_id
            student = Student.query.get(student_id)
            if not student:
                flash('Học sinh không tồn tại!', 'danger')
                return redirect(url_for('add_student_to_class'))

            # Kiểm tra học sinh đã thuộc lớp nào chưa
            if len(student.studies) > 0:
                flash(f'Học sinh {student.name} đã thuộc lớp khác!', 'danger')
                return redirect(url_for('add_student_to_class'))

            # Tìm lớp theo class_id
            class_room = Class.query.get(class_id)

            # Kiểm tra sĩ số lớp
            if len(class_room.studies) >= class_room.classRule.maxNumber:
                flash(f'Lớp {class_room.class_name} đã đủ sĩ số!', 'danger')
                return redirect(url_for('add_student_to_class'))

            # Thêm học sinh vào lớp
            study = Study(studentID=student.studentID, classID=class_room.classID)
            db.session.add(study)
            db.session.commit()

            flash(f'Học sinh {student.name} đã được thêm vào lớp {class_room.class_name}!', 'success')

        # Thêm học sinh tự động
        elif 'auto_add_students' in request.form:
            grade = request.form['auto_grade']

            # Lấy danh sách học sinh chưa có lớp
            students_to_add = Student.query.filter(
                Student.studentID.notin_([study.studentID for study in Study.query.all()])).all()

            # Lấy lớp tương ứng với grade
            class_room = Class.query.filter_by(grade=grade).first()

            if not class_room:
                flash('Lớp không tồn tại!', 'danger')
                return redirect(url_for('add_student_to_class'))

            # Lấy năm hiện tại
            current_year = datetime.now().year

            # Phân bổ học sinh vào lớp tự động theo tiêu chí
            added_students = 0
            for student in students_to_add:
                # Tính toán độ tuổi từ dateOfBirth
                if student.dateOfBirth:
                    age = current_year - student.dateOfBirth.year  # Lấy năm sinh từ dateOfBirth
                    print("tuổi: ", age)
                else:
                    flash(f'Học sinh {student.name} không có thông tin ngày sinh.', 'warning')
                    continue

                # Kiểm tra độ tuổi và phân bổ học sinh vào lớp
                if age == 15 and grade == 'grade10':
                    # Thêm học sinh vào lớp 10
                    if len(class_room.studies) < class_room.classRule.maxNumber:
                        study = Study(studentID=student.studentID, classID=class_room.classID)
                        db.session.add(study)
                        added_students += 1
                    else:
                        break
                elif age == 16 and grade == 'grade11':
                    # Thêm học sinh vào lớp 11
                    if len(class_room.studies) < class_room.classRule.maxNumber:
                        study = Study(studentID=student.studentID, classID=class_room.classID)
                        db.session.add(study)
                        added_students += 1
                    else:
                        break
                elif age == 17 and grade == 'grade12':
                    # Thêm học sinh vào lớp 12
                    if len(class_room.studies) < class_room.classRule.maxNumber:
                        study = Study(studentID=student.studentID, classID=class_room.classID)
                        db.session.add(study)
                        added_students += 1
                    else:
                        break
                else:
                    flash(f'Học sinh {student.name} tuổi không thích hợp để vào lớp {grade}.', 'warning')

            db.session.commit()  # Commit tất cả các thay đổi sau khi thêm học sinh
            if (added_students == 0):
                flash(f'{added_students} học sinh đã được thêm vào lớp {class_room.class_name}!', 'warning')
            else:
                flash(f'{added_students} học sinh đã được thêm tự động vào lớp {class_room.class_name}!', 'success')

        # Xóa học sinh khỏi lớp
        elif 'remove_student' in request.form:
            student_id = request.form['remove_student_id']
            class_id = request.form['remove_class_id']

            # Tìm học sinh theo student_id
            student = Student.query.get(student_id)
            if not student:
                flash('Học sinh không tồn tại!', 'danger')
                return redirect(url_for('add_student_to_class'))

            # Tìm lớp theo class_id
            class_room = Class.query.get(class_id)

            # Kiểm tra học sinh có đang học lớp này không
            study = Study.query.filter_by(studentID=student.studentID, classID=class_room.classID).first()
            if not study:
                flash(f'Học sinh {student.name} không thuộc lớp {class_room.class_name}!', 'danger')
                return redirect(url_for('add_student_to_class'))

            #students_in_class = Study.query.join(Student).filter(Study.classID == class_id).add_columns(
             #   Student.studentID, Student.name).all()
            # Xóa học sinh khỏi lớp
            db.session.delete(study)
            db.session.commit()

            flash(f'Học sinh {student.name} đã được xóa khỏi lớp {class_room.class_name}!', 'success')

        return redirect(url_for('add_student_to_class'))

    # Lấy danh sách lớp và học sinh chưa thuộc lớp nào
    classes = Class.query.all()
    students = Student.query.filter(Student.studentID.notin_([study.studentID for study in Study.query.all()])).all()

    # Lấy danh sách học sinh đã thuộc lớp theo khối và lớp đã chọn
    selected_class_id = request.args.get('remove_class_id')
    print("id lop remove: ", selected_class_id)
    if selected_class_id:
        students_in_class = Study.query.join(Student).filter(Study.classID == selected_class_id).add_columns(
            Student.studentID, Student.name).all()
    else:
        students_in_class = []

    print("lớp hs: ", students_in_class)
    # Lấy các lớp theo khối
    grades = [class_room.grade for class_room in classes]
    grades = list(set(grades))  # Loại bỏ các khối trùng lặp

    return render_template('add_student_to_class.html', classes=classes, students=students,
                           students_in_class=students_in_class, grades=grades)


# @app.route('/auto_add_students/<int:grade>/<int:class_id>', methods=['GET'])
# def auto_add_students(grade, class_id):
#     # Lấy tất cả học sinh chưa có lớp (study is None)
#     students = db.session.query(Student).outerjoin(Study).filter(Study.classID.is_(None)).all()
#
#     # Phân loại học sinh dựa trên năm sinh và tên
#     sorted_students = sorted(students, key=lambda x: (x.birth_year, x.name))  # Sắp xếp theo năm sinh và tên
#
#     # Thêm học sinh vào lớp
#     for student in sorted_students:
#         study = Study(studentID=student.studentID, classID=class_id)
#         db.session.add(study)
#     db.session.commit()
#
#     return jsonify({'message': 'Đã thêm học sinh tự động vào lớp thành công!'})


# @app.route('/remove_student_from_class/<int:studentID>', methods=['POST'])
# def remove_student_from_class(studentID):
#     # Xóa học sinh khỏi lớp
#     study = Study.query.filter_by(studentID=studentID).first()
#     if study:
#         db.session.delete(study)
#         db.session.commit()
#         return jsonify({'message': 'Học sinh đã được xóa khỏi lớp.'})
#     else:
#         return jsonify({'error': 'Không tìm thấy học sinh.'}), 400


@app.route('/class_students', methods=['GET', 'POST'])
def class_students():
    grades = Class.query.with_entities(Class.grade).distinct()  # Lấy danh sách khối
    class_id = None
    students_in_class = []
    total_students = 0

    if request.method == 'POST':
        class_id = request.form.get('class_id', type=int)
        class_room = Class.query.get(class_id)

        if class_room:
            class_name = class_room.class_name  # Lấy tên lớp
            students_in_class = [study.student for study in class_room.studies]
            # Sắp xếp theo tên cuối cùng
            students_in_class = sorted(
                students_in_class,
                key=lambda s: s.name.strip().split()[-1].lower()  # Sắp xếp theo tên cuối cùng
            )
            total_students = len(students_in_class)

    return render_template('class_students.html', grades=grades, class_name=class_name,
                           students_in_class=students_in_class, total_students=total_students)
###Add student end###

###Them 1 mon học và lớp cho giáo viên
# @app.route('/assign_subject', methods=['POST'])
# @login_required(role='admin')
# def assign_subject():
#     # Giả sử bạn nhận thông tin từ form hoặc API request
#     teacher_id = request.form.get('teacher_id')
#     subject_name = request.form.get('subject_name')
#     class_name = request.form.get('class_name')
#
#     # Tìm giáo viên, môn học, lớp học tương ứng
#     teacher = Teacher.query.filter_by(teacherID=teacher_id).first()
#     subject = Subject.query.filter_by(subjectName=subject_name).first()
#     class_ = Class.query.filter_by(class_name=class_name).first()
#
#     if not teacher or not subject or not class_:
#         flash("Không tìm thấy giáo viên, môn học hoặc lớp học.", "error")
#         return redirect(url_for('assign_subject'))
#
#     # Tạo mối quan hệ giữa giáo viên, lớp học và môn học
#     teach_entry = Teach(teacherID=teacher.teacherID, classID=class_.classID, subjectID=subject.subjectID)
#
#     db.session.add(teach_entry)
#     db.session.commit()
#
#     flash("Môn học đã được gán cho giáo viên và lớp học thành công.", "success")
#     return redirect(url_for('assign_subject'))
# ###End

###Staff start###
@app.route('/staff_page')
@login_required(role='staff')
def staff_page():
    return render_template('staff.html')


###Staff end###

if __name__ == '__main__':
    app.run(debug=True)
