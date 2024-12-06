from flask import render_template, Flask, jsonify, request, flash, redirect, url_for, session
from flask_mysqldb import MySQL
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

app.secret_key = 'your_unique_secret_key'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'huyduong2004'  # Đảm bảo mật khẩu đúng
app.config['MYSQL_DB'] = 'student_management'

mysql = MySQL(app)

# Hàm kiểm tra và thêm tài khoản mặc định
def ensure_default_users():
    cur = mysql.connection.cursor()

    # Kiểm tra và thêm tài khoản admin
    cur.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)", 
                    ('admin', generate_password_hash('admin123'), 'admin'))

    # Kiểm tra và thêm tài khoản teacher
    cur.execute("SELECT COUNT(*) FROM users WHERE username = 'teacher'")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)", 
                    ('teacher', generate_password_hash('teacher123'), 'teacher'))

    # Kiểm tra và thêm tài khoản staff
    cur.execute("SELECT COUNT(*) FROM users WHERE username = 'staff'")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)", 
                    ('staff', generate_password_hash('staff123'), 'staff'))

    mysql.connection.commit()
    cur.close()

# Gọi hàm trong application context
with app.app_context():
    ensure_default_users()

@app.route('/')
def index():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM student")
    data = cur.fetchall()
    cur.close()
    return render_template('index.html', students=data)

### LOGIN start ###
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']  # Vai trò được gửi từ form (value: teacher, staff, admin)

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user[2], password):  # `user[2]` là cột mật khẩu
            if user[3] == role:  # So sánh role trong DB với vai trò từ form
                session['username'] = user[1]  # `user[1]` là cột tên đăng nhập
                session['role'] = user[3]      # `user[3]` là cột vai trò

                # Điều hướng dựa trên vai trò
                if role == 'admin':
                    return redirect(url_for('admin_dashboard'))
                elif role == 'teacher':
                    return redirect(url_for('teacher_dashboard'))
                elif role == 'staff':
                    return redirect(url_for('staff_dashboard'))
            else:
                flash("Vai trò không đúng với tài khoản!", "error")
        else:
            flash("Tên đăng nhập hoặc mật khẩu không đúng!", "error")

        return redirect(url_for('login'))

    return render_template('login.html')
### LOGIN end ###

### LOGOUT start ###
@app.route('/logout')
def logout():
    # Xóa thông tin trong session
    session.pop('username', None)
    session.pop('role', None)

    return redirect(url_for('index'))  
### LOGOUT end ###

### ADMIN start ###

@app.route('/admin_dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        flash("Bạn không có quyền truy cập vào trang này", "error")
        return redirect(url_for('login'))
    return render_template('admin.html')  

### Thống kê báo cáo start ###
@app.route('/report', methods=['GET', 'POST'])
def report():
    subject_id = None
    semester_id = None
    year_id = None
    subject_name = None
    year_name = None
    semester_name = None
    show_chart = False  # Biến để xác định có hiển thị biểu đồ hay không

    # Lấy dữ liệu môn học, năm học, học kỳ để hiển thị trên form
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM Subject")
    subjects = cur.fetchall()
    cur.execute("SELECT * FROM Year")
    years = cur.fetchall()
    cur.execute("SELECT * FROM Semester")
    semesters = cur.fetchall()

    if request.method == 'POST':
        subject_id = int(request.form['subject']) if request.form['subject'] else None
        year_id = int(request.form['year']) if request.form['year'] else None
        semester_id = int(request.form['semester']) if request.form['semester'] else None
        show_chart = 'showChart' in request.form  # Kiểm tra nếu người dùng chọn checkbox

        # Truy vấn cơ sở dữ liệu để lấy kết quả báo cáo
        query = '''
        SELECT c.class_name, 
               COUNT(s.studentID) AS total_students,
               SUM(CASE WHEN avg_point >= 5 THEN 1 ELSE 0 END) AS pass_students
        FROM Class c
        JOIN Study st ON st.classID = c.classID
        JOIN Student s ON st.studentID = s.studentID
        JOIN (
            SELECT p.studentID, AVG(pd.value) AS avg_point
            FROM Point p
            JOIN PointDetails pd ON p.pointID = pd.pointID
            WHERE p.subjectID = %s AND p.semesterID = %s
            GROUP BY p.studentID
        ) AS avg_points ON avg_points.studentID = s.studentID
        JOIN Semester sm ON sm.semesterID = %s
        JOIN Year y ON sm.yearID = y.yearID
        WHERE y.yearID = %s
        GROUP BY c.class_name
        '''

        cur.execute(query, (subject_id, semester_id, semester_id, year_id))
        report_data = cur.fetchall()

        # Lấy tên môn học từ bảng Subject
        cur.execute("SELECT subjectName FROM Subject WHERE subjectID = %s", (subject_id,))
        subject_name = cur.fetchone()[0]

        # Lấy tên năm học từ bảng Year (sửa theo yearName)
        cur.execute("SELECT yearName FROM Year WHERE yearID = %s", (year_id,))
        year_name = cur.fetchone()[0]

        # Xác định tên học kỳ từ semester_id
        semester_name = "Học kỳ 1" if semester_id == 1 else "Học kỳ 2"
        
        cur.close()

        # Tính tỷ lệ đạt
        report_data_with_rate = []
        for row in report_data:
            total_students = row[1]
            pass_students = row[2]
            pass_rate = (pass_students / total_students) * 100 if total_students else 0
            report_data_with_rate.append({
                'class_name': row[0],
                'total_students': total_students,
                'pass_students': pass_students,
                'pass_rate': round(pass_rate, 2)
            })

        return render_template('report.html', 
                               report_data=report_data_with_rate, 
                               subject_name=subject_name,
                               year_name=year_name,
                               semester_name=semester_name,
                               subjects=subjects, 
                               years=years, 
                               semesters=semesters,
                               subject_id=subject_id,
                               semester_id=semester_id,
                               year_id=year_id,
                               show_chart=show_chart)  # Truyền thêm thông tin show_chart vào template

    else:
        # GET request: lấy danh sách môn học, năm học và học kỳ
        cur.close()
        return render_template('report.html', subjects=subjects, years=years, semesters=semesters)
### Thống kê báo cáo end ###


### Tạo tài khoản start ###
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        
        # Mã hóa mật khẩu
        hashed_password = generate_password_hash(password)

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)", 
                    (username, hashed_password, role))
        mysql.connection.commit()
        cur.close()

        # Flash success message
        flash("Tạo tài khoản thành công!", "success")
        
        # Render lại trang đăng ký mà không redirect
        return render_template('register.html')
    
    return render_template('register.html')


