from QLHS import create_app
from flask import render_template, Flask, jsonify, request, flash, redirect, url_for, session

app = create_app()

@app.route('/')
def index():
    return render_template('index.html')

###LOGIN start###
@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('login.html')
###LOGIN end###

###LOGOUT start###
@app.route('/logout')
def logout():
    return redirect(url_for('index'))
###LOGOUT end###

###ADMIN start###
@app.route('/admin')
def admin():
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
@app.route('/teacher')
def teacher():
    return render_template('teacher.html') 
###Teacher end###

###Staff start###
@app.route('/staff')
def staff():
    return render_template('staff.html')
###Staff end###

if __name__ == '__main__':
    app.run(debug=True)
