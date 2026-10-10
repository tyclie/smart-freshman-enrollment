# 在 config.py 或 app.py 顶部添加
import os

from flask import Flask, request, jsonify, render_template, redirect, url_for, abort
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
import base64
import json
import requests
from datetime import datetime

from config import DATABASE_PATH, SECRET_KEY, DASHSCOPE_API_KEY, DASHSCOPE_OCR_URL, BAIDU_MAP_AK
from database import get_db_connection, init_db

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'index'

class User(UserMixin):
    def __init__(self, id, username, role):
        self.id = id
        self.username = username
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role FROM user WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return User(row['id'], row['username'], row['role'])
    return None

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated

def counselor_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.role != 'counselor':
            abort(403)
        return f(*args, **kwargs)
    return decorated

init_db()

# ==================== 页面路由 ====================

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.*, d.building, d.room_number, b.bed_number
        FROM student s
        LEFT JOIN bed b ON s.bed_id = b.id
        LEFT JOIN dorm d ON b.dorm_id = d.id
        WHERE s.student_id = ?
    """, (current_user.username,))
    student_row = cursor.fetchone()
    conn.close()
    student = dict(student_row) if student_row else None
    return render_template('dashboard.html', username=current_user.username, student=student, role=current_user.role)

@app.route('/ocr_upload')
@login_required
def ocr_upload():
    return render_template('ocr_upload.html')

@app.route('/navigation')
@login_required
def navigation():
    """渲染导航页面"""
    return render_template('navigation.html')

@app.route('/api/navigation', methods=['GET'])
def api_navigation():
    """
    返回校园地点坐标数据和地图 AK。
    坐标格式：[lng, lat]（百度 BD09 坐标系）
    """
    locations = [
        {"id": 1, "name": "校门口", "lng": 115.027390, "lat": 30.215162, "icon": "entrance",
         "type": "gate", "desc": "校园主要出入口", "open": "全天开放", "color": "#8d6e63", "height": 12},
        {"id": 2, "name": "教学楼J1", "lng": 115.031383, "lat": 30.216170, "icon": "building",
         "type": "teaching", "desc": "计算机学院教学楼", "open": "7:00-22:00", "color": "#4285f4", "height": 42},
        {"id": 3, "name": "图书馆", "lng": 115.031021, "lat": 30.216409, "icon": "library",
         "type": "library", "desc": "藏书超过50万册", "open": "7:00-22:00", "color": "#fbbc04", "height": 34},
        {"id": 4, "name": "静园食堂", "lng": 115.034196, "lat": 30.214929, "icon": "canteen",
         "type": "canteen", "desc": "三层美食广场", "open": "6:30-20:00", "color": "#ea4335", "height": 24},
        {"id": 5, "name": "毓真学生公寓", "lng": 115.025000, "lat": 30.210727, "icon": "dorm",
         "type": "dorm", "desc": "四人间，独立卫浴", "open": "全天开放", "color": "#9c27b0", "height": 52},
        {"id": 6, "name": "东门体育馆", "lng": 115.034730, "lat": 30.213500, "icon": "gym",
         "type": "gym", "desc": "篮球场、游泳馆", "open": "9:00-21:00", "color": "#34a853", "height": 28},
        {"id": 7, "name": "豁度楼", "lng": 115.034049, "lat": 30.214040, "icon": "admin",
         "type": "office", "desc": "行政办公与报到中心", "open": "8:30-17:30", "color": "#78909c", "height": 40},
        {"id": 8, "name": "智慧大楼", "lng": 115.038831, "lat": 30.212400, "icon": "register",
         "type": "modern", "desc": "新生报到服务大厅", "open": "8:00-20:00", "color": "#ff7043", "height": 46},
    ]
    return jsonify({
        'success': True,
        'ak': BAIDU_MAP_AK,
        'locations': locations,
        'roads': [
            [1, 8], [8, 7], [7, 2], [2, 3],
            [3, 5], [5, 4], [4, 6], [6, 8]
        ],
        'tour_order': [1, 8, 7, 2, 3, 5, 4, 6, 1]
    })

@app.route('/api/campus', methods=['GET'])
def api_campus():
    """为 3D 校园页面提供与导航一致的地点、道路与漫游顺序。"""
    response = api_navigation().get_json()
    response.pop('ak', None)
    return jsonify(response)

@app.route('/register_flow')
@login_required
def register_flow():
    return render_template('register_flow.html')

@app.route('/campus3d')
@login_required
def campus3d():
    return render_template('campus3d.html')

@app.route('/dorm_selection')
@login_required
def dorm_selection():
    return render_template('dorm_selection.html')

@app.route('/admin_dashboard')
@login_required
@admin_required
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app.route('/counselor_dashboard')
@login_required
@counselor_required
def counselor_dashboard():
    class_label = '软件工程1班' if current_user.username == 'cs1' else current_user.username
    return render_template('counselor_dashboard.html', class_label=class_label)

@app.route('/chat')
@login_required
def chat():
    return render_template('chat.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))



# ==================== 登录相关 ====================

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    if not username or not password:
        return jsonify({'success': False, 'message': '账号和密码不能为空'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()

    if row and check_password_hash(row['password_hash'], password):
        user = User(row['id'], row['username'], row['role'])
        login_user(user)
        # 根据角色跳转
        if user.role == 'admin':
            redirect_url = '/admin_dashboard'
        elif user.role == 'counselor':
            redirect_url = '/counselor_dashboard'
        else:
            redirect_url = '/dashboard'
        return jsonify({'success': True, 'redirect': redirect_url})
    else:
        return jsonify({'success': False, 'message': '账号或密码错误'}), 401

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'student')
    if not username or not password:
        return jsonify({'success': False, 'message': '账号和密码不能为空'}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM user WHERE username = ?", (username,))
    if cursor.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': '账号已存在'}), 400
    cursor.execute("INSERT INTO user (username, password_hash, role) VALUES (?, ?, ?)",
                   (username, generate_password_hash(password), role))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': '注册成功'})

# ==================== 智能填报 OCR ====================

def call_dashscope_ocr(image_path):
    """
    调用通义千问VL多模态API进行OCR识别。
    成功返回解析后的JSON字典；失败返回None。
    """
    api_key = DASHSCOPE_API_KEY
    url = DASHSCOPE_OCR_URL

    if not api_key or api_key == "sk-xxxxxxxxxxxxxxxx":
        print("⚠️ 未配置通义千问API Key，使用Mock数据")
        return None

    # 读取图片并转为base64
    with open(image_path, "rb") as f:
        image_data = f.read()
    image_base64 = base64.b64encode(image_data).decode("utf-8")

    # 根据图片扩展名推断 MIME 类型（默认 jpeg）
    img_type = os.path.splitext(image_path)[1].lstrip('.').lower() or 'jpeg'
    if img_type in ('jpg', 'jpe'):
        img_type = 'jpeg'
    if img_type not in ('jpeg', 'png', 'gif', 'bmp', 'webp'):
        img_type = 'jpeg'
    mime = f"image/{img_type}"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    prompt = """
