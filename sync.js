// sync.js — Cloud sync layer for FreightDesk Pro
// Loaded after the main app script. Patches auth, save, and load to use a remote API.
// Falls back gracefully to local-only mode when no server is configured.
(function () {
  'use strict';

  var SURL_KEY = 'fdp_server_url';
  var JWT_KEY  = 'fdp_jwt';
  var BASE     = (localStorage.getItem(SURL_KEY) || '').trim().replace(/\/$/, '');
  var TOKEN    = localStorage.getItem(JWT_KEY) || '';

  function setToken(t) { TOKEN = t || ''; localStorage.setItem(JWT_KEY, TOKEN); }
  function setBase(u)  { BASE  = (u || '').trim().replace(/\/$/, ''); localStorage.setItem(SURL_KEY, BASE); }

  // ── Core fetch wrapper ───────────────────────────────────────────────────────
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

  // ── Push all in-memory data to server ────────────────────────────────────────
  function pushAll() {
    if (!BASE || !TOKEN || !window.CU) return;
    api('PUT', '/api/data', {
      tr: window.trips,
      py: window.payments,
      iv: window.invoices,
      cl: window.clients,
      co: window.COMPANY,
      fi: window.finData,
      ml: window.savedMails
    }).catch(function (e) { console.warn('[FDP Sync] push failed:', e.message); });
  }

  // ── Pull from server, update globals and localStorage cache ──────────────────
  function pullAll() {
    if (!BASE || !TOKEN || !window.CU) return;
    api('GET', '/api/data').then(function (d) {
      var k = 'fdp_' + window.CU + '_';
      var map = { tr: 'trips', py: 'payments', iv: 'invoices', cl: 'clients',
                  co: 'COMPANY', fi: 'finData', ml: 'savedMails' };
      Object.keys(map).forEach(function (type) {
        if (d[type] != null) {
          window[map[type]] = d[type];
          localStorage.setItem(k + type, JSON.stringify(d[type]));
        }
      });
      if (typeof window.render === 'function') window.render();
      document.getElementById('sbCo').textContent = (window.COMPANY && window.COMPANY.name) || '—';
      setSyncStatus('synced');
    }).catch(function (e) {
      console.warn('[FDP Sync] pull failed:', e.message);
      setSyncStatus('error');
    });
  }

  // ── Patch saveAll ────────────────────────────────────────────────────────────
  var _origSaveAll = window.saveAll;
  if (typeof _origSaveAll === 'function') {
    window.saveAll = function () {
      _origSaveAll.apply(this, arguments);
      pushAll();
    };
  }

  // ── Patch loadAll (local-first, then server) ─────────────────────────────────
  var _origLoadAll = window.loadAll;
  if (typeof _origLoadAll === 'function') {
    window.loadAll = function () {
      _origLoadAll.apply(this, arguments);
      pullAll();
    };
  }

  // ── Patch doLogout (clear JWT) ───────────────────────────────────────────────
  var _origDoLogout = window.doLogout;
  if (typeof _origDoLogout === 'function') {
    window.doLogout = function () {
      setToken('');
      _origDoLogout.apply(this, arguments);
    };
  }

  // ── Server auth on registration (obFinish) ───────────────────────────────────
  // After the user registers locally, we also register on the server.
  // This is done in the background so local mode still works if server is down.
  var _origObFinish = window.obFinish;
  if (typeof _origObFinish === 'function') {
    window.obFinish = function () {
      // Capture credentials before the form clears
      var name = (document.getElementById('ob_name').value || '').trim();
      var user = (document.getElementById('ob_user').value || '').trim().toLowerCase().replace(/\s/g, '');
      var pass = document.getElementById('ob_pass').value || '';

      if (!BASE) { _origObFinish(); return; }

      var e3 = document.getElementById('ob_e3'); e3.textContent = '';

      api('POST', '/api/auth/register', { username: user, name: name, password: pass })
        .then(function (data) {
          setToken(data.token);
          _origObFinish(); // let the original flow run (saves locally, nav to dashboard)
        })
        .catch(function (err) {
          if (err.message === 'Username already taken') {
            // User may already have a server account — try logging in
            return api('POST', '/api/auth/login', { username: user, password: pass })
              .then(function (data) { setToken(data.token); _origObFinish(); })
              .catch(function () {
                e3.textContent = 'Server: username taken. Use a different username or clear server URL in Settings.';
              });
          }
          // Server down / other error — continue in local mode
          console.warn('[FDP Sync] server registration failed:', err.message);
          _origObFinish();
        });
    };
  }

  // ── Auto-login to server when session is restored from sessionStorage ────────
  // loginUser() is called at startup if a local session exists.
  var _origLoginUser = window.loginUser;
  if (typeof _origLoginUser === 'function') {
    window.loginUser = function (u, obj) {
      _origLoginUser.apply(this, arguments);
      // If we have a stored JWT but no BASE, nothing to do.
      // If we have BASE but no JWT, we cannot auto-authenticate (no password).
      // Just try pulling data if we already have a valid JWT.
      if (BASE && TOKEN) {
        api('GET', '/api/auth/me').then(function () {
          pullAll();
        }).catch(function (err) {
          console.warn('[FDP Sync] JWT invalid or expired:', err.message);
          setToken('');
          showServerLogin(u);
        });
      }
    };
  }

  // ── Server login overlay (shown when JWT expired and server is configured) ────
  function showServerLogin(username) {
    var existing = document.getElementById('srvLoginOverlay');
    if (existing) return;

    var overlay = document.createElement('div');
    overlay.id = 'srvLoginOverlay';
    overlay.style.cssText = 'position:fixed;inset:0;background:rgba(15,23,42,.85);z-index:7500;display:flex;align-items:center;justify-content:center;backdrop-filter:blur(4px)';
    overlay.innerHTML =
      '<div style="background:#fff;border-radius:16px;padding:28px;width:340px;max-width:calc(100vw - 32px);box-shadow:0 20px 60px rgba(0,0,0,.3)">' +
        '<div style="font-size:18px;font-weight:700;margin-bottom:4px">Re-connect to server</div>' +
        '<div style="font-size:13px;color:#666;margin-bottom:20px">Your server session expired. Enter your password to sync again.</div>' +
        '<div style="margin-bottom:12px"><label style="font-size:11px;font-weight:600;color:#555;text-transform:uppercase;letter-spacing:.05em;display:block;margin-bottom:4px">Username</label>' +
          '<input id="srl_u" type="text" value="' + (username || '') + '" style="width:100%;padding:10px;border:1.5px solid #ddd;border-radius:6px;font-size:14px" readonly></div>' +
        '<div style="margin-bottom:12px"><label style="font-size:11px;font-weight:600;color:#555;text-transform:uppercase;letter-spacing:.05em;display:block;margin-bottom:4px">Password</label>' +
          '<input id="srl_p" type="password" style="width:100%;padding:10px;border:1.5px solid #ddd;border-radius:6px;font-size:14px" placeholder="Your password"></div>' +
        '<div id="srl_err" style="font-size:12px;color:#dc2626;min-height:18px;margin-bottom:10px"></div>' +
        '<div style="display:flex;gap:8px">' +
          '<button onclick="doSrvLogin()" style="flex:1;padding:11px;background:#2563EB;color:#fff;border:none;border-radius:6px;font-size:13px;font-weight:600;cursor:pointer">Sign in to server</button>' +
          '<button onclick="dismissSrvLogin()" style="padding:11px 16px;background:#f0f0f2;border:1.5px solid #ddd;border-radius:6px;font-size:13px;cursor:pointer">Skip</button>' +
        '</div>' +
      '</div>';
    document.body.appendChild(overlay);

    var pi = overlay.querySelector('#srl_p');
    if (pi) pi.focus();
    pi.addEventListener('keydown', function (e) { if (e.key === 'Enter') window.doSrvLogin(); });
  }

  window.doSrvLogin = function () {
    var u = (document.getElementById('srl_u').value || '').trim();
    var p = document.getElementById('srl_p').value || '';
    var err = document.getElementById('srl_err');
    err.textContent = 'Signing in…';
    api('POST', '/api/auth/login', { username: u, password: p })
      .then(function (data) {
        setToken(data.token);
        var overlay = document.getElementById('srvLoginOverlay');
        if (overlay) overlay.remove();
        pullAll();
        setSyncStatus('synced');
      })
      .catch(function (e) {
        err.textContent = e.message;
      });
  };

  window.dismissSrvLogin = function () {
    var overlay = document.getElementById('srvLoginOverlay');
    if (overlay) overlay.remove();
  };

  // ── Sync status indicator ─────────────────────────────────────────────────────
  function setSyncStatus(state) {
    var el = document.getElementById('syncStatusBadge');
    if (!el) return;
    var map = {
      synced: { text: '☁ Synced', color: '#059669' },
      error:  { text: '☁ Sync error', color: '#dc2626' },
      none:   { text: '☁ Local only', color: '#888' }
    };
    var s = map[state] || map.none;
    el.textContent = s.text;
    el.style.color = s.color;
  }

  // ── Inject Server Settings card into Settings page ────────────────────────────
  function injectServerSettings() {
    var settingsPage = document.getElementById('settings');
    if (!settingsPage) return;
    if (document.getElementById('srvSettingsCard')) return;

    var card = document.createElement('div');
    card.id = 'srvSettingsCard';
    card.className = 'card';
    card.style.borderColor = '#2563EB';
    card.innerHTML =
      '<div class="ch" style="border-bottom-color:#dbeafe">' +
        '<span class="ct" style="color:#2563EB">☁ Server Sync</span>' +
        '<span id="syncStatusBadge" style="font-size:11px;font-weight:500"></span>' +
      '</div>' +
      '<div class="cb">' +
        '<div class="ib" style="margin-bottom:14px">' +
          'Connect to a self-hosted FreightDesk Pro server so your data syncs across devices and multiple users can share access. ' +
          'Leave blank to use <strong>local-only</strong> mode.' +
        '</div>' +
        '<div class="fgr">' +
          '<div class="fg"><label>Server URL</label>' +
            '<input type="url" id="srv_url" class="w300" placeholder="https://your-server.com  or  http://localhost:3742">' +
          '</div>' +
          '<div class="fg"><label>&nbsp;</label>' +
            '<button class="btn btn-p" onclick="srvConnect()">Connect</button>' +
          '</div>' +
          '<div class="fg"><label>&nbsp;</label>' +
            '<button class="btn" onclick="srvTest()">Test</button>' +
          '</div>' +
          '<div class="fg"><label>&nbsp;</label>' +
            '<button class="btn btn-r btn-sm" onclick="srvDisconnect()" id="srvDisconnBtn" style="display:none">Disconnect</button>' +
          '</div>' +
        '</div>' +
        '<div id="srvMsg" style="font-size:12px;margin-top:6px;color:var(--tx2)"></div>' +
        '<div id="srvLoginSection" style="display:none;margin-top:14px;padding-top:14px;border-top:1px solid var(--bd)">' +
          '<div style="font-size:13px;font-weight:600;margin-bottom:10px">Sign in to server</div>' +
          '<div class="fgr">' +
            '<div class="fg"><label>Username</label><input type="text" id="srv_loginU" class="w160"></div>' +
            '<div class="fg"><label>Password</label><input type="password" id="srv_loginP" class="w160"></div>' +
            '<div class="fg"><label>&nbsp;</label><button class="btn btn-p" onclick="srvLogin()">Sign in</button></div>' +
          '</div>' +
          '<div id="srvLoginMsg" style="font-size:12px;margin-top:4px;color:var(--tx2)"></div>' +
        '</div>' +
      '</div>';

    settingsPage.insertBefore(card, settingsPage.firstChild);
    refreshSrvUI();
  }

  function refreshSrvUI() {
    var urlInput = document.getElementById('srv_url');
    var discBtn  = document.getElementById('srvDisconnBtn');
    var loginSec = document.getElementById('srvLoginSection');
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
    fetch(url + '/api/health')
      .then(function (r) { return r.json(); })
      .then(function (d) {
        msg.style.color = '#059669';
        msg.textContent = '✓ Server is online — FreightDesk Pro server v' + (d.version || '?');
      })
      .catch(function () {
        msg.style.color = '#dc2626';
        msg.textContent = '✗ Could not reach server. Check the URL and make sure it is running.';
      });
  };

  window.srvConnect = function () {
    var url = (document.getElementById('srv_url').value || '').trim();
    var msg = document.getElementById('srvMsg');
    if (!url) { srvDisconnect(); return; }

    msg.style.color = 'var(--tx2)'; msg.textContent = 'Connecting…';
    var cleanURL = url.replace(/\/$/, '');
    fetch(cleanURL + '/api/health')
      .then(function (r) { return r.json(); })
      .then(function (d) {
        setBase(cleanURL);
        msg.style.color = '#059669';
        msg.textContent = '✓ Connected. Sign in below to start syncing.';
        refreshSrvUI();
      })
      .catch(function () {
        msg.style.color = '#dc2626';
        msg.textContent = '✗ Could not reach server. Check the URL.';
      });
  };

  window.srvLogin = function () {
    var u = (document.getElementById('srv_loginU').value || '').trim();
    var p = document.getElementById('srv_loginP').value || '';
    var msg = document.getElementById('srvLoginMsg');
    msg.style.color = 'var(--tx2)'; msg.textContent = 'Signing in…';
    api('POST', '/api/auth/login', { username: u, password: p })
      .then(function (data) {
        setToken(data.token);
        msg.style.color = '#059669';
        msg.textContent = '✓ Signed in as ' + (data.name || data.username) + '. Syncing data…';
        refreshSrvUI();
        pullAll();
      })
      .catch(function (e) {
        msg.style.color = '#dc2626';
        msg.textContent = '✗ ' + e.message;
      });
  };

  window.srvDisconnect = function () {
    setBase('');
    setToken('');
    document.getElementById('srvMsg').textContent = 'Disconnected. Running in local-only mode.';
    refreshSrvUI();
  };

  // ── Bootstrap ─────────────────────────────────────────────────────────────────
  // Wait for the page to fully render before injecting UI
  function init() {
    injectServerSettings();
    setSyncStatus(BASE ? (TOKEN ? 'synced' : 'error') : 'none');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    // DOMContentLoaded already fired — run on next tick so the app scripts finish first
    setTimeout(init, 0);
  }

})();
