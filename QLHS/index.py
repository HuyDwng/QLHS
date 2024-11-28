from flask import render_template, Flask, jsonify, request, flash, redirect, url_for
from flask_mysqldb import MySQL

app = Flask(__name__)

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


@app.route('/login')
def login():
    return render_template('login.html')

### ADMIN start ###

### Thống kê báo cáo start ###
@app.route('/report')
def report():
    return render_template('report.html')

### Thống kê báo cáo start ###

@app.route('/create')
def create():
    return render_template('create.html')

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

if __name__ == '__main__':
    app.run(debug=True)