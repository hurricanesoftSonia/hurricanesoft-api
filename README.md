# HurricaneSoft Unified API Server

**HurricaneSoft API** 是一個輕量級、整合式的 REST API 伺服器，統一管理所有 HurricaneSoft 工具（Todo、Memo、記帳、公告、訊息、郵件、系統監控）。

- 🌀 **統一介面** — 單一 API 伺服器管理所有工具
- 🔒 **企業級認證** — 支援 LIDS（本地身份與目錄服務）
- 🗄️ **多資料庫支援** — SQLite（本地開發）、PostgreSQL（生產環境）
- 🌐 **Web Dashboard** — 內建網頁管理介面
- 📦 **多種部署方式** — Docker、.pyz、原始碼

---

## 快速開始

### 方式 1：使用 .pyz 單檔執行檔（推薦！）

```bash
# 下載 hurricanesoft-api.pyz
wget https://your-server/hurricanesoft-api.pyz
chmod +x hurricanesoft-api.pyz

# 啟動（預設 0.0.0.0:8080）
python3 hurricanesoft-api.pyz

# 或指定參數
python3 hurricanesoft-api.pyz --host 127.0.0.1 --port 9000 --static ./my-dashboard
```

### 方式 2：使用 Docker

```bash
# 使用 docker-compose（推薦）
docker-compose up -d

# 或手動啟動
docker build -t hurricanesoft-api .
docker run -d -p 8080:8080 \
  -v ~/.hurricanesoft:/root/.hurricanesoft \
  hurricanesoft-api
```

### 方式 3：從原始碼安裝

```bash
# Clone repository
git clone https://github.com/hurricanesoftSonia/hurricanesoft-api.git
cd hurricanesoft-api

# 安裝（開發模式）
pip install -e .

# 啟動
python -m hurricanesoft_api.server --port 8080
```

---

## 系統概述

### 架構

```
hurricanesoft-api
├── server.py          — HTTP 伺服器（Python stdlib http.server，無 Flask/FastAPI）
├── middleware.py      — 認證、CORS
├── routes/            — API 路由模組
│   ├── todo.py        — TodoTool 待辦事項
│   ├── memo.py        — MemoTool 備忘錄
│   ├── account.py     — AccounTool 記帳
│   ├── announce.py    — AnnounceTool 公告
│   ├── msg.py         — MsgTool 訊息
│   ├── mail.py        — MailTool 郵件
│   └── health.py      — HealthTool 系統監控
└── static/            — Web Dashboard（HTML/CSS/JS）
```

### 核心功能

| 工具 | API 前綴 | 功能 |
|------|----------|------|
| **TodoTool** | `/api/todo/*` | 待辦事項 CRUD、標籤、優先級、到期日提醒 |
| **MemoTool** | `/api/memo/*` | 備忘錄 CRUD、釘選、封存、全文搜尋 |
| **AccounTool** | `/api/account/*` | 記帳 CRUD、分類管理、月報表、統計分析、定期提醒 |
| **AnnounceTool** | `/api/announce/*` | 公告發布、收件人管理、已讀確認、提醒計數 |
| **MsgTool** | `/api/msg/*` | 站內訊息、收件匣、已發送、@提及、廣播、對話串 |
| **MailTool** | `/api/mail/*` | 郵件管理、收發信、搜尋、標籤、附件 |
| **HealthTool** | `/api/health/*` | 系統監控（CPU、記憶體、磁碟、網路） |

---

## 設定

### 設定檔位置

`~/.hurricanesoft/config.json`

### 範例設定