### Tạo tài khoản end ###

### Thay đổi quy định start ###
@app.route('/rule', methods=['GET', 'POST'])
def rule():
    if request.method == 'POST':
        min_age = int(request.form['min-age'])
        max_age = int(request.form['max-age'])
        max_students = int(request.form['max-students'])

        # Kiểm tra ràng buộc
        if min_age > max_age:
            flash("Độ tuổi tối thiểu không thể lớn hơn độ tuổi tối đa!", "error")
            return redirect(url_for('rule'))
        
        if max_age < min_age:
            flash("Độ tuổi tối đa không thể nhỏ hơn độ tuổi tối thiểu!", "error")
            return redirect(url_for('rule'))

        if min_age < 6 or min_age > 30:
            flash("Độ tuổi tối thiểu phải trong khoảng 6-30!", "error")
            return redirect(url_for('rule'))
        
        if max_age < 6 or max_age > 30:
            flash("Độ tuổi tối đa phải trong khoảng 6-30!", "error")
            return redirect(url_for('rule'))
        
        if max_students < 0 or max_students > 100:
            flash("Sĩ số tối đa không thể nhỏ hơn 0 hoặc vượt quá 100!", "error")
            return redirect(url_for('rule'))

        # Nếu tất cả đều hợp lệ
        flash(f"Thay đổi đã được lưu! Độ tuổi tối thiểu: {min_age}, Độ tuổi tối đa: {max_age}, Sĩ số tối đa: {max_students}", "success")
        return redirect(url_for('rule'))

    return render_template('rule.html')

### Thay đổi quy định end ###

### Quản lý môn học start ###
@app.route('/manage', methods=['GET', 'POST'])
def manage():
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        # Thêm môn học
        if 'add_subject' in request.form:
            subject_name = request.form['subjectName']
            subject_code = request.form['subjectCode']
            
            cur.execute("INSERT INTO Subject (subjectCode, subjectName) VALUES (%s, %s)", (subject_code, subject_name))
            mysql.connection.commit()
            flash("Thêm môn học thành công!", "success")

        # Xóa môn học
        elif 'delete_subject' in request.form:
            subject_id = request.form['subjectID']
            cur.execute("DELETE FROM Subject WHERE subjectID = %s", (subject_id,))
            mysql.connection.commit()
            flash("Xóa môn học thành công!", "success")

        # Cập nhật môn học
        elif 'edit_subject' in request.form:
            subject_id = request.form['subjectID']
            subject_name = request.form['subjectName']
            subject_code = request.form['subjectCode']
            cur.execute(
                "UPDATE Subject SET subjectCode = %s, subjectName = %s WHERE subjectID = %s",
                (subject_code, subject_name, subject_id),
            )
            mysql.connection.commit()
            flash("Cập nhật môn học thành công!", "success")

    # Hiển thị danh sách môn học
    cur.execute("SELECT * FROM Subject")
    subjects = cur.fetchall()
    cur.close()

    return render_template('manage.html', subjects=subjects)
### Quản lý môn học end ###

### ADMIN end ###


### Teacher start ###
@app.route('/teacher_dashboard')
def teacher_dashboard():
    if session.get('role') != 'teacher':
        flash("Bạn không có quyền truy cập vào trang này", "error")
        return redirect(url_for('login'))
    return render_template('teacher.html') 
### Teacher end ###

### Staff start ###
@app.route('/staff_dashboard')
def staff_dashboard():
    if session.get('role') != 'staff':
        flash("Bạn không có quyền truy cập vào trang này", "error")
        return redirect(url_for('login'))
    return render_template('staff.html')
### Staff end ###

if __name__ == '__main__':
    app.run(debug=True)