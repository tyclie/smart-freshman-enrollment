import sqlite3
from database import get_db_connection

def set_flow_step(student_id, step):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE student SET flow_step=? WHERE student_id=?", (step, student_id))
    conn.commit()
    conn.close()
    print(f"✅ 已将学生 {student_id} 的报到步骤更新为第 {step} 步")

if __name__ == '__main__':
    # 在这里修改学号和目标步骤
    set_flow_step('2024001', 1)   # 把 2024001 改为第1步
    # set_flow_step('2024002', 2)  # 可以添加更多

