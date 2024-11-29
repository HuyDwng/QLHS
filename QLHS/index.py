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

@app.route('/')
def index():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM students")
    data = cur.fetchall()
    cur.close()
    return render_template('index.html', students=data)

### LOGIN start ###
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user[2], password):  # `user[2]` là cột mật khẩu
            # Lưu thông tin vào session
            session['username'] = user[1]  # `user[1]` là cột tên đăng nhập
            session['role'] = user[3]      # `user[3]` là cột vai trò

            # Điều hướng dựa trên vai trò
            if user[3] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user[3] == 'teacher':
                return redirect(url_for('teacher_dashboard'))
            elif user[3] == 'staff':
                return redirect(url_for('staff_dashboard'))
        else:
            # Đảm bảo chỉ gọi flash một lần
            flash("Tên đăng nhập hoặc mật khẩu không đúng", "error")
            return redirect(url_for('login'))  # Redirect để tránh gửi lại form khi có lỗi

    return render_template('login.html')


### LOGIN ###


### ADMIN start ###

@app.route('/admin')
def admin_dashboard():
    if 'role' in session and session['role'] == 'admin':
        return render_template('admin.html')
    else:
        flash("Bạn không có quyền truy cập trang này", "error")
        return redirect(url_for('login'))

### Thống kê báo cáo start ###
@app.route('/report')
def report():
    return render_template('report.html')

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

@app.route('/manage')
def manage():
    return render_template('manage.html')

@app.route("/search/<action>")
def search_course(action):
    query = request.args.get("query", "").strip()  # Loại bỏ khoảng trắng thừa

    # Dữ liệu giả lập từ database (thay thế bằng truy vấn thực tế nếu cần)
    courses = ["Toán", "Lý", "Hóa", "Sinh"]

    if action in ["view", "update", "delete"]:
        # Kiểm tra nếu môn học có tồn tại (phân biệt chữ hoa chữ thường)
        if query in courses:
            return jsonify({"success": True, "data": f"Môn học '{query}' có trong danh sách."})
        else:
            return jsonify({"success": False, "error": f"Môn học '{query}' không tồn tại."})
    else:
        return jsonify({"success": False, "error": "Hành động không hợp lệ."}), 400


@app.route("/action/<action>")
def handle_action(action):
    courses = ["Toán", "Lý", "Hóa", "Sinh"]  # Dữ liệu giả lập

    if action == "add":
        return render_template("partials/add_course.html")
    else:
        return jsonify({"success": False, "error": "Hành động không hỗ trợ."}), 400

### Quản lý môn học end ###

### ADMIN end ###


### Teacher start ###
@app.route('/teacher')
def teacher_dashboard():
    if 'role' in session and session['role'] == 'teacher':
        return render_template('teacher.html')
    else:
        flash("Bạn không có quyền truy cập trang này", "error")
        return redirect(url_for('login'))
### Teacher end ###

### Staff start ###
@app.route('/staff')
def staff_dashboard():
    if 'role' in session and session['role'] == 'staff':
        return render_template('staff.html')
    else:
        flash("Bạn không có quyền truy cập trang này", "error")
        return redirect(url_for('login'))
### Staff end ###

if __name__ == '__main__':
    app.run(debug=True)