/* Excalidraw Admin Helper: add "Save to Admin" near the Share/Copy Link UI.
   - No upstream modifications required.
   - Works by observing the DOM for a "Copy Link" (or "复制链接") button in the Share dialog.
   - When clicked, reads the share link from a nearby input or, as a fallback,
     temporarily hooks navigator.clipboard.writeText by simulating a click on Copy Link.
   - Prompts for a name, then POSTs { name, key } to /api/v2/admin/documents/{id}/meta.
*/
(function () {
  function parseShareLink(input) {
    try {
      var s = (input || '').trim();
      if (!s) return null;
      if (s[0] === '#') s = 'http://x/' + s;
      if (!/^https?:\/\//i.test(s)) s = 'http://x/#json=' + s;
      var u = new URL(s);
      var m = (u.hash || '').match(/#json=([^,]+),(.+)/);
      if (!m) return null;
      var id = m[1];
      var key = decodeURIComponent(m[2]);
      if (!id || !key) return null;
      return { id: id, key: key };
    } catch (e) {
      return null;
    }
  }

  function postMeta(id, key, name) {
    return fetch('/api/v2/admin/documents/' + id + '/meta', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: name || null, key: key })
    });
  }

  function ensureModalStyles() {
    if (document.getElementById('adm-modal-style')) return;
    var css = '\n'
      + '.adm-modal-overlay{position:fixed;inset:0;background:rgba(0,0,0,0.35);display:flex;align-items:center;justify-content:center;z-index:2147483000;}\n'
      + '.adm-modal{background:#fff;width:420px;max-width:92vw;border-radius:8px;box-shadow:0 10px 30px rgba(0,0,0,0.25);padding:16px;font-family:system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;}\n'
      + '.adm-modal h3{margin:0 0 12px;font-size:16px;}\n'
      + '.adm-field{display:flex;flex-direction:column;gap:6px;margin:10px 0;}\n'
      + '.adm-field label{font-size:12px;color:#555;}\n'
      + '.adm-field input{padding:8px;border:1px solid #ddd;border-radius:6px;box-sizing:border-box;}\n'
      + '.adm-actions{display:flex;gap:8px;margin-top:12px;justify-content:flex-end;}\n'
      + '.adm-btn{padding:8px 12px;border:1px solid #ccc;border-radius:6px;background:#fff;cursor:pointer;}\n'
      + '.adm-btn.primary{background:#3b82f6;border-color:#3b82f6;color:#fff;}\n'
      + '.adm-error{color:#c00;font-size:12px;min-height:16px;margin-top:4px;}\n';
    var style = document.createElement('style');
    style.id = 'adm-modal-style';
    style.type = 'text/css';
    style.appendChild(document.createTextNode(css));
    document.head.appendChild(style);
  }

  function openNameModal(defaultName, onSubmit) {
    ensureModalStyles();
    // overlay
    var overlay = document.createElement('div');
    overlay.className = 'adm-modal-overlay';
    overlay.addEventListener('click', function (e) { if (e.target === overlay) close(); });
    // modal
    var modal = document.createElement('div');
    modal.className = 'adm-modal';
    var title = document.createElement('h3');
    title.textContent = 'Save to Admin';
    var field = document.createElement('div');
    field.className = 'adm-field';
    var label = document.createElement('label');
    label.textContent = 'Name (optional)';
    label.setAttribute('for', 'adm-name-input');
    var input = document.createElement('input');
    input.type = 'text';
    input.id = 'adm-name-input';
    input.placeholder = '(optional)';
    input.value = defaultName || '';
    var error = document.createElement('div');
    error.className = 'adm-error';
    var actions = document.createElement('div');
    actions.className = 'adm-actions';
    var btnSave = document.createElement('button');
    btnSave.className = 'adm-btn primary';
    btnSave.textContent = 'Save';
    var btnCancel = document.createElement('button');
    btnCancel.className = 'adm-btn';
    btnCancel.textContent = 'Cancel';

    actions.appendChild(btnSave);
    actions.appendChild(btnCancel);
    field.appendChild(label);
    field.appendChild(input);
    modal.appendChild(title);
    modal.appendChild(field);
    modal.appendChild(error);
    modal.appendChild(actions);
    overlay.appendChild(modal);
    document.body.appendChild(overlay);

    function close() {
      try { document.body.removeChild(overlay); } catch (e) {}
    }

    function submit() {
      if (btnSave.disabled) return;
      btnSave.disabled = true;
      error.textContent = '';
      Promise.resolve(onSubmit(input.value.trim() || null)).then(function (ok) {
        if (ok === false) {
          error.textContent = '保存失败';
          btnSave.disabled = false;
        } else {
          close();
        }
      }).catch(function () {
        error.textContent = '请求失败';
        btnSave.disabled = false;
      });
    }

    btnSave.addEventListener('click', submit);
    btnCancel.addEventListener('click', close);
    input.addEventListener('keydown', function (e) { if (e.key === 'Enter') submit(); if (e.key === 'Escape') close(); });
    setTimeout(function () { try { input.focus(); input.select(); } catch (e) {} }, 0);
  }

  function findCopyButton(container) {
    // Prefer explicit aria-label
    var btn = container.querySelector('button[aria-label="Copy link"]');
    if (btn) return btn;
    var btns = Array.from(container.querySelectorAll('button, [role="button"], a'));
    return btns.find(function (el) {
      var t = (el.textContent || '').trim();
      return /Copy\s*link/i.test(t) || /复制链接/.test(t);
    }) || null;
  }

  function findShareInput(container) {
    // Prefer the readonly input used by Excalidraw share dialog
    var el = container.querySelector('.ShareableLinkDialog__linkRow .ExcTextField__input--readonly input[readonly]')
          || container.querySelector('.ExcTextField__input--readonly input[readonly]');
    if (el) return el;
    var inputs = Array.from(container.querySelectorAll('input, textarea'));
    return inputs.find(function (el) {
      var v = (el.value || el.textContent || '').trim();
      return /#json=.+,.+/.test(v);
    }) || null;
  }

  function captureByClicking(copyBtn) {
    return new Promise(function (resolve) {
      var saved = navigator.clipboard && navigator.clipboard.writeText;
      if (!saved) {
        try { copyBtn.click(); } catch (e) {}
        resolve(null);
        return;
      }
      navigator.clipboard.writeText = function (text) {
        try { resolve(text); } catch (e) { resolve(null); }
        return saved.call(navigator.clipboard, text);
      };
      try { copyBtn.click(); } catch (e) { resolve(null); }
      setTimeout(function(){ navigator.clipboard.writeText = saved; }, 50);
    });
  }

  function ensureButton(container) {
    if (container.querySelector('[data-admin-save-btn]')) return;
    var copyBtn = findCopyButton(container);
    if (!copyBtn) return;
    var btn = document.createElement('button');
    btn.className = copyBtn.className || 'ExcButton'; // mimic styling
    btn.type = 'button';
    btn.setAttribute('data-admin-save-btn', '1');
    btn.style.marginLeft = '8px';
    // Prefer using the same inner structure as ExcButton for consistent layout
    var inner = document.createElement('div');
    inner.className = 'ExcButton__contents';
    inner.textContent = 'Save to Admin';
    btn.appendChild(inner);
    btn.addEventListener('click', async function () {
      // Try read from input first
      var input = findShareInput(container);
      var link = input ? (input.value || input.textContent || '').trim() : '';
      if (!/#json=.+,.+/.test(link)) {
        // Fallback: capture by triggering Copy Link
        link = await captureByClicking(copyBtn);
      }
      var parsed = parseShareLink(link || '');
      if (!parsed) { alert('未找到分享链接，请先生成 Share Link'); return; }
      openNameModal('', async function (name) {
        try {
          var r = await postMeta(parsed.id, parsed.key, name);
          if (!r.ok) return false;
          return true;
        } catch (e) { return false; }
      });
    });
    // Insert after copy button
    copyBtn.parentElement.insertBefore(btn, copyBtn.nextSibling);
  }

  function scan() {
    // Prefer the specific share dialog container
    var rows = Array.from(document.querySelectorAll('.ShareableLinkDialog__linkRow'));
    if (rows.length) {
      rows.forEach(ensureButton);
      return;
    }
    // Fallback heuristic
    var candidates = Array.from(document.querySelectorAll('div, section, dialog, form'));
    candidates.forEach(function (c) {
      if (findCopyButton(c)) ensureButton(c);
    });
  }

  var mo = new MutationObserver(function () { try { scan(); } catch (e) {} });
  try { mo.observe(document.documentElement, { childList: true, subtree: true }); } catch (e) {}
  // initial
  try { scan(); } catch (e) {}
})();