请识别这张图片中的以下信息，以严格的JSON格式返回，不要包含任何其他文字：
{
    "name": "姓名",
    "id_card": "身份证号",
    "gender": "性别",
    "class_name": "班级",
    "major": "专业",
    "student_id": "学号",
    "contact": "联系电话"
}
如果某项无法识别或不存在，请将该字段设为null。
"""

    payload = {
        "model": "qwen-vl-plus",
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"image": f"data:{mime};base64,{image_base64}"},
                        {"text": prompt}
                    ]
                }
            ]
        },
        "parameters": {
            "max_tokens": 1000
        }
    }

    try:
        print("正在调用通义千问OCR接口...")
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()

        content_list = result.get("output", {}).get("choices", [{}])[0].get("message", {}).get("content", [])
        text = ""
        for item in content_list:
            if isinstance(item, dict) and "text" in item:
                text += item["text"]

        # 提取JSON部分
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            json_str = text[start:end+1]
            ocr_data = json.loads(json_str)
            return ocr_data
        else:
            print("⚠️ API返回内容中未找到JSON，原始内容：", text)
            return None
    except Exception as e:
        print(f"❌ OCR API调用失败: {e}")
        return None

@app.route('/api/ocr', methods=['POST'])
@login_required
def api_ocr():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '未上传文件'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': '未选择文件'}), 400
    filename = os.path.join(app.config['UPLOAD_FOLDER'], 'ocr_temp.jpg')
    file.save(filename)
    ocr_data = call_dashscope_ocr(filename)
    if ocr_data is None:
        ocr_data = {
            'name': '张三', 'id_card': '110101200001011234', 'gender': '男',
            'major': '计算机科学与技术', 'student_id': '2024001',
            'contact': '13800138000', 'class_name': '软件工程1班'
        }
    os.remove(filename)
    return jsonify({'success': True, 'data': ocr_data})

@app.route('/api/report', methods=['POST'])
@login_required
def api_report():
    data = request.get_json()
    student_id = current_user.username
    name = data.get('name', '')
    id_card = data.get('id_card', '')
    gender = data.get('gender', '')
    class_name = data.get('class_name', '')
    major = data.get('major', '')
    contact = data.get('contact', '')
    if not name or not id_card:
        return jsonify({'success': False, 'message': '姓名和身份证号不能为空'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT flow_step FROM student WHERE student_id = ?", (student_id,))
    row = cursor.fetchone()
    current_step = row['flow_step'] if row else 1
    # 保存信息后，如果当前步骤 <= 2，则设置为 2；否则保留原步骤
    new_step = 2 if current_step <= 2 else current_step

    cursor.execute("SELECT id FROM student WHERE student_id = ?", (student_id,))
    if cursor.fetchone():
        cursor.execute("""
            UPDATE student SET name=?, id_card=?, gender=?, class_name=?, major=?, contact=?, flow_step=?
            WHERE student_id=?
        """, (name, id_card, gender, class_name, major, contact, new_step, student_id))
    else:
        cursor.execute("""
            INSERT INTO student (student_id, name, id_card, gender, class_name, major, contact, flow_step)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (student_id, name, id_card, gender, class_name, major, contact, new_step))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': '报到信息已保存'})

