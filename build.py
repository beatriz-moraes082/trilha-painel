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

NICHO_CSS = {
    "Imobiliário": ("background:#ede9fe;color:#5b21b6;", "imobiliario"),
    "Hotelaria":   ("background:#fce7f3;color:#9d174d;", "hotelaria"),
    "Auto":        ("background:#dbeafe;color:#1e40af;", "auto"),
}

def _chip(text, bg, color, size="11px"):
    return (f'<span style="display:inline-block;font-size:{size};font-weight:700;'
            f'letter-spacing:.03em;padding:2px 9px;border-radius:20px;'
            f'background:{bg};color:{color};white-space:nowrap;">{text}</span>')

def report_badge_html(cd):
    conc = cd["report_conclusion"]
    days = cd["report_days_ago"]
    repo = cd["client"].get("report_repo")
    note = cd["client"].get("note")
    if note and not repo:
        return _chip("Manual", "#f3f4f6", "#6b7280")
    if not repo:
        return _chip("—", "#f3f4f6", "#6b7280")
    if conc in (None, "no_token"):
        return _chip("sem dados", "#f3f4f6", "#6b7280")
    if conc == "failure":
        return _chip("FALHOU", "#fee2e2", "#991b1b")
    if conc == "success":
        label = f"✓ há {days}d" if days is not None else "✓ ok"
        bg, col = ("#dcfce7", "#166534") if (days or 0) <= 7 else ("#fef9c3", "#854d0e")
        return _chip(label, bg, col)
    return _chip(conc, "#f3f4f6", "#6b7280")

def meta_line(acc):
    """Uma linha limpa por conta Meta."""
    if not acc["is_active"]:
        dot = '<span style="color:#dc2626;font-size:10px;">●</span>'
        status = f'<span style="color:#dc2626;font-weight:600;">{acc["status_label"]}</span>'
    else:
        dot = '<span style="color:#16a34a;font-size:10px;">●</span>'
        camps = acc.get("active_campaigns")
        camp_str = f" · {camps} camp." if camps is not None else ""
        status = f'<span style="color:#16a34a;font-weight:600;">Ativa{camp_str}</span>'

    bal_str = f' · <span style="color:#374151;">R$ {fmt_br(acc["balance"])}</span>' if acc.get("balance") is not None else ""
    burn_str = (f' · <span style="color:#6b7280;">R$ {fmt_br(acc["burn_daily"])}/dia</span>'
                if acc.get("burn_daily") else "")
    days_str = ""
    if acc.get("days_left") is not None:
        dc = "#dc2626" if acc["days_left"] < 5 else ("#ca8a04" if acc["days_left"] < 10 else "#6b7280")
        days_str = f' · <span style="color:{dc};font-weight:600;">{acc["days_left"]}d</span>'

    name_short = acc["name"]
    return (f'<div style="display:flex;align-items:center;gap:6px;padding:5px 0;'
            f'border-bottom:1px solid #f3f4f6;font-size:13px;">'
            f'{dot} {status}{bal_str}{burn_str}{days_str}'
            f'<span style="color:#9ca3af;font-size:11px;margin-left:auto;text-align:right;max-width:140px;'
            f'overflow:hidden;white-space:nowrap;text-overflow:ellipsis;">{name_short}</span>'
            f'</div>')

