from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import hashlib
import logging
import re
import os

# 创建 Flask 应用
app = Flask(__name__)

# 配置日志记录
logging.basicConfig(level=logging.DEBUG)

# 配置数据库连接
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://mobilenumber_user:XEFhJvAdxq5AWTOQ60wDfWF5TmIeWClR@dpg-crt6lht6l47c73d7g0l0-a/mobilenumber'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库对象
db = SQLAlchemy(app)

# 创建用户信息的数据库模型
class UserInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)

# 创建数据库表
with app.app_context():
    db.create_all()

# 获取文件路径，使用跨平台的方法
fortunes_file_path = os.path.join(os.path.dirname(__file__), 'fortunes.xlsx')

# 读取运势列表
try:
    fortunes = pd.read_excel(fortunes_file_path, engine='openpyxl')['运势'].tolist()
    app.logger.debug("Successfully loaded fortunes from fortunes.xlsx")
except FileNotFoundError:
    app.logger.error("Error: fortunes.xlsx file not found. Please ensure the file is in the correct location.")
    fortunes = []

# 验证手机号码格式
def is_valid_phone_number(phone_number):
    pattern = r'^09\d{8}$'
    return re.match(pattern, phone_number) is not None

# 计算哈希值
def get_hash(name, phone_number):
    hash_input = f"{name}{phone_number}"
    return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()

# 获取运势
def get_fortune(name, phone_number):
    if not fortunes:
        return "Fortunes data is unavailable."

    hash_value = get_hash(name, phone_number)
    index = int(hash_value, 16) % len(fortunes)
    return fortunes[index]

# 保存用户信息到数据库
def save_user_info(name, gender, phone_number):
    try:
        # 检查数据库中是否已经存在此号码
        existing_user = UserInfo.query.filter_by(phone_number=phone_number).first()
        if not existing_user:
            # 如果用户不存在，则添加新用户
            user = UserInfo(name=name, gender=gender, phone_number=phone_number)
            db.session.add(user)
            db.session.commit()
            app.logger.debug("User info saved successfully to the database")
        else:
            app.logger.debug("User with this phone number already exists in the database")
    except Exception as e:
        app.logger.error(f"Error saving user info: {e}")

# 定义路由和视图函数
@app.route('/', methods=['GET', 'POST'])
def index():
    app.logger.debug("Index route accessed")
    if request.method == 'POST':
        app.logger.debug("POST request received")
        try:
            name = request.form['name']
            gender = request.form['gender']
            phone_number = request.form['phone_number']

            # 验证手机号码格式
            if not is_valid_phone_number(phone_number):
                app.logger.error("Invalid phone number format.")
                return "Invalid phone number format. Please enter a valid number starting with 09 followed by 8 digits."

            app.logger.debug(f"Received name: {name}, gender: {gender}, phone number: {phone_number}")

            # 获取运势
            fortune = get_fortune(name, phone_number)
            app.logger.debug(f"Calculated fortune: {fortune}")

            # 保存用户信息到数据库
            save_user_info(name, gender, phone_number)

            return render_template('result.html', name=name, fortune=fortune)
        except Exception as e:
            app.logger.error(f"Error processing form data: {e}")
            return "An error occurred while processing your request. Please try again."

    # 如果是 GET 请求，渲染表单页面
    return render_template('index.html')

# 启动应用程序
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050)