```json
{
  "db": {
    "backend": "sqlite",
    "sqlite_base": "~/.hurricanesoft/db/",
    "pg_host": "localhost",
    "pg_port": 5432,
    "pg_user": "hurricanesoft",
    "pg_password": "your_password",
    "pg_database": "hurricanesoft"
  },
  "lids": {
    "use_lids": false,
    "users_file": "~/.hurricanesoft/users.json",
    "api_keys_file": "~/.hurricanesoft/api_keys.json"
  },
  "mail": {
    "email": "your-email@example.com",
    "password": "your-mail-password",
    "pop3_host": "pop.example.com",
    "pop3_port": 995,
    "smtp_host": "smtp.example.com",
    "smtp_port": 465,
    "signature": "\n--\nBest regards,\nHurricaneSoft Team"
  }
}
```

### 資料庫選擇

#### SQLite（預設，適合個人/小團隊）

```json
{
  "db": {
    "backend": "sqlite",
    "sqlite_base": "~/.hurricanesoft/db/"
  }
}
```

#### PostgreSQL（推薦用於生產環境）

```json
{
  "db": {
    "backend": "postgresql",
    "pg_host": "your-db-host",
    "pg_port": 5432,
    "pg_user": "hurricanesoft",
    "pg_password": "your_password",
    "pg_database": "hurricanesoft"
  }
}
```

**注意**：PostgreSQL 需要手動建立資料庫和 schema（見 [DEPLOY.md](docs/DEPLOY.md)）。

---

## 認證

### LIDS 開啟時（企業模式）

所有 API 請求需帶 Bearer token：

```bash
curl -H "Authorization: Bearer your-api-key" \
  http://localhost:8080/api/todo/list
```

### LIDS 關閉時（個人模式）

不需要認證，直接存取：

```bash
curl http://localhost:8080/api/todo/list
```

**建議**：生產環境開啟 LIDS 並配合 HTTPS。

---

## API 端點

完整 API 文件請見 [docs/API.md](docs/API.md)。

### 快速參考

#### 系統資訊

- `GET /api` 或 `GET /api/version` — API 版本與端點列表

#### TodoTool

- `GET /api/todo/list` — 列出待辦事項
- `POST /api/todo/add` — 新增待辦
- `PUT /api/todo/<id>` — 編輯待辦
- `POST /api/todo/<id>/done` — 標記完成
- `GET /api/todo/tags` — 列出所有標籤
- `GET /api/todo/due` — 即將到期的待辦

#### MemoTool

- `GET /api/memo/list` — 列出備忘錄
- `POST /api/memo/add` — 新增備忘錄
- `PUT /api/memo/<id>` — 更新備忘錄
- `DELETE /api/memo/<id>` — 刪除備忘錄
- `POST /api/memo/<id>/pin` — 釘選
- `GET /api/memo/search` — 搜尋

#### AccounTool

- `GET /api/account/list` — 列出交易
- `POST /api/account/add` — 新增交易
- `GET /api/account/balance` — 目前餘額
- `GET /api/account/report` — 月報表
- `GET /api/account/categories` — 分類列表
- `POST /api/account/reminders` — 新增定期提醒

#### AnnounceTool

- `GET /api/announce/list` — 列出公告
- `POST /api/announce/add` — 發布公告
- `POST /api/announce/<id>/recipients` — 新增收件人
- `POST /api/announce/<id>/ack` — 確認已讀

#### MsgTool

- `GET /api/msg/inbox` — 收件匣
- `POST /api/msg/send` — 發送訊息
- `POST /api/msg/broadcast` — 廣播
- `GET /api/msg/mentions` — @提及我的訊息

#### MailTool

- `GET /api/mail/list` — 列出郵件
- `POST /api/mail/send` — 發送郵件
- `POST /api/mail/fetch` — 從伺服器抓取新郵件
- `GET /api/mail/search` — 搜尋郵件

#### HealthTool

- `GET /api/health/status` — 目前系統狀態
- `POST /api/health/run` — 執行健康檢查
- `GET /api/health/history` — 歷史記錄

---

## Web Dashboard

啟動伺服器時，Web Dashboard 會掛載在根路徑 `/`。

### 存取

開啟瀏覽器訪問：`http://localhost:8080`

### 功能

