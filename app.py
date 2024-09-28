from flask import Flask, render_template, request
import pandas as pd
import hashlib
import logging
import re


# 创建 Flask 应用
app = Flask(__name__)

# 配置日志记录
logging.basicConfig(level=logging.DEBUG)

# 读取运势列表
try:
    fortunes = pd.read_excel('fortunes.xlsx', engine='openpyxl')['运势'].tolist()
    app.logger.debug("Successfully loaded fortunes from fortunes.xlsx")
except FileNotFoundError:
    app.logger.error("Error: fortunes.xlsx file not found. Please ensure the file is in the correct location.")
    fortunes = []

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

# 保存用户信息
def save_user_info(name, gender, phone_number):
    df = pd.DataFrame([[name, gender, phone_number]], columns=['姓名', '性别', '手机号码'])
    try:
        # 使用 utf-8-sig 编码保存，确保 Excel 能正确显示中文
        df.to_csv('user_info.csv', mode='a', header=False, index=False, encoding='utf-8-sig')
        app.logger.debug("User info saved successfully to user_info.csv")
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

            # 保存用户信息
            save_user_info(name, gender, phone_number)

            return render_template('result.html', name=name, fortune=fortune)
        except Exception as e:
            app.logger.error(f"Error processing form data: {e}")
            return "An error occurred while processing your request. Please try again."

    # 如果是 GET 请求，渲染表单页面
    return render_template('index.html')


# 启动应用程序
if __name__ == '__main__':
        app.run(debug=True, port=8050)

