// sync.js — FreightDesk Pro: login screen, session persistence, and cloud sync layer.
(function () {
  'use strict';

  var SURL_KEY  = 'fdp_server_url';
  var JWT_KEY   = 'fdp_jwt';
  var SESS_KEY  = 'fdp_persist_session';
  var BASE      = (localStorage.getItem(SURL_KEY) || '').trim().replace(/\/$/, '');
  var TOKEN     = localStorage.getItem(JWT_KEY) || '';

  function setToken(t) { TOKEN = t || ''; localStorage.setItem(JWT_KEY, TOKEN); }
  function setBase(u)  { BASE  = (u || '').trim().replace(/\/$/, ''); localStorage.setItem(SURL_KEY, BASE); }

  function api(method, path, body) {
    if (!BASE) return Promise.reject(new Error('no_server'));
    var opts = { method: method, headers: { 'Content-Type': 'application/json' } };
    if (TOKEN) opts.headers['Authorization'] = 'Bearer ' + TOKEN;
    if (body !== undefined) opts.body = JSON.stringify(body);
    return fetch(BASE + path, opts).then(function (r) {
      return r.json().then(function (d) {
        if (!r.ok) throw new Error(d.error || ('HTTP ' + r.status));
        return d;
      });
    });
  }

  function pushAll() {
    if (!BASE || !TOKEN || !window.CU) return;
    api('PUT', '/api/data', {
      tr: window.trips, py: window.payments, iv: window.invoices,
      cl: window.clients, co: window.COMPANY, fi: window.finData, ml: window.savedMails
    }).catch(function (e) { console.warn('[FDP] push failed:', e.message); });
  }

  function pullAll() {
    if (!BASE || !TOKEN || !window.CU) return;
    setSyncStatus('syncing');
    api('GET', '/api/data').then(function (d) {
      var k = 'fdp_' + window.CU + '_';
      var map = { tr:'trips', py:'payments', iv:'invoices', cl:'clients', co:'COMPANY', fi:'finData', ml:'savedMails' };
      Object.keys(map).forEach(function (type) {
        if (d[type] != null) { window[map[type]] = d[type]; localStorage.setItem(k + type, JSON.stringify(d[type])); }
      });
      if (typeof window.render === 'function') window.render();
      var sbCo = document.getElementById('sbCo');
      if (sbCo) sbCo.textContent = (window.COMPANY && window.COMPANY.name) || '—';
      setSyncStatus('synced');
    }).catch(function (e) { console.warn('[FDP] pull failed:', e.message); setSyncStatus('error'); });
  }

  var _origSaveAll = window.saveAll;
  if (typeof _origSaveAll === 'function') {
    window.saveAll = function () { _origSaveAll.apply(this, arguments); pushAll(); };
  }

  var _origLoadAll = window.loadAll;
  if (typeof _origLoadAll === 'function') {
    window.loadAll = function () { _origLoadAll.apply(this, arguments); };
  }

  var _origLoginUser = window.loginUser;
  if (typeof _origLoginUser === 'function') {
    window.loginUser = function (u, obj) {
      _origLoginUser.apply(this, arguments);
      localStorage.setItem(SESS_KEY, u);
      updateSidebarSync();
    };
  }

  var _origDoLogout = window.doLogout;
  if (typeof _origDoLogout === 'function') {
    window.doLogout = function () {
      setToken(''); localStorage.removeItem(SESS_KEY);
      _origDoLogout.apply(this, arguments);
    };
  }

  // obFinish: LOCAL ALWAYS WORKS FIRST — server sync is background-only
  var _origObFinish = window.obFinish;
  if (typeof _origObFinish === 'function') {
    window.obFinish = function () {
      var name = '', user = '', pass = '';
      var elName = document.getElementById('ob_name');
      var elUser = document.getElementById('ob_user');
      var elPass = document.getElementById('ob_pass');
      if (elName) name = (elName.value || '').trim();
      if (elUser) user = (elUser.value || '').trim().toLowerCase().replace(/\s/g, '');
      if (elPass) pass = elPass.value || '';
      _origObFinish();
      if (!BASE || !user || !pass) return;
      api('POST', '/api/auth/register', { username: user, name: name, password: pass })
        .then(function (data) { setToken(data.token); pushAll(); })
        .catch(function (err) {
          if (err.message === 'Username already taken') {
            api('POST', '/api/auth/login', { username: user, password: pass })
              .then(function (data) { setToken(data.token); pullAll(); })
              .catch(function () {});
          }
        });
    };
  }

  // LOGIN SCREEN
  function injectLoginScreen() {
    var obCard = document.querySelector('#onboard .ob-card');
    if (!obCard || document.getElementById('fdp-tabs')) return;

    var tabBar = document.createElement('div');
    tabBar.id = 'fdp-tabs';
    tabBar.style.cssText = 'display:flex;background:#f0f0f2;border-bottom:1px solid #e0e0e6;flex-shrink:0';

    var tReg = document.createElement('button');
    tReg.id = 'tab-reg'; tReg.textContent = 'New Account';
    _tabStyle(tReg, true); tReg.onclick = function () { showTab('register'); };

    var tLog = document.createElement('button');
    tLog.id = 'tab-log'; tLog.textContent = 'Sign In';
    _tabStyle(tLog, false); tLog.onclick = function () { showTab('login'); };

    tabBar.appendChild(tReg); tabBar.appendChild(tLog);
    var obBody = obCard.querySelector('.ob-body');
    obCard.insertBefore(tabBar, obBody);

    var loginDiv = document.createElement('div');
    loginDiv.id = 'ob-login-pane';
    loginDiv.style.display = 'none';
    loginDiv.innerHTML =
      '<div style="padding:24px 24px 20px">' +
        '<div class="ob-title" style="margin-bottom:3px">Welcome back</div>' +
        '<div class="ob-sub">Sign in with your FreightDesk Pro credentials.</div>' +
        '<div class="ob-f"><label>Username</label>' +
          '<input type="text" id="li_user" placeholder="Your username" autocomplete="username" style="width:100%" ' +
          'onkeydown="if(event.key===\'Enter\')document.getElementById(\'li_pass\').focus()"></div>' +
        '<div class="ob-f"><label>Password</label>' +
          '<input type="password" id="li_pass" placeholder="Your password" autocomplete="current-password" style="width:100%" ' +
          'onkeydown="if(event.key===\'Enter\')fdpLogin()"></div>' +
        '<div id="li_err" style="font-size:12px;color:#dc2626;min-height:18px;margin:6px 0"></div>' +
        '<button onclick="fdpLogin()" style="width:100%;padding:12px;background:#2563EB;color:#fff;border:none;border-radius:6px;font-size:14px;font-weight:600;cursor:pointer;font-family:Inter,sans-serif;margin-top:4px">Sign In →</button>' +
      '</div>';
    obCard.appendChild(loginDiv);
  }

  function _tabStyle(btn, active) {
    btn.style.cssText = 'flex:1;padding:13px;border:none;cursor:pointer;font-size:13px;font-weight:600;font-family:Inter,sans-serif;transition:all .15s;' +
      (active ? 'background:#fff;color:#2563EB;border-bottom:2px solid #2563EB;' : 'background:transparent;color:#888;border-bottom:2px solid transparent;');
  }

  window.showTab = function (tab) {
    var obBody = document.querySelector('#onboard .ob-body');
    var loginPane = document.getElementById('ob-login-pane');
    var tReg = document.getElementById('tab-reg');
    var tLog = document.getElementById('tab-log');
    if (!obBody || !loginPane) return;
    if (tab === 'login') {
      obBody.style.display = 'none'; loginPane.style.display = '';
      _tabStyle(tReg, false); _tabStyle(tLog, true);
      var u = document.getElementById('li_user'); if (u) setTimeout(function () { u.focus(); }, 50);
    } else {
      obBody.style.display = ''; loginPane.style.display = 'none';
      _tabStyle(tReg, true); _tabStyle(tLog, false);
    }
  };

  window.fdpLogin = function () {
    var u = (document.getElementById('li_user').value || '').trim().toLowerCase().replace(/\s/g, '');
    var p = document.getElementById('li_pass').value || '';
    var err = document.getElementById('li_err');
    err.textContent = '';
    if (!u || !p) { err.textContent = 'Enter username and password.'; return; }

    var localUsers = typeof window.gU === 'function' ? window.gU() : {};
    var localUser = localUsers[u];
    var localOk = localUser && (localUser.pass === btoa(unescape(encodeURIComponent(p))));

    if (!BASE) {
      if (!localUser) { err.textContent = 'Username not found on this device.'; return; }
      if (!localOk) { err.textContent = 'Incorrect password.'; return; }
      _finishLogin(u, localUser); return;
    }

    err.textContent = 'Signing in…';
    api('POST', '/api/auth/login', { username: u, password: p })
      .then(function (data) {
        setToken(data.token);
        if (!localUsers[u]) { localUsers[u] = { pass: btoa(unescape(encodeURIComponent(p))), name: data.name }; if (typeof window.sU === 'function') window.sU(localUsers); }
        _finishLogin(u, localUsers[u] || { name: data.name });
      })
      .catch(function (e) {
        if (localOk) { err.textContent = ''; _finishLogin(u, localUser); return; }
        err.textContent = '✗ ' + (localUser ? e.message : 'Username not found.');
      });
  };

  function _finishLogin(u, userObj) {
    var ob = document.getElementById('onboard'); if (ob) ob.style.display = 'none';
    if (typeof window.defCo === 'function') window.COMPANY = window.defCo();
    window.loginUser(u, userObj);
    if (BASE && TOKEN) pullAll();
  }

  // SERVER SETTINGS CARD
  function injectServerSettings() {
    var settingsPage = document.getElementById('settings');
    if (!settingsPage || document.getElementById('srvSettingsCard')) return;
    var card = document.createElement('div');
    card.id = 'srvSettingsCard'; card.className = 'card'; card.style.borderColor = '#2563EB';
    card.innerHTML =
      '<div class="ch" style="border-bottom-color:#dbeafe"><span class="ct" style="color:#2563EB">☁ Server Sync</span><span id="syncStatusBadge" style="font-size:11px;font-weight:500"></span></div>' +
      '<div class="cb">' +
        '<div class="ib" style="margin-bottom:14px">Connect to a self-hosted FreightDesk Pro server for multi-device sync. Leave blank for <strong>local-only</strong> mode.</div>' +
        '<div class="fgr">' +
          '<div class="fg"><label>Server URL</label><input type="url" id="srv_url" class="w300" placeholder="https://your-server.com"></div>' +
          '<div class="fg"><label>&nbsp;</label><button class="btn btn-p" onclick="srvConnect()">Connect</button></div>' +
          '<div class="fg"><label>&nbsp;</label><button class="btn" onclick="srvTest()">Test</button></div>' +
          '<div class="fg"><label>&nbsp;</label><button class="btn btn-r btn-sm" onclick="srvDisconnect()" id="srvDisconnBtn" style="display:none">Disconnect</button></div>' +
        '</div>' +
        '<div id="srvMsg" style="font-size:12px;margin-top:6px;color:var(--tx2)"></div>' +
        '<div id="srvLoginSection" style="display:none;margin-top:14px;padding-top:14px;border-top:1px solid var(--bd)">' +
          '<div style="font-size:13px;font-weight:600;margin-bottom:10px">Sign in to server</div>' +
          '<div class="fgr"><div class="fg"><label>Username</label><input type="text" id="srv_loginU" class="w160"></div><div class="fg"><label>Password</label><input type="password" id="srv_loginP" class="w160"></div><div class="fg"><label>&nbsp;</label><button class="btn btn-p" onclick="srvLogin()">Sign in</button></div></div>' +
          '<div id="srvLoginMsg" style="font-size:12px;margin-top:4px;color:var(--tx2)"></div>' +
        '</div>' +
      '</div>';
    settingsPage.insertBefore(card, settingsPage.firstChild);
    refreshSrvUI();
  }

  function refreshSrvUI() {
    var urlInput = document.getElementById('srv_url'), discBtn = document.getElementById('srvDisconnBtn'), loginSec = document.getElementById('srvLoginSection');
    if (!urlInput) return;
    urlInput.value = BASE || '';
    if (discBtn) discBtn.style.display = BASE ? '' : 'none';
    if (loginSec) loginSec.style.display = (BASE && !TOKEN) ? '' : 'none';
    setSyncStatus(BASE ? (TOKEN ? 'synced' : 'error') : 'none');
  }

  window.srvTest = function () {
    var url = (document.getElementById('srv_url').value || '').trim().replace(/\/$/, '');
    var msg = document.getElementById('srvMsg');
    if (!url) { msg.textContent = 'Enter a server URL first.'; return; }
    msg.style.color = 'var(--tx2)'; msg.textContent = 'Testing…';
    fetch(url + '/api/health').then(function (r) { return r.json(); })
      .then(function (d) { msg.style.color = '#059669'; msg.textContent = '✓ Server online — FreightDesk Pro v' + (d.version || '?'); })
      .catch(function () { msg.style.color = '#dc2626'; msg.textContent = '✗ Could not reach server.'; });
  };

  window.srvConnect = function () {
    var url = (document.getElementById('srv_url').value || '').trim(), msg = document.getElementById('srvMsg');
    if (!url) { srvDisconnect(); return; }
    var clean = url.replace(/\/$/, '');
    msg.style.color = 'var(--tx2)'; msg.textContent = 'Connecting…';
    fetch(clean + '/api/health').then(function (r) { return r.json(); })
      .then(function () { setBase(clean); msg.style.color = '#059669'; msg.textContent = '✓ Connected. Sign in below to start syncing.'; refreshSrvUI(); })
      .catch(function () { msg.style.color = '#dc2626'; msg.textContent = '✗ Could not reach server.'; });
  };

  window.srvLogin = function () {
    var u = (document.getElementById('srv_loginU').value || '').trim(), p = document.getElementById('srv_loginP').value || '', msg = document.getElementById('srvLoginMsg');
    if (!u || !p) { msg.style.color = '#dc2626'; msg.textContent = '✗ Enter username and password.'; return; }
    // Verify local credentials first
    var localUsers = typeof window.gU === 'function' ? window.gU() : {};
    var localUser = localUsers[u];
    var localOk = localUser && (localUser.pass === btoa(unescape(encodeURIComponent(p))));
    if (!localOk) { msg.style.color = '#dc2626'; msg.textContent = '✗ Incorrect username or password.'; return; }
    msg.style.color = 'var(--tx2)'; msg.textContent = 'Signing in…';
    api('POST', '/api/auth/login', { username: u, password: p })
      .then(function (data) {
        setToken(data.token); refreshSrvUI();
        // Pull from server first — if it has data use it, otherwise push local
        api('GET', '/api/data').then(function (d) {
          var hasData = d && ((d.iv && d.iv.length) || (d.tr && d.tr.length) || (d.co && d.co.name));
          if (hasData) {
            msg.style.color = '#059669'; msg.textContent = '✓ Signed in. Loading your data…';
            pullAll();
          } else {
            msg.style.color = '#059669'; msg.textContent = '✓ Signed in. Uploading your data…';
            pushAll();
          }
        }).catch(function () { pushAll(); });
      })
      .catch(function () {
        // Not on server yet — register automatically using local credentials
        msg.textContent = 'First time on this server, registering…';
        api('POST', '/api/auth/register', { username: u, name: localUser.name || u, password: p })
          .then(function (data) {
            setToken(data.token); refreshSrvUI();
            msg.style.color = '#059669'; msg.textContent = '✓ Registered on server. Uploading your data…';
            pushAll();
          })
          .catch(function (e2) { msg.style.color = '#dc2626'; msg.textContent = '✗ ' + e2.message; });
      });
  };

  window.srvDisconnect = function () {
    setBase(''); setToken('');
    var msg = document.getElementById('srvMsg'); if (msg) msg.textContent = 'Disconnected. Running in local-only mode.';
    refreshSrvUI();
  };

  window.doSrvLogin = function () {
    var u = (document.getElementById('srl_u').value || '').trim(), p = document.getElementById('srl_p').value || '', err = document.getElementById('srl_err');
    err.textContent = 'Signing in…';
    api('POST', '/api/auth/login', { username: u, password: p })
      .then(function (data) { setToken(data.token); document.getElementById('srvLoginOverlay').remove(); pullAll(); setSyncStatus('synced'); })
      .catch(function (e) { err.textContent = e.message; });
  };
  window.dismissSrvLogin = function () { var el = document.getElementById('srvLoginOverlay'); if (el) el.remove(); };

  function showServerReloginOverlay(username) {
    if (document.getElementById('srvLoginOverlay')) return;
    var ov = document.createElement('div');
    ov.id = 'srvLoginOverlay';
    ov.style.cssText = 'position:fixed;inset:0;background:rgba(15,23,42,.85);z-index:7500;display:flex;align-items:center;justify-content:center;backdrop-filter:blur(4px)';
    ov.innerHTML = '<div style="background:#fff;border-radius:16px;padding:28px;width:340px;max-width:calc(100vw - 32px);box-shadow:0 20px 60px rgba(0,0,0,.3)">' +
      '<div style="font-size:18px;font-weight:700;margin-bottom:4px">Re-connect to server</div>' +
      '<div style="font-size:13px;color:#666;margin-bottom:18px">Server session expired. Enter your password to resume syncing.</div>' +
      '<div style="margin-bottom:10px"><label style="font-size:11px;font-weight:600;color:#555;display:block;margin-bottom:4px">Username</label><input id="srl_u" type="text" value="' + (username || '') + '" readonly style="width:100%;padding:10px;border:1.5px solid #ddd;border-radius:6px;font-size:14px;background:#f5f5f5"></div>' +
      '<div style="margin-bottom:10px"><label style="font-size:11px;font-weight:600;color:#555;display:block;margin-bottom:4px">Password</label><input id="srl_p" type="password" placeholder="Your password" style="width:100%;padding:10px;border:1.5px solid #ddd;border-radius:6px;font-size:14px" onkeydown="if(event.key===\'Enter\')doSrvLogin()"></div>' +
      '<div id="srl_err" style="font-size:12px;color:#dc2626;min-height:16px;margin-bottom:10px"></div>' +
      '<div style="display:flex;gap:8px"><button onclick="doSrvLogin()" style="flex:1;padding:11px;background:#2563EB;color:#fff;border:none;border-radius:6px;font-size:13px;font-weight:600;cursor:pointer">Sign in to server</button><button onclick="dismissSrvLogin()" style="padding:11px 16px;background:#f0f0f2;border:1.5px solid #ddd;border-radius:6px;font-size:13px;cursor:pointer">Skip</button></div>' +
      '</div>';
    document.body.appendChild(ov);
    var pi = ov.querySelector('#srl_p'); if (pi) setTimeout(function () { pi.focus(); }, 50);
  }

  function setSyncStatus(state) {
    var map = { syncing: { text: '☁ Syncing…', color: '#2563EB' }, synced: { text: '☁ Synced', color: '#059669' }, error: { text: '☁ Error', color: '#dc2626' }, none: { text: '⊙ Local', color: '#888' } };
    var s = map[state] || map.none;
    ['syncStatusBadge', 'sbSyncBadge'].forEach(function (id) { var el = document.getElementById(id); if (!el) return; el.textContent = s.text; el.style.color = s.color; });
  }
  function updateSidebarSync() { setSyncStatus(BASE ? (TOKEN ? 'synced' : 'error') : 'none'); }

  function injectSidebarSyncBadge() {
    var sbFoot = document.querySelector('.sb-foot');
    if (!sbFoot || document.getElementById('sbSyncBadge')) return;
    var badge = document.createElement('div');
    badge.id = 'sbSyncBadge'; badge.style.cssText = 'font-size:10px;font-weight:600;margin-bottom:8px;letter-spacing:.03em;cursor:pointer';
    badge.title = 'Cloud sync status — click to open Settings';
    badge.onclick = function () { if (typeof window.nav === 'function') window.nav('settings'); };
    sbFoot.insertBefore(badge, sbFoot.firstChild);
    updateSidebarSync();
  }

  function init() {
    injectLoginScreen();
    injectServerSettings();
    injectSidebarSyncBadge();
    updateSidebarSync();

    // Case 1: boot IIFE already restored session from sessionStorage
    if (window.CU) {
      var ob = document.getElementById('onboard'); if (ob) ob.style.display = 'none';
      localStorage.setItem(SESS_KEY, window.CU);
      updateSidebarSync();
      if (BASE && TOKEN) {
        api('GET', '/api/auth/me').then(function () { pullAll(); })
          .catch(function () { setToken(''); updateSidebarSync(); showServerReloginOverlay(window.CU); });
      }
      return;
    }

    // Case 2: cold start — restore from localStorage persistence
    var persisted = localStorage.getItem(SESS_KEY);
    if (persisted) {
      var users = typeof window.gU === 'function' ? window.gU() : {};
      if (users[persisted]) {
        var ob2 = document.getElementById('onboard'); if (ob2) ob2.style.display = 'none';
        if (typeof window.defCo === 'function') window.COMPANY = window.defCo();
        window.loginUser(persisted, users[persisted]);
        if (BASE && TOKEN) {
          api('GET', '/api/auth/me').then(function () { pullAll(); })
            .catch(function () { setToken(''); updateSidebarSync(); showServerReloginOverlay(persisted); });
        }
        return;
      } else { localStorage.removeItem(SESS_KEY); }
    }

    // Case 3: no session — show Sign In tab if accounts exist on this device
    if (typeof window.gU === 'function' && Object.keys(window.gU()).length > 0) {
      showTab('login');
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    setTimeout(init, 0);
  }
})();