# ==================== 报到流程状态 ====================

@app.route('/api/report/status', methods=['GET', 'POST'])
@login_required
def api_report_status():
    if request.method == 'GET':
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT flow_step FROM student WHERE student_id = ?", (current_user.username,))
        row = cursor.fetchone()
        conn.close()
        step = row['flow_step'] if row else 1
        return jsonify({'success': True, 'flow_step': step})

    # POST
    data = request.get_json()
    new_step = int(data.get('flow_step', 1))
    if new_step < 1 or new_step > 5:
        return jsonify({'success': False, 'message': '步骤无效'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM student WHERE student_id = ?", (current_user.username,))
    student = cursor.fetchone()
    if not student:
        conn.close()
        return jsonify({'success': False, 'message': '学生信息不存在，请先填报'}), 400

    current_step = student['flow_step']
    if new_step > current_step + 1:
        conn.close()
        return jsonify({'success': False, 'message': '请按顺序完成步骤'}), 400

    # 步骤3需要已选宿舍
    if new_step == 3 and new_step > current_step:
        cursor.execute("SELECT bed_id FROM student WHERE student_id = ?", (current_user.username,))
        bed_row = cursor.fetchone()
        if not bed_row or not bed_row['bed_id']:
            conn.close()
            return jsonify({'success': False, 'message': '请先选择宿舍'}), 400

    # 步骤5需要已缴费
    if new_step == 5 and new_step > current_step:
        cursor.execute("SELECT status FROM payment WHERE student_id = ?", (current_user.username,))
        pay_row = cursor.fetchone()
        if not pay_row or pay_row['status'] != 'paid':
            conn.close()
            return jsonify({'success': False, 'message': '请先完成缴费'}), 400

    # 回退到步骤<=2，释放床位
    if new_step < current_step and new_step <= 2:
        cursor.execute("SELECT bed_id FROM student WHERE student_id = ?", (current_user.username,))
        bed_row = cursor.fetchone()
        if bed_row and bed_row['bed_id']:
            cursor.execute("UPDATE bed SET status='free', student_id=NULL WHERE id=?", (bed_row['bed_id'],))
            cursor.execute("UPDATE student SET bed_id=NULL, dorm_id=NULL WHERE student_id=?", (current_user.username,))

    cursor.execute("UPDATE student SET flow_step=? WHERE student_id=?", (new_step, current_user.username))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'flow_step': new_step})