def build_html(results, now_str):
    n_red    = sum(1 for r in results if r["health"] == "red")
    n_yellow = sum(1 for r in results if r["health"] == "yellow")
    n_green  = sum(1 for r in results if r["health"] == "green")
    n_total  = len(results)

    # ── Briefing ──────────────────────────────────────────────────────────────
    p1_items, p2_items = [], []
    for cd in results:
        name = cd["client"]["name"]
        for a in cd["alerts"]:
            p1_items.append({**a, "client_name": name})
        for w in cd["warnings"]:
            p2_items.append({**w, "client_name": name})

    def briefing_rows(items, level):
        bc = "#fef2f2" if level == "red" else "#fefce8"
        lc = "#dc2626" if level == "red" else "#ca8a04"
        oc = "#dc2626" if level == "red" else "#ca8a04"
        icon = "⚠" if level == "red" else "⚡"
        rows = ""
        for it in items:
            rows += f"""
      <div style="display:grid;grid-template-columns:160px 1fr auto;gap:0;border-bottom:1px solid #f3f4f6;align-items:start;">
        <div style="padding:12px 16px 12px 0;border-right:1px solid #f3f4f6;">
          <div style="font-size:13px;font-weight:700;color:#1a1a1a;">{it['client_name']}</div>
        </div>
        <div style="padding:12px 16px;">
          <div style="font-size:13px;font-weight:600;color:#1a1a1a;">{icon} {it['title']}</div>
          <div style="font-size:12px;color:#6b7280;margin-top:3px;line-height:1.5;">{it['action']}</div>
        </div>
        <div style="padding:12px 0 12px 8px;">
          <span style="display:inline-block;font-size:11px;font-weight:700;padding:3px 10px;border-radius:20px;background:{oc};color:white;white-space:nowrap;">{it['owner']}</span>
        </div>
      </div>"""
        return rows

    briefing_p1 = ""
    if p1_items:
        briefing_p1 = f"""
    <div style="margin-bottom:24px;">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">
        <span style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:#dc2626;">P1 — Resolver hoje</span>
        <span style="font-size:11px;font-weight:700;padding:2px 9px;border-radius:20px;background:#fee2e2;color:#dc2626;">{len(p1_items)}</span>
      </div>
      <div style="border:1px solid #fecaca;border-radius:8px;overflow:hidden;background:white;">
        <div style="display:grid;grid-template-columns:160px 1fr auto;background:#fef2f2;border-bottom:1px solid #fecaca;">
          <div style="padding:7px 16px 7px 0;font-size:11px;font-weight:700;color:#dc2626;text-transform:uppercase;letter-spacing:.05em;">Cliente</div>
          <div style="padding:7px 16px;font-size:11px;font-weight:700;color:#dc2626;text-transform:uppercase;letter-spacing:.05em;">Problema · Próximo passo</div>
          <div style="padding:7px 0;font-size:11px;font-weight:700;color:#dc2626;text-transform:uppercase;letter-spacing:.05em;">Dono</div>
        </div>
        {briefing_rows(p1_items, 'red')}
      </div>
    </div>"""

    briefing_p2 = ""
    if p2_items:
        briefing_p2 = f"""
    <div>
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">
        <span style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:#ca8a04;">P2 — Esta semana</span>
        <span style="font-size:11px;font-weight:700;padding:2px 9px;border-radius:20px;background:#fef9c3;color:#ca8a04;">{len(p2_items)}</span>
      </div>
      <div style="border:1px solid #fde68a;border-radius:8px;overflow:hidden;background:white;">
        <div style="display:grid;grid-template-columns:160px 1fr auto;background:#fefce8;border-bottom:1px solid #fde68a;">
          <div style="padding:7px 16px 7px 0;font-size:11px;font-weight:700;color:#ca8a04;text-transform:uppercase;letter-spacing:.05em;">Cliente</div>
          <div style="padding:7px 16px;font-size:11px;font-weight:700;color:#ca8a04;text-transform:uppercase;letter-spacing:.05em;">Aviso · Próximo passo</div>
          <div style="padding:7px 0;font-size:11px;font-weight:700;color:#ca8a04;text-transform:uppercase;letter-spacing:.05em;">Dono</div>
        </div>
        {briefing_rows(p2_items, 'yellow')}
      </div>
    </div>"""

    if not p1_items and not p2_items:
        briefing_p1 = """
    <div style="text-align:center;padding:32px 0;color:#16a34a;">
      <div style="font-size:28px;margin-bottom:8px;">✓</div>
      <div style="font-size:15px;font-weight:600;">Carteira saudável — nenhuma ação pendente</div>
    </div>"""

    # ── Cards ─────────────────────────────────────────────────────────────────
    sorted_results = sorted(
        results,
        key=lambda r: ({"red": 0, "yellow": 1, "green": 2}[r["health"]], r["client"]["nicho"], r["client"]["name"])
    )

    cards_html = ""
    for cd in sorted_results:
        cl   = cd["client"]
        h    = cd["health"]
        nicho = cl["nicho"]
        nicho_css, nicho_id = NICHO_CSS.get(nicho, ("background:#f3f4f6;color:#374151;", normalize(nicho)))
        _np = {k.strip(): v.strip() for k, v in (p.split(":", 1) for p in nicho_css.rstrip(";").split(";") if ":" in p)}
        nicho_bg, nicho_col = _np.get("background", "#f3f4f6"), _np.get("color", "#374151")

        # Top border color per health
        top_border = {"red": "#dc2626", "yellow": "#f59e0b", "green": "#22c55e"}[h]

        # Prio chip
        prio_chip = {
            "red":    _chip("P1", "#fee2e2", "#dc2626"),
            "yellow": _chip("P2", "#fef9c3", "#ca8a04"),
            "green":  _chip("OK", "#f0fdf4", "#16a34a"),
        }[h]

        # Alert lines in card (condensed — detail is in briefing)
        alert_lines = ""
        all_issues = [("red", a) for a in cd["alerts"]] + [("yellow", w) for w in cd["warnings"]]
        for lv, it in all_issues:
            icon = "⚠" if lv == "red" else "⚡"
            tc   = "#dc2626" if lv == "red" else "#92400e"
            bc   = "#fef2f2" if lv == "red" else "#fefce8"
            alert_lines += (f'<div style="font-size:12px;font-weight:600;color:{tc};'
                            f'background:{bc};padding:7px 14px;margin:0 -1px;">'
                            f'{icon} {it["title"]}</div>')

        # Meta rows
        meta_rows = ""
        for acc in cd["meta"]:
            meta_rows += meta_line(acc)
        if not cd["meta"] and (cl.get("meta_ids") or cl.get("meta_names")):
            meta_rows = '<div style="font-size:13px;color:#dc2626;padding:6px 0;">Conta não encontrada</div>'
        if not meta_rows:
            meta_rows = '<div style="font-size:13px;color:#9ca3af;padding:6px 0;">Sem conta Meta mapeada</div>'

        # Total spend
        spend_line = ""
        if cd["total_spend_7d"] is not None and len(cd["meta"]) > 1:
            spend_line = (f'<div style="text-align:right;font-size:11px;color:#9ca3af;padding-top:4px;">'
                          f'Total 7d: R$ {fmt_br(cd["total_spend_7d"])}</div>')

        # Report row
        note_html = (f'<div style="font-size:11px;color:#9ca3af;margin-top:2px;">{cl["note"]}</div>'
                     if cl.get("note") else "")
        rdate = cd["report_date"] or ""
        rdate_html = (f'<span style="font-size:11px;color:#9ca3af;">{rdate}</span>' if rdate else "")
        report_row = (f'<div style="display:flex;align-items:center;gap:10px;padding:10px 0 2px;">'
                      f'{report_badge_html(cd)}{rdate_html}'
                      f'</div>{note_html}')

        cards_html += f"""
  <div class="card" data-nicho="{nicho_id}" data-health="{h}" data-assessor="{cl.get('assessor','').lower()}"
       style="background:white;border-radius:10px;border:1px solid #e5e7eb;overflow:hidden;
              box-shadow:0 1px 4px rgba(0,0,0,.06);border-top:3px solid {top_border};">
    <div style="padding:14px 16px 10px;display:flex;justify-content:space-between;align-items:flex-start;gap:8px;">
      <div>
        <div style="font-size:15px;font-weight:700;color:#111;margin-bottom:5px;">{cl['name']}</div>
        <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;">
          {_chip(nicho, nicho_bg, nicho_col, '11px')}
          {_chip(cl.get('assessor','?'), '#f3f4f6', '#374151', '11px')}
        </div>
      </div>
      {prio_chip}
    </div>
    {alert_lines}
    <div style="padding:10px 16px 14px;">
      <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:#9ca3af;margin-bottom:6px;">Meta Ads</div>
      {meta_rows}
      {spend_line}
      <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:#9ca3af;margin-top:12px;margin-bottom:2px;">Relatório</div>
      {report_row}
    </div>
  </div>"""

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Painel Beatriz — Trilha</title>
<style>
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{ font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
        background:#f5f4f0;color:#111;min-height:100vh; }}
.card {{ transition:box-shadow .15s,transform .15s; }}
.card:hover {{ box-shadow:0 6px 20px rgba(0,0,0,.1) !important;transform:translateY(-1px); }}
.hidden {{ display:none !important; }}
.filter-btn {{ padding:6px 14px;border-radius:20px;border:1.5px solid #d1d5db;background:white;
               font-size:13px;font-weight:600;cursor:pointer;transition:all .15s;color:#374151; }}
.filter-btn:hover {{ border-color:#ee4c20;color:#ee4c20; }}
.filter-btn.active {{ background:#111;border-color:#111;color:white; }}
.filter-btn.f-red.active {{ background:#dc2626;border-color:#dc2626; }}
.filter-btn.f-yellow.active {{ background:#ca8a04;border-color:#ca8a04; }}
.filter-btn.f-green.active {{ background:#16a34a;border-color:#16a34a; }}
@media(max-width:600px){{
  .briefing-table {{ display:none; }}
  .briefing-mobile {{ display:block !important; }}
}}
</style>
</head>
<body>

<!-- ── Header ──────────────────────────────────────────────────────────── -->
<div style="background:#111;padding:16px 28px;display:flex;align-items:center;gap:14px;flex-wrap:wrap;">
  <span style="color:#ee4c20;font-size:12px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;">Trilha</span>
  <span style="color:white;font-size:17px;font-weight:700;">Painel Beatriz</span>
  <span style="color:#6b7280;font-size:12px;margin-left:auto;">{now_str}</span>
</div>

<!-- ── Métricas ────────────────────────────────────────────────────────── -->
<div style="background:#1a1a1a;display:grid;grid-template-columns:repeat(4,1fr);border-bottom:1px solid #2a2a2a;">
  <div style="padding:18px 24px;border-right:1px solid #2a2a2a;">
    <div style="font-size:32px;font-weight:900;color:white;line-height:1;">{n_total}</div>
    <div style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.07em;color:#6b7280;margin-top:4px;">Clientes</div>
  </div>
  <div style="padding:18px 24px;border-right:1px solid #2a2a2a;">
    <div style="font-size:32px;font-weight:900;color:#f87171;line-height:1;">{n_red}</div>
    <div style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.07em;color:#6b7280;margin-top:4px;">P1 Crítico</div>
  </div>
  <div style="padding:18px 24px;border-right:1px solid #2a2a2a;">
    <div style="font-size:32px;font-weight:900;color:#fbbf24;line-height:1;">{n_yellow}</div>
    <div style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.07em;color:#6b7280;margin-top:4px;">P2 Atenção</div>
  </div>
  <div style="padding:18px 24px;">
    <div style="font-size:32px;font-weight:900;color:#4ade80;line-height:1;">{n_green}</div>
    <div style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.07em;color:#6b7280;margin-top:4px;">Saudável</div>
  </div>
</div>

<!-- ── Briefing ────────────────────────────────────────────────────────── -->
<div style="background:white;border-bottom:1px solid #e5e7eb;padding:28px 28px 24px;">
  <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:#9ca3af;margin-bottom:20px;">Briefing do dia</div>
  {briefing_p1}
  {briefing_p2}
</div>

<!-- ── Filtros ─────────────────────────────────────────────────────────── -->
<div style="background:white;padding:12px 28px;display:flex;flex-wrap:wrap;gap:8px;align-items:center;
            border-bottom:1px solid #e5e7eb;position:sticky;top:0;z-index:10;box-shadow:0 1px 4px rgba(0,0,0,.06);">
  <span style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:#9ca3af;margin-right:2px;">Prioridade</span>
  <button class="filter-btn active" data-filter="all">Todos</button>
  <button class="filter-btn f-red"    data-filter="health:red">P1 Crítico</button>
  <button class="filter-btn f-yellow" data-filter="health:yellow">P2 Atenção</button>
  <button class="filter-btn f-green"  data-filter="health:green">Saudável</button>
  <div style="width:1px;height:20px;background:#e5e7eb;margin:0 4px;"></div>
  <span style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:#9ca3af;margin-right:2px;">Nicho</span>
  <button class="filter-btn" data-filter="nicho:imobiliario">Imobiliário</button>
  <button class="filter-btn" data-filter="nicho:hotelaria">Hotelaria</button>
  <button class="filter-btn" data-filter="nicho:auto">Auto</button>
  <div style="width:1px;height:20px;background:#e5e7eb;margin:0 4px;"></div>
  <span style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:#9ca3af;margin-right:2px;">Assessor</span>
  <button class="filter-btn" data-filter="assessor:enrique">Enrique</button>
  <button class="filter-btn" data-filter="assessor:bruno">Bruno</button>
</div>

<!-- ── Grid ────────────────────────────────────────────────────────────── -->
<div id="grid" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px;padding:24px 28px;">
{cards_html}
</div>

<div style="text-align:center;padding:28px;font-size:12px;color:#9ca3af;">
  Trilha Performance Digital · Carteira Beatriz · atualiza a cada 6h
</div>

<script>
const btns  = document.querySelectorAll('.filter-btn');
const cards = document.querySelectorAll('#grid .card');
function applyFilters() {{
  const active = [...btns].filter(b => b.classList.contains('active')).map(b => b.dataset.filter);
  if (active.includes('all')) {{ cards.forEach(c => c.classList.remove('hidden')); return; }}
  cards.forEach(c => {{
    const show = active.every(f => {{
      if (f.startsWith('health:'))   return c.dataset.health   === f.slice(7);
      if (f.startsWith('nicho:'))    return c.dataset.nicho    === f.slice(6);
      if (f.startsWith('assessor:')) return c.dataset.assessor === f.slice(9);
      return true;
    }});
    c.classList.toggle('hidden', !show);
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
