from flask import Flask, redirect, url_for, render_template, request
from flask_sqlalchemy import SQLAlchemy
import pymysql
from sqlalchemy import text

# 让 SQLAlchemy 使用 pymysql 作为 MySQL 数据库的驱动
pymysql.install_as_MySQLdb()

app = Flask(__name__)
# 正确配置 MySQL 数据库连接 URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:686663@localhost:3306/test'
db = SQLAlchemy(app)


# 定义 User 模型类
class User(db.Model):
    __tablename__ = 'N_users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80))
    password = db.Column(db.String(120))  # 这里将 password 改为字符串类型更合理，用于存储密码


class Bags(db.Model):
    __tablename__ = 'N_bags'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    number = db.Column(db.Integer)


def create_tables():
    # 创建所有表
    with app.app_context():
        db.create_all()


# 手动调用创建表函数
create_tables()


@app.route('/')
def begin():
    return render_template('主界面.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            return "登录成功！"
        else:
            return "用户名或密码错误，请重试。"
    return render_template('登录系统.html')


@app.route('/insert')
def insert_data():
    try:
        # 使用新的 API 执行插入操作
        with db.engine.connect() as connection:
            # 使用 text 函数将 SQL 字符串转换为可执行对象
            connection.execute(text("INSERT INTO N_bags (name, number) VALUES ('Amas', '3')"))
            connection.commit()
        # 插入成功后重定向到展示页面
        return redirect(url_for('Bshow'))
    except Exception as e:
        return f'Error: {str(e)}'


@app.route('/submit', methods=['POST'])
def submit():
    username = request.form.get('username')
    password = request.form.get('password')
    if username and password:
        try:
            new_user = User(username=username, password=password)
            db.session.add(new_user)
            db.session.commit()
            return '数据已成功保存到数据库！'
        except Exception as e:
            db.session.rollback()
            return f'保存数据时出现错误: {str(e)}'
    return '请填写完整的用户名和密码！'


# 修改后的 /register 路由 - 处理注册全流程
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return '用户名和密码不能为空！', 400

        # 检查用户名是否已存在
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return '用户名已被使用，请选择其他用户名', 400

        try:
            new_user = User(username=username, password=password)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))  # 注册成功后跳转到登录页
        except Exception as e:
            db.session.rollback()
            return f'注册失败: {str(e)}', 500

    # GET 请求时显示注册表单
    return render_template('register.html')


# 删除原来的 /submit 路由（功能已整合到/register）
@app.route('/show')
def show():
    try:
        with db.engine.connect() as connection:
            result = connection.execute(text("SELECT * FROM N_users"))
            rows = result.fetchall()
            data = []
            for row in rows:
                # 手动构建字典
                row_dict = {
                    'id': row.id,
                    'username': row.username,
                    'password': row.password
                }
                data.append(row_dict)
        # 渲染模板并传递数据
        return render_template('show_users.html', users=data)
    except Exception as e:
        return f'Error: {str(e)}'


@app.route('/Bshow')
def Bshow():
    try:
        with db.engine.connect() as connection:
            result = connection.execute(text("SELECT * FROM N_bags"))
            rows = result.fetchall()
            data = []
            for row in rows:
                # 手动构建字典
                row_dict = {
                    'id': row.id,
                    'name': row.name,
                    'number': row.number
                }
                data.append(row_dict)
        # 渲染模板并传递数据
        return render_template('show_bags.html', bags=data)  # 修复：改为 bags=data
    except Exception as e:
        return f'Error: {str(e)}'


@app.route('/B_in', methods=['POST'])
def B_in_submit():
    try:
        name = request.form.get('name')
        number = request.form.get('number')

        # 验证输入是否有效
        if not name or not number:
            return "品牌和数量不能为空！", 400

        # 检查品牌是否已存在
        existing_bag = Bags.query.filter_by(name=name).first()

        if existing_bag:
            # 如果品牌已存在，增加数量
            existing_bag.number += int(number)
            action = "更新"
        else:
            # 如果品牌不存在，创建新记录
            new_bag = Bags(name=name, number=int(number))
            db.session.add(new_bag)
            action = "添加"

        db.session.commit()
        return redirect(url_for('Bshow'))

    except ValueError:
        return "数量必须是有效的数字！", 400
    except Exception as e:
        db.session.rollback()
        return f'操作失败: {str(e)}', 500


# 修改原有的Bin路由（仅显示表单）
@app.route('/Bin')
def B_in_form():
    return render_template('IN.html')  # 移除了不必要的users=data参数


@app.route('/Bout', methods=['GET', 'POST'])
def B_out():
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            number = request.form.get('number')

            # 验证输入是否有效
            if not name or not number:
                return "品牌和数量不能为空！", 400

            # 检查品牌是否存在
            existing_bag = Bags.query.filter_by(name=name).first()

            if not existing_bag:
                return "该品牌的包包不存在！", 400

            # 检查库存是否足够
            if existing_bag.number < int(number):
                return f"库存不足！当前库存为：{existing_bag.number}", 400

            # 减少库存
            existing_bag.number -= int(number)

            # 如果库存为0，可以选择删除记录或保留
            if existing_bag.number == 0:
                db.session.delete(existing_bag)

            db.session.commit()
            return redirect(url_for('Bshow'))

        except ValueError:
            return "数量必须是有效的数字！", 400
        except Exception as e:
            db.session.rollback()
            return f'操作失败: {str(e)}', 500

    # GET 请求时显示表单
    return render_template('out.html')


# 添加内部管理系统路由
@app.route('/internal_management')
def internal_management():
    return render_template('内部管理系统.html')


# 添加退出登录路由
@app.route('/logout')
def logout():
    return redirect(url_for('begin'))


if __name__ == '__main__':
    app.run()