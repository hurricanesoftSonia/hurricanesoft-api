# HurricaneSoft API 部署指南

完整部署指南，涵蓋開發、測試、生產環境。

---

## 目錄

1. [開發環境](#開發環境)
2. [生產環境部署](#生產環境部署)
3. [PostgreSQL 設定](#postgresql-設定)
4. [Nginx + SSL](#nginx--ssl)
5. [Docker 部署](#docker-部署)
6. [Kubernetes 部署](#kubernetes-部署)
7. [監控與日誌](#監控與日誌)
8. [備份與還原](#備份與還原)
9. [故障排除](#故障排除)

---

## 開發環境

### 1. Clone Repository

```bash
git clone https://github.com/hurricanesoftSonia/hurricanesoft-api.git
cd hurricanesoft-api
```

### 2. 安裝依賴

```bash
# 使用虛擬環境（推薦）
python3 -m venv venv
source venv/bin/activate

# 安裝（開發模式）
pip install -e .
pip install -e ../hurricanesoft_cli/
pip install -e ../todotool/
pip install -e ../memotool/
pip install -e ../accountool/
pip install -e ../announcetool/
pip install -e ../msgtool/
pip install -e ../mailtool/
pip install -e ../healthtool/
pip install -e ../hurricanesoft_auth/
```

### 3. 設定檔

建立 `~/.hurricanesoft/config.json`：

```json
{
  "db": {
    "backend": "sqlite",
    "sqlite_base": "~/.hurricanesoft/db/"
  },
  "lids": {
    "use_lids": false
  }
}
```

### 4. 啟動開發伺服器

```bash
python -m hurricanesoft_api.server --port 8080
```

開啟瀏覽器：`http://localhost:8080`

---

## 生產環境部署

### 方案 A：使用 .pyz（推薦！輕量快速）

#### 1. 打包

```bash
# 安裝 shiv
pip install shiv

# 打包成單檔執行檔
cd /path/to/workspace
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
```

#### 2. 部署到伺服器

```bash
# 複製到伺服器
scp hurricanesoft-api.pyz user@your-server:/opt/hurricanesoft/

# SSH 登入伺服器
ssh user@your-server

# 測試執行
python3 /opt/hurricanesoft/hurricanesoft-api.pyz --help
```

#### 3. 設定 systemd 服務

建立 `/etc/systemd/system/hurricanesoft-api.service`：

```ini
[Unit]
Description=HurricaneSoft Unified API Server
After=network.target

[Service]
Type=simple
User=hurricanesoft
WorkingDirectory=/opt/hurricanesoft
ExecStart=/usr/bin/python3 /opt/hurricanesoft/hurricanesoft-api.pyz --host 127.0.0.1 --port 8080
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

啟用並啟動服務：

```bash
sudo systemctl daemon-reload
sudo systemctl enable hurricanesoft-api
sudo systemctl start hurricanesoft-api
sudo systemctl status hurricanesoft-api
```

### 方案 B：從原始碼部署

```bash
# Clone repository
cd /opt
sudo git clone https://github.com/hurricanesoftSonia/hurricanesoft-api.git
cd hurricanesoft-api

# 安裝
sudo pip install -e .

# systemd 服務（同上，但 ExecStart 改為）
ExecStart=/usr/bin/python3 -m hurricanesoft_api.server --host 127.0.0.1 --port 8080
```

---

## PostgreSQL 設定

### 1. 安裝 PostgreSQL

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# CentOS/RHEL
sudo yum install postgresql-server postgresql-contrib
sudo postgresql-setup initdb
sudo systemctl enable postgresql
sudo systemctl start postgresql
```

### 2. 建立資料庫與使用者

**重要：由 DBA（Arianny）執行，工程師不自己建表！**

```bash
# 切換到 postgres 使用者
sudo -u postgres psql

# 建立資料庫與使用者
CREATE DATABASE hurricanesoft;
CREATE USER hurricanesoft_user WITH ENCRYPTED PASSWORD 'your_strong_password';
GRANT ALL PRIVILEGES ON DATABASE hurricanesoft TO hurricanesoft_user;
\q
```

### 3. 初始化 Schema

**工程師提供 SQL，DBA 執行**。

建立 `schema/init_pg.sql`（各工具的建表 SQL）：

```sql
-- TodoTool
CREATE TABLE IF NOT EXISTS todotool_todos (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    priority TEXT DEFAULT 'medium',
    due_date DATE,
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tags TEXT
);

CREATE TABLE IF NOT EXISTS todotool_history (
    id SERIAL PRIMARY KEY,
    todo_id INT REFERENCES todotool_todos(id) ON DELETE CASCADE,
    action TEXT NOT NULL,
    changed_by TEXT,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    details TEXT
);

-- MemoTool
CREATE TABLE IF NOT EXISTS memotool_memos (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    body TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    pinned BOOLEAN DEFAULT FALSE,
    archived BOOLEAN DEFAULT FALSE,
    tags TEXT
);

-- AccounTool
CREATE TABLE IF NOT EXISTS accountool_categories (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    type TEXT CHECK (type IN ('income', 'expense')),
    description TEXT
);

CREATE TABLE IF NOT EXISTS accountool_transactions (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    type TEXT CHECK (type IN ('income', 'expense')),
    amount NUMERIC(12, 2) NOT NULL,
    category_id INT REFERENCES accountool_categories(id),
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT
);

CREATE TABLE IF NOT EXISTS accountool_reminders (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    amount NUMERIC(12, 2),
    category_id INT REFERENCES accountool_categories(id),
    day_of_month INT CHECK (day_of_month >= 1 AND day_of_month <= 31),
    note TEXT,
    active BOOLEAN DEFAULT TRUE
);

-- AnnounceTool
CREATE TABLE IF NOT EXISTS announcetool_announcements (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    body TEXT,
    priority TEXT DEFAULT 'normal',
    posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    posted_by TEXT,
    archived BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS announcetool_contacts (
    name TEXT PRIMARY KEY,
    email TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS announcetool_recipients (
    id SERIAL PRIMARY KEY,
    announcement_id INT REFERENCES announcetool_announcements(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    remind_count INT DEFAULT 0,
    read_at TIMESTAMP
);

-- MsgTool
CREATE TABLE IF NOT EXISTS msgtool_messages (
    id SERIAL PRIMARY KEY,
    from_user TEXT NOT NULL,
    to_user TEXT NOT NULL,
    body TEXT NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP,
    reply_to INT REFERENCES msgtool_messages(id)
);

CREATE INDEX idx_msgtool_to_user ON msgtool_messages(to_user);
CREATE INDEX idx_msgtool_from_user ON msgtool_messages(from_user);

-- MailTool
CREATE TABLE IF NOT EXISTS mailtool_messages (
    id SERIAL PRIMARY KEY,
    message_id TEXT UNIQUE,
    folder TEXT DEFAULT 'inbox',
    from_addr TEXT,
    to_addr TEXT,
    subject TEXT,
    body TEXT,
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_read BOOLEAN DEFAULT FALSE,
    labels TEXT
);

CREATE TABLE IF NOT EXISTS mailtool_attachments (
    id SERIAL PRIMARY KEY,
    message_id INT REFERENCES mailtool_messages(id) ON DELETE CASCADE,
    filename TEXT,
    content_type TEXT,
    size_bytes INT,
    data BYTEA
);

-- HealthTool
CREATE TABLE IF NOT EXISTS healthtool_checks (
    id SERIAL PRIMARY KEY,
    machine TEXT NOT NULL,
    check_name TEXT NOT NULL,
    status TEXT,
    detail TEXT,
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    raw_data JSONB
);

CREATE INDEX idx_healthtool_machine ON healthtool_checks(machine);
CREATE INDEX idx_healthtool_time ON healthtool_checks(checked_at);
```

執行 SQL：

```bash
sudo -u postgres psql -d hurricanesoft -f schema/init_pg.sql
```

### 4. 更新設定檔

```json
{
  "db": {
    "backend": "postgresql",
    "pg_host": "localhost",
    "pg_port": 5432,
    "pg_user": "hurricanesoft_user",
    "pg_password": "your_strong_password",
    "pg_database": "hurricanesoft"
  },
  "lids": {
    "use_lids": true,
    "users_file": "~/.hurricanesoft/users.json",
    "api_keys_file": "~/.hurricanesoft/api_keys.json"
  }
}
```

### 5. 測試連線

```bash
python3 hurricanesoft-api.pyz --help
# 若無錯誤，表示 PG 連線成功
```

---

## Nginx + SSL

### 1. 安裝 Nginx

```bash
sudo apt install nginx
```

### 2. 設定反向代理

建立 `/etc/nginx/sites-available/hurricanesoft-api`：

```nginx
upstream hurricanesoft_backend {
    server 127.0.0.1:8080;
}

server {
    listen 80;
    server_name api.hurricanesoft.com.tw;

    # Redirect HTTP to HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.hurricanesoft.com.tw;

    # SSL 證書（使用 Let's Encrypt 或自己的證書）
    ssl_certificate /etc/letsencrypt/live/api.hurricanesoft.com.tw/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.hurricanesoft.com.tw/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # 日誌
    access_log /var/log/nginx/hurricanesoft-api.access.log;
    error_log /var/log/nginx/hurricanesoft-api.error.log;

    # Proxy settings
    location / {
        proxy_pass http://hurricanesoft_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (if needed in future)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # 靜態檔案快取（如果有 Web Dashboard）
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|woff|woff2|ttf)$ {
        proxy_pass http://hurricanesoft_backend;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

啟用並重啟 Nginx：

```bash
sudo ln -s /etc/nginx/sites-available/hurricanesoft-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 3. 設定 SSL（Let's Encrypt）

```bash
# 安裝 certbot
sudo apt install certbot python3-certbot-nginx

# 取得證書
sudo certbot --nginx -d api.hurricanesoft.com.tw

# 自動續約（cron）
sudo crontab -e
# 加入：
0 3 * * * certbot renew --quiet
```

---

## Docker 部署

### 1. 使用 docker-compose（推薦）

`docker-compose.yml`：

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8080:8080"
    volumes:
      - ~/.hurricanesoft:/root/.hurricanesoft
    environment:
      - HURRICANESOFT_DB_BACKEND=postgresql
      - HURRICANESOFT_PG_HOST=db
      - HURRICANESOFT_PG_USER=hurricanesoft
      - HURRICANESOFT_PG_PASSWORD=your_password
      - HURRICANESOFT_PG_DATABASE=hurricanesoft
    depends_on:
      - db
    restart: unless-stopped

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: hurricanesoft
      POSTGRES_PASSWORD: your_password
      POSTGRES_DB: hurricanesoft
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./schema/init_pg.sql:/docker-entrypoint-initdb.d/init.sql
    restart: unless-stopped

volumes:
  pgdata:
```

啟動：

```bash
docker-compose up -d
docker-compose logs -f api
```

### 2. 單獨執行容器

```bash
docker build -t hurricanesoft-api .
docker run -d \
  --name hurricanesoft-api \
  -p 8080:8080 \
  -v ~/.hurricanesoft:/root/.hurricanesoft \
  hurricanesoft-api
```

---

## Kubernetes 部署

### 1. Deployment

`k8s/deployment.yaml`：

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hurricanesoft-api
  namespace: hurricanesoft
spec:
  replicas: 3
  selector:
    matchLabels:
      app: hurricanesoft-api
  template:
    metadata:
      labels:
        app: hurricanesoft-api
    spec:
      containers:
      - name: api
        image: hurricanesoft/api:latest
        ports:
        - containerPort: 8080
        env:
        - name: HURRICANESOFT_DB_BACKEND
          value: "postgresql"
        - name: HURRICANESOFT_PG_HOST
          value: "postgres-service"
        - name: HURRICANESOFT_PG_USER
          valueFrom:
            secretKeyRef:
              name: hurricanesoft-db-secret
              key: username
        - name: HURRICANESOFT_PG_PASSWORD
          valueFrom:
            secretKeyRef:
              name: hurricanesoft-db-secret
              key: password
        volumeMounts:
        - name: config
          mountPath: /root/.hurricanesoft
      volumes:
      - name: config
        configMap:
          name: hurricanesoft-config
```

### 2. Service

`k8s/service.yaml`：

```yaml
apiVersion: v1
kind: Service
metadata:
  name: hurricanesoft-api
  namespace: hurricanesoft
spec:
  selector:
    app: hurricanesoft-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: LoadBalancer
```

部署：

```bash
kubectl apply -f k8s/
kubectl get pods -n hurricanesoft
```

---

## 監控與日誌

### 1. 日誌

#### systemd 日誌

```bash
sudo journalctl -u hurricanesoft-api -f
```

#### Nginx 日誌

```bash
tail -f /var/log/nginx/hurricanesoft-api.access.log
tail -f /var/log/nginx/hurricanesoft-api.error.log
```

### 2. 監控（使用 HealthTool）

設定定期健康檢查：

```bash
# crontab
*/5 * * * * curl -X POST http://localhost:8080/api/health/run
```

查看狀態：

```bash
curl http://localhost:8080/api/health/status
```

---

## 備份與還原

### SQLite 備份

```bash
# 備份
cp ~/.hurricanesoft/db/*.db /backup/

# 還原
cp /backup/*.db ~/.hurricanesoft/db/
```

### PostgreSQL 備份

```bash
# 備份
pg_dump -U hurricanesoft_user hurricanesoft > hurricanesoft_backup.sql

# 還原
psql -U hurricanesoft_user hurricanesoft < hurricanesoft_backup.sql
```

---

## 故障排除

### API 無法啟動

1. 檢查 log：`sudo journalctl -u hurricanesoft-api`
2. 檢查 port 是否被占用：`sudo lsof -i:8080`
3. 檢查設定檔：`cat ~/.hurricanesoft/config.json`

### 資料庫連線失敗

1. 檢查 PostgreSQL 是否啟動：`sudo systemctl status postgresql`
2. 檢查連線參數：`psql -U hurricanesoft_user -d hurricanesoft`
3. 檢查防火牆：`sudo ufw status`

### 認證失敗

1. 檢查 LIDS 設定：`cat ~/.hurricanesoft/api_keys.json`
2. 檢查 token：`curl -H "Authorization: Bearer your-token" http://localhost:8080/api/version`

---

## 效能調校

### 1. 使用 Gunicorn（生產環境推薦）

```bash
pip install gunicorn

# 啟動（4 workers）
gunicorn -w 4 -b 127.0.0.1:8080 hurricanesoft_api.server:app
```

### 2. Nginx 快取

```nginx
# 在 Nginx 加入快取設定
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=hurricanesoft_cache:10m max_size=100m;

location /api/ {
    proxy_cache hurricanesoft_cache;
    proxy_cache_valid 200 5m;
    # ...
}
```

---

完成！你的 HurricaneSoft API 現在已經在生產環境運行了 🎉
