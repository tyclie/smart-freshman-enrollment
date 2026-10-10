"""项目配置。

所有敏感配置均通过环境变量注入，仓库中不保存任何真实密钥。
可以直接设置系统环境变量，也可以在项目根目录放置 .env 文件
（.env 已加入 .gitignore，不会被提交），格式参考 .env.example。
"""

import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _load_dotenv():
    """读取同目录下的 .env 文件，已存在的环境变量优先。"""
    env_path = os.path.join(BASE_DIR, '.env')
    if not os.path.exists(env_path):
        return
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv()


# SQLite 数据库文件路径
DATABASE_PATH = os.getenv('DATABASE_PATH', os.path.join(BASE_DIR, 'demo.db'))

# 阿里云通义千问 VL 多模态识别接口
# 未配置 API Key 时，系统自动降级为内置模拟数据，不影响演示与流程测试
DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY', '')
DASHSCOPE_OCR_URL = os.getenv(
    'DASHSCOPE_OCR_URL',
    'https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation',
)

# 百度地图浏览器端 AK
BAIDU_MAP_AK = os.getenv('BAIDU_MAP_AK', '')

# Flask 会话密钥（部署到公网前务必替换为随机值）
SECRET_KEY = os.getenv('SECRET_KEY', 'freshman-demo-secret-key')
