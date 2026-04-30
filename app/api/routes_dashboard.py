from html import escape
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse

from app.api.dependencies import get_store
from app.models.api import ProxyResponse
from app.models.dashboard import DashboardView
from app.services.dashboard_service import DashboardService
from app.storage.redis_store import RedisStore

router = APIRouter(tags=["dashboard"])


def get_dashboard_service(store: Annotated[RedisStore, Depends(get_store)]) -> DashboardService:
    return DashboardService(store)


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    service: Annotated[DashboardService, Depends(get_dashboard_service)],
) -> HTMLResponse:
    view = await service.get_dashboard()
    return HTMLResponse(_render_dashboard(view))


def _render_dashboard(view: DashboardView) -> str:
    pool_rows = "\n".join(
        f"""
        <tr>
          <th>{escape(pool)}</th>
          <td>{count}</td>
        </tr>
        """
        for pool, count in view.pools.items()
    )
    source_rows = "\n".join(
        f"""
        <tr>
          <th>{escape(item.source)}</th>
          <td>{item.count}</td>
        </tr>
        """
        for item in view.sources
    ) or '<tr><td colspan="2" class="empty">No sources</td></tr>'
    proxy_rows = "\n".join(_render_proxy_row(proxy) for proxy in view.proxies)
    proxy_rows = proxy_rows or '<tr><td colspan="8" class="empty">No proxies</td></tr>'

    average_latency = _format_number(view.average_latency_ms, suffix=" ms")
    success_rate = _format_percent(view.success_rate)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ProxyPool Architect Dashboard</title>
  <style>
    :root {{
      --bg: #f6f7f4;
      --surface: #ffffff;
      --border: #d9ded6;
      --text: #20241f;
      --muted: #667064;
      --accent: #2f6f4e;
      --danger: #a13d32;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: Aptos, "IBM Plex Sans", sans-serif;
      font-size: 14px;
      line-height: 1.45;
    }}
    main {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 28px;
    }}
    header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
      margin-bottom: 20px;
    }}
    h1, h2 {{
      margin: 0;
      font-size: 18px;
      font-weight: 650;
      letter-spacing: 0;
    }}
    h2 {{ font-size: 15px; margin-bottom: 10px; }}
    .muted {{ color: var(--muted); }}
    .summary {{
      display: grid;
      grid-template-columns: repeat(4, minmax(120px, 1fr));
      gap: 12px;
      margin-bottom: 20px;
    }}
    .summary-item, section {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
    }}
    .summary-item {{ padding: 12px; }}
    .summary-item b {{ display: block; font-size: 20px; margin-bottom: 2px; }}
    .columns {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
      margin-bottom: 16px;
    }}
    section {{ padding: 14px; }}
    table {{
      width: 100%;
      border-collapse: collapse;
    }}
    th, td {{
      padding: 9px 8px;
      border-bottom: 1px solid var(--border);
      text-align: left;
      vertical-align: middle;
      white-space: nowrap;
    }}
    th {{ font-weight: 600; }}
    tr:last-child th, tr:last-child td {{ border-bottom: 0; }}
    .table-wrap {{ overflow-x: auto; }}
    .empty {{ color: var(--muted); text-align: center; }}
    button {{
      border: 1px solid var(--border);
      border-radius: 6px;
      background: #fff;
      color: var(--danger);
      padding: 6px 9px;
      cursor: pointer;
      font: inherit;
    }}
    button:hover {{ border-color: var(--danger); }}
    @media (max-width: 780px) {{
      main {{ padding: 18px; }}
      header {{ align-items: flex-start; flex-direction: column; }}
      .summary, .columns {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <main>
    <header>
      <h1>ProxyPool Architect</h1>
      <div class="muted">Dashboard</div>
    </header>

    <div class="summary">
      <div class="summary-item"><b>{view.total}</b><span>Total proxies</span></div>
      <div class="summary-item"><b>{view.pools.get("elite", 0)}</b><span>Elite</span></div>
      <div class="summary-item"><b>{average_latency}</b><span>Average latency</span></div>
      <div class="summary-item"><b>{success_rate}</b><span>Success rate</span></div>
    </div>

    <div class="columns">
      <section>
        <h2>Pools</h2>
        <table><tbody>{pool_rows}</tbody></table>
      </section>
      <section>
        <h2>Sources</h2>
        <table><tbody>{source_rows}</tbody></table>
      </section>
    </div>

    <section>
      <h2>Proxies</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Status</th>
              <th>Source</th>
              <th>Country</th>
              <th>Anonymity</th>
              <th>Latency</th>
              <th>Score</th>
              <th></th>
            </tr>
          </thead>
          <tbody>{proxy_rows}</tbody>
        </table>
      </div>
    </section>
  </main>
  <script>
    document.addEventListener("click", async (event) => {{
      const button = event.target.closest("[data-delete-id]");
      if (!button) return;
      button.disabled = true;
      const id = button.getAttribute("data-delete-id");
      const response = await fetch(`/proxy/${{encodeURIComponent(id)}}`, {{ method: "DELETE" }});
      if (response.ok) window.location.reload();
      else button.disabled = false;
    }});
  </script>
</body>
</html>"""


def _render_proxy_row(proxy: ProxyResponse) -> str:
    latency = _format_number(proxy.latency_ms, suffix=" ms")
    country = escape(proxy.country or "")
    return f"""
    <tr>
      <td>{escape(proxy.id)}</td>
      <td>{escape(proxy.status)}</td>
      <td>{escape(proxy.source)}</td>
      <td>{country}</td>
      <td>{escape(proxy.anonymity)}</td>
      <td>{latency}</td>
      <td>{proxy.score}</td>
      <td><button type="button" data-delete-id="{escape(proxy.id)}">Delete</button></td>
    </tr>
    """


def _format_number(value: float | int | None, suffix: str = "") -> str:
    if value is None:
        return "-"
    return f"{round(value, 1)}{suffix}"


def _format_percent(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{round(value * 100, 1)}%"
