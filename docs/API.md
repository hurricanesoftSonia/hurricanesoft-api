# HurricaneSoft API 文件

完整 REST API 端點說明。

---

## 目錄

1. [通用規則](#通用規則)
2. [認證](#認證)
3. [系統資訊](#系統資訊)
4. [TodoTool API](#todotool-api)
5. [MemoTool API](#memotool-api)
6. [AccounTool API](#accountool-api)
7. [AnnounceTool API](#announcetool-api)
8. [MsgTool API](#msgtool-api)
9. [MailTool API](#mailtool-api)
10. [HealthTool API](#healthtool-api)
11. [錯誤代碼](#錯誤代碼)

---

## 通用規則

### Base URL

```
http://localhost:8080
```

生產環境請使用 HTTPS：

```
https://api.hurricanesoft.com.tw
```

### 請求格式

- **Content-Type**: `application/json`
- **Method**: `GET`, `POST`, `PUT`, `DELETE`, `PATCH`

### 回應格式

所有回應均為 JSON 格式：

```json
{
  "id": 123,
  "message": "success"
}
```

錯誤回應：

```json
{
  "error": "error message"
}
```

### 日期時間格式

- **Date**: `YYYY-MM-DD`（例如 `2026-02-13`）
- **DateTime**: `YYYY-MM-DD HH:MM:SS`（例如 `2026-02-13 14:30:00`）

### CORS

所有端點支援 CORS，允許跨域請求。

---

## 認證

### LIDS 開啟時（企業模式）

所有請求需帶 Bearer token：

```bash
curl -H "Authorization: Bearer your-api-key" \
  http://localhost:8080/api/todo/list
```

### LIDS 關閉時（個人模式）

無需認證，直接存取。

### 取得 API Key

請聯絡系統管理員或在 `~/.hurricanesoft/api_keys.json` 手動建立。

---

## 系統資訊

### GET /api

取得 API 版本與端點列表。

**回應範例**：

```json
{
  "name": "hurricanesoft-api",
  "version": "0.1.0",
  "endpoints": [
    "/api/todo",
    "/api/memo",
    "/api/account",
    "/api/announce",
    "/api/msg",
    "/api/mail",
    "/api/health"
  ]
}
```

---

## TodoTool API

### GET /api/todo/list

列出待辦事項。

**Query Parameters**:

- `status` (optional): `pending`, `done`, `all`
- `tag` (optional): 標籤過濾
- `priority` (optional): `low`, `medium`, `high`
- `limit` (optional): 限制筆數（預設 50）

**範例**:

```bash
curl "http://localhost:8080/api/todo/list?status=pending&priority=high&limit=10"
```

**回應**:

```json
[
  {
    "id": 1,
    "title": "完成 API 文件",
    "status": "pending",
    "priority": "high",
    "due_date": "2026-02-15",
    "note": "包含所有端點說明",
    "created_at": "2026-02-13 10:00:00",
    "created_by": "sonia",
    "tags": "documentation,api"
  }
]
```

---

### GET /api/todo/{id}

取得單筆待辦事項。

**範例**:

```bash
curl http://localhost:8080/api/todo/1
```

**回應**:

```json
{
  "id": 1,
  "title": "完成 API 文件",
  "status": "pending",
  "priority": "high",
  "due_date": "2026-02-15",
  "note": "包含所有端點說明",
  "created_at": "2026-02-13 10:00:00",
  "created_by": "sonia",
  "tags": "documentation,api"
}
```

---

### POST /api/todo/add

新增待辦事項。

**Request Body**:

```json
{
  "title": "完成部署指南",
  "priority": "medium",
  "due_date": "2026-02-20",
  "note": "包含 Docker 和 Kubernetes",
  "tags": "documentation,deployment"
}
```

**回應**:

```json
{
  "id": 2,
  "message": "created"
}
```

---

### PUT /api/todo/{id}

編輯待辦事項。

**Request Body**:

```json
{
  "title": "完成部署指南（已更新）",
  "priority": "high",
  "note": "新增 Nginx 設定"
}
```

**回應**:

```json
{
  "message": "updated"
}
```

---

### POST /api/todo/{id}/done

標記待辦事項為完成。

**範例**:

```bash
curl -X POST http://localhost:8080/api/todo/1/done
```

**回應**:

```json
{
  "message": "marked done"
}
```

---

### GET /api/todo/{id}/history

取得待辦事項的變更歷史。

**回應**:

```json
[
  {
    "id": 1,
    "todo_id": 1,
    "action": "created",
    "changed_by": "sonia",
    "changed_at": "2026-02-13 10:00:00",
    "details": "待辦事項已建立"
  },
  {
    "id": 2,
    "todo_id": 1,
    "action": "updated",
    "changed_by": "sonia",
    "changed_at": "2026-02-13 11:00:00",
    "details": "優先級從 medium 改為 high"
  }
]
```

---

### GET /api/todo/tags

列出所有標籤。

**回應**:

```json
[
  {"tag": "documentation", "count": 5},
  {"tag": "api", "count": 3},
  {"tag": "deployment", "count": 2}
]
```

---

### GET /api/todo/due

列出即將到期的待辦事項。

**Query Parameters**:

- `days` (optional): 未來 N 天內到期（預設 7）

**範例**:

```bash
curl "http://localhost:8080/api/todo/due?days=3"
```

**回應**:

```json
[
  {
    "id": 1,
    "title": "完成 API 文件",
    "due_date": "2026-02-15",
    "priority": "high"
  }
]
```

---

## MemoTool API

### GET /api/memo/list

列出備忘錄。

**Query Parameters**:

- `tag` (optional): 標籤過濾
- `pinned` (optional): `1` 只顯示釘選
- `archived` (optional): `1` 只顯示封存
- `limit` (optional): 限制筆數（預設 50）

**範例**:

```bash
curl "http://localhost:8080/api/memo/list?pinned=1&limit=10"
```

**回應**:

```json
[
  {
    "id": 1,
    "title": "重要會議記錄",
    "body": "2026/02/13 討論 API 架構...",
    "created_at": "2026-02-13 09:00:00",
    "created_by": "sonia",
    "pinned": true,
    "archived": false,
    "tags": "meeting,important"
  }
]
```

---

### GET /api/memo/{id}

取得單筆備忘錄。

**範例**:

```bash
curl http://localhost:8080/api/memo/1
```

---

### POST /api/memo/add

新增備忘錄。

**Request Body**:

```json
{
  "title": "API 設計筆記",
  "body": "RESTful 設計原則：\n1. 使用標準 HTTP 方法\n2. ...",
  "tags": "api,design"
}
```

**回應**:

```json
{
  "id": 2,
  "message": "created"
}
```

---

### PUT /api/memo/{id}

更新備忘錄。

**Request Body**:

```json
{
  "title": "API 設計筆記（已更新）",
  "body": "新增內容..."
}
```

---

### DELETE /api/memo/{id}

刪除備忘錄。

**回應**:

```json
{
  "message": "deleted"
}
```

---

### POST /api/memo/{id}/pin

釘選備忘錄。

---

### POST /api/memo/{id}/unpin

取消釘選。

---

### POST /api/memo/{id}/archive

封存備忘錄。

---

### POST /api/memo/{id}/unarchive

取消封存。

---

### GET /api/memo/search

搜尋備忘錄（全文搜尋）。

**Query Parameters**:

- `q`: 搜尋關鍵字
- `limit` (optional): 限制筆數（預設 20）

**範例**:

```bash
curl "http://localhost:8080/api/memo/search?q=API&limit=5"
```

---

## AccounTool API

### GET /api/account/list

列出交易記錄。

**Query Parameters**:

- `start` (optional): 起始日期 `YYYY-MM-DD`
- `end` (optional): 結束日期
- `type` (optional): `income`, `expense`
- `category_id` (optional): 分類 ID
- `keyword` (optional): 關鍵字搜尋
- `limit` (optional): 限制筆數（預設 50）

**範例**:

```bash
curl "http://localhost:8080/api/account/list?type=expense&start=2026-02-01&end=2026-02-28"
```

**回應**:

```json
[
  {
    "id": 1,
    "date": "2026-02-13",
    "type": "expense",
    "amount": 150.00,
    "category_id": 5,
    "category_name": "午餐",
    "note": "與客戶餐敘",
    "created_at": "2026-02-13 12:30:00",
    "created_by": "sonia"
  }
]
```

---

### POST /api/account/add

新增交易。

**Request Body**:

```json
{
  "date": "2026-02-13",
  "type": "expense",
  "amount": 150.00,
  "category_id": 5,
  "note": "與客戶餐敘"
}
```

**回應**:

```json
{
  "id": 1,
  "message": "created"
}
```

---

### DELETE /api/account/{id}

刪除交易。

---

### GET /api/account/balance

取得目前餘額。

**回應**:

```json
{
  "balance": 125000.50,
  "total_income": 150000.00,
  "total_expense": 24999.50
}
```

---

### GET /api/account/report

月報表。

**Query Parameters**:

- `year`: 年份（例如 `2026`）
- `month`: 月份（例如 `2`）

**範例**:

```bash
curl "http://localhost:8080/api/account/report?year=2026&month=2"
```

**回應**:

```json
{
  "year": 2026,
  "month": 2,
  "total_income": 50000.00,
  "total_expense": 8500.00,
  "net": 41500.00,
  "by_category": [
    {"category": "薪資", "type": "income", "amount": 50000.00},
    {"category": "餐飲", "type": "expense", "amount": 3500.00},
    {"category": "交通", "type": "expense", "amount": 2000.00}
  ]
}
```

---

### GET /api/account/stats

分類統計。

**Query Parameters**:

- `start` (optional): 起始日期
- `end` (optional): 結束日期

**回應**:

```json
[
  {"category_id": 1, "category_name": "薪資", "type": "income", "total": 50000.00, "count": 1},
  {"category_id": 5, "category_name": "午餐", "type": "expense", "total": 3500.00, "count": 8}
]
```

---

### GET /api/account/categories

列出分類。

**Query Parameters**:

- `type` (optional): `income`, `expense`

**回應**:

```json
[
  {"id": 1, "name": "薪資", "type": "income", "description": "月薪"},
  {"id": 5, "name": "午餐", "type": "expense", "description": ""}
]
```

---

### POST /api/account/categories

新增分類。

**Request Body**:

```json
{
  "name": "獎金",
  "type": "income",
  "description": "年終獎金"
}
```

---

### GET /api/account/reminders

列出定期提醒。

**回應**:

```json
[
  {
    "id": 1,
    "name": "房租",
    "amount": 15000.00,
    "category_id": 10,
    "day_of_month": 1,
    "note": "每月 1 號繳房租",
    "active": true
  }
]
```

---

### POST /api/account/reminders

新增定期提醒。

**Request Body**:

```json
{
  "name": "房租",
  "amount": 15000.00,
  "category_id": 10,
  "day_of_month": 1,
  "note": "每月 1 號繳房租"
}
```

---

## AnnounceTool API

### GET /api/announce/list

列出公告。

**Query Parameters**:

- `priority` (optional): `low`, `normal`, `high`, `urgent`
- `archived` (optional): `1` 只顯示封存
- `limit` (optional): 限制筆數（預設 50）

**回應**:

```json
[
  {
    "id": 1,
    "title": "系統維護通知",
    "body": "2026/02/15 凌晨 2:00-4:00 進行系統維護",
    "priority": "high",
    "posted_at": "2026-02-13 10:00:00",
    "posted_by": "admin",
    "archived": false
  }
]
```

---

### GET /api/announce/{id}

取得單筆公告。

---

### POST /api/announce/add

發布公告。

**Request Body**:

```json
{
  "title": "系統維護通知",
  "body": "詳細內容...",
  "priority": "high"
}
```

---

### POST /api/announce/{id}/archive

封存公告。

---

### POST /api/announce/{id}/unarchive

取消封存。

---

### POST /api/announce/{id}/recipients

新增收件人。

**Request Body**:

```json
{
  "contacts": ["alice", "bob", "charlie"]
}
```

**回應**:

```json
{
  "message": "recipients added"
}
```

---

### GET /api/announce/{id}/recipients

取得收件人列表。

**回應**:

```json
[
  {
    "email": "alice@example.com",
    "is_read": false,
    "remind_count": 0,
    "read_at": null
  },
  {
    "email": "bob@example.com",
    "is_read": true,
    "remind_count": 0,
    "read_at": "2026-02-13 11:00:00"
  }
]
```

---

### POST /api/announce/{id}/ack

確認已讀。

**Request Body**:

```json
{
  "email": "alice@example.com"
}
```

---

### POST /api/announce/{id}/remind

增加提醒次數。

**Request Body**:

```json
{
  "email": "charlie@example.com"
}
```

---

### GET /api/announce/contacts

列出聯絡人。

**回應**:

```json
[
  {"name": "alice", "email": "alice@example.com"},
  {"name": "bob", "email": "bob@example.com"}
]
```

---

### POST /api/announce/contacts

新增聯絡人。

**Request Body**:

```json
{
  "name": "dave",
  "email": "dave@example.com"
}
```

---

### DELETE /api/announce/contacts/{name}

刪除聯絡人。

**範例**:

```bash
curl -X DELETE http://localhost:8080/api/announce/contacts/dave
```

---

## MsgTool API

### GET /api/msg/inbox

收件匣。

**Query Parameters**:

- `unread` (optional): `1` 只顯示未讀
- `limit` (optional): 限制筆數（預設 50）

**回應**:

```json
[
  {
    "id": 1,
    "from_user": "alice",
    "to_user": "sonia",
    "body": "你好，關於 API 設計有個問題...",
    "sent_at": "2026-02-13 10:30:00",
    "is_read": false,
    "read_at": null,
    "reply_to": null
  }
]
```

---

### GET /api/msg/sent

已發送訊息。

**Query Parameters**:

- `limit` (optional): 限制筆數（預設 50）

---

### GET /api/msg/{id}

取得單筆訊息。

---

### POST /api/msg/send

發送訊息。

**Request Body**:

```json
{
  "to": "alice",
  "body": "謝謝你的問題，我會盡快回覆。",
  "reply_to": 1
}
```

**回應**:

```json
{
  "id": 2,
  "message": "sent"
}
```

---

### POST /api/msg/broadcast

廣播訊息（發送給所有使用者）。

**Request Body**:

```json
{
  "body": "系統將於今晚維護，請提前保存工作。"
}
```

**回應**:

```json
{
  "count": 25,
  "message": "broadcast sent"
}
```

---

### POST /api/msg/{id}/read

標記訊息為已讀。

---

### GET /api/msg/{id}/thread

取得對話串。

**回應**:

```json
[
  {
    "id": 1,
    "from_user": "alice",
    "body": "原始訊息",
    "sent_at": "2026-02-13 10:30:00"
  },
  {
    "id": 2,
    "from_user": "sonia",
    "body": "回覆訊息",
    "sent_at": "2026-02-13 10:35:00",
    "reply_to": 1
  }
]
```

---

### GET /api/msg/mentions

提及我的訊息（@提及）。

**Query Parameters**:

- `limit` (optional): 限制筆數（預設 20）

---

### GET /api/msg/unread

未讀訊息數量。

**回應**:

```json
{
  "count": 3
}
```

---

### GET /api/msg/users

列出所有使用者。

**回應**:

```json
[
  {"username": "alice"},
  {"username": "bob"},
  {"username": "sonia"}
]
```

---

## MailTool API

### GET /api/mail/list

列出郵件。

**Query Parameters**:

- `folder` (optional): 資料夾（`inbox`, `sent`, `draft`，預設 `inbox`）
- `limit` (optional): 限制筆數（預設 20）
- `unread` (optional): `1` 只顯示未讀
- `read` (optional): `1` 只顯示已讀

**回應**:

```json
[
  {
    "id": 1,
    "message_id": "<unique-id@example.com>",
    "folder": "inbox",
    "from_addr": "client@example.com",
    "to_addr": "sonia@hurricanesoft.com.tw",
    "subject": "API 專案詢價",
    "body": "您好，我們對貴公司的 API 服務有興趣...",
    "received_at": "2026-02-13 09:00:00",
    "is_read": false,
    "labels": "important,客戶"
  }
]
```

---

### GET /api/mail/{id}

讀取郵件。

---

### POST /api/mail/{id}/read

標記為已讀。

---

### POST /api/mail/send

發送郵件。

**Request Body**:

```json
{
  "to": "client@example.com",
  "subject": "Re: API 專案詢價",
  "body": "感謝您的詢問...",
  "cc": "manager@hurricanesoft.com.tw",
  "bcc": null
}
```

**回應**:

```json
{
  "message": "sent"
}
```

---

### GET /api/mail/search

搜尋郵件。

**Query Parameters**:

- `q`: 搜尋關鍵字
- `limit` (optional): 限制筆數（預設 20）

**範例**:

```bash
curl "http://localhost:8080/api/mail/search?q=API"
```

---

### POST /api/mail/fetch

從郵件伺服器抓取新郵件。

**回應**:

```json
{
  "fetched": 5
}
```

---

### GET /api/mail/{id}/attachments

列出附件。

**回應**:

```json
[
  {
    "id": 1,
    "filename": "proposal.pdf",
    "content_type": "application/pdf",
    "size_bytes": 524288
  }
]
```

---

### POST /api/mail/{id}/label

新增標籤。

**Request Body**:

```json
{
  "label": "重要"
}
```

---

### DELETE /api/mail/{id}/label

移除標籤。

**Request Body**:

```json
{
  "label": "重要"
}
```

---

## HealthTool API

### GET /api/health/status

取得最新系統狀態。

**Query Parameters**:

- `machine` (optional): 機器名稱（預設當前主機）

**回應**:

```json
[
  {
    "id": 101,
    "machine": "server-01",
    "check_name": "cpu",
    "status": "ok",
    "detail": "CPU usage: 25%",
    "checked_at": "2026-02-13 12:00:00",
    "raw_data": {"usage": 25.3, "cores": 8}
  },
  {
    "id": 102,
    "machine": "server-01",
    "check_name": "memory",
    "status": "ok",
    "detail": "Memory usage: 60%",
    "checked_at": "2026-02-13 12:00:00"
  }
]
```

---

### POST /api/health/run

執行健康檢查（CPU、記憶體、磁碟、網路）。

**回應**:

```json
[
  {
    "name": "cpu",
    "status": "ok",
    "detail": "CPU usage: 25%",
    "usage": 25.3,
    "cores": 8
  },
  {
    "name": "memory",
    "status": "warning",
    "detail": "Memory usage: 85%",
    "total_mb": 16384,
    "used_mb": 13926,
    "free_mb": 2458
  },
  {
    "name": "disk",
    "status": "ok",
    "detail": "Disk usage: 45%",
    "path": "/",
    "total_gb": 500,
    "used_gb": 225,
    "free_gb": 275
  },
  {
    "name": "network",
    "status": "ok",
    "detail": "Network reachable"
  }
]
```

---

### GET /api/health/history

取得歷史記錄。

**Query Parameters**:

- `machine` (optional): 機器名稱
- `check` (optional): 檢查項目（`cpu`, `memory`, `disk`, `network`）
- `limit` (optional): 限制筆數（預設 100）
- `days` (optional): 近 N 天內（預設 30）

**範例**:

```bash
curl "http://localhost:8080/api/health/history?machine=server-01&check=cpu&days=7"
```

---

### GET /api/health/machines

列出所有監控的機器。

**回應**:

```json
[
  {"machine": "server-01", "last_check": "2026-02-13 12:00:00"},
  {"machine": "server-02", "last_check": "2026-02-13 11:55:00"}
]
```

---

## 錯誤代碼

| HTTP Code | 說明 |
|-----------|------|
| **200** | 成功 |
| **201** | 已建立（新增成功）|
| **400** | 錯誤請求（缺少必要參數或格式錯誤）|
| **401** | 未授權（認證失敗或缺少 token）|
| **403** | 禁止存取 |
| **404** | 找不到資源 |
| **500** | 伺服器內部錯誤 |

### 錯誤回應範例

```json
{
  "error": "title is required"
}
```

---

完整 API 文件到此結束。有問題請聯絡 sonia@hurricanesoft.com.tw 🌀
