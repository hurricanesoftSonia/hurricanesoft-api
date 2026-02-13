# HurricaneSoft API 使用手冊

給一般使用者的完整使用指南。

---

## 目錄

1. [開始使用](#開始使用)
2. [待辦事項管理](#待辦事項管理-todotool)
3. [備忘錄管理](#備忘錄管理-memotool)
4. [記帳管理](#記帳管理-accountool)
5. [公告系統](#公告系統-announcetool)
6. [站內訊息](#站內訊息-msgtool)
7. [郵件管理](#郵件管理-mailtool)
8. [系統監控](#系統監控-healthtool)
9. [整合應用](#整合應用)
10. [常見問題](#常見問題)

---

## 開始使用

### 存取方式

#### 1. Web Dashboard（推薦）

開啟瀏覽器訪問：

```
http://localhost:8080
```

或生產環境：

```
https://api.hurricanesoft.com.tw
```

#### 2. 命令列（curl）

```bash
# 查看 API 版本
curl http://localhost:8080/api/version

# 列出待辦事項
curl http://localhost:8080/api/todo/list
```

#### 3. 程式整合（Python 範例）

```python
import requests

API_BASE = "http://localhost:8080"

# 列出待辦事項
response = requests.get(f"{API_BASE}/api/todo/list")
todos = response.json()

for todo in todos:
    print(f"[{todo['priority']}] {todo['title']}")
```

---

## 待辦事項管理 (TodoTool)

### 情境 1：新增待辦事項

**Web Dashboard**：

1. 點擊「待辦事項」
2. 點擊「新增」按鈕
3. 填寫標題、優先級、到期日、標籤
4. 點擊「儲存」

**命令列**：

```bash
curl -X POST http://localhost:8080/api/todo/add \
  -H "Content-Type: application/json" \
  -d '{
    "title": "完成季度報告",
    "priority": "high",
    "due_date": "2026-02-28",
    "tags": "work,report"
  }'
```

### 情境 2：查看即將到期的待辦

**Web Dashboard**：

點擊「即將到期」篩選器。

**命令列**：

```bash
# 查看未來 3 天內到期的待辦
curl "http://localhost:8080/api/todo/due?days=3"
```

### 情境 3：標記完成

**Web Dashboard**：

勾選待辦事項旁的核取方塊。

**命令列**：

```bash
curl -X POST http://localhost:8080/api/todo/1/done
```

### 情境 4：依標籤篩選

```bash
curl "http://localhost:8080/api/todo/list?tag=work&status=pending"
```

### 使用技巧

- **優先級**：`high` > `medium` > `low`，高優先級會置頂
- **標籤**：用逗號分隔（例如 `work,urgent,report`）
- **到期日提醒**：系統會在到期前 1 天發送提醒（需設定）

---

## 備忘錄管理 (MemoTool)

### 情境 1：快速記錄想法

**Web Dashboard**：

1. 點擊「備忘錄」
2. 點擊「快速新增」
3. 輸入標題和內容
4. 按 `Ctrl+Enter` 快速儲存

**命令列**：

```bash
curl -X POST http://localhost:8080/api/memo/add \
  -H "Content-Type: application/json" \
  -d '{
    "title": "API 設計想法",
    "body": "考慮加入 GraphQL 支援...",
    "tags": "ideas,api"
  }'
```

### 情境 2：釘選重要備忘錄

**用途**：會議記錄、專案筆記、常用資訊

```bash
# 釘選
curl -X POST http://localhost:8080/api/memo/5/pin

# 取消釘選
curl -X POST http://localhost:8080/api/memo/5/unpin
```

### 情境 3：全文搜尋

**Web Dashboard**：

使用上方搜尋框輸入關鍵字。

**命令列**：

```bash
curl "http://localhost:8080/api/memo/search?q=API&limit=10"
```

### 情境 4：封存舊備忘錄

**用途**：保留但不顯示在主列表，保持介面整潔

```bash
curl -X POST http://localhost:8080/api/memo/3/archive
```

### 使用技巧

- **釘選**：重要資訊置頂，隨時查看
- **標籤**：分類管理（例如 `meeting`, `ideas`, `references`）
- **封存**：不刪除但隱藏，需要時可搜尋找回

---

## 記帳管理 (AccounTool)

### 情境 1：記錄日常開支

**Web Dashboard**：

1. 點擊「記帳」→「新增交易」
2. 選擇日期、類型（收入/支出）
3. 輸入金額、選擇分類
4. 填寫備註（可選）
5. 點擊「儲存」

**命令列**：

```bash
curl -X POST http://localhost:8080/api/account/add \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2026-02-13",
    "type": "expense",
    "amount": 85.00,
    "category_id": 3,
    "note": "午餐 - 便當"
  }'
```

### 情境 2：查看月報表

**Web Dashboard**：

1. 點擊「報表」
2. 選擇年份和月份
3. 查看收支統計、分類圖表

**命令列**：

```bash
curl "http://localhost:8080/api/account/report?year=2026&month=2"
```

**回應範例**：

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

### 情境 3：查看目前餘額

```bash
curl http://localhost:8080/api/account/balance
```

**回應**：

```json
{
  "balance": 125000.50,
  "total_income": 150000.00,
  "total_expense": 24999.50
}
```

### 情境 4：設定定期提醒

**用途**：房租、水電費、訂閱服務等固定支出

```bash
curl -X POST http://localhost:8080/api/account/reminders \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Netflix 訂閱",
    "amount": 390.00,
    "category_id": 8,
    "day_of_month": 5,
    "note": "每月 5 號扣款"
  }'
```

### 使用技巧

- **分類管理**：先建立常用分類（餐飲、交通、娛樂等），記帳更快速
- **備註欄位**：記錄詳細資訊，方便日後查詢
- **定期提醒**：避免忘記固定支出，可整合行事曆或通知
- **標籤搜尋**：使用 `keyword` 參數快速找到特定交易

---

## 公告系統 (AnnounceTool)

### 情境 1：發布全員公告

**適用於**：系統維護、重要通知、政策變更

**Web Dashboard**：

1. 點擊「公告」→「發布新公告」
2. 輸入標題和內容
3. 選擇優先級（`urgent`, `high`, `normal`, `low`）
4. 選擇收件人或群組
5. 點擊「發布」

**命令列**：

```bash
# 1. 發布公告
curl -X POST http://localhost:8080/api/announce/add \
  -H "Content-Type: application/json" \
  -d '{
    "title": "系統維護通知",
    "body": "2026/02/15 凌晨 2:00-4:00 進行系統維護，屆時服務暫停。",
    "priority": "high"
  }'

# 回應: {"id": 10, "message": "created"}

# 2. 新增收件人
curl -X POST http://localhost:8080/api/announce/10/recipients \
  -H "Content-Type: application/json" \
  -d '{
    "contacts": ["alice", "bob", "charlie", "全體員工"]
  }'
```

### 情境 2：追蹤已讀狀態

**Web Dashboard**：

在公告詳情頁面查看「已讀 / 未讀」列表。

**命令列**：

```bash
curl http://localhost:8080/api/announce/10/recipients
```

**回應**：

```json
[
  {"email": "alice@example.com", "is_read": true, "read_at": "2026-02-13 10:30:00"},
  {"email": "bob@example.com", "is_read": false, "remind_count": 1},
  {"email": "charlie@example.com", "is_read": false, "remind_count": 0}
]
```

### 情境 3：提醒未讀收件人

```bash
curl -X POST http://localhost:8080/api/announce/10/remind \
  -H "Content-Type: application/json" \
  -d '{"email": "bob@example.com"}'
```

系統會增加 `remind_count`，可整合郵件或 Telegram 通知。

### 情境 4：收件人確認已讀

**收件人操作**：

```bash
curl -X POST http://localhost:8080/api/announce/10/ack \
  -H "Content-Type: application/json" \
  -d '{"email": "bob@example.com"}'
```

### 使用技巧

- **優先級**：`urgent` 會立即推播通知，`high` 置頂顯示
- **封存**：過期公告封存後不會顯示在主列表
- **整合通知**：結合 MailTool 或 Telegram 自動通知收件人

---

## 站內訊息 (MsgTool)

### 情境 1：發送訊息

**Web Dashboard**：

1. 點擊「訊息」→「撰寫」
2. 選擇收件人
3. 輸入內容
4. 點擊「發送」

**命令列**：

```bash
curl -X POST http://localhost:8080/api/msg/send \
  -H "Content-Type: application/json" \
  -d '{
    "to": "alice",
    "body": "你好，關於 API 專案有個問題想請教..."
  }'
```

### 情境 2：回覆訊息

```bash
curl -X POST http://localhost:8080/api/msg/send \
  -H "Content-Type: application/json" \
  -d '{
    "to": "alice",
    "body": "謝謝你的回覆！",
    "reply_to": 5
  }'
```

### 情境 3：廣播訊息

**用途**：重要通知、緊急訊息

```bash
curl -X POST http://localhost:8080/api/msg/broadcast \
  -H "Content-Type: application/json" \
  -d '{
    "body": "系統將於今晚 22:00 進行更新，請提前保存工作。"
  }'
```

### 情境 4：查看 @提及

**Web Dashboard**：

點擊「@提及」標籤頁。

**命令列**：

```bash
curl "http://localhost:8080/api/msg/mentions?limit=20"
```

### 情境 5：查看對話串

```bash
curl http://localhost:8080/api/msg/5/thread
```

顯示完整對話歷史（原始訊息 + 所有回覆）。

### 使用技巧

- **@提及**：訊息中包含 `@username` 會自動標記
- **已讀狀態**：系統自動追蹤，未讀訊息會高亮顯示
- **對話串**：使用 `reply_to` 保持對話脈絡

---

## 郵件管理 (MailTool)

### 情境 1：收取郵件

**Web Dashboard**：

點擊「郵件」→「收取新郵件」按鈕。

**命令列**：

```bash
curl -X POST http://localhost:8080/api/mail/fetch
```

**回應**：

```json
{
  "fetched": 5
}
```

### 情境 2：發送郵件

**Web Dashboard**：

1. 點擊「撰寫」
2. 填寫收件人、主旨、內容
3. （可選）填寫 CC、BCC
4. 點擊「發送」

**命令列**：

```bash
curl -X POST http://localhost:8080/api/mail/send \
  -H "Content-Type: application/json" \
  -d '{
    "to": "client@example.com",
    "subject": "專案報價單",
    "body": "您好，附件為專案報價單...",
    "cc": "manager@hurricanesoft.com.tw"
  }'
```

### 情境 3：搜尋郵件

```bash
curl "http://localhost:8080/api/mail/search?q=專案&limit=10"
```

### 情境 4：管理標籤

**用途**：分類郵件（重要、客戶、內部、待處理等）

```bash
# 新增標籤
curl -X POST http://localhost:8080/api/mail/15/label \
  -H "Content-Type: application/json" \
  -d '{"label": "重要"}'

# 移除標籤
curl -X DELETE http://localhost:8080/api/mail/15/label \
  -H "Content-Type: application/json" \
  -d '{"label": "重要"}'
```

### 使用技巧

- **定期抓取**：設定 cron job 每 10 分鐘自動抓取新郵件
- **標籤系統**：類似 Gmail，可多標籤分類
- **搜尋功能**：全文搜尋（主旨 + 內文）

---

## 系統監控 (HealthTool)

### 情境 1：查看系統狀態

**Web Dashboard**：

點擊「監控」查看即時 CPU、記憶體、磁碟、網路狀態。

**命令列**：

```bash
curl http://localhost:8080/api/health/status
```

**回應**：

```json
[
  {"check_name": "cpu", "status": "ok", "detail": "CPU usage: 25%"},
  {"check_name": "memory", "status": "warning", "detail": "Memory usage: 85%"},
  {"check_name": "disk", "status": "ok", "detail": "Disk usage: 45%"},
  {"check_name": "network", "status": "ok", "detail": "Network reachable"}
]
```

### 情境 2：執行健康檢查

```bash
curl -X POST http://localhost:8080/api/health/run
```

### 情境 3：查看歷史趨勢

```bash
# 查看 server-01 過去 7 天的 CPU 記錄
curl "http://localhost:8080/api/health/history?machine=server-01&check=cpu&days=7&limit=100"
```

### 情境 4：設定定期監控

**crontab 範例**：

```bash
# 每 5 分鐘執行一次健康檢查
*/5 * * * * curl -X POST http://localhost:8080/api/health/run
```

### 使用技巧

- **警告閥值**：CPU > 80%、記憶體 > 90%、磁碟 > 95% 會標記 `warning`
- **多機監控**：支援監控多台機器，依 `machine` 參數區分
- **整合告警**：結合 AnnounceTool 或 MsgTool 自動發送異常通知

---

## 整合應用

### 整合 1：Telegram 通知

**情境**：新公告、重要訊息、系統告警自動推播到 Telegram

**範例腳本**（Python）：

```python
import requests

API_BASE = "http://localhost:8080"
TELEGRAM_BOT_TOKEN = "your-bot-token"
TELEGRAM_CHAT_ID = "your-chat-id"

# 檢查未讀訊息
response = requests.get(f"{API_BASE}/api/msg/unread")
count = response.json()["count"]

if count > 0:
    # 發送 Telegram 通知
    message = f"⚠️ 你有 {count} 則未讀訊息"
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", json={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    })
```

### 整合 2：行事曆同步

**情境**：待辦事項到期日同步到 Google Calendar

**範例**：

```python
from googleapiclient.discovery import build
import requests

# 取得即將到期的待辦
todos = requests.get("http://localhost:8080/api/todo/due?days=7").json()

# 同步到 Google Calendar
service = build('calendar', 'v3', credentials=creds)
for todo in todos:
    event = {
        'summary': todo['title'],
        'start': {'date': todo['due_date']},
        'end': {'date': todo['due_date']},
    }
    service.events().insert(calendarId='primary', body=event).execute()
```

### 整合 3：Slack 通知

**情境**：系統健康檢查異常時發送 Slack 通知

```python
import requests

# 執行健康檢查
health = requests.post("http://localhost:8080/api/health/run").json()

# 檢查是否有 warning
warnings = [h for h in health if h['status'] == 'warning']

if warnings:
    # 發送 Slack 通知
    slack_webhook = "your-slack-webhook-url"
    message = "\n".join([f"⚠️ {w['name']}: {w['detail']}" for w in warnings])
    requests.post(slack_webhook, json={"text": message})
```

### 整合 4：自動備份

**情境**：每日自動備份資料庫

**crontab**：

```bash
0 3 * * * /usr/local/bin/backup-hurricanesoft.sh
```

**backup-hurricanesoft.sh**：

```bash
#!/bin/bash
DATE=$(date +%Y-%m-%d)
BACKUP_DIR="/backup/hurricanesoft"

mkdir -p $BACKUP_DIR

# SQLite 備份
cp ~/.hurricanesoft/db/*.db $BACKUP_DIR/$DATE/

# 或 PostgreSQL 備份
pg_dump -U hurricanesoft_user hurricanesoft > $BACKUP_DIR/$DATE/hurricanesoft.sql

# 保留 30 天
find $BACKUP_DIR -type d -mtime +30 -exec rm -rf {} \;
```

---

## 常見問題

### Q1: 忘記 API Key 怎麼辦？

**A**: 聯絡系統管理員重設，或手動編輯 `~/.hurricanesoft/api_keys.json`。

---

### Q2: 如何匯出資料？

**A**: 使用 API 匯出為 JSON，或直接備份資料庫檔案。

**範例**（匯出待辦事項）：

```bash
curl http://localhost:8080/api/todo/list?limit=1000 > todos.json
```

---

### Q3: 可以同時使用 SQLite 和 PostgreSQL 嗎？

**A**: 不行，同一時間只能選擇一種資料庫後端。建議開發用 SQLite，生產用 PostgreSQL。

---

### Q4: Web Dashboard 可以自訂嗎？

**A**: 可以！修改 `static/` 目錄下的 HTML/CSS/JS，或使用自己的前端框架（React、Vue）。

---

### Q5: 如何設定郵件伺服器？

**A**: 編輯 `~/.hurricanesoft/config.json`：

```json
{
  "mail": {
    "email": "your-email@example.com",
    "password": "your-password",
    "pop3_host": "pop.example.com",
    "pop3_port": 995,
    "smtp_host": "smtp.example.com",
    "smtp_port": 465
  }
}
```

---

### Q6: API 速率限制（Rate Limit）是多少？

**A**: 目前無速率限制。生產環境建議在 Nginx 層加入限制。

**Nginx 設定範例**：

```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

location /api/ {
    limit_req zone=api burst=20;
    # ...
}
```

---

### Q7: 如何備份/還原資料？

**A**: 

**SQLite**：

```bash
# 備份
cp ~/.hurricanesoft/db/*.db /backup/

# 還原
cp /backup/*.db ~/.hurricanesoft/db/
```

**PostgreSQL**：

```bash
# 備份
pg_dump -U hurricanesoft_user hurricanesoft > backup.sql

# 還原
psql -U hurricanesoft_user hurricanesoft < backup.sql
```

---

### Q8: 如何升級到新版本？

**A**:

**使用 .pyz**：

```bash
# 下載新版本
wget https://your-server/hurricanesoft-api-v0.2.0.pyz

# 停止服務
sudo systemctl stop hurricanesoft-api

# 替換檔案
sudo mv hurricanesoft-api-v0.2.0.pyz /opt/hurricanesoft/hurricanesoft-api.pyz

# 啟動服務
sudo systemctl start hurricanesoft-api
```

**使用 Docker**：

```bash
docker-compose pull
docker-compose up -d
```

---

### Q9: 系統支援多語言嗎？

**A**: 目前僅支援繁體中文和英文（API 端點和錯誤訊息）。未來版本會加入 i18n 支援。

---

### Q10: 可以在內網使用嗎？

**A**: 可以！只要內網機器能連線到 API 伺服器即可。建議設定 HTTPS 和 LIDS 認證。

---

## 結語

HurricaneSoft API 提供完整的工具整合，從待辦、備忘、記帳到訊息、郵件、監控，一站式管理。

有問題或建議？歡迎聯絡：

- **Email**: sonia@hurricanesoft.com.tw
- **GitHub**: [hurricanesoftSonia/hurricanesoft-api](https://github.com/hurricanesoftSonia/hurricanesoft-api)

🌀 讓我們一起打造更好的工作流程！
