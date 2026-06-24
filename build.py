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
        for r in runs:
            if r.get("event", "") in ("schedule", "workflow_dispatch", "push"):
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
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        now_brt = datetime.utcnow() - timedelta(hours=3)
        return (now_brt.replace(tzinfo=None) - dt).days
    except Exception:
        return 999

def fmt_br(v):
    if v is None:
        return "—"
    return f"{v:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")

def build_client_data(client, acc_by_id, acc_by_name_norm, meta_token, gh_token):
    # — Meta accounts —
    found_accs = []
    for mid in client.get("meta_ids", []):
        acc = acc_by_id.get(mid)
        if acc:
            found_accs.append(acc)
    for mname in client.get("meta_names", []):
        mn = normalize(mname)
        acc = acc_by_name_norm.get(mn)
        if acc and acc["id"] not in {a["id"] for a in found_accs}:
            found_accs.append(acc)

    seen = set()
    unique_accs = []
    for a in found_accs:
        if a["id"] not in seen:
            seen.add(a["id"])
            unique_accs.append(a)

    # — Alertas por conta Meta —
    # Cada alerta tem: level, title, action, owner, detail
    alerts = []  # P1 (red)
    warnings = []  # P2 (yellow)

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

        burn_daily = (spend_7d / 7.0) if (spend_7d and spend_7d > 0) else None
        days_left = int(balance / burn_daily) if (balance is not None and burn_daily and burn_daily > 0) else None
        recharge_30d = int(burn_daily * 30) if burn_daily else None

        if not is_active:
            alerts.append({
                "title": f"{acc.get('name','?')}: conta {status_label.lower()}",
                "action": f"Investigar motivo no Meta Business — possível limite de gasto ou suspensão. Acionar {client['assessor']} hoje.",
                "owner": client["assessor"],
            })
        elif balance is not None and balance == 0:
            alerts.append({
                "title": f"{acc.get('name','?')}: saldo zerado — entrega parada",
                "action": f"Recarga urgente. {('Queima média R$' + fmt_br(burn_daily) + '/dia → recarga 30d ~R$' + fmt_br(recharge_30d)) if recharge_30d else 'Calcular valor de recarga.'}",
                "owner": client["assessor"],
            })
        elif days_left is not None and days_left < 5:
            alerts.append({
                "title": f"{acc.get('name','?')}: saldo para {days_left}d",
                "action": f"Recarga urgente esta semana. ~R${fmt_br(recharge_30d)} pra 30d de runway.",
                "owner": client["assessor"],
            })
        elif days_left is not None and days_left < 10:
            warnings.append({
                "title": f"{acc.get('name','?')}: saldo para ~{days_left}d",
                "action": f"Avisar cliente sobre recarga. ~R${fmt_br(recharge_30d)} pra 30d.",
                "owner": client["assessor"],
            })

        meta_summary.append({
            "name": acc.get("name", acc["id"]),
            "id": acc["id"],
            "status_code": status_code,
            "status_label": status_label,
            "is_active": is_active,
            "balance": balance,
            "spend_7d": spend_7d,
            "burn_daily": burn_daily,
            "days_left": days_left,
            "active_campaigns": active_camps,
            "recharge_30d": recharge_30d,
        })

    if not unique_accs and (client.get("meta_ids") or client.get("meta_names")):
        warnings.append({
            "title": "Conta Meta não encontrada na API",
            "action": "Verificar se a conta ainda está associada ao token. Checar BM.",
            "owner": "Bia",
        })

    # — Relatório —
    repo = client.get("report_repo")
    report_conclusion = None
    report_date = None
    report_days_ago = None

    if repo and gh_token:
        report_conclusion, report_date = fetch_gh_last_run(repo, gh_token)
        if report_date:
            report_days_ago = days_since(report_date)

        if report_conclusion == "failure":
            alerts.append({
                "title": f"Relatório automático falhou",
                "action": f"Ver logs em github.com/{GH_OWNER}/{repo}/actions e corrigir. Re-disparar via workflow_dispatch.",
                "owner": "Bia",
            })
        elif report_days_ago is not None and report_days_ago > 9:
            warnings.append({
                "title": f"Relatório há {report_days_ago}d sem atualização",
                "action": f"Verificar se o cron está ativo em {repo}. Pode ser token expirado.",
                "owner": "Bia",
            })
    elif repo and not gh_token:
        report_conclusion = "no_token"

    health = "red" if alerts else ("yellow" if warnings else "green")

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

