from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import os
from datetime import datetime
from urllib.parse import quote

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key_Change_in_production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# إنشاء المجلدات إذا لم تكن موجودة
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('static/images/products', exist_ok=True)

db = SQLAlchemy(app)

# نموذج المنتج
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    old_price = db.Column(db.Float, nullable=True)
    image = db.Column(db.String(100), nullable=False, default='default.jpg')
    category = db.Column(db.String(50), nullable=False)
    in_stock = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# نموذج المستخدم (للمسؤول)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# ديكوراتور للتحقق من تسجيل الدخول
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('يجب تسجيل الدخول أولاً', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# ديكوراتور للتحقق من صلاحية المسؤول
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('يجب تسجيل الدخول أولاً', 'error')
            return redirect(url_for('admin_login'))
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# دالة لإنشاء رابط واتساب
def get_whatsapp_link(product_name, product_price):
    phone_number = "212632256568"
    message = f"أهلاً، أريد طلب هذا المنتج: {product_name} - بسعر: {product_price} درهم"
    encoded_message = quote(message)
    return f"https://wa.me/{phone_number}?text={encoded_message}"

@app.context_processor
def utility_processor():
    return dict(get_whatsapp_link=get_whatsapp_link)

# الصفحة الرئيسية
@app.route('/')
def index():
    products = Product.query.filter_by(in_stock=True).order_by(Product.created_at.desc()).limit(8).all()
    return render_template('index.html', products=products)

# صفحة المتجر
@app.route('/shop')
def shop():
    category = request.args.get('category', '')
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    if category:
        products = Product.query.filter_by(in_stock=True, category=category).order_by(Product.created_at.desc())
    else:
        products = Product.query.filter_by(in_stock=True).order_by(Product.created_at.desc())
    
    products = products.paginate(page=page, per_page=per_page, error_out=False)
    return render_template('shop.html', products=products, category=category)

# صفحة المنتج
@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    related_products = Product.query.filter(Product.id != product_id, Product.in_stock == True, 
                                          Product.category == product.category).limit(4).all()
    return render_template('product.html', product=product, related_products=related_products)

# تسجيل دخول المسؤول
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password) and user.is_admin:
            session['user_id'] = user.id
            flash('تم تسجيل الدخول بنجاح', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'error')
    
    return render_template('admin/login.html')

# لوحة تحكم المسؤول
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    products_count = Product.query.count()
    return render_template('admin/dashboard.html', products_count=products_count)

# إدارة المنتجات
@app.route('/admin/products', methods=['GET', 'POST'])
@admin_required
def admin_products():
    if request.method == 'POST':
        # إضافة منتج جديد
        name = request.form.get('name')
        description = request.form.get('description')
        price = float(request.form.get('price'))
        old_price = float(request.form.get('old_price')) if request.form.get('old_price') else None
        category = request.form.get('category')
        
        # معالجة صورة المنتج
        image = request.files.get('image')
        image_filename = 'default.jpg'
        if image and image.filename != '':
            image_filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
            image.save(image_path)
        
        product = Product(
            name=name,
            description=description,
            price=price,
            old_price=old_price,
            image=image_filename,
            category=category
        )
        
        db.session.add(product)
        db.session.commit()
        flash('تم إضافة المنتج بنجاح', 'success')
        return redirect(url_for('admin_products'))
    
    # عرض المنتجات
    page = request.args.get('page', 1, type=int)
    per_page = 10
    products = Product.query.order_by(Product.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin/products.html', products=products)

# تسجيل الخروج
@app.route('/admin/logout')
def admin_logout():
    session.pop('user_id', None)
    flash('تم تسجيل الخروج بنجاح', 'success')
    return redirect(url_for('index'))

# تهيئة قاعدة البيانات وإنشاء مستخدم مسؤول افتراضي
def create_tables():
    with app.app_context():
        db.create_all()
        
        # إنشاء مستخدم مسؤول افتراضي إذا لم يكن موجوداً
        if not User.query.filter_by(username='admin').first():
            admin_user = User(username='admin', is_admin=True)
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            db.session.commit()
            print("تم إنشاء المستخدم المسؤول الافتراضي")

# إنشاء الجداول عند بدء التشغيل
create_tables()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
