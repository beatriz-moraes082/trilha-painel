"""
Painel de saúde Beatriz — Trilha Performance Digital.
Gera index.html com status de todos os clientes da carteira.

Uso local:
    python3 build.py

GitHub Actions: roda a cada 6h, deploy pra GitHub Pages.
"""

import json
import os
import re
import sys
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path

# ─── ENV ─────────────────────────────────────────────────────────────────────

def load_env():
    env = dict(os.environ)
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                k, v = k.strip(), v.strip()
                if k not in env:
                    env[k] = v
    return env

ENV = load_env()

# ─── HTTP ─────────────────────────────────────────────────────────────────────

def http_get(url, headers=None, params=None):
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise RuntimeError(f"HTTP {e.code}: {body[:200]}") from e

# ─── CATÁLOGO DE CLIENTES ─────────────────────────────────────────────────────

CLIENTS = [
    # Auto
    {
        "id": "motochefe",
        "name": "MotoChefe",
        "nicho": "Auto",
        "assessor": "Enrique",
        "meta_names": ["Grupo MGS [Moto Chefe/ Mixmobi]"],
        "report_repo": "motochefe-report",
    },
    {
        "id": "taiyo",
        "name": "Taiyo Honda",
        "nicho": "Auto",
        "assessor": "Enrique",
        "meta_names": ["Taiyo - Novos", "Taiyo - Pós-vendas"],
        "report_repo": "taiyo-report",
    },
    # Hotelaria
    {
        "id": "pontaverde",
        "name": "Hotel Ponta Verde",
        "nicho": "Hotelaria",
        "assessor": "Enrique",
        "meta_ids": ["act_299642416227987", "act_317304155022732"],
        "meta_names": ["Hotéis Ponta Verde | Fateixa"],
        "report_repo": "pontaverde-report",
    },
    {
        "id": "mme",
        "name": "MME Vacation Club",
        "nicho": "Hotelaria",
        "assessor": "Enrique",
        "meta_ids": ["act_2352574621900370"],
        "report_repo": "mensuracao-mme",
    },
    {
        "id": "porto-kaete",
        "name": "Porto Kaetê",
        "nicho": "Hotelaria",
        "assessor": "Bruno",
        "meta_ids": ["act_1694414861799101"],
        "report_repo": None,
        "note": "Relatório manual",
    },
    # Imobiliário — carteira Bruno
    {
        "id": "ni",
        "name": "NI Terceiros",
        "nicho": "Imobiliário",
        "assessor": "Bruno",
        "meta_ids": ["act_916115436468748"],
        "report_repo": "niterceiros-report",
    },
    {
        "id": "lion",
        "name": "Lion Imob",
        "nicho": "Imobiliário",
        "assessor": "Bruno",
        "meta_ids": ["act_944021396852680"],
        "report_repo": "lion-report",
    },
    {
        "id": "cros",
        "name": "CROS Empreendimentos",
        "nicho": "Imobiliário",
        "assessor": "Bruno",
        "meta_ids": ["act_3085974161605140"],
        "meta_names": ["Reserva do Peba"],
        "report_repo": "cros-report",
    },
    {
        "id": "inove",
        "name": "Inove Engenharia",
        "nicho": "Imobiliário",
        "assessor": "Bruno",
        "meta_names": ["Mansões - Inove Engenharia", "UANÁ - Inove Engenharia"],
        "report_repo": "inove-report",
    },
    {
        "id": "thiago",
        "name": "Thiago Lessa",
        "nicho": "Imobiliário",
        "assessor": "Bruno",
        "meta_names": ["Thiago Lessa"],
        "report_repo": "thiago-report",
    },
    {
        "id": "maia",
        "name": "Maia Imóveis",
        "nicho": "Imobiliário",
        "assessor": "Bruno",
        "meta_ids": ["act_919375583445318"],
        "report_repo": "maia-report",
    },
    # Imobiliário — outros
    {
        "id": "fellipe",
        "name": "Fellipe Carneiro",
        "nicho": "Imobiliário",
        "assessor": "Enrique",
        "meta_ids": ["act_2366001220473104"],
        "report_repo": "fellipe-report",
    },
    {
        "id": "adelmo",
        "name": "Adelmo Buffone",
        "nicho": "Imobiliário",
        "assessor": "Enrique",
        "meta_ids": ["act_1283935755954413"],
        "report_repo": "adelmo-report",
    },
    {
        "id": "andaza",
        "name": "Andaza Imóveis",
        "nicho": "Imobiliário",
        "assessor": "Enrique",
        "meta_names": ["ANDAZA", "Marca + Andaza"],
        "report_repo": "andaza-report",
    },
    {
        "id": "queiroz",
        "name": "Queiroz Azevedo",
        "nicho": "Imobiliário",
        "assessor": "Enrique",
        "meta_names": ["Queiroz Azevedo"],
        "report_repo": "queiroz-report",
    },
    {
        "id": "henrique",
        "name": "Henrique",
        "nicho": "Imobiliário",
        "assessor": "Enrique",
        "meta_names": ["Henrique"],
        "report_repo": "henrique-report",
    },
    {
        "id": "ype",
        "name": "Ypê",
        "nicho": "Imobiliário",
        "assessor": "Enrique",
        "meta_names": ["Ypê"],
        "report_repo": "ype-report",
    },
    {
        "id": "rafa",
        "name": "Rafaella Mauricio",
        "nicho": "Imobiliário",
        "assessor": "Enrique",
        "meta_names": ["Rafaella Mauricio"],
        "report_repo": "rafaella-report",
    },
    {
        "id": "lucas",
        "name": "Lucas Ferreira",
        "nicho": "Imobiliário",
        "assessor": "Enrique",
        "meta_ids": ["act_107324402700387"],
        "report_repo": None,
        "note": "Relatório manual",
    },
    {
        "id": "renato",
        "name": "Renato Vidal",
        "nicho": "Imobiliário",
        "assessor": "Enrique",
        "meta_ids": ["act_605681643942822"],
        "report_repo": "renato-vidal-report",
    },
    {
        "id": "hl-imoveis",
        "name": "HL Imóveis",
        "nicho": "Imobiliário",
        "assessor": "Enrique",
        "meta_names": ["HL IMOVEIS -  LANCAMENTOS"],
        "report_repo": None,
        "note": "Relatório manual",
    },
    {
        "id": "hl-prime",
        "name": "HL Prime",
        "nicho": "Imobiliário",
        "assessor": "Enrique",
        "meta_names": ["HL Prime"],
        "report_repo": None,
        "note": "Relatório manual",
    },
    {
        "id": "mixmobi",
        "name": "Mix Mobi",
        "nicho": "Auto",
        "assessor": "Enrique",
        "meta_names": ["Grupo MGS [Moto Chefe/ Mixmobi]"],
        "report_repo": None,
        "note": "Conta Meta compartilhada com MotoChefe",
    },
]