def nicho_badge_style(nicho):
    styles = {
        "Imobiliário": "background:#ede9fe;color:#5b21b6;",
        "Hotelaria": "background:#fce7f3;color:#9d174d;",
        "Auto": "background:#dbeafe;color:#1e40af;",
    }
    return styles.get(nicho, "background:#f3f4f6;color:#374151;")

def report_badge_html(cd):
    conc = cd["report_conclusion"]
    days = cd["report_days_ago"]
    repo = cd["client"].get("report_repo")
    note = cd["client"].get("note")

    if note and not repo:
        return '<span style="font-size:.65rem;font-weight:700;padding:2px 8px;border-radius:10px;background:#f3f4f6;color:#6b7280;">Manual</span>'
    if not repo:
        return '<span style="font-size:.65rem;font-weight:700;padding:2px 8px;border-radius:10px;background:#f3f4f6;color:#6b7280;">—</span>'
    if conc == "no_token":
        return '<span style="font-size:.65rem;font-weight:700;padding:2px 8px;border-radius:10px;background:#f3f4f6;color:#6b7280;">sem token</span>'
    if conc is None:
        return '<span style="font-size:.65rem;font-weight:700;padding:2px 8px;border-radius:10px;background:#f3f4f6;color:#6b7280;">sem runs</span>'
    if conc == "failure":
        return '<span style="font-size:.65rem;font-weight:700;padding:2px 8px;border-radius:10px;background:#fee2e2;color:#991b1b;">FALHOU</span>'
    if conc == "success":
        label = f"há {days}d" if days is not None else "ok"
        color = ("background:#dcfce7;color:#166534;" if (days or 0) <= 7
                 else "background:#fef9c3;color:#854d0e;")
        return f'<span style="font-size:.65rem;font-weight:700;padding:2px 8px;border-radius:10px;{color}">✓ {label}</span>'
    return f'<span style="font-size:.65rem;font-weight:700;padding:2px 8px;border-radius:10px;background:#f3f4f6;color:#6b7280;">{conc}</span>'

def meta_status_pill(acc):
    if not acc["is_active"]:
        return '<span style="color:#dc2626;font-weight:700;font-size:.78rem;">● Desativada</span>'
    camps = acc.get("active_campaigns")
    camp_str = f" · {camps} camp." if camps is not None else ""
    return f'<span style="color:#16a34a;font-weight:700;font-size:.78rem;">●</span><span style="font-size:.78rem;"> Ativa{camp_str}</span>'

def build_action_rows(items, level):
    if not items:
        return ""
    bg = "#fee2e2" if level == "red" else "#fef9c3"
    border = "#fca5a5" if level == "red" else "#fde047"
    icon = "⚠" if level == "red" else "⚡"
    rows = ""
    for item in items:
        owner_style = ("background:#dc2626;color:white;" if level == "red"
                       else "background:#ca8a04;color:white;")
        rows += f"""
        <div style="border-left:3px solid {border};background:{bg};border-radius:0 6px 6px 0;padding:7px 10px;margin-bottom:6px;">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:8px;">
            <span style="font-size:.78rem;font-weight:700;color:#1a1a1a;">{icon} {item['title']}</span>
            <span style="font-size:.62rem;font-weight:800;text-transform:uppercase;letter-spacing:.05em;padding:2px 7px;border-radius:10px;white-space:nowrap;flex-shrink:0;{owner_style}">{item['owner']}</span>
          </div>
          <div style="font-size:.72rem;color:#374151;margin-top:3px;line-height:1.4;">{item['action']}</div>
        </div>"""
    return rows

