from QLHS import create_app
from flask import render_template, Flask, jsonify, request, flash, redirect, url_for, session
from QLHS.models import userLogin

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
@app.route('/report')
def report():
        return render_template('report.html')
###Thống kê báo cáo end###
###Tạo tài khoản start###
@app.route('/register')
def register():
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
