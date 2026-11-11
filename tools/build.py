#!/usr/bin/env python3
"""Build sfc-gh-dfreriks.github.io: one page listing every public SAP / Snowflake demo.

    python3 tools/build.py            # capture screenshots of every live demo, then write index.html
    python3 tools/build.py --no-shots # reuse img/*.jpg, only rewrite index.html

To add a demo, add an entry to DEMOS and rerun.
"""
import asyncio
import datetime as dt
import html
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
IMG = ROOT / "img"
GH = "https://github.com/sfc-gh-dfreriks/"
PAGES = "https://sfc-gh-dfreriks.github.io/"

SECTIONS = [
    ("sap360", "SAP Business Data Cloud 360 apps",
     "Full applications over SAP BDC data products shared zero-copy into Snowflake: medallion SQL, a semantic view, "
     "a Cortex Agent and a React app. Each also ships as a Snowflake Native App."),
    ("mfg", "Manufacturing use cases",
     "Portable apps on the mfg-use-cases framework: any SAP (ECC, S/4HANA, BW or BDC) plus non-SAP sources, "
     "spec-generated dbt adapters, gold dynamic tables, a semantic view and a Cortex Agent."),
    ("oge", "Oil, Gas & Energy use cases",
     "The same framework for oil, gas, energy and utilities: SAP IS-Oil and IS-U (simulated) plus operational sources such as "
     "historians, LDAR, CTRM, satellite and CEMS emissions, partner portals and smart meters."),
    ("explore", "Ontologies and explorers",
     "Browse the SAP BDC catalog and the knowledge graphs that tie the 360 apps together."),
]

# Shorter names for the tab bar.
TAB_LABEL = {"sap360": "SAP BDC 360", "mfg": "Manufacturing", "oge": "Oil, Gas & Energy", "explore": "Ontologies & explorers"}

