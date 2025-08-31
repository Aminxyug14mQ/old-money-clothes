#!/usr/bin/env python3
import sys
import os

# أضف مسار المشروع إلى Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    # تحقق إذا كان المستخدم موجوداً
    existing_user = User.query.filter_by(username='admin').first()
    if existing_user:
        print("المستخدم موجود بالفعل، جاري التحديث...")
        existing_user.password_hash = generate_password_hash('Fatiha123@#')
        existing_user.is_admin = True
    else:
        print("جاري إنشاء مستخدم جديد...")
        admin_user = User(username='admin', is_admin=True)
        admin_user.password_hash = generate_password_hash('Fatiha123@#')
        db.session.add(admin_user)
    
    db.session.commit()
    print("تم إعداد المستخدم المسؤول بنجاح!")
    print("بيانات الدخول:")
    print("اسم المستخدم: admin")
    print("كلمة المرور: Fatiha123@#")