# ─── META ─────────────────────────────────────────────────────────────────────

META_API = "https://graph.facebook.com/v21.0"

def normalize(s):
    return "".join(c.lower() for c in (s or "") if c.isalnum())

def fetch_meta_accounts(token):
    out = []
    after = None
    while True:
        params = {
            "fields": "name,account_id,balance,amount_spent,currency,account_status,"
                      "funding_source_details,is_prepay_account",
            "limit": 50,
        }
        if after:
            params["after"] = after
        try:
            data = http_get(
                f"{META_API}/me/adaccounts",
                headers={"Authorization": f"Bearer {token}"},
                params=params,
            )
        except Exception as e:
            print(f"  ! erro ao buscar contas Meta: {e}", file=sys.stderr)
            break
        out.extend(data.get("data", []))
        after = data.get("paging", {}).get("cursors", {}).get("after")
        if not after or not data.get("data"):
            break
    return out

def parse_balance(acc):
    fsd = acc.get("funding_source_details") or {}
    s = fsd.get("display_string") or ""
    m = re.search(r"R\$\s*([\d.]*\d+,\d+)", s)
    if m:
        return float(m.group(1).replace(".", "").replace(",", "."))
    return int(acc.get("balance", 0)) / 100.0

def has_readable_balance(acc):
    if acc.get("is_prepay_account"):
        fsd = acc.get("funding_source_details") or {}
        s = fsd.get("display_string") or ""
        return bool(re.search(r"R\$\s*[\d.]*\d+,\d+", s))
    return False

