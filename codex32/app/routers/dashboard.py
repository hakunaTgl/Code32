"""
Interactive dashboard for system monitoring and bot management.

Serves an HTML dashboard that displays:
- System health status
- Bot inventory with status breakdown
- Real-time recommendations
- Quick action buttons for common operations
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from app.dependencies import get_registry, get_executor
from app.supervisor import get_supervisor
from app.bot_registry import SecureRegistry
from app.adaptive_executor import AdaptiveExecutor

router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])


def _get_supervisor():
    """Get singleton supervisor instance."""
    try:
        return get_supervisor()
    except:
        return None


def _compute_dashboard_state(registry: SecureRegistry, executor: AdaptiveExecutor) -> dict:
    """Compute the dashboard snapshot used by both HTML and JSON endpoints."""
    supervisor = _get_supervisor()

    # `SecureRegistry` exposes `get_all_bots()`.
    bots = registry.get_all_bots()
    total_bots = len(bots)

    # Count statuses
    running = sum(1 for b in bots if b.status == "running")
    stopped = sum(1 for b in bots if b.status == "stopped")
    deploying = sum(1 for b in bots if b.status == "deploying")
    failed = sum(1 for b in bots if b.status == "failed")

    # Determine health
    if failed > 0:
        system_health = "critical"
        health_color = "#dc3545"
        health_emoji = "🔴"
    elif deploying > 0:
        system_health = "degraded"
        health_color = "#ffc107"
        health_emoji = "🟡"
    else:
        system_health = "healthy"
        health_color = "#28a745"
        health_emoji = "🟢"

    # Supervisor incidents are stored in an IncidentLog; use `.tail()`.
    incidents_count = len(supervisor.incidents.tail()) if supervisor else 0

    # Build recommendations
    recommendations: list[dict] = []
    if total_bots == 0:
        recommendations.append(
            {
                "priority": "high",
                "emoji": "🚀",
                "title": "Get Started",
                "description": "Create your first bot",
                "action": {"method": "POST", "path": "/api/v1/bots"},
                "button_text": "Create Bot",
            }
        )
    elif running == 0 and total_bots > 0:
        recommendations.append(
            {
                "priority": "high",
                "emoji": "▶️",
                "title": "Start Bots",
                "description": f"You have {total_bots} bot(s) ready to run",
                "action": {"method": "POST", "path": "/api/v1/bots/{bot_id}/start"},
                "button_text": "Start First Bot",
            }
        )

    if failed > 0:
        recommendations.append(
            {
                "priority": "high",
                "emoji": "⚠️",
                "title": "Check Failures",
                "description": f"{failed} bot(s) have failed",
                "action": {"method": "GET", "path": "/api/v1/self/incidents"},
                "button_text": "View Incidents",
            }
        )

    recommendations.append(
        {
            "priority": "medium",
            "emoji": "📚",
            "title": "Explore API",
            "description": "Browse all available endpoints",
            "action": {"method": "GET", "path": "/docs"},
            "button_text": "API Docs",
        }
    )

    bots_payload = []
    for b in bots:
        bots_payload.append(
            {
                "id": b.id,
                "name": getattr(b, "name", None),
                "role": getattr(b, "role", None),
                "status": getattr(b, "status", None),
            }
        )

    return {
        "health": {
            "system_health": system_health,
            "emoji": health_emoji,
            "color": health_color,
        },
        "bots": {
            "total": total_bots,
            "running": running,
            "stopped": stopped,
            "deploying": deploying,
            "failed": failed,
            "items": bots_payload,
        },
        "executor": {
            "running_processes": list(executor.running_processes.keys()),
            "running_containers": executor.running_containers,
        },
        "supervisor": {
            "enabled": bool(supervisor),
            "incidents_count": incidents_count,
        },
        "recommendations": recommendations,
        "links": {
            "dashboard": "/api/v1/dashboard",
            "api_docs": "/docs",
            "guide": "/api/v1/guide/hello",
            "onboarding": "/api/v1/guide/onboarding",
            "bot_inventory": "/api/v1/bots",
            "incidents": "/api/v1/self/incidents",
        },
    }


@router.get("/data", summary="Dashboard data", response_description="JSON snapshot used by the HTML dashboard")
def dashboard_data(
    registry: SecureRegistry = Depends(get_registry),
    executor: AdaptiveExecutor = Depends(get_executor),
) -> dict:
    """Return a JSON snapshot of dashboard state for live updates."""
    return _compute_dashboard_state(registry=registry, executor=executor)


@router.get("", response_class=HTMLResponse)
def dashboard(
    registry: SecureRegistry = Depends(get_registry),
    executor: AdaptiveExecutor = Depends(get_executor),
) -> str:
    """
    Interactive dashboard for system monitoring.

    Displays system status, bot inventory, health metrics, and actionable recommendations.
    Auto-refreshes every 5 seconds.
    """
    state = _compute_dashboard_state(registry=registry, executor=executor)
    total_bots = state["bots"]["total"]
    running = state["bots"]["running"]
    stopped = state["bots"]["stopped"]
    deploying = state["bots"]["deploying"]
    failed = state["bots"]["failed"]
    incidents_count = state["supervisor"]["incidents_count"]
    health = state["health"]["system_health"]
    health_color = state["health"]["color"]
    health_emoji = state["health"]["emoji"]
    recommendations = state["recommendations"]

    # Convert structured action {method,path} into a simple string for the existing HTML template.
    for rec in recommendations:
        action = rec.get("action")
        if isinstance(action, dict):
            rec["action"] = f"{action.get('method', 'GET')} {action.get('path', '')}".strip()

    bots = registry.get_all_bots()

    # Build bot list HTML
    bot_rows = ""
    if total_bots == 0:
        bot_rows = '<tr><td colspan="5" class="text-center text-muted">No bots created yet</td></tr>'
    else:
        for bot in bots:
            status_badge = {
                "running": '<span class="badge bg-success">▶️ Running</span>',
                "stopped": '<span class="badge bg-secondary">⏹️ Stopped</span>',
                "deploying": '<span class="badge bg-info">⏳ Deploying</span>',
                "failed": '<span class="badge bg-danger">❌ Failed</span>',
                "created": '<span class="badge bg-light text-dark">✨ Created</span>',
            }.get(bot.status, f'<span class="badge bg-dark">{bot.status}</span>')

            start_button = '<button class="btn btn-sm btn-outline-success" onclick="startBot(\'' + bot.id + '\')">Start</button>' if bot.status in ["stopped", "failed", "created"] else ''
            stop_button = '<button class="btn btn-sm btn-outline-warning" onclick="stopBot(\'' + bot.id + '\')">Stop</button>' if bot.status == "running" else ''

            bot_rows += f"""
            <tr>
                <td><code>{bot.id}</code></td>
                <td>{bot.name or "—"}</td>
                <td>{status_badge}</td>
                <td>{bot.role or "—"}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="viewBot('{bot.id}')">View</button>
                    {start_button}
                    {stop_button}
                </td>
            </tr>
            """

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Codex-32 Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            * {{
                --primary: #007bff;
                --success: #28a745;
                --danger: #dc3545;
                --warning: #ffc107;
                --dark: #343a40;
            }}

            body {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                color: #333;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }}

            /* More professional look */
            .navbar {{
                box-shadow: 0 10px 30px rgba(0,0,0,0.18);
            }}

            .health-card, .recommendations-section, .bots-section {{
                border: 1px solid rgba(15, 23, 42, 0.06);
            }}

            .badge {{
                font-weight: 600;
                letter-spacing: 0.2px;
            }}

            .btn {{
                border-radius: 10px;
            }}

            .btn:focus {{
                box-shadow: 0 0 0 .25rem rgba(0, 123, 255, 0.25);
            }}

            .modal-content {{
                border-radius: 14px;
                border: 1px solid rgba(15, 23, 42, 0.10);
                box-shadow: 0 25px 80px rgba(0,0,0,0.35);
            }}

            .form-control, .form-select {{
                border-radius: 10px;
            }}

            .toast-container {{
                z-index: 1100;
            }}

            .navbar-brand {{
                font-weight: 700;
                font-size: 1.5rem;
                letter-spacing: -0.5px;
            }}

            .dashboard-container {{
                margin-top: 2rem;
                margin-bottom: 2rem;
            }}

            .health-card {{
                background: white;
                border-radius: 12px;
                padding: 2rem;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                margin-bottom: 2rem;
                border-left: 6px solid {health_color};
            }}

            .health-header {{
                display: flex;
                align-items: center;
                gap: 1rem;
                margin-bottom: 1.5rem;
            }}

            .health-emoji {{
                font-size: 3rem;
            }}

            .health-info h2 {{
                margin: 0;
                font-size: 1.8rem;
                font-weight: 700;
            }}

            .health-status {{
                color: #666;
                font-size: 0.95rem;
            }}

            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
                gap: 1rem;
                margin-bottom: 2rem;
            }}

            .stat-card {{
                background: white;
                border-radius: 8px;
                padding: 1.5rem;
                text-align: center;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
                border-top: 4px solid #007bff;
            }}

            .stat-number {{
                font-size: 2.5rem;
                font-weight: 700;
                color: #007bff;
                margin-bottom: 0.5rem;
            }}

            .stat-label {{
                color: #666;
                font-size: 0.9rem;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}

            .recommendations-section {{
                background: white;
                border-radius: 12px;
                padding: 2rem;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                margin-bottom: 2rem;
            }}

            .recommendation-card {{
                padding: 1.5rem;
                border-left: 4px solid #007bff;
                background: #f8f9fa;
                border-radius: 6px;
                margin-bottom: 1rem;
                transition: all 0.3s ease;
            }}

            .recommendation-card:hover {{
                transform: translateX(4px);
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            }}

            .recommendation-card.high {{
                border-left-color: #dc3545;
                background: #fff5f5;
            }}

            .recommendation-card.medium {{
                border-left-color: #ffc107;
                background: #fffbf0;
            }}

            .recommendation-card.low {{
                border-left-color: #28a745;
                background: #f5fff5;
            }}

            .rec-header {{
                display: flex;
                align-items: center;
                gap: 0.5rem;
                margin-bottom: 0.5rem;
            }}

            .rec-emoji {{
                font-size: 1.5rem;
            }}

            .rec-title {{
                font-weight: 700;
                font-size: 1.1rem;
                margin: 0;
            }}

            .rec-description {{
                color: #666;
                font-size: 0.9rem;
                margin: 0.5rem 0 0 0;
            }}

            .rec-action {{
                color: #007bff;
                font-size: 0.85rem;
                font-family: 'Courier New', monospace;
                margin-top: 0.5rem;
            }}

            .bots-section {{
                background: white;
                border-radius: 12px;
                padding: 2rem;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}

            .section-title {{
                font-size: 1.5rem;
                font-weight: 700;
                margin-bottom: 1.5rem;
                color: #333;
            }}

            table {{
                margin: 0;
            }}

            tbody tr {{
                border-bottom: 1px solid #e9ecef;
                transition: background-color 0.2s ease;
            }}

            tbody tr:hover {{
                background-color: #f8f9fa;
            }}

            .btn {{
                font-size: 0.85rem;
                padding: 0.4rem 0.8rem;
            }}

            .refresh-info {{
                color: #666;
                font-size: 0.9rem;
                margin-top: 1rem;
                text-align: center;
            }}

            .footer {{
                background: rgba(255, 255, 255, 0.1);
                color: white;
                padding: 2rem;
                text-align: center;
                margin-top: 3rem;
            }}

            .footer a {{
                color: #fff;
                text-decoration: none;
            }}

            .footer a:hover {{
                text-decoration: underline;
            }}
        </style>
    </head>
    <body>
        <nav class="navbar navbar-dark bg-dark">
            <div class="container-fluid">
                <span class="navbar-brand">Codex-32 Console</span>
                <span class="navbar-text">Operations & bot intelligence</span>
            </div>
        </nav>

        <div class="container dashboard-container">
            <!-- Health Status -->
            <div class="health-card" id="healthCard" data-health="{health}">
                <div class="health-header">
                    <div class="health-emoji" id="healthEmoji">{health_emoji}</div>
                    <div class="health-info">
                        <h2>System Health: <span id="healthText">{health.upper()}</span></h2>
                        <p class="health-status">Updated: <span id="lastUpdate">Just now</span> • <span id="pollStatus">Live</span></p>
                    </div>
                </div>

                <!-- Stats Grid -->
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number" id="statTotal">{total_bots}</div>
                        <div class="stat-label">Total Bots</div>
                    </div>
                    <div class="stat-card" style="border-top-color: #28a745;">
                        <div class="stat-number" style="color: #28a745;" id="statRunning">{running}</div>
                        <div class="stat-label">Running</div>
                    </div>
                    <div class="stat-card" style="border-top-color: #6c757d;">
                        <div class="stat-number" style="color: #6c757d;" id="statStopped">{stopped}</div>
                        <div class="stat-label">Stopped</div>
                    </div>
                    <div class="stat-card" style="border-top-color: #17a2b8;">
                        <div class="stat-number" style="color: #17a2b8;" id="statDeploying">{deploying}</div>
                        <div class="stat-label">Deploying</div>
                    </div>
                    <div class="stat-card" style="border-top-color: #dc3545;">
                        <div class="stat-number" style="color: #dc3545;" id="statFailed">{failed}</div>
                        <div class="stat-label">Failed</div>
                    </div>
                    <div class="stat-card" style="border-top-color: #6f42c1;">
                        <div class="stat-number" style="color: #6f42c1;" id="statIncidents">{incidents_count}</div>
                        <div class="stat-label">Incidents</div>
                    </div>
                </div>
            </div>

            <!-- Recommendations -->
            <div class="recommendations-section">
                <h3 class="section-title">Next best actions</h3>
                <div class="text-muted" style="margin-top:-6px; margin-bottom: 12px; font-size: 0.95rem;">Recommendations adapt to current live state.</div>
                <div id="recommendationsRoot">
                {''.join([f'''
                <div class="recommendation-card {rec['priority']}">
                    <div class="rec-header">
                        <span class="rec-emoji">{rec['emoji']}</span>
                        <h4 class="rec-title">{rec['title']}</h4>
                    </div>
                    <p class="rec-description">{rec['description']}</p>
                    <div class="rec-action">API: {rec['action']}</div>
                    <button class="btn btn-sm btn-primary mt-2" onclick="executeAction('{rec['action']}')">{rec['button_text']}</button>
                </div>
                ''' for rec in recommendations])}
                </div>
            </div>

            <!-- Bots Inventory -->
            <div class="bots-section">
                <h3 class="section-title">🤖 Bot Inventory</h3>
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <div class="text-muted" style="font-size: 0.95rem;">Fast actions. Live health. Zero docs required.</div>
                    <div class="d-flex gap-2">
                        <button class="btn btn-primary" type="button" id="openCreateBotBtn">+ Create bot</button>
                        <button class="btn btn-outline-secondary" type="button" id="manualRefreshBtn">Refresh</button>
                    </div>
                </div>
                <div class="table-responsive">
                    <table class="table table-hover">
                        <thead class="table-light">
                            <tr>
                                <th>Bot ID</th>
                                <th>Name</th>
                                <th>Status</th>
                                <th>Role</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="botTableBody">
                            {bot_rows}
                        </tbody>
                    </table>
                </div>
                <div class="refresh-info">
                    Live updates: every 2 seconds (pauses while you’re creating a bot).
                </div>
            </div>
        </div>

        <div class="footer">
            <p>
                📖 <a href="/docs">API Docs</a> •
                🧭 <a href="/api/v1/guide/hello">Guide</a> •
                📋 <a href="/api/v1/bots">Bot Inventory</a> •
                🆘 <a href="/api/v1/self/incidents">Incidents</a>
            </p>
            <p style="font-size: 0.9rem; margin-top: 1rem;">Codex-32 Autonomous Bot Framework</p>
        </div>

                <!-- Create Bot Modal -->
                <div class="modal fade" id="createBotModal" tabindex="-1" aria-hidden="true">
                    <div class="modal-dialog modal-dialog-centered">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">Create bot</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                            </div>
                            <form id="createBotForm">
                                <div class="modal-body">
                                                        <div class="mb-3">
                                                            <label for="botName" class="form-label">Name</label>
                                                            <input class="form-control" id="botName" name="name" autocomplete="off" required />
                                                            <div class="form-text">Example: “Invoice Runner”, “Support Agent”, “Deploy Bot”.</div>
                                                        </div>

                                                        <div class="mb-3">
                                                            <label for="botId" class="form-label">Bot ID</label>
                                                            <input class="form-control" id="botId" name="id" autocomplete="off" />
                                                            <div class="form-text">Auto-generated from the name (editable). Use lowercase and hyphens.</div>
                                                        </div>

                                    <div class="row g-3">
                                        <div class="col-md-6">
                                            <label for="botRole" class="form-label">Role</label>
                                            <select class="form-select" id="botRole" name="role">
                                                <option value="worker" selected>worker</option>
                                                <option value="supervisor">supervisor</option>
                                                <option value="coordinator">coordinator</option>
                                            </select>
                                        </div>
                                        <div class="col-md-6">
                                                                    <label for="botBlueprint" class="form-label">Blueprint</label>
                                                                    <input class="form-control" id="botBlueprint" name="blueprint" autocomplete="off" value="sample_bot.py" list="blueprintSuggestions" />
                                        </div>
                                    </div>
                                                            <datalist id="blueprintSuggestions">
                                                                <option value="sample_bot.py"></option>
                                                                <option value="support_bot.py"></option>
                                                                <option value="automation_bot.py"></option>
                                                                <option value="research_bot.py"></option>
                                                            </datalist>
                                                            <div class="form-text mt-1">Tip: store blueprints in <code>bots/</code>.</div>

                                    <div class="mt-3">
                                        <label for="botDescription" class="form-label">Description (optional)</label>
                                        <textarea class="form-control" id="botDescription" name="description" rows="3" spellcheck="false"></textarea>
                                    </div>

                                    <div class="alert alert-danger mt-3 d-none" id="createBotError" role="alert"></div>
                                </div>
                                <div class="modal-footer">
                                    <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Cancel</button>
                                    <button type="submit" class="btn btn-primary" id="createBotSubmit">Create</button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>

                <!-- Toast -->
                <div class="toast-container position-fixed top-0 end-0 p-3">
                    <div id="opToast" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
                        <div class="toast-header">
                            <strong class="me-auto" id="opToastTitle">Codex-32</strong>
                            <small class="text-muted">now</small>
                            <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
                        </div>
                        <div class="toast-body" id="opToastBody"></div>
                    </div>
                </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            // Live polling (fast) instead of full page reload.
            const DATA_URL = '/api/v1/dashboard/data';
            const POLL_MS = 2000;
            let pollTimer = null;

            function nowTime() {{
                return new Date().toLocaleTimeString();
            }}

            function escapeHtml(s) {{
                return String(s)
                    .replaceAll('&', '&amp;')
                    .replaceAll('<', '&lt;')
                    .replaceAll('>', '&gt;')
                    .replaceAll('"', '&quot;')
                    .replaceAll("'", '&#039;');
            }}

            function slugify(s) {{
                return String(s || '')
                    .trim()
                    .toLowerCase()
                    .replace(/[^a-z0-9]+/g, '-')
                    .replace(/(^-|-$)/g, '');
            }}

            function rememberDefaults(role, blueprint) {{
                try {{
                    localStorage.setItem('codex32:lastRole', role || 'worker');
                    localStorage.setItem('codex32:lastBlueprint', blueprint || 'sample_bot.py');
                }} catch (e) {{}}
            }}

            function loadDefaults() {{
                try {{
                    return {{
                        role: localStorage.getItem('codex32:lastRole') || 'worker',
                        blueprint: localStorage.getItem('codex32:lastBlueprint') || 'sample_bot.py',
                    }};
                }} catch (e) {{
                    return {{ role: 'worker', blueprint: 'sample_bot.py' }};
                }}
            }}

            function badgeForStatus(status) {{
                const map = {{
                    running: '<span class="badge bg-success">▶️ Running</span>',
                    stopped: '<span class="badge bg-secondary">⏹️ Stopped</span>',
                    deploying: '<span class="badge bg-info">⏳ Deploying</span>',
                    failed: '<span class="badge bg-danger">❌ Failed</span>',
                    created: '<span class="badge bg-light text-dark">✨ Created</span>',
                }};
                return map[status] || (`<span class="badge bg-dark">${{escapeHtml(status)}}</span>`);
            }}

            function rowForBot(bot) {{
                const id = escapeHtml(bot.id || '');
                const name = escapeHtml(bot.name || '—');
                const role = escapeHtml(bot.role || '—');
                const status = escapeHtml(bot.status || 'unknown');

                const startBtn = (['stopped', 'failed', 'created'].includes(bot.status))
                    ? `<button class="btn btn-sm btn-outline-success" onclick="startBot('${{id}}')">Start</button>`
                    : '';
                const stopBtn = (bot.status === 'running')
                    ? `<button class="btn btn-sm btn-outline-warning" onclick="stopBot('${{id}}')">Stop</button>`
                    : '';

                return `
                <tr>
                    <td><code>${{id}}</code></td>
                    <td>${{name}}</td>
                    <td>${{badgeForStatus(status)}}</td>
                    <td>${{role}}</td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary" onclick="viewBot('${{id}}')">View</button>
                        ${{startBtn}}
                        ${{stopBtn}}
                    </td>
                </tr>
                `;
            }}

            function renderRecommendations(recs) {{
                const root = document.getElementById('recommendationsRoot');
                if (!root) return;
                if (!Array.isArray(recs) || recs.length === 0) {{
                    root.innerHTML = '<div class="text-muted">No recommendations right now.</div>';
                    return;
                }}

                root.innerHTML = recs.map((rec) => {{
                    const priority = escapeHtml(rec.priority || 'medium');
                    const emoji = escapeHtml(rec.emoji || '💡');
                    const title = escapeHtml(rec.title || 'Action');
                    const desc = escapeHtml(rec.description || '');
                    const action = rec.action;
                    const actionStr = (typeof action === 'string') ? action : `${{action?.method || 'GET'}} ${{action?.path || ''}}`;
                    const buttonText = escapeHtml(rec.button_text || 'Run');
                    const actionEsc = escapeHtml(actionStr);
                    return `
                    <div class="recommendation-card ${{priority}}">
                        <div class="rec-header">
                            <span class="rec-emoji">${{emoji}}</span>
                            <h4 class="rec-title">${{title}}</h4>
                        </div>
                        <p class="rec-description">${{desc}}</p>
                        <div class="rec-action">API: ${{actionEsc}}</div>
                        <button class="btn btn-sm btn-primary mt-2" onclick="executeAction('${{actionEsc}}')">${{buttonText}}</button>
                    </div>
                    `;
                }}).join('');
            }}

            function applySnapshot(state) {{
                if (!state) return;
                const health = state.health || {{}};
                const bots = state.bots || {{}};
                const sup = state.supervisor || {{}};

                const card = document.getElementById('healthCard');
                if (card && health.color) card.style.borderLeftColor = health.color;
                const healthEmojiEl = document.getElementById('healthEmoji');
                const healthTextEl = document.getElementById('healthText');
                if (healthEmojiEl) healthEmojiEl.textContent = health.emoji || '🟢';
                if (healthTextEl) {{
                    const t = (health.system_health || 'healthy');
                    healthTextEl.textContent = String(t).toUpperCase();
                }}

                const setText = (id, value) => {{
                    const el = document.getElementById(id);
                    if (el) el.textContent = String(value ?? '0');
                }};
                setText('statTotal', bots.total);
                setText('statRunning', bots.running);
                setText('statStopped', bots.stopped);
                setText('statDeploying', bots.deploying);
                setText('statFailed', bots.failed);
                setText('statIncidents', sup.incidents_count);

                const body = document.getElementById('botTableBody');
                if (body) {{
                    const items = Array.isArray(bots.items) ? bots.items : [];
                    if (items.length === 0) {{
                        body.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No bots created yet</td></tr>';
                    }} else {{
                        body.innerHTML = items.map(rowForBot).join('');
                    }}
                }}

                renderRecommendations(state.recommendations || []);

                const lastUpdateEl = document.getElementById('lastUpdate');
                if (lastUpdateEl) lastUpdateEl.textContent = nowTime();
            }}

            async function pollOnce() {{
                const pollStatus = document.getElementById('pollStatus');
                try {{
                    if (pollStatus) pollStatus.textContent = 'Live';
                    const resp = await fetch(DATA_URL, {{ cache: 'no-store' }});
                    if (!resp.ok) throw new Error('Bad status: ' + resp.status);
                    const state = await resp.json();
                    applySnapshot(state);
                }} catch (e) {{
                    if (pollStatus) pollStatus.textContent = 'Offline';
                }}
            }}

            function startPolling() {{
                if (pollTimer) return;
                pollOnce();
                pollTimer = setInterval(() => {{
                    const modalEl = document.getElementById('createBotModal');
                    const isModalOpen = modalEl && modalEl.classList.contains('show');
                    if (!isModalOpen) pollOnce();
                }}, POLL_MS);
            }}

            function stopPolling() {{
                if (pollTimer) clearInterval(pollTimer);
                pollTimer = null;
            }}

            const createModalEl = document.getElementById('createBotModal');
            const createModal = createModalEl ? new bootstrap.Modal(createModalEl, {{
                backdrop: 'static',
                keyboard: true,
                focus: true,
            }}) : null;

            if (createModalEl) {{
                createModalEl.addEventListener('shown.bs.modal', () => {{
                    stopPolling();
                }});
                createModalEl.addEventListener('hidden.bs.modal', () => {{
                    startPolling();
                }});
            }}

            const manualRefreshBtn = document.getElementById('manualRefreshBtn');
            if (manualRefreshBtn) {{
                manualRefreshBtn.addEventListener('click', () => {{
                    pollOnce();
                }});
            }}

            const openCreateBotBtn = document.getElementById('openCreateBotBtn');
            if (openCreateBotBtn && createModal) {{
                openCreateBotBtn.addEventListener('click', () => {{
                    const form = document.getElementById('createBotForm');
                    const err = document.getElementById('createBotError');
                    const defs = loadDefaults();
                    if (form) form.reset();
                    if (err) {{
                        err.classList.add('d-none');
                        err.textContent = '';
                    }}
                    const roleEl = document.getElementById('botRole');
                    const bpEl = document.getElementById('botBlueprint');
                    if (roleEl) roleEl.value = defs.role;
                    if (bpEl) bpEl.value = defs.blueprint;
                    createModal.show();
                    setTimeout(() => {{
                        const nameEl = document.getElementById('botName');
                        if (nameEl) nameEl.focus();
                    }}, 150);
                }});
            }}

            const botNameEl = document.getElementById('botName');
            const botIdEl = document.getElementById('botId');
            if (botNameEl && botIdEl) {{
                botNameEl.addEventListener('input', () => {{
                    const name = botNameEl.value || '';
                    const current = botIdEl.value || '';
                    if (!current || current === slugify(current)) {{
                        const slug = slugify(name);
                        if (slug) botIdEl.value = slug;
                    }}
                }});
            }}

            function toast(title, body) {{
                const titleEl = document.getElementById('opToastTitle');
                const bodyEl = document.getElementById('opToastBody');
                if (titleEl) titleEl.textContent = title;
                if (bodyEl) bodyEl.textContent = body;
                const toastEl = document.getElementById('opToast');
                if (toastEl) {{
                    const t = new bootstrap.Toast(toastEl, {{ delay: 2500 }});
                    t.show();
                }}
            }}

            function viewBot(botId) {{
                // Show bot details (could expand to a modal in future)
                const msg = "Viewing bot: " + botId + "\n\nAPI Endpoint: GET /api/v1/bots/" + botId;
                alert(msg);
            }}

            function startBot(botId) {{
                if (confirm("Start bot: " + botId + "?")) {{
                    fetch("/api/v1/bots/" + botId + "/start", {{ method: 'POST' }})
                        .then(r => r.json())
                        .then(data => {{
                            toast('Bot start', data.message || 'Starting bot...');
                            setTimeout(() => pollOnce(), 250);
                        }})
                        .catch(e => alert("Error: " + e.message));
                }}
            }}

            function stopBot(botId) {{
                if (confirm("Stop bot: " + botId + "?")) {{
                    fetch("/api/v1/bots/" + botId + "/stop", {{ method: 'POST' }})
                        .then(r => r.json())
                        .then(data => {{
                            toast('Bot stop', data.message || 'Stopping bot...');
                            setTimeout(() => pollOnce(), 250);
                        }})
                        .catch(e => alert("Error: " + e.message));
                }}
            }}

            function executeAction(action) {{
                // For create actions, open the modal instead of using a prompt.
                if (action.startsWith('POST') && action.includes('/api/v1/bots')) {{
                    if (createModal) createModal.show();
                    return;
                }}
                window.location.href = action;
            }}

            const createBotForm = document.getElementById('createBotForm');
            if (createBotForm) {{
                createBotForm.addEventListener('submit', async (e) => {{
                    e.preventDefault();
                    const err = document.getElementById('createBotError');
                    const submitBtn = document.getElementById('createBotSubmit');
                    if (err) {{
                        err.classList.add('d-none');
                        err.textContent = '';
                    }}
                    if (submitBtn) submitBtn.disabled = true;

                    const name = (document.getElementById('botName')?.value || '').trim();
                    const botIdRaw = (document.getElementById('botId')?.value || '').trim();
                    const role = (document.getElementById('botRole')?.value || 'worker').trim();
                    const blueprint = (document.getElementById('botBlueprint')?.value || 'sample_bot.py').trim();
                    const description = (document.getElementById('botDescription')?.value || '').trim();

                    if (!name) {{
                        if (err) {{
                            err.textContent = 'Name is required.';
                            err.classList.remove('d-none');
                        }}
                        if (submitBtn) submitBtn.disabled = false;
                        return;
                    }}

                    const botId = botIdRaw || (slugify(name) || ('bot-' + Date.now()));

                    try {{
                        const resp = await fetch('/api/v1/bots', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json' }},
                            body: JSON.stringify({{
                                id: botId,
                                name,
                                description,
                                blueprint,
                                role,
                                status: 'created',
                                deployment_config: {{ deployment_type: 'local_process' }},
                            }}),
                        }});

                        if (!resp.ok) {{
                            const txt = await resp.text();
                            throw new Error(txt || 'Failed to create bot');
                        }}

                        rememberDefaults(role, blueprint);
                        toast('Bot created', 'Created ' + botId);
                        if (createModal) createModal.hide();
                        setTimeout(() => pollOnce(), 250);
                    }} catch (e) {{
                        if (err) {{
                            err.textContent = (e && e.message) ? e.message : 'Error creating bot';
                            err.classList.remove('d-none');
                        }}
                    }} finally {{
                        if (submitBtn) submitBtn.disabled = false;
                    }}
                }});
            }}

            // Start polling once page loads.
            startPolling();
        </script>
    </body>
    </html>
    """

    return html
