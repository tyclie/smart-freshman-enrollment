import sqlite3
from database import init_db, get_db_connection
from werkzeug.security import generate_password_hash

def insert_seed_data():
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    # 清空旧数据
    cursor.execute("DELETE FROM chat_message")
    cursor.execute("DELETE FROM payment")
    cursor.execute("DELETE FROM bed")
    cursor.execute("DELETE FROM student")
    cursor.execute("DELETE FROM dorm")
    cursor.execute("DELETE FROM user WHERE username NOT IN ('2024001','admin','cs1')")

    # 插入宿舍楼 1-32栋，前16女，后16男
    for building_num in range(1, 33):
        gender = '女' if building_num <= 16 else '男'
        building = f"{building_num}栋"
        for room in range(1, 3):  # 每栋2个房间
            room_number = f"{room:02d}"
            cursor.execute("""
                INSERT INTO dorm (building, room_number, gender_limit, bed_count)
                VALUES (?, ?, ?, ?)
            """, (building, room_number, gender, 4))
            dorm_id = cursor.lastrowid
            # 每个房间4个床位
            for bed_num in range(1, 5):
                bed_number = f"{bed_num}床"
                cursor.execute("""
                    INSERT INTO bed (dorm_id, bed_number, status, student_id)
                    VALUES (?, ?, 'free', NULL)
                """, (dorm_id, bed_number))

    # 插入学生
    student_data = [
        ('2024001', '张三', '110101200001011234', '男', '软件工程1班', '计算机科学与技术', '13800138000', 2),
        ('2024002', '李四', '110101200002022345', '女', '软件工程1班', '软件工程', '13900139000', 4),
        ('2024003', '王五', '110101200003033456', '男', '软件工程1班', '信息管理', '13700137000', 5),
        ('2024004', '赵六', '110101200004044567', '女', '软件工程1班', '计算机科学', '13600136000', 1),
    ]
    for sid, name, id_card, gender, cls, major, contact, step in student_data:
        cursor.execute("""
            INSERT INTO student (student_id, name, id_card, gender, class_name, major, contact, status, flow_step)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'submitted', ?)
        """, (sid, name, id_card, gender, cls, major, contact, step))

    # 插入缴费记录
    cursor.execute("INSERT INTO payment (student_id, amount, pay_time, status) VALUES ('2024001', 5000, '2025-08-01', 'unpaid')")
    cursor.execute("INSERT INTO payment (student_id, amount, pay_time, status) VALUES ('2024002', 5000, '2025-08-02', 'paid')")
    cursor.execute("INSERT INTO payment (student_id, amount, pay_time, status) VALUES ('2024003', 5000, '2025-08-03', 'paid')")

    # 插入示例聊天记录
    cursor.execute("INSERT INTO chat_message (sender_username, sender_role, content, timestamp) VALUES ('admin', 'admin', '欢迎新同学！', '2025-08-01 09:00:00')")
    cursor.execute("INSERT INTO chat_message (sender_username, sender_role, content, timestamp) VALUES ('cs1', 'counselor', '软件工程1班的同学请尽快完成填报', '2025-08-01 10:00:00')")

    conn.commit()
    conn.close()
    print("✅ 测试数据插入完成")

if __name__ == '__main__':
    insert_seed_data()
