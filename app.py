from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import pandas as pd
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'quran_secret_key_123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quran_paltform.db'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- نماذج قاعدة البيانات ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)

# --- نظام تحميل المستخدم ---
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- تنظيف بيانات الجدول (من الملف اللي رفعته) ---
def get_daily_schedule(day_index):
    try:
        # قراءة الملف (بافتراض وجوده في نفس المجلد)
        df = pd.read_csv('جدول الحصون الخمسة V 5.6.xlsx - The Five Sheilds.csv', header=None)
        # البيانات الحقيقية بتبدأ من الصف رقم 7 (اندكس 6)
        data_row = df.iloc[6 + day_index] 
        return {
            "day_name": data_row[0],
            "reading": data_row[1],   # القراءة المنهجية
            "listening": data_row[3], # الاستماع المنهجي
            "prep_weekly": data_row[5],# التحضير الأسبوعي
            "prep_prev": data_row[7], # التحضير القبلي
            "new_save": data_row[9],  # حفظ الجديد
            "near_rev": data_row[11], # مراجعة القريب
            "far_rev": data_row[13]   # مراجعة البعيد
        }
    except:
        return None

# --- المسارات (Routes) ---

@app.route('/')
@login_required
def index():
    # حساب اليوم الحالي (الفرق بين تاريخ النهاردة وتاريخ التسجيل)
    delta = datetime.utcnow() - current_user.start_date
    day_number = delta.days 
    schedule = get_daily_schedule(day_number)
    return render_template('dashboard.html', schedule=schedule, day_num=day_number+1)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('index'))
        flash('خطأ في اسم المستخدم أو كلمة المرور')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        hashed_pw = generate_password_hash(request.form['password'], method='sha256')
        new_user = User(username=request.form['username'], password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)