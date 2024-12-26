from flask import Flask, render_template, request, flash, redirect, url_for
from werkzeug.security import generate_password_hash
from flask_mysqldb import MySQL

app = Flask(__name__)

app.secret_key = 'your_unique_secret_key'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Admin@123'
app.config['MYSQL_DB'] = 'student_management'

mysql = MySQL(app)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        # Mã hóa mật khẩu
        hashed_password = generate_password_hash(password)

        # Thêm người dùng vào cơ sở dữ liệu
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)", 
                    (username, hashed_password, role))
        mysql.connection.commit()
        cur.close()

        flash("Tạo tài khoản thành công!", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)