# ==================== 宿舍选择 ====================

@app.route('/api/dorms', methods=['GET'])
@login_required
def api_dorms():
    # 返回当前学生性别对应的所有楼栋、房间、床位
    student_id = current_user.username
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT gender FROM student WHERE student_id = ?", (student_id,))
    row = cursor.fetchone()
    if not row:
        return jsonify({'success': False, 'message': '请先填报个人信息'}), 400
    gender = row['gender']
    cursor.execute("""
        SELECT d.id as dorm_id, d.building, d.room_number, d.gender_limit, d.bed_count,
               b.id as bed_id, b.bed_number, b.status, b.student_id
        FROM dorm d LEFT JOIN bed b ON d.id = b.dorm_id
        WHERE d.gender_limit = ? OR d.gender_limit = '不限'
        ORDER BY d.building, d.room_number, b.bed_number
    """, (gender,))
    rows = cursor.fetchall()
    conn.close()

    dorms = {}
    for r in rows:
        key = r['dorm_id']
        if key not in dorms:
            dorms[key] = {
                'dorm_id': r['dorm_id'],
                'building': r['building'],
                'room_number': r['room_number'],
                'gender_limit': r['gender_limit'],
                'bed_count': r['bed_count'],
                'beds': []
            }
        dorms[key]['beds'].append({
            'bed_id': r['bed_id'],
            'bed_number': r['bed_number'],
            'status': r['status'],
            'student_id': r['student_id']
        })
    return jsonify({'success': True, 'dorms': list(dorms.values())})

