# 基于多模态OCR的智慧迎新系统

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-black)
![SQLite](https://img.shields.io/badge/Database-SQLite-003B57)
![Three.js](https://img.shields.io/badge/Three.js-r128-000000)
![License](https://img.shields.io/badge/License-MIT-green)

高校新生集中报到长期存在**流程冗长、信息重复采集、部门协同效率低**等问题。本项目设计并实现了一套面向高校迎新业务的一站式服务系统：后端以 Python Flask 为核心，通过 Flask-Login 实现基于角色的会话管理与接口权限拦截，数据持久化采用 SQLite；前端在原生 JavaScript 基础上引入 Three.js 构建三维校园漫游场景，并使用百度地图 JavaScript API 实现二维地图导航与路径规划；系统的关键创新点是将**通义千问 VL 多模态大模型**应用于证件信息采集环节，通过图像理解直接抽取身份证与录取通知书中的姓名、身份证号、专业、学号等字段，将证件信息录入由分钟级缩短至秒级。

> 本仓库为毕业设计《基于多模态OCR的智慧迎新系统设计与实现》的工程实现，系统设计文档、测试报告与图表见 [`docs/`](docs/)。

## 功能概览

| 模块 | 主要功能点 | 面向角色 |
| --- | --- | --- |
| 用户认证与权限管理 | 注册、登录、会话保持、基于角色的接口拦截 | 全部角色 |
| 智能信息填报 | 证件图像上传、多模态识别、字段回填、人工校正 | 新生 |
| 报到流程引擎 | 进度展示、步骤推进、前置条件校验、回退与资源释放 | 新生 |
| 宿舍资源管理 | 按性别筛选宿舍、床位状态展示、选床与退宿 | 新生、管理员 |
| 校园导览 | 二维地图导航与路径规划、三维场景漫游、地点检索 | 新生 |
| 后台管理与监控 | 全量数据查询、打回重填、班级统计 | 辅导员、管理员 |
| 实时交流社区 | 消息收发、角色样式渲染、轮询刷新、内容转义 | 全部角色 |

## 系统架构

系统采用三层 B/S 架构：页面由服务端 Jinja2 模板渲染，前端通过 Ajax 调用 JSON 接口获取数据，三维与地图资源在浏览器端渲染。

```text
┌──────────────────────────────────────────────────────────────┐
│ 表现层                                                        │
│  Jinja2 模板 + 原生 JavaScript/Fetch                          │
│  Three.js 三维校园场景      百度地图 JavaScript API 二维导航   │
├──────────────────────────────────────────────────────────────┤
│ 业务逻辑层                                                     │
│  Flask 路由 → 流程校验 / 床位分配 / 权限判定 / 识别服务调用      │
│  Flask-Login 会话管理 + 角色装饰器（admin / counselor）        │
├──────────────────────────────────────────────────────────────┤
│ 数据层                                                        │
│  SQLite（sqlite3）：user / student / dorm / bed / payment /   │
│  chat_message 共 6 张业务表                                    │
└──────────────────────────────────────────────────────────────┘
```

![系统总体架构图](<docs/figures/图3-1 系统总体架构图.png>)

功能模块划分与用例分析见下图，详细说明见[系统设计文档](docs/系统设计.md)。

<img src="docs/figures/图3-2 系统功能模块图.png" alt="系统功能模块图" width="420">
<img src="docs/figures/图2-1 系统用例图.png" alt="系统用例图" width="420">

## 报到流程状态机

报到业务被抽象为五个递进状态，由 `student.flow_step` 字段统一控制，所有推进与回退都需通过服务端前置校验：

| 步骤 | 状态 | 进入条件 | 推进后关联动作 |
| --- | --- | --- | --- |
| 1 | 信息填报 | — | 保存档案并将步骤推进至 2 |
| 2 | 资格审核 | 已提交完整的姓名、身份证号等字段 | 完成选床后将步骤推进至 3 |
| 3 | 宿舍分配 | 已在 `bed` 表中绑定床位 | 完成缴费后可推进至 4 / 5 |
| 4 | 缴费确认 | — | 缴费记录 `status = paid` 后可推进至 5 |
| 5 | 报到完成 | 最新缴费记录为已支付 | — |

关键规则：

- **禁止跳步**：目标步骤大于 `当前步骤 + 1` 时直接拒绝，提示“请按顺序完成步骤”。
- **资源联动**：流程回退到步骤 1/2 时，在同一事务内释放该生已占用的床位。
- **弱依赖降级**：识别服务不可用时返回内置模拟数据，保证填报与演示流程不中断。

## 技术栈

| 层次 | 技术选型 | 说明 |
| --- | --- | --- |
| 后端框架 | Python / Flask | 路由分发、模板渲染、JSON 接口 |
| 会话与权限 | Flask-Login + 自定义装饰器 | 学生 / 辅导员 / 管理员三级权限隔离 |
| 数据持久化 | SQLite + 标准库 `sqlite3` | 事务提交保证选床一致性 |
| 图像识别 | 通义千问 VL（`qwen-vl-plus`） | 证件结构化字段抽取，含 JSON 片段容错解析 |
| 三维渲染 | Three.js + OrbitControls + CSS2DRenderer | 本地静态资源，经 importmap 加载，不依赖 CDN |
| 二维地图 | 百度地图 JavaScript API | 驾车 / 步行 / 骑行三种路径规划 |
| 前端 | 原生 JavaScript + Jinja2 模板 | 全局请求封装、Toast 提示、HTML 转义 |

## 快速开始

### 环境要求

- Python 3.9 及以上（已在 Python 3.12 验证）
- 现代浏览器（Chrome / Edge / Firefox / Safari）

### 安装与运行

```powershell
git clone <your-repo-url>
cd smart-freshman-enrollment

python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

python seed_data.py   # 初始化演示数据（会重置 demo.db）
python app.py
```

浏览器访问 <http://127.0.0.1:5000>。Windows 环境也可直接运行一键脚本：

```powershell
.\start.ps1
```

### 演示账号

| 角色 | 账号 | 密码 | 登录后入口 |
| --- | --- | --- | --- |
| 学生 | `2024001` | `123456` | `/dashboard` |
| 辅导员 | `cs1` | `123456` | `/counselor_dashboard`（对应“软件工程1班”） |
| 管理员 | `admin` | `admin123` | `/admin_dashboard` |

### 可选配置

复制 `.env.example` 为 `.env` 后按需填写（`.env` 已被 `.gitignore` 忽略）：

| 变量 | 作用 | 缺省行为 |
| --- | --- | --- |
| `DASHSCOPE_API_KEY` | 通义千问 VL 识别接口凭证 | 留空时使用内置模拟数据 |
| `BAIDU_MAP_AK` | 百度地图浏览器端 AK | 留空时二维导航页无法加载底图 |
| `SECRET_KEY` | Flask 会话密钥 | 使用演示默认值，公网部署务必替换 |
| `DATABASE_PATH` | 数据库文件路径 | 项目根目录下的 `demo.db` |

## 项目结构

```text
smart-freshman-enrollment/
├─ app.py                     # Flask 应用入口：页面路由 + 业务接口
├─ config.py                  # 配置读取（环境变量 / .env）
├─ database.py                # 表结构定义与连接管理
├─ seed_data.py               # 演示数据生成脚本
├─ update_flow_step.py        # 调试用：手动调整学生报到步骤
├─ requirements.txt
├─ start.ps1                  # Windows 一键启动脚本
├─ demo.db                    # 演示数据库（由 seed_data.py 生成）
├─ .env.example               # 配置模板
├─ static/
│  ├─ css/style.css
│  └─ js/
│     ├─ app.js               # 全局请求封装、Toast、HTML 转义
│     ├─ three-scene.js       # 三维校园场景构建与交互
│     └─ vendor/              # Three.js / OrbitControls / CSS2DRenderer
├─ templates/                 # Jinja2 页面模板（含公共导航栏 _navbar.html）
└─ docs/
   ├─ 系统设计.md
   ├─ 数据库设计.md
   ├─ API接口.md
   ├─ 测试报告.md
   ├─ 优化方案.md
   ├─ 参考文献.md
   ├─ figures/                # 用例图、架构图、功能模块图、E-R 图
   └─ references/             # 开题报告（脱敏版）
```

## 主要接口

完整参数、返回值与调用示例见 [API 接口文档](docs/API接口.md)。

| 接口 | 方法 | 功能 | 权限 |
| --- | --- | --- | --- |
| `/login` | POST | 用户登录，返回角色对应跳转地址 | 公开 |
| `/register` | POST | 用户注册 | 公开 |
| `/api/ocr` | POST | 证件图像多模态识别 | 登录 |
| `/api/report` | POST | 提交 / 更新个人信息，推进至步骤 2 | 登录 |
| `/api/report/status` | GET / POST | 查询或推进报到流程 | 登录 |
| `/api/dorms` | GET | 按性别查询宿舍与床位 | 登录 |
| `/api/select_bed` | POST | 选择床位（二次校验 + 事务） | 登录 |
| `/api/cancel_bed` | POST | 退宿并释放床位 | 登录 |
| `/api/pay` | POST | 提交缴费状态（模拟） | 登录 |
| `/api/campus` | GET | 获取校园地点、道路与漫游顺序 | 登录 |
| `/api/chat/messages` | GET | 拉取聊天消息 | 登录 |
| `/api/chat/send` | POST | 发送聊天消息 | 登录 |
| `/api/admin/students` | GET | 全量学生数据（含缴费与住宿） | 管理员 |
| `/api/admin/student/<id>/reject` | POST | 打回重填并释放床位 | 管理员 |
| `/api/counselor/students` | GET | 按班级查询本班学生 | 辅导员 |

## 数据库设计

数据模型围绕“学生—宿舍—床位—缴费”主线展开，同时对账号与聊天消息建模，共 6 张表。

![系统E-R图](<docs/figures/图3-3 系统E-R图.png>)

| 表名 | 说明 | 关键字段 |
| --- | --- | --- |
| `user` | 账号与角色 | `username`、`password_hash`、`role` |
| `student` | 学生档案（业务核心） | `student_id`、`flow_step`、`bed_id`、`dorm_id` |
| `dorm` | 宿舍楼栋与房间 | `building`、`room_number`、`gender_limit` |
| `bed` | 床位与占用状态 | `dorm_id`、`bed_number`、`status`、`student_id` |
| `payment` | 缴费记录 | `student_id`、`amount`、`status`、`pay_time` |
| `chat_message` | 聊天消息 | `sender_username`、`sender_role`、`content` |

字段级说明与建表语句见 [数据库设计文档](docs/数据库设计.md)。

## 关键实现

### 1. 多模态证件识别与容错

提示词中固定字段名与 JSON 结构，后端对模型返回文本做“定位 + 截取”式解析，解析失败或接口异常时降级为模拟数据，页面仍可手工填写：

```python
prompt = """
请识别这张图片中的以下信息，以严格的JSON格式返回，不要包含任何其他文字：
{"name": "姓名", "id_card": "身份证号", "gender": "性别", "class_name": "班级",
 "major": "专业", "student_id": "学号", "contact": "联系电话"}
如果某项无法识别或不存在，请将该字段设为null。
"""

start, end = text.find("{"), text.rfind("}")
if start != -1 and end > start:
    ocr_data = json.loads(text[start:end + 1])
```

### 2. 流程状态机的前置校验

校验全部放在服务端，学生即使绕过前端按钮直接调用接口也无法跳步；回退时在同一事务内释放床位，避免“状态已回退但床位仍被占用”：

```python
if new_step > current_step + 1:
    return jsonify({'success': False, 'message': '请按顺序完成步骤'}), 400
if new_step == 3 and new_step > current_step and not bed_row['bed_id']:
    return jsonify({'success': False, 'message': '请先选择宿舍'}), 400
if new_step == 5 and new_step > current_step and pay_row['status'] != 'paid':
    return jsonify({'success': False, 'message': '请先完成缴费'}), 400
```

### 3. 并发选床的一致性控制

采用“**应用层二次校验 + 数据库事务**”策略：请求到达后重新读取床位状态，非空闲直接拒绝；仍空闲则在同一事务内更新床位表与学生表，并释放学生原有床位。20 并发请求同一床位的测试中，仅 1 个请求成功，未出现重复占用。

### 4. 经纬度到三维世界坐标的映射

三维场景不再写死场景中心，而是从 `/api/campus` 读取地点数据并动态计算中心点，按米制比例完成换算，新增或调整地点后无需修改坐标常量：

```javascript
const latScale = 111320;
const lngScale = 111320 * Math.cos(center.lat * Math.PI / 180);
```

### 5. 安全与工程化

- 口令以加盐哈希存储，数据库中不保留可逆明文；
- 除登录与注册外的接口统一由 `@login_required` 拦截，管理端与辅导员端接口叠加角色装饰器；
- 辅导员接口仅返回其管辖班级学生，学生端接口不返回他人隐私字段；
- 聊天内容在存储与展示环节均做 HTML 转义，避免脚本注入；
- 公共导航栏、Toast 提示与请求封装抽取为公共模板与全局脚本，三维依赖全部本地化。

## 测试结果

功能测试共执行 32 个用例，首次通过 30 个（93.75%），补充识别接口的异常捕获与 30 秒超时后回归全部通过。代表性结果：

| 编号 | 测试项 | 预期结果 | 结果 |
| --- | --- | --- | --- |
| FT-001 | 正确账号密码登录 | 跳转对应仪表板 | 通过 |
| FT-002 | 上传清晰身份证照片 | 自动抽取并回填字段 | 通过 |
| FT-010 | 步骤 2 直接点击“报到完成” | 被拦截并提示按顺序完成 | 通过 |
| FT-011 | 两个浏览器同时选择同一床位 | 一个成功，另一个提示已占用 | 通过 |
| FT-012 | 学生直接访问管理端路由 | 返回禁止访问状态码 | 通过 |
| FT-013 | 管理员执行打回重填 | 流程回到步骤 1 且床位被释放 | 通过 |

| 接口 | 功能 | 平均响应时间 | 最大响应时间 |
| --- | --- | --- | --- |
| `/api/dorms` | 查询可用宿舍列表 | 85 ms | 143 ms |
| `/api/select_bed` | 选择床位 | 96 ms | 187 ms |
| `/api/report/status` | 查询报到状态 | 62 ms | 118 ms |
| `/api/chat/messages` | 拉取最新消息 | 54 ms | 102 ms |
| `/api/ocr` | 证件图像识别 | 3.2 s | 5.1 s |

完整用例与环境配置见 [测试报告](docs/测试报告.md)。

## 文档索引

| 文档 | 内容 |
| --- | --- |
| [系统设计](docs/系统设计.md) | 架构设计、模块划分、流程状态机、关键实现 |
| [数据库设计](docs/数据库设计.md) | E-R 关系、6 张表的字段说明与建表语句 |
| [API 接口](docs/API接口.md) | 全部页面路由与业务接口的参数、返回值 |
| [测试报告](docs/测试报告.md) | 测试环境、功能用例、性能与并发结果 |
| [优化方案](docs/优化方案.md) | 三维场景与前后端问题的定位与改造记录 |
| [参考文献](docs/参考文献.md) | 17 篇中英文参考文献 |
| [开题报告（脱敏版）](docs/references/开题报告-脱敏版.pdf) | 毕业设计开题报告，已隐去个人与学校信息 |

## 已知限制与后续方向

- **支付渠道**：缴费目前为状态模拟，后续可对接微信支付 / 支付宝校园服务接口并通过回调写入缴费表；
- **实时通信**：聊天采用 5 秒轮询，可引入 WebSocket 服务端推送以降低延迟与无效请求；
- **识别依赖**：证件识别完全依赖云端模型，可增加端侧轻量识别作为补充；
- **服务扩展**：可将识别、聊天服务从主应用中拆分独立部署，数据库由 SQLite 迁移到更高并发的关系型数据库；
- **数据统计**：可增加报到实时大屏，展示各时段报到人数曲线、学院完成率排名与宿舍占用趋势。

## 作者与许可

- 作者：tyclie
- 许可证：[MIT](LICENSE)

本项目仅用于学习与研究，请勿将演示数据用于真实业务；部署到生产环境前请替换 `SECRET_KEY`、改用生产级 WSGI 服务器，并妥善保管第三方服务凭证。
