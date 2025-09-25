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
  </style>
  <script>
    const APP_ORIGIN = __APP_ORIGIN__;
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
              <a href="${APP_ORIGIN ? APP_ORIGIN : ''}/api/v2/${it.id}" target="_blank"><button>Open</button></a>
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
    <span class="muted">Manage saved canvases</span>
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
    origin = settings.APP_PUBLIC_ORIGIN or ""
    injected = PAGE.replace("__APP_ORIGIN__", f"{origin!r}")
    return HTMLResponse(injected)
