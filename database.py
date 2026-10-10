import sqlite3
import os
from werkzeug.security import generate_password_hash
from config import DATABASE_PATH

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 用户表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'student'
    )
    ''')

    # 学生表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS student (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT UNIQUE NOT NULL,
        name TEXT,
        id_card TEXT,
        gender TEXT,
        class_name TEXT,
        major TEXT,
        contact TEXT,
        status TEXT DEFAULT 'submitted',
        dorm_id INTEGER,
        bed_id INTEGER,
        flow_step INTEGER DEFAULT 1,
        FOREIGN KEY (dorm_id) REFERENCES dorm(id),
        FOREIGN KEY (bed_id) REFERENCES bed(id)
    )
    ''')

    # 宿舍楼表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS dorm (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        building TEXT NOT NULL,
        room_number TEXT NOT NULL,
        gender_limit TEXT,
        bed_count INTEGER DEFAULT 4
    )
    ''')

    # 床位表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bed (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dorm_id INTEGER NOT NULL,
        bed_number TEXT NOT NULL,
        status TEXT DEFAULT 'free',
        student_id TEXT,
        FOREIGN KEY (dorm_id) REFERENCES dorm(id),
        FOREIGN KEY (student_id) REFERENCES student(student_id)
    )
    ''')

    # 缴费表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS payment (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT NOT NULL,
        amount REAL,
        pay_time TEXT,
        status TEXT DEFAULT 'unpaid',
        FOREIGN KEY (student_id) REFERENCES student(student_id)
    )
    ''')

    # 聊天消息表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chat_message (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_username TEXT,
        sender_role TEXT,
        content TEXT,
        timestamp TEXT
    )
    ''')

    # 默认测试账号（学生）
    cursor.execute("SELECT id FROM user WHERE username = '2024001'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO user (username, password_hash, role) VALUES (?, ?, ?)",
                       ('2024001', generate_password_hash('123456'), 'student'))

    # 默认管理员账号
    cursor.execute("SELECT id FROM user WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO user (username, password_hash, role) VALUES (?, ?, ?)",
                       ('admin', generate_password_hash('admin123'), 'admin'))

    # 默认辅导员账号（辅导员账号即班级名）
    cursor.execute("SELECT id FROM user WHERE username = 'cs1'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO user (username, password_hash, role) VALUES (?, ?, ?)",
                       ('cs1', generate_password_hash('123456'), 'counselor'))

    conn.commit()
    conn.close()
    print("✅ 数据库初始化完成")

if __name__ == '__main__':
    init_db()