def fetch_spend_7d(account_id, token):
    try:
        data = http_get(
            f"{META_API}/{account_id}/insights",
            headers={"Authorization": f"Bearer {token}"},
            params={"date_preset": "last_7d", "fields": "spend"},
        )
        rows = data.get("data", [])
        return float(rows[0]["spend"]) if rows else 0.0
    except Exception as e:
        print(f"  ! spend 7d {account_id}: {e}", file=sys.stderr)
        return None

def fetch_active_campaigns(account_id, token):
    total = 0
    try:
        data = http_get(
            f"{META_API}/{account_id}/campaigns",
            headers={"Authorization": f"Bearer {token}"},
            params={"fields": "effective_status", "limit": 200},
        )
        for c in data.get("data", []):
            if c.get("effective_status") == "ACTIVE":
                total += 1
    except Exception as e:
        print(f"  ! campaigns {account_id}: {e}", file=sys.stderr)
        return None
    return total

# ─── GITHUB ACTIONS ───────────────────────────────────────────────────────────

GH_API = "https://api.github.com"
GH_OWNER = "beatriz-moraes082"

def fetch_gh_last_run(repo, token):
    """Retorna (conclusion, run_date_str) do último workflow run concluído."""
    if not token:
        return None, None
    try:
        data = http_get(
            f"{GH_API}/repos/{GH_OWNER}/{repo}/actions/runs",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
            params={"per_page": 5, "status": "completed"},
        )
        runs = data.get("workflow_runs", [])
        if not runs:
            return None, None
        # Pegar o run mais recente que não seja de push (schedule/workflow_dispatch)
        for r in runs:
            ev = r.get("event", "")
            if ev in ("schedule", "workflow_dispatch", "push"):
                return r.get("conclusion"), r.get("updated_at", "")[:10]
        return runs[0].get("conclusion"), runs[0].get("updated_at", "")[:10]
    except Exception as e:
        print(f"  ! gh runs {repo}: {e}", file=sys.stderr)
        return None, None

# ─── LÓGICA DE SAÚDE ─────────────────────────────────────────────────────────

ACCOUNT_STATUS_LABELS = {
    1: "Ativa",
    2: "Desativada",
    3: "Não confirmada",
    7: "Pendente de revisão",
    9: "Encerrada",
    100: "Pendente de encerramento",
    101: "Encerrada por inatividade",
    201: "Suspensa por fraude",
    202: "Suspensa por regras",
}

def days_since(date_str):
    """Retorna número de dias desde a data YYYY-MM-DD até hoje (BRT)."""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        now_brt = datetime.utcnow() - timedelta(hours=3)
        return (now_brt.replace(tzinfo=None) - dt).days
    except Exception:
        return 999