# (section, site repo, title, description, tags, source repo)
DEMOS = [
    ("sap360", "finance-360-public", "Finance 360",
     "Live, AI-powered finance analytics from SAP BDC standard data products, with Ask Cortex on every page and a "
     "Cortex Agent in Snowflake Intelligence.", ["SAP BDC", "Cortex Agent", "Native App"], "sap-bdc-finance-360"),
    ("sap360", "sales-360-public", "Sales 360",
     "Sales and CRM analytics from SAP BDC standard data products, with Ask Cortex on every page and a Cortex Agent "
     "in Snowflake Intelligence.", ["SAP BDC", "Cortex Agent", "Native App"], "sap-bdc-sales-360"),
    ("sap360", "spend-360-public", "Spend 360",
     "Spend intelligence from SAP BDC standard data products: procurement and supplier spend, with Ask Cortex on "
     "every page and a Cortex Agent in Snowflake Intelligence.", ["SAP BDC", "Cortex Agent", "Native App"], "sap-bdc-spend-360"),
    ("sap360", "people-360-public", "People 360",
     "Workforce analytics from SAP BDC standard data products, with Ask Cortex on every page and a Cortex Agent in "
     "Snowflake Intelligence.", ["SAP BDC", "Cortex Agent", "Native App"], "sap-bdc-people-360"),
    ("sap360", "supply-chain-360-public", "Supply Chain 360",
     "Supply-chain analytics from SAP BDC standard data products, with Ask Cortex on every page and a Cortex Agent "
     "in Snowflake Intelligence.", ["SAP BDC", "Cortex Agent", "Native App"], "sap-bdc-supply-chain-360"),
    ("sap360", "working-capital-360-public", "Working Capital 360",
     "Cash conversion from SAP BDC data products: DSO, DPO, DIO and the cash conversion cycle, AR and AP, cash "
     "and liquidity, early payment and supply chain finance, and inventory.", ["SAP BDC", "Cortex Agent", "Native App"], "sap-bdc-working-capital-360"),
    ("mfg", "mfg-order-to-cash-public", "Orders to Cash",
     "Quote to cash across SAP and Salesforce CPQ, carrier tracking, AR automation and bank statements: OTIF, DSO "
     "against best possible, CEI, disputes by root cause, cash application and Customer 360.",
     ["Any SAP", "Non-SAP sources", "dbt", "Cortex"], "mfg-use-cases"),
    ("mfg", "mfg-multi-erp-spend-public", "Multi-ERP Spend & Supplier Risk",
     "One spend and supplier-risk view across two SAP instances and acquired Oracle EBS, Dynamics 365, NetSuite and "
     "Coupa: supplier golden record, price variance by plant, risk and a supplier optimization model.",
     ["Any SAP", "Non-SAP ERPs", "dbt", "Cortex"], "mfg-use-cases"),
    ("mfg", "mfg-procure-to-pay-public", "Procure to Pay",
     "Full procure-to-pay cycle across SAP and non-SAP sources: guided buying, sourcing events, POs, supplier "
     "confirmations, goods receipt, invoice 3-way match, AP open items and payment runs with discount capture.",
     ["Any SAP", "Non-SAP sources", "dbt", "Cortex"], "mfg-use-cases"),
    ("oge", "mfg-hydrocarbon-accounting-public", "Hydrocarbon Accounting 360",
     "From the wellhead to the owner check: production volumes, valuation and realized prices, royalties and owner "
     "distribution, lease operating expense, netbacks and volume-to-revenue reconciliation.",
     ["Any SAP", "IS-Oil", "Land & field tickets", "Cortex"], "mfg-use-cases"),
    ("oge", "mfg-asset-integrity-public", "Asset Integrity & Reliability",
     "Which critical assets will fail or leak next: SAP PM plus process historian, inspections and LDAR, with an "
     "asset risk score, deferred production, work order backlog and methane.",
     ["Any SAP", "Historian", "LDAR", "Cortex"], "mfg-use-cases"),
    ("oge", "mfg-downstream-margin-public", "Downstream Margin",
     "Terminal-to-rack margin: nominations vs receipts, QCI gains and losses, exchange imbalances, rack price vs "
     "benchmark and trading positions from a CTRM.",
     ["Any SAP", "IS-Oil", "CTRM", "Cortex"], "mfg-use-cases"),
    ("oge", "mfg-emissions-mrv-public", "Emissions MRV & Methane Intelligence",
     "What did we emit and how does measured methane compare with what we report: SAP EHS estimates plus CEMS and "
     "satellite plume detections, leak repair and regulatory cost.",
     ["Any SAP", "CEMS", "Satellite", "Cortex"], "mfg-use-cases"),
    ("oge", "mfg-jv-partner-exchange-public", "JV Partner Data Exchange",
     "What each joint-venture partner owes, what they dispute and how to share it securely: JIB billing, cash calls, "
     "AFEs, disputes and a per-partner secure share.",
     ["Any SAP", "Partner portal", "Secure share", "Cortex"], "mfg-use-cases"),
    ("oge", "mfg-utilities-m2c-public", "Utilities Meter-to-Cash",
     "The seven-stage meter-to-cash cycle on SAP IS-U: meter reading, VEE, rate calculation, bill generation and "
     "delivery, payment collection and exceptions, with ten KPIs against industry benchmarks.",
     ["Any SAP", "IS-U", "AMI", "Cortex"], "mfg-use-cases"),
    ("explore", "enterprise-ontology", "Enterprise Ontology",
     "The master ontology across six SAP BDC 360 apps on Snowflake: the business entities they share and the "
     "graph that links them.", ["Ontology", "Knowledge graph"], "enterprise-ontology"),
    ("explore", "supply-chain-ontology", "Supply Chain Ontology",
     "Ontology explorer for the supply-chain slice of the SAP BDC catalog: 36 data products and 338 CDS entities, "
     "with graph traversal and Cortex Analyst.", ["Ontology", "Cortex Analyst"], "supply-chain-ontology"),
    ("explore", "sap-bdc-data-products", "SAP BDC Data Products",
     "Interactive explorer for the SAP Business Data Cloud data product portfolio, mined from the public SAP "
     "Business Accelerator Hub catalog.", ["SAP BDC", "Catalog"], "sap-bdc-data-products"),
]


PAGES_FOUND: dict = {}
PAGES_FILE = IMG / "pages.json"


async def capture():
    from playwright.async_api import async_playwright
    IMG.mkdir(exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1440, "height": 900})
        for _, repo, title, *_ in DEMOS:
            await pg.goto(PAGES + repo + "/", wait_until="networkidle", timeout=120000)
            await pg.wait_for_timeout(4000)
            await pg.screenshot(path=str(IMG / f"{repo}.jpg"), type="jpeg", quality=78)
            names = await pg.eval_on_selector_all(
                "aside button, aside a, nav button, nav a",
                "els => els.map(e => e.innerText.trim()).filter(t => t && t.length < 40 && !t.includes('\\n'))")
            names = list(dict.fromkeys(names))
            stop = next((i for i, n in enumerate(names) if n in ("All", "None", "USD")), len(names))
            PAGES_FOUND[repo] = names[:stop]  # the sidebar filters follow the page list
            print("captured", title, len(PAGES_FOUND[repo]), "pages")
        await b.close()
    PAGES_FILE.write_text(json.dumps(PAGES_FOUND, indent=1))


