# API 接口文档

本文档以当前代码（[`app.py`](../app.py)）为准，列出系统的页面路由与业务接口。除标注“公开”的接口外，其余接口均需登录，权限列使用 `登录 / 学生 / 辅导员 / 管理员` 表示最低角色要求。

## 1 通用约定

- **基础地址**：`http://127.0.0.1:5000`
- **数据格式**：请求体与响应体均为 JSON（文件上传接口除外）
- **统一响应结构**：

```json
{
  "success": true,
  "message": "操作结果说明"
}
```

业务数据放在 `data`、`students`、`dorms`、`messages`、`locations` 等字段中。失败响应同时返回非 2xx 状态码（400 参数或业务校验失败、401 未认证、403 越权、404 资源不存在）。

## 2 页面路由

| 路径 | 方法 | 页面 | 权限 |
| --- | --- | --- | --- |
| `/` | GET | 登录页（已登录则跳转仪表板） | 公开 |
| `/dashboard` | GET | 学生主面板 | 登录 |
| `/ocr_upload` | GET | 智能信息填报（证件识别） | 登录 |
| `/register_flow` | GET | 报到流程引导 | 登录 |
| `/dorm_selection` | GET | 宿舍选择 | 登录 |
| `/navigation` | GET | 二维地图导航 | 登录 |
| `/campus3d` | GET | 三维校园漫游 | 登录 |
| `/chat` | GET | 实时交流社区 | 登录 |
| `/admin_dashboard` | GET | 管理员后台 | 管理员 |
| `/counselor_dashboard` | GET | 辅导员后台 | 辅导员 |
| `/logout` | GET | 退出登录 | 登录 |

## 3 认证接口

### POST /login

登录成功后建立 Flask-Login 会话，并按角色返回跳转地址。

- 权限：公开
- 请求体：

```json
{ "username": "2024001", "password": "123456" }
```

- 响应：

```json
{ "success": true, "redirect": "/dashboard" }
```

| 角色 | 返回的跳转地址 |
| --- | --- |
| student | `/dashboard` |
| counselor | `/counselor_dashboard` |
| admin | `/admin_dashboard` |

账号或密码错误时返回 `401` 与 `{"success": false, "message": "账号或密码错误"}`。

### POST /register

- 权限：公开
- 请求体：

```json
{ "username": "2024005", "password": "123456", "role": "student" }
```

- 响应：`{"success": true, "message": "注册成功"}`；账号重复返回 `400` 与“账号已存在”。

> 注意：注册接口主要用于演示，生产环境应增加验证码、学号白名单与密码强度校验。

### GET /logout

清除会话并跳转回登录页。

## 4 智能信息填报

### POST /api/ocr

证件图像多模态识别，使用 `multipart/form-data` 上传。

- 权限：登录
- 请求参数：`file`（JPG / PNG 图像文件）
- 成功响应：

```json
{
  "success": true,
  "data": {
    "name": "张三",
    "id_card": "110101200001011234",
    "gender": "男",
    "class_name": "软件工程1班",
    "major": "计算机科学与技术",
    "student_id": "2024001",
    "contact": "13800138000"
  }
}
```

- 说明：未配置 `DASHSCOPE_API_KEY`、调用超时或返回结果无法解析时，接口自动返回内置模拟数据，保证填报流程不中断；识别结果仅回填表单，需人工核对后再提交。

### POST /api/report

提交或更新学生个人信息，成功后把流程推进到第 2 步（若当前步骤大于 2 则保持原步骤）。

- 权限：登录（学号取自当前会话用户）
- 请求体：

```json
{
  "name": "张三",
  "id_card": "110101200001011234",
  "gender": "男",
  "class_name": "软件工程1班",
  "major": "计算机科学与技术",
  "contact": "13800138000"
}
```

- 响应：`{"success": true, "message": "报到信息已保存"}`；姓名或身份证号为空时返回 `400`。

## 5 报到流程

### GET /api/report/status

查询当前学生的报到步骤。

- 权限：登录
- 响应：`{"success": true, "flow_step": 2}`

### POST /api/report/status

推进或回退报到步骤。

- 权限：登录
- 请求体：`{ "flow_step": 3 }`（取值 1~5）
- 校验规则：

  | 场景 | 校验 | 失败提示 |
  | --- | --- | --- |
  | 目标步骤 > 当前步骤 + 1 | 拒绝 | 请按顺序完成步骤 |
  | 推进到第 3 步 | 需已绑定床位 | 请先选择宿舍 |
  | 推进到第 5 步 | 需最新缴费记录为 `paid` | 请先完成缴费 |
  | 回退到第 1、2 步 | 自动释放已占用床位 | — |

