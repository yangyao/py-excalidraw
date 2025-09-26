from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from ..config import settings


router = APIRouter()


PAGE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Excalidraw Admin</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif; margin: 24px; }
    h1 { font-size: 20px; margin: 0 0 16px; }
    .toolbar { display: flex; gap: 8px; align-items: center; margin-bottom: 12px; }
    table { border-collapse: collapse; width: 100%; }
    th, td { border-bottom: 1px solid #eee; text-align: left; padding: 8px; }
    th { background: #fafafa; }
    button { padding: 6px 10px; border: 1px solid #ccc; background: #fff; border-radius: 4px; cursor: pointer; }
    button:hover { background: #f5f5f5; }
    .muted { color: #666; font-size: 12px; }
    .id { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }
    input[type="text"] { padding: 6px 8px; border: 1px solid #ddd; border-radius: 4px; }
    /* Modal */
    .modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.35); display: none; align-items: center; justify-content: center; z-index: 1000; }
    .modal { background: #fff; width: 520px; max-width: 92vw; border-radius: 8px; box-shadow: 0 10px 30px rgba(0,0,0,0.25); padding: 16px; }
    .modal h3 { margin: 0 0 12px; font-size: 16px; }
    .field { display: flex; flex-direction: column; gap: 6px; margin: 10px 0; }
    .field label { font-size: 12px; color: #555; }
    .field input { width: 100%; box-sizing: border-box; }
    .modal-actions { display: flex; gap: 8px; margin-top: 12px; justify-content: flex-end; }
    .error { color: #c00; }
  </style>
  <script>
    const APP_ORIGIN = __APP_ORIGIN__;
    function parseShareLink(input) {
      try {
        let s = (input || '').trim();
        if (!s) return null;
        if (s.startsWith('#')) s = 'http://x/' + s;
        if (!/^https?:\\/\\//i.test(s)) s = 'http://x/#json=' + s; // allow raw id,key
        const u = new URL(s);
        const m = (u.hash || '').match(/#json=([^,]+),(.+)/);
        if (!m) return null;
        const id = m[1];
        const key = decodeURIComponent(m[2]);
        if (!id || !key) return null;
        return { id, key };
      } catch { return null; }
    }
    function openAddModal() {
      const el = document.getElementById('add-modal');
      const name = document.getElementById('add-name-input');
      const link = document.getElementById('add-link-input');
      const err = document.getElementById('add-error');
      name.value = '';
      link.value = '';
      err.textContent = '';
      el.style.display = 'flex';
      setTimeout(()=> name.focus(), 0);
    }
    function closeAddModal() {
      const el = document.getElementById('add-modal');
      el.style.display = 'none';
    }
    async function submitAddCanvas() {
      const name = (document.getElementById('add-name-input').value || '').trim() || null;
      const link = (document.getElementById('add-link-input').value || '').trim();
      const err = document.getElementById('add-error');
      const btn = document.getElementById('add-submit-btn');
      err.textContent = '';
      const parsed = parseShareLink(link);
      if (!parsed) { err.textContent = '无法解析分享链接'; return; }
      btn.disabled = true;
      try {
        const res = await fetch(`/api/v2/admin/documents/${parsed.id}/meta`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, key: parsed.key })
        });
        if (!res.ok) {
          const msg = await res.text();
          err.textContent = '保存失败：' + msg;
          return;
        }
        closeAddModal();
        await render();
      } catch (e) {
        err.textContent = '请求失败';
      } finally {
        btn.disabled = false;
      }
    }
    // Keys are included as shareLink in list response.
    async function fetchList() {
      const res = await fetch('/api/v2/admin/documents');
      if (!res.ok) throw new Error('Failed to fetch list');
      return res.json();
    }

    async function remove(id) {
      if (!confirm('Delete document ' + id + '?')) return;
      const res = await fetch('/api/v2/' + id, { method: 'DELETE' });
      if (res.status !== 204) {
        const msg = await res.text();
        alert('Delete failed: ' + msg);
      }
      await render();
    }

    async function saveName(id) {
      const el = document.getElementById('name-' + id);
      const name = el.value.trim();
      const res = await fetch('/api/v2/admin/documents/' + id + '/name', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name || null }),
      });
      if (!res.ok) {
        const msg = await res.text();
        alert('Save failed: ' + msg);
      }
    }

    function openWithLink(link) { window.open(link, '_blank'); }

    async function copyLink(link) {
      try { await navigator.clipboard.writeText(link); alert('链接已复制'); }
      catch (e) { prompt('复制失败，请手动复制：', link); }
    }

    function toLocal(ts) {
      if (!ts) return '';
      const d = new Date(ts);
      return d.toLocaleString();
    }

    async function render() {
      document.getElementById('tbody').innerHTML = '<tr><td colspan="5" class="muted">Loading...</td></tr>';
      try {
        const items = await fetchList();
        if (!items.length) {
          document.getElementById('tbody').innerHTML = '<tr><td colspan="5" class="muted">No documents</td></tr>';
          return;
        }
        const rows = items.map((it, idx) => `
          <tr>
            <td>${idx + 1}</td>
            <td>
              <input id="name-${it.id}" type="text" value="${(it.name || '').replace(/"/g, '&quot;')}" placeholder="(untitled)" style="width: 220px" />
              <button onclick="saveName('${it.id}')">Save</button>
            </td>
            <td class="id">${it.id}</td>
            <td>${(it.size || 0)} bytes<br/><span class="muted">${toLocal(it.createdAt)}</span></td>
            <td>
              <button onclick="openWithLink('${it.shareLink}')">Open</button>
              <button onclick="copyLink('${it.shareLink}')">Copy Link</button>
              <button onclick="remove('${it.id}')">Delete</button>
            </td>
          </tr>
        `).join('');
        document.getElementById('tbody').innerHTML = rows;
      } catch (e) {
        document.getElementById('tbody').innerHTML = '<tr><td colspan="5" class="muted">Failed: ' + e.message + '</td></tr>';
      }
    }

    window.addEventListener('DOMContentLoaded', render);
  </script>
</head>
<body>
  <h1>Excalidraw Admin</h1>
  <div class="toolbar">
    <button onclick="render()">Refresh</button>
    <span class="muted">List shows canvases with saved key</span>
    <button onclick="openAddModal()">Add Canvas</button>
  </div>
  <div id="add-modal" class="modal-overlay" onclick="if(event.target===this) closeAddModal()">
    <div class="modal" role="dialog" aria-modal="true" aria-labelledby="add-title">
      <h3 id="add-title">Add Canvas</h3>
      <div class="field">
        <label for="add-name-input">Name</label>
        <input id="add-name-input" type="text" placeholder="(optional)" />
      </div>
      <div class="field">
        <label for="add-link-input">Share Link</label>
        <input id="add-link-input" type="text" placeholder="https://…/#json=… 或 id,key 或 #json=id,key" onkeydown="if(event.key==='Enter'){submitAddCanvas()}" />
      </div>
      <div id="add-error" class="error"></div>
      <div class="modal-actions">
        <button id="add-submit-btn" onclick="submitAddCanvas()">Save</button>
        <button onclick="closeAddModal()">Cancel</button>
      </div>
    </div>
  </div>
  <table>
    <thead>
      <tr><th>#</th><th>Name</th><th>ID</th><th>Info</th><th>Actions</th></tr>
    </thead>
    <tbody id="tbody"></tbody>
  </table>
</body>
</html>
"""


@router.get("/admin", response_class=HTMLResponse)
def admin_page():
    origin = settings.PUBLIC_ORIGIN or ""
    injected = PAGE.replace("__APP_ORIGIN__", f"{origin!r}")
    return HTMLResponse(injected)