def card(repo, title, desc, tags, src):
    e = html.escape
    tag_html = "".join(f"<span class=tag>{e(t)}</span>" for t in tags)
    found = json.loads(PAGES_FILE.read_text()).get(repo, []) if PAGES_FILE.exists() else []
    pages = f"<p class=pages><b>{len(found)} pages:</b> {e(' · '.join(found))}</p>" if len(found) >= 3 else ""
    return f"""      <article class=card>
        <a class=thumb href="{PAGES}{repo}/" target=_blank rel=noopener><img src="img/{repo}.jpg" alt="{e(title)} screenshot" loading=lazy></a>
        <div class=body>
          <h3><a href="{PAGES}{repo}/" target=_blank rel=noopener>{e(title)}</a></h3>
          <p>{e(desc)}</p>
          {pages}
          <div class=tags>{tag_html}</div>
          <div class=links><a class=btn href="{PAGES}{repo}/" target=_blank rel=noopener>Open demo</a><a class=src href="{GH}{src}" target=_blank rel=noopener>Source</a></div>
        </div>
      </article>"""


def page():
    sections = []
    for key, name, blurb in SECTIONS:
        cards = "\n".join(card(r, t, d, tg, s) for sec, r, t, d, tg, s in DEMOS if sec == key)
        sections.append(f"""  <section id={key}>
    <h2>{html.escape(name)}</h2>
    <p class=lead>{html.escape(blurb)}</p>
    <div class=grid>
{cards}
    </div>
  </section>""")
    count = {k: sum(1 for d in DEMOS if d[0] == k) for k, _, _ in SECTIONS}
    tab = lambda k, n, c: f'<a class=tab href="#{k}" data-tab="{k}">{html.escape(n)}<span>{c}</span></a>'
    tabs = tab("all", "All", len(DEMOS)) + "".join(tab(k, TAB_LABEL.get(k, n), count[k]) for k, n, _ in SECTIONS)
    return f"""<!doctype html>
<html lang=en>
<head>
<meta charset=utf-8>
<meta name=viewport content="width=device-width, initial-scale=1">
<title>SAP + Snowflake demos · Dave Freriks</title>
<meta name=description content="Public SAP and Snowflake demo applications: SAP BDC 360 apps, manufacturing and oil, gas and energy use cases, and ontology explorers.">
<link rel=icon href="img/snowflake_logo.svg">
<link rel=stylesheet href="style.css">
</head>
<body>
<header class=hero>
  <div class=wrap>
    <div class=brand><img src="img/snowflake_logo.svg" alt="Snowflake" class=logo><span>SAP + Snowflake demos</span></div>
    <h1>Public demo applications</h1>
    <p>Working demos of SAP data on Snowflake: SAP Business Data Cloud 360 apps, portable manufacturing and oil, gas and
    energy use cases, and catalog explorers. Every demo runs in the browser with no login, on synthetic or representative data.</p>
  </div>
</header>
<nav class=tabs aria-label="Demo groups"><div class=wrap>{tabs}</div></nav>
<main class=wrap>
{chr(10).join(sections)}
  <p class=note>All data in these demos is synthetic or representative; company, customer and supplier names are fictional.
  Each public site is a read-only static snapshot of an application that runs live on Snowflake.</p>
</main>
<script>
// Tabs: show one group (or all). The hash keeps the choice shareable; without JavaScript every group shows.
const tabs = document.querySelectorAll(".tab"), groups = document.querySelectorAll("main section");
function show(key) {{
  if (![...tabs].some((t) => t.dataset.tab === key)) key = "all";
  tabs.forEach((t) => t.classList.toggle("on", t.dataset.tab === key));
  groups.forEach((g) => (g.hidden = key !== "all" && g.id !== key));
}}
tabs.forEach((t) => t.addEventListener("click", (e) => {{ e.preventDefault(); history.replaceState(null, "", "#" + t.dataset.tab); show(t.dataset.tab); }}));
show(location.hash.slice(1));
</script>
<footer><div class=wrap>Dave Freriks · Snowflake · <a href="https://github.com/sfc-gh-dfreriks">github.com/sfc-gh-dfreriks</a> · updated {dt.date.today():%d %B %Y}</div></footer>
</body>
</html>
"""


def main():
    if "--no-shots" not in sys.argv:
        asyncio.run(capture())
    (ROOT / "index.html").write_text(page())
    print("wrote", ROOT / "index.html")


if __name__ == "__main__":
    main()