- 📋 **待辦事項管理** — 新增、編輯、標記完成、篩選
- 📝 **備忘錄管理** — 搜尋、釘選、封存
- 💰 **記帳管理** — 記錄收支、查看報表、分類統計
- 📢 **公告管理** — 發布、追蹤已讀狀態
- 💬 **訊息中心** — 收發站內訊息
- 📧 **郵件管理** — 收發郵件、管理標籤
- 📊 **系統監控** — CPU、記憶體、磁碟、網路即時狀態

### 自訂 Dashboard

```bash
# 使用自己的前端
python3 hurricanesoft-api.pyz --static /path/to/your/frontend/build
```

---

## 部署指南

請見 [docs/DEPLOY.md](docs/DEPLOY.md) 了解：

- 生產環境部署（Nginx + Gunicorn/uWSGI）
- PostgreSQL 設定與 schema 初始化
- SSL/HTTPS 設定
- 容器化部署（Docker/Kubernetes）
- 效能調校與監控

---

## 使用手冊

請見 [docs/USER-GUIDE.md](docs/USER-GUIDE.md) 了解：

- 各工具詳細使用方法
- 常見使用情境範例
- 整合其他服務（Telegram、Slack、Email）
- 故障排除

---

## 開發

### 專案結構

```
hurricanesoft_api/
├── __init__.py
├── __main__.py        — 允許 python -m hurricanesoft_api
├── server.py          — 主伺服器
├── middleware.py      — 認證與 CORS
├── setup.py           — 打包設定
├── routes/            — API 路由
│   ├── __init__.py
│   ├── todo.py
│   ├── memo.py
│   ├── account.py
│   ├── announce.py
│   ├── msg.py
│   ├── mail.py
│   └── health.py
├── static/            — Web Dashboard 前端
│   ├── index.html
│   ├── css/
│   └── js/
├── Dockerfile
└── docker-compose.yml
```

### 新增路由

1. 在 `routes/` 建立新模組（例如 `newtool.py`）
2. 定義 `handle(method, path, body, user)` 函數
3. 在 `server.py` 的 `ROUTE_MAP` 註冊路由前綴

範例：

```python
# routes/newtool.py
def handle(method, path, body, user):
    if method == 'GET':
        return 200, {'message': 'hello from newtool'}
    return 404, {'error': 'not found'}
```

```python
# server.py
ROUTE_MAP = {
    # ...
    '/api/newtool': 'hurricanesoft_api.routes.newtool',
}
```

### 測試

```bash
# 單元測試（TODO）
pytest

# 手動測試
python3 hurricanesoft-api.pyz --port 8080
curl http://localhost:8080/api/version
```

---

## 打包成 .pyz

使用 [shiv](https://github.com/linkedin/shiv) 打包成單檔執行檔：

```bash
# 安裝 shiv
pip install shiv

# 打包
shiv -c hurricanesoft-api -o hurricanesoft-api.pyz \
  ./hurricanesoft_api/ \
  ./hurricanesoft_cli/ \
  ./mailtool/ \
  ./todotool/ \
  ./memotool/ \
  ./msgtool/ \
  ./accountool/ \
  ./announcetool/ \
  ./healthtool/ \
  ./hurricanesoft_auth/

# 測試
python3 hurricanesoft-api.pyz --help
```

---

## 授權

MIT License

---

## 聯絡

- **作者**：Sonia
- **Email**：sonia@hurricanesoft.com.tw
- **GitHub**：[hurricanesoftSonia/hurricanesoft-api](https://github.com/hurricanesoftSonia/hurricanesoft-api)

---

## 更新日誌

### v0.1.0 (2026-02-13)

- ✨ 初版釋出
- 🌀 整合 7 個工具（Todo、Memo、Account、Announce、Msg、Mail、Health）
- 🔒 LIDS 認證支援
- 🗄️ SQLite + PostgreSQL 支援
- 🌐 Web Dashboard
- 📦 Docker + .pyz 部署方式