def build_client_data(client, acc_by_id, acc_by_name_norm, meta_token, gh_token):
    """Coleta todos os dados de saúde do cliente e retorna um dict."""
    alerts = []
    warnings = []

    # — Meta accounts —
    meta_ids_cfg = client.get("meta_ids", [])
    meta_names_cfg = client.get("meta_names", [])

    found_accs = []
    for mid in meta_ids_cfg:
        acc = acc_by_id.get(mid)
        if acc:
            found_accs.append(acc)

    for mname in meta_names_cfg:
        mn = normalize(mname)
        acc = acc_by_name_norm.get(mn)
        if acc and acc["id"] not in {a["id"] for a in found_accs}:
            found_accs.append(acc)

    # Dedup por ID
    seen = set()
    unique_accs = []
    for a in found_accs:
        if a["id"] not in seen:
            seen.add(a["id"])
            unique_accs.append(a)

    meta_summary = []
    total_spend_7d = 0.0
    has_spend = False

    for acc in unique_accs:
        status_code = acc.get("account_status", 1)
        status_label = ACCOUNT_STATUS_LABELS.get(status_code, f"Status {status_code}")
        is_active = status_code == 1

        balance = parse_balance(acc) if has_readable_balance(acc) else None
        spend_7d = fetch_spend_7d(acc["id"], meta_token) if meta_token else None
        active_camps = fetch_active_campaigns(acc["id"], meta_token) if meta_token else None

        if spend_7d is not None:
            total_spend_7d += spend_7d
            has_spend = True

        # Alertas de conta
        if not is_active:
            alerts.append(f"Conta {acc.get('name','?')} {status_label.lower()}")
        elif balance is not None and balance == 0:
            alerts.append(f"Conta {acc.get('name','?')} zerada")
        elif balance is not None and spend_7d and spend_7d > 0:
            burn_daily = spend_7d / 7.0
            days_left = balance / burn_daily if burn_daily > 0 else 999
            if days_left < 5:
                alerts.append(f"Saldo {acc.get('name','?')} para {int(days_left)}d")
            elif days_left < 10:
                warnings.append(f"Saldo {acc.get('name','?')} para ~{int(days_left)}d")

        meta_summary.append({
            "name": acc.get("name", acc["id"]),
            "id": acc["id"],
            "status_code": status_code,
            "status_label": status_label,
            "is_active": is_active,
            "balance": balance,
            "spend_7d": spend_7d,
            "active_campaigns": active_camps,
        })

    if not unique_accs and (meta_ids_cfg or meta_names_cfg):
        warnings.append("Conta Meta não encontrada na API")

    # — Report —
    repo = client.get("report_repo")
    report_conclusion = None
    report_date = None
    report_days_ago = None

    if repo and gh_token:
        report_conclusion, report_date = fetch_gh_last_run(repo, gh_token)
        if report_date:
            report_days_ago = days_since(report_date)

        if report_conclusion == "failure":
            alerts.append("Relatório automático falhou")
        elif report_days_ago is not None and report_days_ago > 9:
            warnings.append(f"Relatório há {report_days_ago}d")
    elif repo and not gh_token:
        report_conclusion = "no_token"

    # — Health —
    if alerts:
        health = "red"
    elif warnings:
        health = "yellow"
    else:
        health = "green"

    return {
        "client": client,
        "health": health,
        "alerts": alerts,
        "warnings": warnings,
        "meta": meta_summary,
        "total_spend_7d": total_spend_7d if has_spend else None,
        "report_conclusion": report_conclusion,
        "report_date": report_date,
        "report_days_ago": report_days_ago,
    }

# ─── HTML ────────────────────────────────────────────────────────────────────

def fmt_br(v):
    return f"{v:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")

def health_dot(health):
    colors = {"green": "#16a34a", "yellow": "#ca8a04", "red": "#dc2626"}
    return f'<span class="dot dot-{health}" style="background:{colors.get(health,"#888")}"></span>'

def report_badge(cd):
    conc = cd["report_conclusion"]
    days = cd["report_days_ago"]
    repo = cd["client"].get("report_repo")
    note = cd["client"].get("note")

    if note and not repo:
        return f'<span class="badge badge-gray">Manual</span>'
    if not repo:
        return f'<span class="badge badge-gray">—</span>'
    if conc == "no_token":
        return f'<span class="badge badge-gray">sem token</span>'
    if conc is None:
        return f'<span class="badge badge-gray">sem runs</span>'
    if conc == "failure":
        return f'<span class="badge badge-red">FALHOU</span>'
    if conc == "success":
        label = f"há {days}d" if days is not None else "ok"
        color = "badge-green" if (days or 0) <= 7 else "badge-yellow"
        return f'<span class="badge {color}">✓ {label}</span>'
    return f'<span class="badge badge-gray">{conc}</span>'

