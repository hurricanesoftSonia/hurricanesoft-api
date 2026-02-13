/* HurricaneSoft Dashboard SPA */
(function () {
  'use strict';

  let user = '', pass = '', currentPage = 'todo';
  let pollTimer = null;

  // --- Auth helpers ---
  function api(method, path, body) {
    const opts = { method, headers: { 'X-User': user, 'X-Password': pass } };
    if (body && method !== 'GET') {
      opts.headers['Content-Type'] = 'application/json';
      opts.body = JSON.stringify(body);
    }
    return fetch(path, opts).then(r => {
      if (r.status === 401) { doLogout(); throw new Error('未授權'); }
      return r.json();
    });
  }

  // --- Login ---
  window.doLogin = function () {
    user = document.getElementById('loginUser').value.trim();
    pass = document.getElementById('loginPass').value.trim();
    if (!user || !pass) { document.getElementById('loginError').textContent = '請輸入帳號密碼'; return; }
    api('GET', '/api/health/status').then(() => {
      document.getElementById('loginOverlay').style.display = 'none';
      document.getElementById('app').style.display = 'flex';
      document.getElementById('userName').textContent = user;
      go('dashboard');
      startPolling();
    }).catch(() => {
      document.getElementById('loginError').textContent = '登入失敗，請確認帳號密碼';
    });
  };
  window.doLogout = function () {
    user = ''; pass = '';
    stopPolling();
    document.getElementById('loginOverlay').style.display = '';
    document.getElementById('app').style.display = 'none';
    document.getElementById('loginPass').value = '';
    document.getElementById('loginError').textContent = '';
  };
  document.getElementById('loginPass').addEventListener('keydown', e => { if (e.key === 'Enter') doLogin(); });

  // --- Sidebar ---
  window.toggleSidebar = function () { document.getElementById('sidebar').classList.toggle('open'); };
  window.go = function (page) {
    currentPage = page;
    document.querySelectorAll('.nav-item').forEach(el => el.classList.toggle('active', el.dataset.page === page));
    document.getElementById('sidebar').classList.remove('open');
    const c = document.getElementById('content');
    c.innerHTML = '<div class="empty">載入中…</div>';
    pages[page] ? pages[page](c) : (c.innerHTML = '<div class="empty">頁面不存在</div>');
  };

  // --- Polling ---
  function startPolling() { stopPolling(); poll(); pollTimer = setInterval(poll, 8000); }
  function stopPolling() { if (pollTimer) { clearInterval(pollTimer); pollTimer = null; } }
  function poll() {
    api('GET', '/api/msg/inbox').then(d => {
      const n = d.unread || 0;
      const el = document.getElementById('badgeMsg');
      const elN = document.getElementById('badgeMsgN');
      if (n > 0) { el.style.display = ''; elN.textContent = n; } else { el.style.display = 'none'; }
    }).catch(() => {});
    api('GET', '/api/mail/list').then(d => {
      const msgs = d.messages || [];
      const n = msgs.filter(m => !m.read && !m.seen).length;
      const el = document.getElementById('badgeMail');
      const elN = document.getElementById('badgeMailN');
      if (n > 0) { el.style.display = ''; elN.textContent = n; } else { el.style.display = 'none'; }
    }).catch(() => {});
  }

  // --- Toast ---
  function toast(msg) {
    const d = document.createElement('div'); d.className = 'toast'; d.textContent = msg;
    document.body.appendChild(d); setTimeout(() => d.remove(), 2500);
  }

  // --- Utility ---
  function esc(s) { const d = document.createElement('div'); d.textContent = s || ''; return d.innerHTML; }
  function fmtDate(s) { if (!s) return ''; try { return new Date(s).toLocaleString('zh-TW'); } catch { return s; } }

  // ========== PAGE RENDERERS ==========
  const pages = {};

  // ----- DASHBOARD -----
  pages.dashboard = function (c) {
    api('GET', '/api/dashboard').then(d => {
      const todo = d.todo || {};
      const memo = d.memo || {};
      const msg = d.msg || {};
      const mail = d.mail || {};
      const announce = d.announce || {};
      const health = d.health || {};
      const system = d.system || {};
      
      let h = `<div class="dashboard-grid">
        <div class="dash-card" onclick="go('todo')">
          <div class="dash-icon">📋</div>
          <div class="dash-title">待辦事項</div>
          <div class="dash-stats">
            <span class="stat-pending">${todo.pending || 0} 未完成</span>
            <span class="stat-ok">${todo.completed || 0} 已完成</span>
          </div>
        </div>
        
        <div class="dash-card" onclick="go('memo')">
          <div class="dash-icon">📝</div>
          <div class="dash-title">備忘錄</div>
          <div class="dash-stats">
            <span class="stat-number">${memo.total || 0} 筆</span>
          </div>
        </div>
        
        <div class="dash-card" onclick="go('msg')">
          <div class="dash-icon">💬</div>
          <div class="dash-title">訊息</div>
          <div class="dash-stats">
            <span class="stat-alert">${msg.unread || 0} 未讀</span>
          </div>
        </div>
        
        <div class="dash-card" onclick="go('mail')">
          <div class="dash-icon">📧</div>
          <div class="dash-title">郵件</div>
          <div class="dash-stats">
            <span class="stat-alert">${mail.unread || 0} 未讀</span>
          </div>
        </div>
        
        <div class="dash-card" onclick="go('announce')">
          <div class="dash-icon">📢</div>
          <div class="dash-title">公告</div>
          <div class="dash-stats">
            <span class="stat-pending">${announce.pending || 0} 待確認</span>
          </div>
        </div>
        
        <div class="dash-card" onclick="go('health')">
          <div class="dash-icon">🏥</div>
          <div class="dash-title">系統健康</div>
          <div class="dash-stats">
            <span class="stat-${health.status === 'ok' || health.status === 'healthy' ? 'ok' : 'fail'}">${esc(health.status || 'unknown')}</span>
          </div>
        </div>
        
        <div class="dash-card" onclick="go('account')">
          <div class="dash-icon">💰</div>
          <div class="dash-title">記帳</div>
          <div class="dash-stats">
            <span class="stat-number">管理帳務</span>
          </div>
        </div>
        
        <div class="dash-card">
          <div class="dash-icon">⚙️</div>
          <div class="dash-title">系統資訊</div>
          <div class="dash-stats">
            <span class="stat-number">v${esc(system.version || '1.0')}</span>
            <span class="stat-number">${esc(system.uptime || '0h 0m')}</span>
          </div>
        </div>
      </div>`;
      c.innerHTML = h;
    }).catch(e => {
      c.innerHTML = `<div class="empty">無法載入儀表板: ${esc(e.message)}</div>`;
    });
  };

  // ----- TODO -----
  pages.todo = function (c) {
    let filter = 'all';
    function render(items) {
      const filtered = filter === 'all' ? items : filter === 'done' ? items.filter(i => i.done) : items.filter(i => !i.done);
      let h = `<div class="card"><h2>📋 待辦事項</h2>
        <div class="form-row"><input id="todoInput" placeholder="新增待辦…"><button class="btn btn-primary" onclick="window._todoAdd()">新增</button></div>
        <div class="tabs">
          <button class="tab ${filter==='all'?'active':''}" onclick="window._todoFilter('all')">全部</button>
          <button class="tab ${filter==='pending'?'active':''}" onclick="window._todoFilter('pending')">未完成</button>
          <button class="tab ${filter==='done'?'active':''}" onclick="window._todoFilter('done')">已完成</button>
        </div>`;
      if (!filtered.length) h += '<div class="empty">沒有項目</div>';
      filtered.forEach(i => {
        h += `<div class="list-item">
          <span class="title ${i.done?'done':''}">${esc(i.title || i.text || i.content)}</span>
          <span class="meta">${fmtDate(i.created || i.date)}</span>
          <button class="btn btn-sm ${i.done?'btn-danger':'btn-success'}" onclick="window._todoDone('${i.id}',${!i.done})">${i.done?'取消':'完成'}</button>
        </div>`;
      });
      h += '</div>';
      c.innerHTML = h;
      document.getElementById('todoInput').addEventListener('keydown', e => { if (e.key === 'Enter') window._todoAdd(); });
    }
    function load() { api('GET', '/api/todo/list').then(d => render(d.items || [])).catch(e => { c.innerHTML = `<div class="empty">錯誤: ${esc(e.message)}</div>`; }); }
    window._todoAdd = function () {
      const v = document.getElementById('todoInput').value.trim();
      if (!v) return;
      api('POST', '/api/todo/add', { title: v }).then(() => { toast('已新增'); load(); });
    };
    window._todoDone = function (id, done) {
      api('POST', '/api/todo/done', { id, done }).then(() => load());
    };
    window._todoFilter = function (f) { filter = f; load(); };
    load();
  };

  // ----- MEMO -----
  pages.memo = function (c) {
    let search = '';
    function render(items) {
      const filtered = search ? items.filter(i => (i.title || i.content || '').includes(search)) : items;
      let h = `<div class="card"><h2>📝 備忘錄</h2>
        <div class="form-row"><input id="memoTitle" placeholder="標題"><input id="memoBody" placeholder="內容" style="flex:2"><button class="btn btn-primary" onclick="window._memoAdd()">新增</button></div>
        <div class="form-row"><input id="memoSearch" placeholder="搜尋…" value="${esc(search)}" oninput="window._memoSearch(this.value)"></div>`;
      if (!filtered.length) h += '<div class="empty">沒有備忘錄</div>';
      filtered.forEach(i => {
        h += `<div class="list-item" style="cursor:pointer" onclick="window._memoRead('${i.id}')">
          <span class="title">${esc(i.title || '(無標題)')}</span>
          <span class="meta">${fmtDate(i.created || i.date)}</span>
        </div>`;
      });
      h += '</div><div id="memoDetail"></div>';
      c.innerHTML = h;
    }
    function load() { api('GET', '/api/memo/list').then(d => render(d.items || [])).catch(e => { c.innerHTML = `<div class="empty">錯誤</div>`; }); }
    window._memoAdd = function () {
      const t = document.getElementById('memoTitle').value.trim();
      const b = document.getElementById('memoBody').value.trim();
      if (!t && !b) return;
      api('POST', '/api/memo/add', { title: t, content: b }).then(() => { toast('已新增'); load(); });
    };
    window._memoSearch = function (v) { search = v; load(); };
    window._memoRead = function (id) {
      api('GET', `/api/memo/read/${id}`).then(d => {
        const i = d.item || d;
        document.getElementById('memoDetail').innerHTML = `<div class="card">
          <div class="detail-header"><h3>${esc(i.title)}</h3><div class="meta">${fmtDate(i.created || i.date)}</div></div>
          <div class="detail-body">${esc(i.content || i.body || '')}</div></div>`;
      });
    };
    load();
  };

  // ----- ACCOUNT -----
  pages.account = function (c) {
    let month = new Date().toISOString().slice(0, 7);
    function render(items) {
      const filtered = items.filter(i => (i.date || i.created || '').startsWith(month));
      const income = filtered.filter(i => i.type === 'income').reduce((s, i) => s + (i.amount || 0), 0);
      const expense = filtered.filter(i => i.type === 'expense').reduce((s, i) => s + (i.amount || 0), 0);
      let h = `<div class="card"><h2>💰 記帳</h2>
        <div class="form-row">
          <input id="accDesc" placeholder="說明"><input id="accAmt" type="number" placeholder="金額" style="width:100px">
          <select id="accType"><option value="expense">支出</option><option value="income">收入</option></select>
          <button class="btn btn-primary" onclick="window._accAdd()">新增</button>
        </div>
        <div class="form-row"><input type="month" id="accMonth" value="${month}" onchange="window._accMonth(this.value)"></div>
        <div style="display:flex;gap:20px;margin-bottom:16px">
          <span style="color:#27ae60;font-weight:600">收入: $${income.toLocaleString()}</span>
          <span style="color:#e74c3c;font-weight:600">支出: $${expense.toLocaleString()}</span>
          <span style="font-weight:700">淨額: $${(income - expense).toLocaleString()}</span>
        </div>`;
      if (!filtered.length) h += '<div class="empty">本月無紀錄</div>';
      filtered.forEach(i => {
        h += `<div class="list-item">
          <span class="title">${esc(i.description || i.desc || i.title)}</span>
          <span class="meta" style="color:${i.type==='income'?'#27ae60':'#e74c3c'};font-weight:600">${i.type==='income'?'+':'-'}$${(i.amount||0).toLocaleString()}</span>
          <span class="meta">${fmtDate(i.date || i.created)}</span>
        </div>`;
      });
      h += '</div>';
      c.innerHTML = h;
    }
    function load() { api('GET', '/api/account/list').then(d => render(d.items || [])).catch(() => { c.innerHTML = '<div class="empty">錯誤</div>'; }); }
    window._accAdd = function () {
      const desc = document.getElementById('accDesc').value.trim();
      const amt = parseFloat(document.getElementById('accAmt').value) || 0;
      const type = document.getElementById('accType').value;
      if (!desc || !amt) return;
      api('POST', '/api/account/add', { description: desc, amount: amt, type }).then(() => { toast('已新增'); load(); });
    };
    window._accMonth = function (v) { month = v; load(); };
    load();
  };

  // ----- ANNOUNCE -----
  pages.announce = function (c) {
    function render(items) {
      let h = `<div class="card"><h2>📢 公告</h2>
        <div class="form-row"><input id="annTitle" placeholder="標題"><input id="annBody" placeholder="內容" style="flex:2"><button class="btn btn-primary" onclick="window._annAdd()">發佈</button></div>`;
      if (!items.length) h += '<div class="empty">沒有公告</div>';
      items.forEach(i => {
        const acked = i.acked || i.acknowledged;
        h += `<div class="list-item">
          <span class="title">${esc(i.title)}</span>
          <span class="meta">${fmtDate(i.created || i.date)}</span>
          <span class="meta">${acked ? '✅ 已確認' : '⏳ 未確認'}</span>
          ${!acked ? `<button class="btn btn-sm btn-success" onclick="window._annAck('${i.id}')">確認</button>` : ''}
        </div>`;
      });
      h += '</div>';
      c.innerHTML = h;
    }
    function load() { api('GET', '/api/announce/list').then(d => render(d.items || [])).catch(() => { c.innerHTML = '<div class="empty">錯誤</div>'; }); }
    window._annAdd = function () {
      const t = document.getElementById('annTitle').value.trim();
      const b = document.getElementById('annBody').value.trim();
      if (!t) return;
      api('POST', '/api/announce/add', { title: t, content: b }).then(() => { toast('已發佈'); load(); });
    };
    window._annAck = function (id) { api('POST', '/api/announce/ack', { id }).then(() => load()); };
    load();
  };

  // ----- MSG -----
  pages.msg = function (c) {
    function renderInbox(messages) {
      let h = `<div class="card"><h2>💬 訊息</h2>
        <div class="form-row"><input id="msgTo" placeholder="收件人"><input id="msgBody" placeholder="訊息內容" style="flex:2"><button class="btn btn-primary" onclick="window._msgSend()">傳送</button></div>`;
      if (!messages.length) h += '<div class="empty">沒有訊息</div>';
      messages.forEach(m => {
        h += `<div class="msg-item ${m.read?'':'unread'}" onclick="window._msgRead('${m.id}')">
          <div class="msg-from">${esc(m.from || m.sender)}</div>
          <div class="msg-preview">${esc(m.subject || m.preview || (m.body||'').slice(0,60))}</div>
          <div class="msg-time">${fmtDate(m.date || m.created)}</div>
        </div>`;
      });
      h += '</div><div id="msgDetail"></div>';
      c.innerHTML = h;
    }
    function load() { api('GET', '/api/msg/inbox').then(d => renderInbox(d.messages || [])).catch(() => { c.innerHTML = '<div class="empty">錯誤</div>'; }); }
    window._msgSend = function () {
      const to = document.getElementById('msgTo').value.trim();
      const body = document.getElementById('msgBody').value.trim();
      if (!to || !body) return;
      api('POST', '/api/msg/send', { to, body }).then(() => { toast('已傳送'); load(); });
    };
    window._msgRead = function (id) {
      api('GET', `/api/msg/read/${id}`).then(d => {
        const m = d.message || d;
        document.getElementById('msgDetail').innerHTML = `<div class="card">
          <div class="detail-header"><h3>來自 ${esc(m.from || m.sender)}</h3><div class="meta">${fmtDate(m.date || m.created)}</div></div>
          <div class="detail-body">${esc(m.body || m.content || '')}</div>
          <div style="margin-top:16px">
            <div class="form-row"><input id="msgReply" placeholder="回覆…" style="flex:1"><button class="btn btn-primary" onclick="window._msgReplyTo('${esc(m.from||m.sender)}')">回覆</button></div>
          </div></div>`;
      });
    };
    window._msgReplyTo = function (to) {
      const body = document.getElementById('msgReply').value.trim();
      if (!body) return;
      api('POST', '/api/msg/send', { to, body }).then(() => { toast('已回覆'); load(); });
    };
    load();
  };

  // ----- HEALTH -----
  pages.health = function (c) {
    api('GET', '/api/health/status').then(d => {
      const checks = d.checks || [];
      let h = `<div class="card"><h2>🏥 系統狀態</h2>`;
      if (!checks.length) h += '<div class="empty">沒有檢查結果</div>';
      checks.forEach(ch => {
        const ok = ch.status === 'ok' || ch.status === 'healthy' || ch.ok;
        h += `<div class="list-item">
          <span class="title">${esc(ch.name || ch.service)}</span>
          <span class="${ok?'health-ok':'health-fail'}">${ok?'✅ 正常':'❌ 異常'}</span>
          <span class="meta">${esc(ch.message || ch.detail || '')}</span>
          <span class="meta">${fmtDate(ch.checked_at || ch.timestamp)}</span>
        </div>`;
      });
      h += '</div>';
      c.innerHTML = h;
    }).catch(() => { c.innerHTML = '<div class="empty">無法取得狀態</div>'; });
  };

  // ----- MAIL -----
  pages.mail = function (c) {
    let search = '';
    function renderList(messages) {
      const filtered = search ? messages.filter(m => (m.subject || m.from || m.body || '').includes(search)) : messages;
      let h = `<div class="card"><h2>📧 郵件</h2>
        <div class="form-row"><input id="mailTo" placeholder="收件人"><input id="mailSubj" placeholder="主旨"><input id="mailBody" placeholder="內容" style="flex:2"><button class="btn btn-primary" onclick="window._mailSend()">寄出</button></div>
        <div class="form-row"><input id="mailSearch" placeholder="搜尋…" value="${esc(search)}" oninput="window._mailSearch(this.value)"></div>`;
      if (!filtered.length) h += '<div class="empty">沒有郵件</div>';
      filtered.forEach(m => {
        h += `<div class="msg-item ${m.read||m.seen?'':'unread'}" onclick="window._mailRead('${m.id}')">
          <div class="msg-from">${esc(m.from || m.sender)}</div>
          <div class="msg-preview">${esc(m.subject || '(無主旨)')}</div>
          <div class="msg-time">${fmtDate(m.date || m.created)}</div>
        </div>`;
      });
      h += '</div><div id="mailDetail"></div>';
      c.innerHTML = h;
    }
    function load() { api('GET', '/api/mail/list').then(d => renderList(d.messages || [])).catch(() => { c.innerHTML = '<div class="empty">錯誤</div>'; }); }
    window._mailSend = function () {
      const to = document.getElementById('mailTo').value.trim();
      const subject = document.getElementById('mailSubj').value.trim();
      const body = document.getElementById('mailBody').value.trim();
      if (!to || !body) return;
      api('POST', '/api/mail/send', { to, subject, body }).then(() => { toast('已寄出'); load(); });
    };
    window._mailSearch = function (v) { search = v; load(); };
    window._mailRead = function (id) {
      api('GET', `/api/mail/read/${id}`).then(d => {
        const m = d.message || d;
        document.getElementById('mailDetail').innerHTML = `<div class="card">
          <div class="detail-header"><h3>${esc(m.subject || '(無主旨)')}</h3><div class="meta">來自 ${esc(m.from||m.sender)} — ${fmtDate(m.date||m.created)}</div></div>
          <div class="detail-body">${esc(m.body || m.content || '')}</div></div>`;
      });
    };
    load();
  };

})();
