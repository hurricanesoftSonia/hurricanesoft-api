# HurricaneSoft Unified API Server

統一 REST API，整合所有 HurricaneSoft 工具。

## 快速開始

```bash
# 安裝
pip install -e .

# 啟動
python -m hurricanesoft_api --port 8080

# 或用 Docker
docker-compose up -d
```

## API 端點

| 前綴 | 工具 | 說明 |
|------|------|------|
| `/api/todo/*` | TodoTool | 待辦事項 CRUD |
| `/api/memo/*` | MemoTool | 備忘錄 CRUD |
| `/api/account/*` | AccounTool | 記帳 CRUD |
| `/api/announce/*` | AnnounceTool | 公告 CRUD + ack/remind |
| `/api/msg/*` | MsgTool | 訊息 inbox/send/read |
| `/api/health/*` | HealthTool | 系統監控 |
| `/api/mail/*` | MailTool | Email 管理 |
| `/api/version` | — | API 版本資訊 |

## 認證

設定檔 `~/.hurricanesoft/config.json` 中 `lids.use_lids` 為 `true` 時，需帶 Bearer token：

```
Authorization: Bearer <token>
```

LIDS 關閉時不需要認證。

## 設定

讀取 `~/.hurricanesoft/config.json`，支援 SQLite 和 PostgreSQL。

## CORS

所有 API 回應包含 CORS headers，支援 Web Dashboard 跨域存取。

## 靜態檔案

`--static <dir>` 參數指定 Web Dashboard 靜態檔案目錄，掛載在 `/` 路徑。支援 SPA fallback。