def meta_status_icon(acc):
    if acc["is_active"]:
        camps = acc.get("active_campaigns")
        if camps is not None:
            return f'🟢 {camps} camp. ativas'
        return "🟢 ativa"
    return f'🔴 {acc["status_label"]}'

def build_html(results, now_str):
    n_red = sum(1 for r in results if r["health"] == "red")
    n_yellow = sum(1 for r in results if r["health"] == "yellow")
    n_green = sum(1 for r in results if r["health"] == "green")
    n_total = len(results)

    cards_html = ""
    for cd in sorted(results, key=lambda r: ({"red": 0, "yellow": 1, "green": 2}[r["health"]], r["client"]["nicho"], r["client"]["name"])):
        cl = cd["client"]
        h = cd["health"]

        nicho_class = cl["nicho"].lower().replace("ó", "o").replace("á", "a")

        # Meta rows
        meta_rows = ""
        for acc in cd["meta"]:
            bal_str = f"R$ {fmt_br(acc['balance'])}" if acc["balance"] is not None else "—"
            sp_str = f"R$ {fmt_br(acc['spend_7d'])}/sem" if acc["spend_7d"] is not None else ""
            meta_rows += f"""
            <div class="meta-row">
              <span class="meta-name">{acc['name']}</span>
              <span class="meta-stat">{meta_status_icon(acc)}</span>
              {'<span class="meta-bal">Saldo ' + bal_str + '</span>' if acc['balance'] is not None else ''}
              {'<span class="meta-sp">' + sp_str + '</span>' if sp_str else ''}
            </div>"""

        if not cd["meta"] and (cl.get("meta_ids") or cl.get("meta_names")):
            meta_rows = '<div class="meta-row meta-warn">conta não encontrada</div>'

        # Alerts
        alert_html = ""
        for a in cd["alerts"]:
            alert_html += f'<div class="alert alert-red">⚠ {a}</div>'
        for w in cd["warnings"]:
            alert_html += f'<div class="alert alert-yellow">⚡ {w}</div>'

        # Spend total
        spend_total = ""
        if cd["total_spend_7d"] is not None and len(cd["meta"]) > 1:
            spend_total = f'<div class="spend-total">Total 7d: R$ {fmt_br(cd["total_spend_7d"])}</div>'

        # Note
        note_html = f'<div class="client-note">{cl["note"]}</div>' if cl.get("note") else ""

        assessor_label = cl.get("assessor", "?")

        cards_html += f"""
    <div class="card card-{h}" data-nicho="{nicho_class}" data-health="{h}" data-assessor="{assessor_label.lower()}">
      <div class="card-header">
        <div class="card-title">
          {health_dot(h)}
          <span class="client-name">{cl['name']}</span>
        </div>
        <div class="card-badges">
          <span class="badge-nicho nicho-{nicho_class}">{cl['nicho']}</span>
          <span class="badge-assessor">{assessor_label}</span>
        </div>
      </div>
      <div class="card-body">
        {alert_html}
        <div class="section-label">META ADS</div>
        {meta_rows}
        {spend_total}
        <div class="section-label">RELATÓRIO</div>
        <div class="report-row">
          {report_badge(cd)}
          {'<span class="report-date">' + (cd["report_date"] or "") + '</span>' if cd["report_date"] else ''}
        </div>
        {note_html}
      </div>
    </div>"""

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Painel Beatriz — Trilha</title>
<style>
  :root {{
    --orange: #ee4c20;
    --sand: #e9e8e4;
    --dark: #1a1a1a;
    --green: #16a34a;
    --yellow: #ca8a04;
    --red: #dc2626;
    --bg-green: #f0fdf4;
    --bg-yellow: #fefce8;
    --bg-red: #fef2f2;
    --border-green: #bbf7d0;
    --border-yellow: #fde68a;
    --border-red: #fecaca;
    --text-muted: #6b7280;
    --text-sm: 0.78rem;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background: var(--sand);
    color: var(--dark);
    min-height: 100vh;
  }}
  /* ── Header ── */
  .header {{
    background: var(--dark);
    color: white;
    padding: 20px 28px 16px;
    display: flex;
    align-items: baseline;
    gap: 16px;
    flex-wrap: wrap;
  }}
  .header-logo {{
    font-size: 1.05rem;
    font-weight: 700;
    letter-spacing: -.02em;
    color: var(--orange);
    text-transform: uppercase;
  }}
  .header-title {{
    font-size: 1.15rem;
    font-weight: 600;
    color: white;
  }}
  .header-updated {{
    font-size: var(--text-sm);
    color: #9ca3af;
    margin-left: auto;
  }}
  /* ── Summary bar ── */
  .summary-bar {{
    background: #111;
    display: flex;
    gap: 0;
    border-bottom: 1px solid #333;
  }}
  .summary-item {{
    flex: 1;
    padding: 14px 20px;
    text-align: center;
    border-right: 1px solid #333;
  }}
  .summary-item:last-child {{ border-right: none; }}
  .summary-count {{
    font-size: 1.7rem;
    font-weight: 800;
    line-height: 1;
  }}
  .summary-label {{
    font-size: 0.68rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: .06em;
    margin-top: 4px;
    color: #9ca3af;
  }}
  .summary-item.s-red .summary-count {{ color: #f87171; }}
  .summary-item.s-yellow .summary-count {{ color: #fbbf24; }}
  .summary-item.s-green .summary-count {{ color: #4ade80; }}
  .summary-item.s-total .summary-count {{ color: white; }}
  /* ── Filters ── */
  .filters {{
    padding: 14px 20px;
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    background: white;
    border-bottom: 1px solid #e5e7eb;
    position: sticky;
    top: 0;
    z-index: 10;
  }}
  .filters label {{
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .06em;
    color: var(--text-muted);
    align-self: center;
    margin-right: 4px;
  }}
  .filter-btn {{
    padding: 5px 12px;
    border-radius: 20px;
    border: 1.5px solid #d1d5db;
    background: white;
    font-size: var(--text-sm);
    font-weight: 600;
    cursor: pointer;
    transition: all .15s;
    color: var(--dark);
  }}
  .filter-btn:hover {{ border-color: var(--orange); color: var(--orange); }}
  .filter-btn.active {{ background: var(--dark); border-color: var(--dark); color: white; }}
  .filter-btn.f-red.active {{ background: var(--red); border-color: var(--red); }}
  .filter-btn.f-yellow.active {{ background: var(--yellow); border-color: var(--yellow); }}
  .filter-btn.f-green.active {{ background: var(--green); border-color: var(--green); }}
  .filter-sep {{ width: 1px; background: #e5e7eb; margin: 0 4px; }}
  /* ── Grid ── */
  .grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 14px;
    padding: 20px;
  }}
  /* ── Card ── */
  .card {{
    background: white;
    border-radius: 10px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0,0,0,.06);
    border: 1.5px solid #e5e7eb;
    transition: box-shadow .15s;
  }}
  .card:hover {{ box-shadow: 0 4px 14px rgba(0,0,0,.1); }}
  .card-red {{ border-color: var(--border-red); background: var(--bg-red); }}
  .card-yellow {{ border-color: var(--border-yellow); background: var(--bg-yellow); }}
  .card-green {{ border-color: var(--border-green); }}
  .card-header {{
    padding: 12px 14px 8px;
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 8px;
    border-bottom: 1px solid rgba(0,0,0,.06);
  }}
  .card-title {{
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .dot {{
    width: 10px;
    height: 10px;
    border-radius: 50%;
    flex-shrink: 0;
  }}
  .client-name {{
    font-size: .92rem;
    font-weight: 700;
    color: var(--dark);
  }}
  .card-badges {{
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 3px;
  }}
  .badge-nicho {{
    font-size: .62rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .05em;
    padding: 2px 7px;
    border-radius: 10px;
  }}
  .nicho-imobiliario {{ background: #ede9fe; color: #6d28d9; }}
  .nicho-hotelaria   {{ background: #fce7f3; color: #9d174d; }}
  .nicho-auto        {{ background: #dbeafe; color: #1d4ed8; }}
  .badge-assessor {{
    font-size: .62rem;
    color: var(--text-muted);
    font-weight: 600;
  }}
  .card-body {{
    padding: 10px 14px 12px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }}
  .section-label {{
    font-size: .62rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .07em;
    color: var(--text-muted);
    margin-top: 4px;
  }}
  .meta-row {{
    display: flex;
    flex-wrap: wrap;
    gap: 4px 10px;
    font-size: var(--text-sm);
    align-items: baseline;
    padding: 2px 0;
    border-bottom: 1px solid rgba(0,0,0,.04);
  }}
  .meta-name {{
    font-weight: 600;
    color: var(--dark);
    font-size: .7rem;
  }}
  .meta-stat {{ color: var(--dark); }}
  .meta-bal {{ color: var(--text-muted); }}
  .meta-sp  {{ color: var(--text-muted); }}
  .meta-warn {{ color: var(--red); font-size: .75rem; }}
  .spend-total {{
    font-size: .72rem;
    font-weight: 700;
    color: var(--text-muted);
    text-align: right;
    margin-top: 2px;
  }}
  .report-row {{
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: var(--text-sm);
  }}
  .report-date {{ color: var(--text-muted); font-size: .7rem; }}
  .client-note {{ font-size: .68rem; color: var(--text-muted); font-style: italic; }}
  .alert {{
    font-size: .75rem;
    font-weight: 600;
    padding: 4px 8px;
    border-radius: 5px;
    margin-bottom: 2px;
  }}
  .alert-red    {{ background: #fee2e2; color: #991b1b; }}
  .alert-yellow {{ background: #fef3c7; color: #92400e; }}
  /* Badges */
  .badge {{
    display: inline-block;
    font-size: .66rem;
    font-weight: 700;
    padding: 2px 7px;
    border-radius: 10px;
  }}
  .badge-green  {{ background: #dcfce7; color: #166534; }}
  .badge-yellow {{ background: #fef9c3; color: #854d0e; }}
  .badge-red    {{ background: #fee2e2; color: #991b1b; }}
  .badge-gray   {{ background: #f3f4f6; color: #6b7280; }}
  .hidden {{ display: none !important; }}
  /* ── Footer ── */
  .footer {{
    text-align: center;
    padding: 28px;
    font-size: .72rem;
    color: var(--text-muted);
  }}
</style>
</head>
<body>

<header class="header">
  <span class="header-logo">Trilha</span>
  <span class="header-title">Painel Beatriz</span>
  <span class="header-updated">Atualizado {now_str}</span>
</header>

<div class="summary-bar">
  <div class="summary-item s-total">
    <div class="summary-count">{n_total}</div>
    <div class="summary-label">Clientes</div>
  </div>
  <div class="summary-item s-red">
    <div class="summary-count">{n_red}</div>
    <div class="summary-label">Crítico</div>
  </div>
  <div class="summary-item s-yellow">
    <div class="summary-count">{n_yellow}</div>
    <div class="summary-label">Atenção</div>
  </div>
  <div class="summary-item s-green">
    <div class="summary-count">{n_green}</div>
    <div class="summary-label">Saudável</div>
  </div>
</div>

<div class="filters">
  <label>Status</label>
  <button class="filter-btn active" data-filter="all">Todos</button>
  <button class="filter-btn f-red" data-filter="health:red">Crítico</button>
  <button class="filter-btn f-yellow" data-filter="health:yellow">Atenção</button>
  <button class="filter-btn f-green" data-filter="health:green">Saudável</button>
  <div class="filter-sep"></div>
  <label>Nicho</label>
  <button class="filter-btn" data-filter="nicho:imobiliario">Imobiliário</button>
  <button class="filter-btn" data-filter="nicho:hotelaria">Hotelaria</button>
  <button class="filter-btn" data-filter="nicho:auto">Auto</button>
  <div class="filter-sep"></div>
  <label>Assessor</label>
  <button class="filter-btn" data-filter="assessor:enrique">Enrique</button>
  <button class="filter-btn" data-filter="assessor:bruno">Bruno</button>
</div>

<div class="grid" id="grid">
{cards_html}
</div>

<footer class="footer">
  Trilha Performance Digital · Carteira Beatriz · {now_str}
</footer>

<script>
  const btns = document.querySelectorAll('.filter-btn');
  const cards = document.querySelectorAll('.card');

  function applyFilters() {{
    const active = [...btns].filter(b => b.classList.contains('active')).map(b => b.dataset.filter);
    if (active.includes('all')) {{
      cards.forEach(c => c.classList.remove('hidden'));
      return;
    }}
    cards.forEach(card => {{
      const nicho    = card.dataset.nicho;
      const health   = card.dataset.health;
      const assessor = card.dataset.assessor;
      const show = active.every(f => {{
        if (f.startsWith('health:'))   return health   === f.split(':')[1];
        if (f.startsWith('nicho:'))    return nicho    === f.split(':')[1];
        if (f.startsWith('assessor:')) return assessor === f.split(':')[1];
        return true;
      }});
      card.classList.toggle('hidden', !show);
    }});
  }}

  btns.forEach(btn => {{
    btn.addEventListener('click', () => {{
      const f = btn.dataset.filter;
      if (f === 'all') {{
        btns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
      }} else {{
        const allBtn = document.querySelector('[data-filter="all"]');
        allBtn.classList.remove('active');
        btn.classList.toggle('active');
        if (![...btns].some(b => b.classList.contains('active'))) {{
          allBtn.classList.add('active');
        }}
      }}
      applyFilters();
    }});
  }});
</script>
</body>
</html>"""

# ─── MAIN ────────────────────────────────────────────────────────────────────

def main():
    meta_token = ENV.get("META_ACCESS_TOKEN", "")
    gh_token = ENV.get("GH_PAT", "")

    if not meta_token:
        print("! META_ACCESS_TOKEN não encontrado — dados Meta não disponíveis")
    if not gh_token:
        print("! GH_PAT não encontrado — status de relatórios não disponível")

    print(f"  Buscando {len(CLIENTS)} clientes...")

    # Fetch Meta
    meta_accounts = fetch_meta_accounts(meta_token) if meta_token else []
    print(f"  Meta: {len(meta_accounts)} contas encontradas")

    acc_by_id   = {a["id"]: a for a in meta_accounts}
    acc_by_name = {normalize(a["name"]): a for a in meta_accounts}

    now_brt = datetime.utcnow() - timedelta(hours=3)
    now_str = now_brt.strftime("%d/%m/%Y às %H:%M BRT")

    results = []
    for cl in CLIENTS:
        print(f"  [{cl['id']}] ...", end=" ", flush=True)
        cd = build_client_data(cl, acc_by_id, acc_by_name, meta_token, gh_token)
        results.append(cd)
        h = {"red": "🔴", "yellow": "🟡", "green": "🟢"}[cd["health"]]
        print(f"{h} {len(cd['alerts'])} alertas, {len(cd['warnings'])} avisos")

    html = build_html(results, now_str)
    out_path = Path(__file__).parent / "index.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"\n  ✓ {out_path} gerado — {len(results)} clientes")
    print(f"  🔴 {sum(1 for r in results if r['health']=='red')} críticos  "
          f"🟡 {sum(1 for r in results if r['health']=='yellow')} atenção  "
          f"🟢 {sum(1 for r in results if r['health']=='green')} saudáveis")

if __name__ == "__main__":
    main()