- 响应：`{"success": true, "flow_step": 3}`

## 6 宿舍资源

### GET /api/dorms

按当前学生性别返回可选的宿舍与床位。

- 权限：登录
- 说明：未填报个人信息（学生表中无记录）时返回 `400`。
- 响应：

```json
{
  "success": true,
  "dorms": [
    {
      "dorm_id": 33,
      "building": "17栋",
      "room_number": "01",
      "gender_limit": "男",
      "bed_count": 4,
      "beds": [
        { "bed_id": 129, "bed_number": "1床", "status": "free", "student_id": null },
        { "bed_id": 130, "bed_number": "2床", "status": "occupied", "student_id": "2024001" }
      ]
    }
  ]
}
```

### POST /api/select_bed

选择床位。服务端二次校验床位状态与性别限制，并在同一事务内更新床位表、学生表与流程步骤。

- 权限：登录
- 请求体：`{ "bed_id": 129 }`
- 失败场景：床位不存在（404）、床位已被占用（400）、学生信息不存在（400）、性别不符（400）
- 响应：`{"success": true, "message": "宿舍选择成功"}`

### POST /api/cancel_bed

退宿：释放床位并把流程回退到第 2 步。

- 权限：登录
- 请求体：无
- 响应：`{"success": true, "message": "已取消选择，流程回退到资格审核"}`

## 7 缴费

### POST /api/pay

模拟缴费，把当前学生的缴费记录置为已支付（金额 5000 元）。

- 权限：登录
- 请求体：无
- 响应：`{"success": true, "message": "缴费成功"}`；已缴费时返回“已完成缴费”。

> 当前为状态模拟，未接入真实支付渠道，见[系统设计](系统设计.md)第 8 节。

## 8 校园导览

### GET /api/navigation

返回校园地点、道路连线、漫游顺序与百度地图 AK。

- 权限：公开
- 响应（节选）：

```json
{
  "success": true,
  "ak": "your-baidu-map-ak",
  "locations": [
    { "id": 1, "name": "校门口", "lng": 115.02739, "lat": 30.215162,
      "type": "gate", "desc": "校园主要出入口", "open": "全天开放",
      "color": "#8d6e63", "height": 12 }
  ],
  "roads": [[1, 8], [8, 7]],
  "tour_order": [1, 8, 7, 2, 3, 5, 4, 6, 1]
}
```

### GET /api/campus

为三维校园页面提供与导航一致的地点、道路与漫游顺序（响应中不含 `ak`）。

- 权限：公开

## 9 聊天社区

### GET /api/chat/messages

按时间顺序返回全部聊天消息。

- 权限：登录
- 响应：

```json
{
  "success": true,
  "messages": [
    { "id": 1, "sender_username": "admin", "sender_role": "admin",
      "content": "欢迎新同学！", "timestamp": "2025-08-01 09:00:00" }
  ]
}
```

### POST /api/chat/send

发送一条文本消息，发送者信息取自当前会话。

- 权限：登录
- 请求体：`{ "content": "请问宿舍怎么走？" }`
- 响应：`{"success": true}`；内容为空时返回 `400`。

## 10 后台接口

### GET /api/admin/students

返回全部学生档案，并关联缴费状态与住宿信息（宿舍楼栋、房间号、床位号）。

- 权限：管理员

### POST /api/admin/student/&lt;student_id&gt;/reject

把指定学生的档案打回重填：`status` 置为 `rejected`、流程回退到第 1 步，并释放其已占用的床位。

- 权限：管理员
- 响应：`{"success": true, "message": "已打回重填"}`

### GET /api/counselor/students

返回当前辅导员所辖班级的学生列表（演示账号 `cs1` 对应“软件工程1班”）。

- 权限：辅导员

## 11 调用示例

```javascript
// 登录
await fetch('/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username: '2024001', password: '123456' }),
});

// 上传证件图像
const form = new FormData();
form.append('file', fileInput.files[0]);
const res = await fetch('/api/ocr', { method: 'POST', body: form });
const { data } = await res.json();

// 选择床位
await fetch('/api/select_bed', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ bed_id: 129 }),
});
```