def build_html(results, now_str):
    # Coleta todas as ações P1 e P2 de todos os clientes pra briefing
    p1_actions = []
    p2_actions = []
    for cd in results:
        cl = cd["client"]
        for a in cd["alerts"]:
            p1_actions.append({**a, "client_name": cl["name"], "nicho": cl["nicho"]})
        for w in cd["warnings"]:
            p2_actions.append({**w, "client_name": cl["name"], "nicho": cl["nicho"]})

    n_red = sum(1 for r in results if r["health"] == "red")
    n_yellow = sum(1 for r in results if r["health"] == "yellow")
    n_green = sum(1 for r in results if r["health"] == "green")
    n_total = len(results)

    # ── Briefing de ações ────────────────────────────────────────────────────
    briefing_html = ""

    if p1_actions:
        rows = ""
        for a in p1_actions:
            rows += f"""
          <div style="border-left:3px solid #f87171;background:#1f1f1f;border-radius:0 6px 6px 0;padding:8px 12px;margin-bottom:6px;">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:8px;flex-wrap:wrap;">
              <div>
                <span style="font-size:.68rem;font-weight:800;text-transform:uppercase;letter-spacing:.06em;color:#f87171;">P1 · {a['client_name']}</span>
                <div style="font-size:.82rem;font-weight:700;color:white;margin-top:1px;">{a['title']}</div>
              </div>
              <span style="font-size:.62rem;font-weight:800;text-transform:uppercase;letter-spacing:.05em;padding:2px 8px;border-radius:10px;white-space:nowrap;flex-shrink:0;background:#dc2626;color:white;">{a['owner']}</span>
            </div>
            <div style="font-size:.74rem;color:#9ca3af;margin-top:4px;line-height:1.45;">{a['action']}</div>
          </div>"""
        briefing_html += f"""
      <div style="margin-bottom:16px;">
        <div style="font-size:.65rem;font-weight:800;text-transform:uppercase;letter-spacing:.08em;color:#f87171;margin-bottom:8px;">
          ⚠ Ações P1 — resolver hoje ({len(p1_actions)})
        </div>
        {rows}
      </div>"""

    if p2_actions:
        rows = ""
        for a in p2_actions:
            rows += f"""
          <div style="border-left:3px solid #fbbf24;background:#1f1f1f;border-radius:0 6px 6px 0;padding:8px 12px;margin-bottom:6px;">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:8px;flex-wrap:wrap;">
              <div>
                <span style="font-size:.68rem;font-weight:800;text-transform:uppercase;letter-spacing:.06em;color:#fbbf24;">P2 · {a['client_name']}</span>
                <div style="font-size:.82rem;font-weight:700;color:white;margin-top:1px;">{a['title']}</div>
              </div>
              <span style="font-size:.62rem;font-weight:800;text-transform:uppercase;letter-spacing:.05em;padding:2px 8px;border-radius:10px;white-space:nowrap;flex-shrink:0;background:#ca8a04;color:white;">{a['owner']}</span>
            </div>
            <div style="font-size:.74rem;color:#9ca3af;margin-top:4px;line-height:1.45;">{a['action']}</div>
          </div>"""
        briefing_html += f"""
      <div>
        <div style="font-size:.65rem;font-weight:800;text-transform:uppercase;letter-spacing:.08em;color:#fbbf24;margin-bottom:8px;">
          ⚡ Ações P2 — esta semana ({len(p2_actions)})
        </div>
        {rows}
      </div>"""

    if not p1_actions and not p2_actions:
        briefing_html = """
      <div style="text-align:center;padding:20px;color:#4ade80;">
        <span style="font-size:1.5rem;">✓</span>
        <div style="font-size:.85rem;font-weight:700;color:#4ade80;margin-top:6px;">Carteira saudável — nenhuma ação pendente</div>
      </div>"""

    # ── Cards ────────────────────────────────────────────────────────────────
    cards_html = ""
    sorted_results = sorted(
        results,
        key=lambda r: ({"red": 0, "yellow": 1, "green": 2}[r["health"]], r["client"]["nicho"], r["client"]["name"])
    )

    for cd in sorted_results:
        cl = cd["client"]
        h = cd["health"]
        nicho_id = normalize(cl["nicho"])

        dot_color = {"red": "#dc2626", "yellow": "#ca8a04", "green": "#16a34a"}[h]
        border_color = {"red": "#fca5a5", "yellow": "#fde68a", "green": "#bbf7d0"}[h]
        bg_color = {"red": "#fef2f2", "yellow": "#fefce8", "green": "white"}[h]

        # Prio badge
        if h == "red":
            prio_html = '<span style="font-size:.6rem;font-weight:800;text-transform:uppercase;letter-spacing:.06em;padding:2px 7px;border-radius:10px;background:#dc2626;color:white;">P1</span>'
        elif h == "yellow":
            prio_html = '<span style="font-size:.6rem;font-weight:800;text-transform:uppercase;letter-spacing:.06em;padding:2px 7px;border-radius:10px;background:#ca8a04;color:white;">P2</span>'
        else:
            prio_html = '<span style="font-size:.6rem;font-weight:800;text-transform:uppercase;letter-spacing:.06em;padding:2px 7px;border-radius:10px;background:#f0fdf4;color:#166534;">OK</span>'

        # Alertas no card
        alert_rows = build_action_rows(cd["alerts"], "red") + build_action_rows(cd["warnings"], "yellow")

        # Meta rows
        meta_rows = ""
        for acc in cd["meta"]:
            bal_str = f"R$ {fmt_br(acc['balance'])}" if acc["balance"] is not None else ""
            burn_str = f"R$ {fmt_br(acc['burn_daily'])}/dia" if acc.get("burn_daily") else ""
            days_str = f"{acc['days_left']}d restantes" if acc.get("days_left") else ""

            meta_rows += f"""
            <div style="padding:5px 0;border-bottom:1px solid rgba(0,0,0,.05);font-size:.75rem;">
              <div style="display:flex;align-items:center;gap:6px;margin-bottom:2px;">
                {meta_status_pill(acc)}
                <span style="font-size:.7rem;color:#6b7280;font-weight:600;">{acc['name']}</span>
              </div>"""
            if bal_str or burn_str or days_str:
                meta_rows += '<div style="display:flex;flex-wrap:wrap;gap:6px;margin-left:12px;">'
                if bal_str:
                    meta_rows += f'<span style="font-size:.7rem;color:#374151;">Saldo: <strong>{bal_str}</strong></span>'
                if burn_str:
                    meta_rows += f'<span style="font-size:.7rem;color:#6b7280;">{burn_str}</span>'
                if days_str:
                    color = "#dc2626" if (acc.get("days_left") or 999) < 5 else ("#ca8a04" if (acc.get("days_left") or 999) < 10 else "#374151")
                    meta_rows += f'<span style="font-size:.7rem;font-weight:700;color:{color};">{days_str}</span>'
                meta_rows += "</div>"
            meta_rows += "</div>"

        if not cd["meta"] and (cl.get("meta_ids") or cl.get("meta_names")):
            meta_rows = '<div style="font-size:.72rem;color:#dc2626;padding:4px 0;">Conta não encontrada na API</div>'

        spend_total = ""
        if cd["total_spend_7d"] is not None and len(cd["meta"]) > 1:
            spend_total = f'<div style="text-align:right;font-size:.68rem;color:#6b7280;margin-top:4px;">Total 7d: <strong>R$ {fmt_br(cd["total_spend_7d"])}</strong></div>'

        note_html = f'<div style="font-size:.68rem;color:#9ca3af;font-style:italic;margin-top:4px;">{cl["note"]}</div>' if cl.get("note") else ""

        cards_html += f"""
    <div class="card" style="background:{bg_color};border:1.5px solid {border_color};border-radius:10px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.05);"
         data-nicho="{nicho_id}" data-health="{h}" data-assessor="{cl.get('assessor','').lower()}">
      <div style="padding:10px 13px 8px;border-bottom:1px solid rgba(0,0,0,.06);display:flex;justify-content:space-between;align-items:flex-start;gap:8px;">
        <div style="display:flex;align-items:center;gap:7px;">
          <span style="width:9px;height:9px;border-radius:50%;background:{dot_color};flex-shrink:0;display:inline-block;"></span>
          <span style="font-size:.88rem;font-weight:800;color:#1a1a1a;">{cl['name']}</span>
        </div>
        <div style="display:flex;align-items:center;gap:5px;flex-wrap:wrap;justify-content:flex-end;">
          {prio_html}
          <span style="font-size:.62rem;font-weight:700;text-transform:uppercase;letter-spacing:.04em;padding:2px 7px;border-radius:10px;{nicho_badge_style(cl['nicho'])}">{cl['nicho']}</span>
          <span style="font-size:.62rem;font-weight:700;color:#6b7280;background:#f3f4f6;padding:2px 7px;border-radius:10px;">{cl.get('assessor','?')}</span>
        </div>
      </div>
      <div style="padding:9px 13px 11px;display:flex;flex-direction:column;gap:5px;">
        {alert_rows}
        <div style="font-size:.6rem;font-weight:800;text-transform:uppercase;letter-spacing:.07em;color:#9ca3af;margin-top:2px;">Meta Ads</div>
        {meta_rows}
        {spend_total}
        <div style="font-size:.6rem;font-weight:800;text-transform:uppercase;letter-spacing:.07em;color:#9ca3af;margin-top:5px;">Relatório Auto</div>
        <div style="display:flex;align-items:center;gap:7px;">
          {report_badge_html(cd)}
          {'<span style="font-size:.68rem;color:#9ca3af;">' + (cd["report_date"] or "") + '</span>' if cd["report_date"] else ''}
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
  * {{ box-sizing:border-box;margin:0;padding:0; }}
  body {{ font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:#e9e8e4;color:#1a1a1a;min-height:100vh; }}
  .card {{ transition:box-shadow .15s; }}
  .card:hover {{ box-shadow:0 4px 16px rgba(0,0,0,.1) !important; }}
  .filter-btn {{ padding:5px 12px;border-radius:20px;border:1.5px solid #d1d5db;background:white;font-size:.72rem;font-weight:700;cursor:pointer;transition:all .15s;color:#374151;letter-spacing:.01em; }}
  .filter-btn:hover {{ border-color:#ee4c20;color:#ee4c20; }}
  .filter-btn.active {{ background:#1a1a1a;border-color:#1a1a1a;color:white; }}
  .filter-btn.f-red.active {{ background:#dc2626;border-color:#dc2626; }}
  .filter-btn.f-yellow.active {{ background:#ca8a04;border-color:#ca8a04; }}
  .filter-btn.f-green.active {{ background:#16a34a;border-color:#16a34a; }}
  .hidden {{ display:none !important; }}
</style>
</head>
<body>

<!-- Header -->
<div style="background:#1a1a1a;padding:16px 24px;display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;">
  <span style="color:#ee4c20;font-weight:800;font-size:.8rem;letter-spacing:.1em;text-transform:uppercase;">Trilha</span>
  <span style="color:white;font-weight:700;font-size:1.05rem;">Painel Beatriz</span>
  <span style="color:#6b7280;font-size:.72rem;margin-left:auto;">Atualizado {now_str}</span>
</div>

<!-- Summary strip -->
<div style="background:#111;display:flex;border-bottom:1px solid #222;">
  <div style="flex:1;padding:14px 20px;text-align:center;border-right:1px solid #222;">
    <div style="font-size:1.8rem;font-weight:900;color:white;line-height:1;">{n_total}</div>
    <div style="font-size:.62rem;font-weight:800;text-transform:uppercase;letter-spacing:.08em;color:#6b7280;margin-top:3px;">Clientes</div>
  </div>
  <div style="flex:1;padding:14px 20px;text-align:center;border-right:1px solid #222;">
    <div style="font-size:1.8rem;font-weight:900;color:#f87171;line-height:1;">{n_red}</div>
    <div style="font-size:.62rem;font-weight:800;text-transform:uppercase;letter-spacing:.08em;color:#6b7280;margin-top:3px;">P1 Crítico</div>
  </div>
  <div style="flex:1;padding:14px 20px;text-align:center;border-right:1px solid #222;">
    <div style="font-size:1.8rem;font-weight:900;color:#fbbf24;line-height:1;">{n_yellow}</div>
    <div style="font-size:.62rem;font-weight:800;text-transform:uppercase;letter-spacing:.08em;color:#6b7280;margin-top:3px;">P2 Atenção</div>
  </div>
  <div style="flex:1;padding:14px 20px;text-align:center;">
    <div style="font-size:1.8rem;font-weight:900;color:#4ade80;line-height:1;">{n_green}</div>
    <div style="font-size:.62rem;font-weight:800;text-transform:uppercase;letter-spacing:.08em;color:#6b7280;margin-top:3px;">Saudável</div>
  </div>
</div>

<!-- Briefing de ações -->
<div style="background:#161616;padding:20px 24px;border-bottom:1px solid #222;">
  <div style="max-width:900px;">
    <div style="font-size:.65rem;font-weight:800;text-transform:uppercase;letter-spacing:.1em;color:#6b7280;margin-bottom:14px;">Briefing operacional — foco do dia</div>
    {briefing_html}
  </div>
</div>

<!-- Filtros -->
<div style="background:white;padding:10px 20px;display:flex;flex-wrap:wrap;gap:7px;border-bottom:1px solid #e5e7eb;position:sticky;top:0;z-index:10;">
  <span style="font-size:.62rem;font-weight:800;text-transform:uppercase;letter-spacing:.06em;color:#9ca3af;align-self:center;margin-right:2px;">Prioridade</span>
  <button class="filter-btn active" data-filter="all">Todos</button>
  <button class="filter-btn f-red" data-filter="health:red">P1 Crítico</button>
  <button class="filter-btn f-yellow" data-filter="health:yellow">P2 Atenção</button>
  <button class="filter-btn f-green" data-filter="health:green">Saudável</button>
  <div style="width:1px;background:#e5e7eb;margin:0 4px;"></div>
  <span style="font-size:.62rem;font-weight:800;text-transform:uppercase;letter-spacing:.06em;color:#9ca3af;align-self:center;margin-right:2px;">Nicho</span>
  <button class="filter-btn" data-filter="nicho:imobiliario">Imobiliário</button>
  <button class="filter-btn" data-filter="nicho:hotelaria">Hotelaria</button>
  <button class="filter-btn" data-filter="nicho:auto">Auto</button>
  <div style="width:1px;background:#e5e7eb;margin:0 4px;"></div>
  <span style="font-size:.62rem;font-weight:800;text-transform:uppercase;letter-spacing:.06em;color:#9ca3af;align-self:center;margin-right:2px;">Assessor</span>
  <button class="filter-btn" data-filter="assessor:enrique">Enrique</button>
  <button class="filter-btn" data-filter="assessor:bruno">Bruno</button>
</div>

<!-- Grid de cards -->
<div id="grid" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:12px;padding:18px 20px;">
{cards_html}
</div>

<div style="text-align:center;padding:24px;font-size:.7rem;color:#9ca3af;">
  Trilha Performance Digital · Carteira Beatriz · Atualiza a cada 6h
</div>

<script>
  const btns = document.querySelectorAll('.filter-btn');
  const cards = document.querySelectorAll('#grid .card');

  function applyFilters() {{
    const active = [...btns].filter(b => b.classList.contains('active')).map(b => b.dataset.filter);
    if (active.includes('all')) {{ cards.forEach(c => c.classList.remove('hidden')); return; }}
    cards.forEach(card => {{
      const show = active.every(f => {{
        if (f.startsWith('health:'))   return card.dataset.health   === f.split(':')[1];
        if (f.startsWith('nicho:'))    return card.dataset.nicho    === f.split(':')[1];
        if (f.startsWith('assessor:')) return card.dataset.assessor === f.split(':')[1];
        return true;
      }});
      card.classList.toggle('hidden', !show);
    }});
  }}

  btns.forEach(btn => {{
    btn.addEventListener('click', () => {{
      const f = btn.dataset.filter;
      if (f === 'all') {{ btns.forEach(b => b.classList.remove('active')); btn.classList.add('active'); }}
      else {{
        document.querySelector('[data-filter="all"]').classList.remove('active');
        btn.classList.toggle('active');
        if (![...btns].some(b => b.classList.contains('active')))
          document.querySelector('[data-filter="all"]').classList.add('active');
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
        print("! META_ACCESS_TOKEN não encontrado")
    if not gh_token:
        print("! GH_PAT não encontrado — status de relatórios indisponível")

    print(f"  Buscando {len(CLIENTS)} clientes...")

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
        sym = {"red": "🔴", "yellow": "🟡", "green": "🟢"}[cd["health"]]
        print(f"{sym} P1:{len(cd['alerts'])} P2:{len(cd['warnings'])}")

    html = build_html(results, now_str)
    out = Path(__file__).parent / "index.html"
    out.write_text(html, encoding="utf-8")

    n_p1 = sum(len(r["alerts"])   for r in results)
    n_p2 = sum(len(r["warnings"]) for r in results)
    print(f"\n  ✓ {out} — {len(results)} clientes | {n_p1} ações P1 | {n_p2} avisos P2")
    print(f"  🔴 {sum(1 for r in results if r['health']=='red')} críticos  "
          f"🟡 {sum(1 for r in results if r['health']=='yellow')} atenção  "
          f"🟢 {sum(1 for r in results if r['health']=='green')} saudáveis")

if __name__ == "__main__":
    main()