@app.route('/api/select_bed', methods=['POST'])
@login_required
def api_select_bed():
    data = request.get_json()
    bed_id = data.get('bed_id')
    if not bed_id:
        return jsonify({'success': False, 'message': '缺少床位ID'}), 400
    student_id = current_user.username

    conn = get_db_connection()
    cursor = conn.cursor()
    # 检查床位是否空闲
    cursor.execute("SELECT * FROM bed WHERE id = ?", (bed_id,))
    bed = cursor.fetchone()
    if not bed:
        conn.close()
        return jsonify({'success': False, 'message': '床位不存在'}), 404
    if bed['status'] != 'free':
        conn.close()
        return jsonify({'success': False, 'message': '该床位已被占用，请选择其他床位'}), 400
    # 检查学生性别是否匹配
    cursor.execute("SELECT gender, flow_step FROM student WHERE student_id = ?", (student_id,))
    student = cursor.fetchone()
    if not student:
        conn.close()
        return jsonify({'success': False, 'message': '学生信息不存在，请先填报'}), 400
    cursor.execute("SELECT gender_limit FROM dorm WHERE id = ?", (bed['dorm_id'],))
    dorm = cursor.fetchone()
    if dorm['gender_limit'] != '不限' and dorm['gender_limit'] != student['gender']:
        conn.close()
        return jsonify({'success': False, 'message': '该宿舍性别不符'}), 400

    # 先释放学生原有床位（如果有）
    cursor.execute("SELECT bed_id FROM student WHERE student_id = ?", (student_id,))
    old_bed_row = cursor.fetchone()
    if old_bed_row and old_bed_row['bed_id'] and old_bed_row['bed_id'] != bed_id:
        cursor.execute("UPDATE bed SET status='free', student_id=NULL WHERE id=?", (old_bed_row['bed_id'],))

    # 更新床位
    cursor.execute("UPDATE bed SET status='occupied', student_id=? WHERE id=?", (student_id, bed_id))
    # 更新学生
    next_step = 3 if student['flow_step'] < 3 else student['flow_step']
    cursor.execute("UPDATE student SET bed_id=?, dorm_id=?, flow_step=? WHERE student_id=?",
                   (bed_id, bed['dorm_id'], next_step, student_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': '宿舍选择成功'})

@app.route('/api/cancel_bed', methods=['POST'])
@login_required
def api_cancel_bed():
    student_id = current_user.username
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT bed_id FROM student WHERE student_id = ?", (student_id,))
    row = cursor.fetchone()
    if row and row['bed_id']:
        cursor.execute("UPDATE bed SET status='free', student_id=NULL WHERE id=?", (row['bed_id'],))
        cursor.execute("UPDATE student SET bed_id=NULL, dorm_id=NULL, flow_step=2 WHERE student_id=?", (student_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': '已取消选择，流程回退到资格审核'})
    conn.close()
    return jsonify({'success': False, 'message': '你还没有选择床位'}), 400

@app.route('/api/pay', methods=['POST'])
@login_required
def api_pay():
    """模拟缴费：将当前学生的缴费状态改为已缴费"""
    student_id = current_user.username
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM student WHERE student_id = ?", (student_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': '学生信息不存在'}), 404

    cursor.execute("SELECT * FROM payment WHERE student_id = ?", (student_id,))
    payment = cursor.fetchone()
    if payment and payment['status'] == 'paid':
        conn.close()
        return jsonify({'success': True, 'message': '已完成缴费'})

    if payment:
        cursor.execute("UPDATE payment SET status='paid', pay_time=? WHERE student_id=?",
                       (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), student_id))
    else:
        cursor.execute("INSERT INTO payment (student_id, amount, pay_time, status) VALUES (?, ?, ?, 'paid')",
                       (student_id, 5000, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': '缴费成功'})


# ==================== 辅导员/管理员 ====================

@app.route('/api/admin/students', methods=['GET'])
@login_required
@admin_required
def api_admin_students():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.*, p.status as pay_status, p.amount, p.pay_time, d.building, d.room_number, b.bed_number
        FROM student s
        LEFT JOIN payment p ON s.student_id = p.student_id
        LEFT JOIN bed b ON s.bed_id = b.id
        LEFT JOIN dorm d ON b.dorm_id = d.id
        ORDER BY s.student_id
    """)
    rows = cursor.fetchall()
    conn.close()
    students = [dict(r) for r in rows]
    return jsonify({'success': True, 'students': students})

@app.route('/api/admin/student/<student_id>/reject', methods=['POST'])
@login_required
@admin_required
def api_admin_reject(student_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE student SET flow_step=1, status='rejected' WHERE student_id=?", (student_id,))
    # 释放床位，回退步骤
    cursor.execute("SELECT bed_id FROM student WHERE student_id=?", (student_id,))
    row = cursor.fetchone()
    if row and row['bed_id']:
        cursor.execute("UPDATE bed SET status='free', student_id=NULL WHERE id=?", (row['bed_id'],))
        cursor.execute("UPDATE student SET bed_id=NULL, dorm_id=NULL WHERE student_id=?", (student_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': '已打回重填'})

@app.route('/api/counselor/students', methods=['GET'])
@login_required
@counselor_required
def api_counselor_students():
    # 辅导员账号即班级名；演示账号 cs1 映射到软件工程1班
    class_name = '软件工程1班' if current_user.username == 'cs1' else current_user.username
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM student WHERE class_name=? ORDER BY student_id
    """, (class_name,))
    rows = cursor.fetchall()
    conn.close()
    return jsonify({'success': True, 'students': [dict(r) for r in rows]})

# ==================== 聊天室 ====================

@app.route('/api/chat/messages', methods=['GET'])
@login_required
def api_get_messages():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM chat_message ORDER BY timestamp")
    rows = cursor.fetchall()
    conn.close()
    return jsonify({'success': True, 'messages': [dict(r) for r in rows]})

@app.route('/api/chat/send', methods=['POST'])
@login_required
def api_send_message():
    data = request.get_json()
    content = data.get('content', '').strip()
    if not content:
        return jsonify({'success': False, 'message': '消息内容不能为空'}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO chat_message (sender_username, sender_role, content, timestamp)
        VALUES (?, ?, ?, ?)
    """, (current_user.username, current_user.role, content, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()
    return jsonify({'success': True})



if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
