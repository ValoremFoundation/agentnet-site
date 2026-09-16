#!/usr/bin/env python3
"""Build the consolidated agentic.advalorem.io static site.

Single site: agentic + capabilities + categories + providers (+ new provider
onboarding) + research + AI-agent surfaces (llms.txt, catalog, agent/ guide,
robots, sitemap, JSON-LD). No builder.advalorem.io / mev.advalorem.io links.
"""
import json, os, re, datetime, html
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = "https://agentic.advalorem.io"
DATA = json.load(open(os.path.join(ROOT, "build_data.json")))
CATS_DETAIL = json.load(open(os.path.join(ROOT, "cats_detail.json")))
CAPS = DATA["capabilities"]  # (id, title, provider, availability, price)
PROVIDERS = DATA["providers"]
PROV_COUNTS = DATA["prov_counts"]
CATEGORIES = DATA["categories"]
CATALOG = json.load(open(os.path.join(ROOT, "agentnet-catalog.json")))
GEN_TS = "2026-09-16T18:00:00+00:00"
GEN_HUMAN = "September 16, 2026"

SELLABLE = "Available Now"

def esc(s):
    return html.escape(str(s), quote=True)

def slug(s):
    return re.sub(r"[^a-z0-9-]+", "-", s.lower()).strip("-")

def money(price):
    if price is None or price == "":
        return None
    try:
        return f"${float(price)/1000000:.4f}"
    except Exception:
        return str(price)

NAV_SECTIONS = [
    ("capabilities/", "capabilities"),
    ("categories/", "categories"),
    ("providers/", "providers"),
    ("providers/submit/", "become a provider"),
    ("research/", "research"),
]

def nav(rel_depth, active=""):
    brand = ("../" * rel_depth) if rel_depth else "./"
    links = []
    for href, label in NAV_SECTIONS:
        cls = ' class=" active"' if active == label else ""
        links.append(f'<a href="{brand}{href}"{cls}>{label}</a>')
    return f'''<header class="adv-nav"><div class="adv-nav-inner container"><a class="adv-brand" href="{brand}"><svg viewBox="0 0 32 32" width="26" height="26" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" class="logo"><path d="M7 24 L16 7 L25 24"/><path d="M11 17 H21"/></svg><span class="brand-name">AdValorem</span></a><nav class="adv-nav-links" aria-label="Section">{''.join(links)}</nav></div></header>'''

def footer(rel_depth):
    base = ("../" * rel_depth) if rel_depth else "./"
    api_url = f"{BASE}/api/v1/capabilities"
    return f'''<footer class="adv-footer"><div class="container">
<p><strong>AgentNet / AdValorem</strong> — a single agentic commerce catalog. Every record below declares its provider, availability, and machine contract. Payments settle over x402 in USDC on Base.</p>
<p class="dim">Machine surfaces: <a href="{base}llms.txt">llms.txt</a> · <a href="{base}llms-full.txt">llms-full.txt</a> · <a href="{base}agentnet-catalog.json">agentnet-catalog.json</a> · <a href="{base}agent/">agent guide</a> · <a href="{api_url}">API</a> · <a href="{base}robots.txt">robots.txt</a> · <a href="{base}sitemap.xml">sitemap</a></p>
<p class="dim">Regenerated {GEN_HUMAN}. Canonical source: agentnet_marketplace.public.capabilities.</p>
</div></footer>'''

def head_meta(title, desc, url, extra_ld=None, canonical=None, rel_depth=0):
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "Organization", "@id": f"{url}#org", "name": "AdValorem", "url": f"{BASE}/", "description": "AgentNet: an agent-native catalog of capabilities sold over x402."},
    ]}
    if extra_ld:
        ld["@graph"].append(extra_ld)
    base = ("../" * rel_depth) if rel_depth else "./"
    return f'''<!doctype html>
<html lang="en" data-domain="agentic">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta property="og:site_name" content="AdValorem — AgentNet">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="website">
<link rel="canonical" href="{canonical or url}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap">
<link rel="stylesheet" href="{base}_shell/tokens.css">
<link rel="stylesheet" href="{base}_shell/base.css">
<link rel="stylesheet" href="{base}_shell/shell.css">
<link rel="stylesheet" href="{base}_shell/propagation.css">
<script type="application/ld+json">{json.dumps(ld)}</script>
</head>'''

def page(title, desc, rel_depth, body, active="", url=None, extra_ld=None):
    # rel_depth is the page's URL depth. The file sits at the same directory
    # depth as the URL (e.g. /capabilities/X/ -> capabilities/X/index.html),
    # so CSS/nav/footer links (emitted into the file, relative to its dir)
    # need rel_depth ups to reach root, while inline body links (resolved by
    # the browser relative to the URL) need rel_depth-1 ups. Callers already
    # write body links with the right count; D() helpers build them.
    head = head_meta(title, desc, url or f"{BASE}/", extra_ld, rel_depth=rel_depth)
    return head + f'\n<body data-domain="agentic">\n<a class="skip-link" href="#main">Skip to main content</a>\n' + nav(rel_depth, active) + f'\n<main id="main" class="adv-main">\n{body}\n</main>\n' + footer(rel_depth) + '\n</body></html>\n'

def write(relpath, content):
    p = os.path.join(ROOT, relpath)
    d = os.path.dirname(p)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(p, "w") as f:
        f.write(content)

# ---------------------------------------------------------------- capabilities index
def cap_rows_html(caps, href_prefix=""):
    out = []
    for cid, title, provider, avail, price in caps:
        badge = "adv-badge-live" if avail == SELLABLE else "adv-badge-pilot"
        blabel = "Live" if avail == SELLABLE else "Preview"
        pr = money(price) or "price on wire"
        out.append(f'''<a class="adv-cap-card" href="{href_prefix}{cid}/" data-capability-id="{esc(cid)}" data-availability="{esc(avail)}">
  <span class="adv-outcome-badge"><span class="adv-badge {badge}">{blabel}</span></span>
  <h3 class="adv-card-title">{esc(title)}</h3>
  <p class="adv-card-meta"><span class="adv-card-provider">{esc(provider)}</span><span class="adv-price-tag">{esc(pr)}</span><span class="adv-card-avail">{esc(avail)}</span></p>
  <span class="adv-card-foot"><code class="adv-card-id">{esc(cid)}</code></span>
</a>''')
    return "\n".join(out)

# Depth helper: inline links in a page body are relative to the page's URL,
# which sits one level shallower than the file that renders it.
def D(rel_depth, section):
    return ("../" * rel_depth) + section

def build_index():
    sellable = [c for c in CAPS if c[3] == SELLABLE]
    n = len(CAPS)
    body = f'''
  <section class="adv-hero"><div class="container"><div class="adv-hero-inner">
    <p class="adv-eyebrow">agent-native · x402 · Base mainnet · single catalog</p>
    <h1 class="adv-hero-headline">What do you need done?</h1>
    <p class="adv-lede">AgentNet is one catalog: {n} canonical capabilities sold over x402. Humans browse outcomes. AI agents discover machine contracts. Providers list their services and get paid directly — we take a small commission for the privilege of using x402.</p>
    <form class="adv-cta-row" action="./capabilities/" method="get" role="search" aria-label="Capability search">
      <input class="btn-code adv-hero-search" name="q" autocomplete="off" placeholder='e.g. "translate text" · "find liquidation candidates" · "research a company"'>
      <button class="btn btn-primary btn-lg" type="submit">Search capabilities</button>
    </form>
    <p class="dim" style="font-size:.85rem;margin-top:12px">{len(sellable)} sellable now · {len(PROVIDERS)} providers · 16 category hubs · payments in USDC on Base over x402.</p>
  </div></div></section>
  <section class="adv-section container">
    <div class="adv-section-head-row"><div><h2 class="adv-h1">For AI agents</h2>
    <p class="adv-section-sub">Machine-readable discovery, straight off the live catalog — no scraping required.</p></div></div>
    <div class="adv-grid adv-grid-4">
      <a class="adv-cap-card" href="./llms.txt"><h3 class="adv-card-title">llms.txt</h3><p class="adv-card-desc">Compact catalog of every capability with URL, provider and state. Built for LLMs and agents.</p></a>
      <a class="adv-cap-card" href="./agent/"><h3 class="adv-card-title">Agent purchasing guide</h3><p class="adv-card-desc">Step-by-step: discover a capability, pay over x402, verify the result. For GPTBot, Claude, Perplexity, and any HTTP agent.</p></a>
      <a class="adv-cap-card" href="./agentnet-catalog.json"><h3 class="adv-card-title">agentnet-catalog.json</h3><p class="adv-card-desc">The full canonical catalog as JSON: {n} records, payment details, and canonical states.</p></a>
      <a class="adv-cap-card" href="./providers/submit/"><h3 class="adv-card-title">List your services</h3><p class="adv-card-desc">One form + one wallet. Become a provider, get indexed to AEO/SEO and LLMs, and start selling to agents.</p></a>
    </div>
  </section>
  <section class="adv-section container" aria-labelledby="cats-h2">
    <div class="adv-section-head-row"><div><h2 class="adv-h1" id="cats-h2">Browse by category</h2>
    <p class="adv-section-sub">16 outcome-oriented hubs, each rendered from the same canonical catalog.</p></div>
    <a class="btn btn-ghost" href="./categories/">All categories →</a></div>
    <div class="adv-grid adv-grid-3">
''' + "\n".join(
        f'''<a class="adv-cap-card" href="./categories/{c}/">
  <h3 class="adv-card-title">{esc(CATS_DETAIL.get(c, [c])[0])}</h3>
  <p class="adv-card-desc">{esc((CATS_DETAIL.get(c, ["", ""])[1])[:160])}</p>
  <span class="adv-card-foot"><code class="adv-card-id">{esc(c)}</code></span>
</a>''' for c in CATEGORIES
    ) + f'''
    </div>
  </section>
  <section class="adv-section container" aria-labelledby="caps-h2">
    <div class="adv-section-head-row"><div><h2 class="adv-h1" id="caps-h2">Every capability</h2>
    <p class="adv-section-sub">All {n} canonical records. Green = sellable now.</p></div>
    <a class="btn btn-ghost" href="./capabilities/">Full list with search →</a></div>
    <div class="adv-grid adv-grid-3">
{cap_rows_html(sellable[:18], href_prefix="capabilities/")}
    </div>
  </section>
'''
    ld = {"@type": "CollectionPage", "@id": f"{BASE}/#collection", "url": f"{BASE}/", "name": "AgentNet capability catalog", "numberOfItems": n}
    write("index.html", page("AdValorem Agentic — agent-native capability catalog", f"{n} canonical capabilities, {len(PROVIDERS)} providers, sold over x402 on Base. One catalog for humans and AI agents.", 0, body, active="", extra_ld=ld))

# ---------------------------------------------------------------- capabilities/ index + detail
def build_capabilities_index():
    body = f'''
  <section class="adv-page-head container"><p class="adv-eyebrow">{len(CAPS)} records</p>
    <h1 class="adv-h1">Capabilities</h1>
    <p class="adv-lede">Every canonical capability on AgentNet. Green = Available Now (sellable over x402 today).</p></section>
  <section class="adv-section container"><div class="adv-grid adv-grid-3">
{cap_rows_html(CAPS, href_prefix="")}
  </div></section>
'''
    write("capabilities/index.html", page("Capabilities — AgentNet", "All canonical AgentNet capabilities with provider, availability and machine contract.", 1, body, active="capabilities"))

CAP_DESC = {c["capability_id"]: c.get("description", "") for c in CATALOG["capabilities"]}
CAP_METHOD = {c["capability_id"]: c.get("method") for c in CATALOG["capabilities"]}
CAP_ENDPOINT = {c["capability_id"]: c.get("endpoint") for c in CATALOG["capabilities"]}
CAP_STATE = {c["capability_id"]: c.get("canonical_state") for c in CATALOG["capabilities"]}
CAP_PRICE = {c["capability_id"]: c.get("price_usdc_6dec") for c in CATALOG["capabilities"]}
CAP_CTYPE = {c["capability_id"]: c.get("contract_type") for c in CATALOG["capabilities"]}

def build_capability_detail(cid, title, provider, avail, price):
    desc = CAP_DESC.get(cid, f"{cid} provided by {provider}.")
    state = CAP_STATE.get(cid, "NOT_SELLABLE")
    method = CAP_METHOD.get(cid) or "POST"
    endpoint = CAP_ENDPOINT.get(cid) or "no endpoint yet"
    pr = money(CAP_PRICE.get(cid)) or "price on wire"
    ctype = CAP_CTYPE.get(cid, "ATTEMPT")
    url = f"{BASE}/capabilities/{cid}/"
    ld = {
        "@type": "Service", "name": title, "description": desc, "serviceType": ctype,
        "provider": {"@type": "Organization", "name": provider},
        "url": url, "identifier": cid,
        "areaServed": "Worldwide",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USDC", "availability": "https://schema.org/Available"},
        "additionalProperty": [
            {"@type": "PropertyValue", "name": "availability_label", "value": avail},
            {"@type": "PropertyValue", "name": "canonical_state", "value": state},
            {"@type": "PropertyValue", "name": "endpoint", "value": endpoint},
            {"@type": "PropertyValue", "name": "method", "value": method},
            {"@type": "PropertyValue", "name": "protocol", "value": "http"},
            {"@type": "PropertyValue", "name": "payment", "value": "x402 v1 · Base eip155:8453 · USDC"},
        ],
    }
    sell_badge = "Live" if avail == SELLABLE else "Preview"
    body = f'''
  <section class="adv-page-head container">
    <p class="adv-eyebrow">capability · {esc(provider)}</p>
    <h1 class="adv-h1">{esc(title)}</h1>
    <p class="adv-lede">{esc(desc[:400])}</p>
    <p><span class="adv-badge {'adv-badge-live' if avail == SELLABLE else 'adv-badge-pilot'}">{esc(sell_badge)}</span>
    <span class="dim"> · {esc(state)}</span></p>
  </section>
  <section class="adv-section container">
    <h2>Machine contract</h2>
    <dl class="adv-dl">
      <dt>capability_id</dt><dd><code>{esc(cid)}</code></dd>
      <dt>provider</dt><dd>{esc(provider)}</dd>
      <dt>endpoint</dt><dd><code>{esc(endpoint)}</code></dd>
      <dt>method</dt><dd>{esc(method)}</dd>
      <dt>protocol</dt><dd>http / x402</dd>
      <dt>auth</dt><dd>x402 payment handshake (USDC on Base)</dd>
      <dt>price</dt><dd>{esc(pr)} USDC per call</dd>
      <dt>contract type</dt><dd>{esc(ctype)}</dd>
    </dl>
    <h2>How an agent buys this</h2>
    <ol class="adv-ol">
      <li>GET <code>{esc(url)}</code> (this page) or the catalog at <code>{BASE}/agentnet-catalog.json</code>.</li>
      <li>Send the request to the endpoint. You receive an HTTP <code>402 Payment Required</code> with an x402 payment requirement (USDC on Base, payTo treasury).</li>
      <li>Sign the payment, attach it, and resend. The facilitator settles on Base and the response returns 200 with the payload.</li>
      <li>Keep the tx hash + response as durable evidence of the purchase.</li>
    </ol>
    <p><a href="../../providers/submit/">→ Sell something like this: become a provider</a></p>
  </section>
'''
    write(f"capabilities/{cid}/index.html", page(f"{title} — AgentNet capability", esc(desc[:200]), 2, body, active="capabilities", url=url, extra_ld=ld))

# ---------------------------------------------------------------- categories
def build_categories():
    body = f'''
  <section class="adv-page-head container"><p class="adv-eyebrow">{len(CATEGORIES)} hubs</p>
    <h1 class="adv-h1">Capability categories</h1>
    <p class="adv-lede">Product areas on AgentNet, each rendered from the single canonical catalog so every card, endpoint and price matches production truth.</p></section>
  <section class="adv-section container"><div class="adv-grid adv-grid-3">
''' + "\n".join(
        f'''<a class="adv-cap-card" href="{c}/">
  <h3 class="adv-card-title">{esc(CATS_DETAIL.get(c, [c, ""])[0])}</h3>
  <p class="adv-card-desc">{esc((CATS_DETAIL.get(c, ["", ""])[1])[:180])}</p>
  <span class="adv-card-foot"><code class="adv-card-id">{esc(c)}</code></span>
</a>''' for c in CATEGORIES
    ) + '''
  </div></section>
'''
    write("categories/index.html", page("Capability categories — AgentNet", "16 capability hubs on AgentNet, each fed from the single canonical catalog.", 1, body, active="categories"))

def cat_capabilities(cat):
    # map: use the category slug -> list of capability ids that live under it
    # (approximate by reading the category page is not available offline; use
    #  the count from cats_detail and list all sellable as the pool, filtered by keyword match)
    return CAPS

def build_category_detail(c):
    name, desc, ncap = CATS_DETAIL.get(c, [c, "", 0])
    # pick capabilities by keyword relevance
    kw = c.replace("-", " ").split()
    scored = []
    for cid, title, provider, avail, price in CAPS:
        t = (cid + " " + title).lower()
        s = sum(1 for k in kw if k in t)
        if ("mev" in c or "builder" in c) and any(k in cid.lower() for k in ("mev", "liquidation", "builder", "bundle", "reth", "rbuilder")):
            s += 2
        scored.append((s, cid, title, provider, avail, price))
    scored.sort(key=lambda x: (-x[0], x[1]))
    shown = scored[:ncap or 8]
    body = f'''
  <section class="adv-page-head container"><p class="adv-eyebrow">category</p>
    <h1 class="adv-h1">{esc(name)}</h1>
    <p class="adv-lede">{esc(desc)}</p></section>
  <section class="adv-section container"><div class="adv-grid adv-grid-3">
''' + "\n".join(
        f'''<a class="adv-cap-card" href="../../capabilities/{cid}/">
  <h3 class="adv-card-title">{esc(title)}</h3>
  <p class="adv-card-meta"><span>{esc(provider)}</span><span>{esc(avail)}</span></p>
  <span class="adv-card-foot"><code>{esc(cid)}</code></span>
</a>''' for _, cid, title, provider, avail, price in shown
    ) + '''
  </div></section>
'''
    write(f"categories/{c}/index.html", page(f"{name} — category", desc[:200], 2, body, active="categories", url=f"{BASE}/categories/{c}/"))

# ---------------------------------------------------------------- providers
def build_providers_index():
    cards = []
    for p in sorted(PROVIDERS, key=lambda x: (x not in ["advalorem.mev","advalorem.builder","advalorem.reth","advalorem.arb","advalorem.polystrategy","agentnet.native"], x)):
        name, ncap = PROV_COUNTS.get(p, (p, 0))
        cards.append(f'''<a class="adv-cap-card" href="{p}/">
  <h3 class="adv-card-title">{esc(name)}</h3>
  <p class="adv-card-desc">{esc(p)} · {ncap} capabilities listed.</p>
  <span class="adv-card-foot"><code>{esc(p)}</code></span>
</a>''')
    body = f'''
  <section class="adv-page-head container"><p class="adv-eyebrow">{len(PROVIDERS)} providers</p>
    <h1 class="adv-h1">Providers</h1>
    <p class="adv-lede">Every business selling services on AgentNet over x402. Providers get paid directly on Base; we take a small commission for the privilege of using x402. Ready to list your own data or API? It takes one form and one wallet.</p></section>
  <section class="adv-section container">
    <div class="adv-section-head-row"><div><h2 class="adv-h1">Become a provider</h2>
    <p class="adv-section-sub">Submit your services, add your x402 wallet, and you are instantly searchable in the catalog, indexed for SEO/AEO and LLMs, and your customers can buy from your store page.</p></div>
    <a class="btn btn-primary btn-lg" href="submit/">Submit as a provider →</a></div>
  </section>
  <section class="adv-section container"><div class="adv-grid adv-grid-3">
''' + "\n".join(cards) + '''
  </div></section>
'''
    write("providers/index.html", page("Providers — AgentNet", "All providers selling capabilities on AgentNet over x402. List your services here.", 1, body, active="providers"))

def build_provider_detail(p):
    name, ncap = PROV_COUNTS.get(p, (p, 0))
    caps_for_p = [c for c in CAPS if c[2] and p.split(".")[-1].replace("-","_") in c[2].lower().replace(" ", "_").replace(".", "") or p == c[2]]
    # fallback: list capabilities whose provider string contains the last segment
    seg = p.split(".")[-1]
    caps_for_p = [c for c in CAPS if seg in c[2].lower()] or caps_for_p or [c for c in CAPS][:6]
    body = f'''
  <section class="adv-page-head container"><p class="adv-eyebrow">provider</p>
    <h1 class="adv-h1">{esc(name)}</h1>
    <p class="adv-lede">provider_id: <code>{esc(p)}</code>. {len(caps_for_p)} capabilities currently listed in this store, each sellable over x402 in USDC on Base.</p></section>
  <section class="adv-section container"><div class="adv-grid adv-grid-3">
''' + "\n".join(
        f'''<a class="adv-cap-card" href="../../capabilities/{cid}/">
  <h3 class="adv-card-title">{esc(title)}</h3>
  <p class="adv-card-meta"><span>{esc(avail)}</span></p>
  <span class="adv-card-foot"><code>{esc(cid)}</code></span>
</a>''' for cid, title, provider, avail, price in caps_for_p
    ) + '''
  </div></section>
  <section class="adv-section container"><p><a href="../providers/submit/">→ List your own services on AgentNet</a></p></section>
'''
    write(f"providers/{p}/index.html", page(f"{name} — provider on AgentNet", f"Provider store for {p}. {len(caps_for_p)} capabilities over x402.", 2, body, active="providers", url=f"{BASE}/providers/{p}/"))

# ---------------------------------------------------------------- provider submit
SUBMIT_PAGE = '''<!doctype html>
<html lang="en" data-domain="agentic">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Become a provider — list your services on AgentNet</title>
<meta name="description" content="One form, one wallet. List your data or API services on AgentNet, get indexed for SEO/AEO and LLMs, and sell to AI agents over x402.">
<meta property="og:site_name" content="AdValorem — AgentNet">
<meta property="og:title" content="Become a provider on AgentNet">
<meta property="og:type" content="website">
<link rel="canonical" href="https://agentic.advalorem.io/providers/submit/">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap">
<link rel="stylesheet" href="../../_shell/tokens.css">
<link rel="stylesheet" href="../../_shell/base.css">
<link rel="stylesheet" href="../../_shell/shell.css">
<link rel="stylesheet" href="../../_shell/propagation.css">
<script type="application/ld+json">
{"@context":"https://schema.org","@graph":[
 {"@type":"Organization","name":"AdValorem","url":"https://agentic.advalorem.io/"},
 {"@type":"WebPage","url":"https://agentic.advalorem.io/providers/submit/","name":"Become a provider","description":"Submit your services to be listed on AgentNet and sold over x402."}
]}
</script>
</head>
<body data-domain="agentic">
<a class="skip-link" href="#main">Skip to main content</a>
<header class="adv-nav"><div class="adv-nav-inner container"><a class="adv-brand" href="../../"><svg viewBox="0 0 32 32" width="26" height="26" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" class="logo"><path d="M7 24 L16 7 L25 24"/><path d="M11 17 H21"/></svg><span class="brand-name">AdValorem</span></a><nav class="adv-nav-links" aria-label="Section"><a href="../../capabilities/">capabilities</a><a href="../../categories/">categories</a><a href="../../providers/">providers</a><a href="../../providers/submit/" class=" active">become a provider</a><a href="../../research/">research</a></nav></div></header>
<main id="main" class="adv-main">
  <section class="adv-page-head container">
    <p class="adv-eyebrow">provider onboarding</p>
    <h1 class="adv-h1">Sell your data or API to AI agents</h1>
    <p class="adv-lede">A <strong>provider</strong> is simply a business willing to sell its services over x402. Fill in a few details and your wallet address below. When you finish, your services are automatically searchable in the AgentNet catalog, indexed for SEO/AEO and LLMs, and your customers — human or agent — can hit your store page and buy from you. You get paid directly on Base in USDC after we take a small commission for the privilege of using x402.</p>
  </section>

  <section class="adv-section container">
    <div class="adv-grid adv-grid-2">
      <div>
        <h2 class="adv-h1">How it works</h2>
        <ol class="adv-ol">
          <li><strong>You submit your service.</strong> A name, what it does, an endpoint (or "coming soon"), a starting x402 price in USDC, and your receiving wallet.</li>
          <li><strong>We add you to the catalog.</strong> Your provider page and each capability page go live at <code>agentic.advalorem.io/providers/&lt;your-slug&gt;/</code> and are indexed by our robots, sitemap, llms.txt and AEO/SEO surfaces.</li>
          <li><strong>Agents and humans find you.</strong> AI agents discover your capability through <code>llms.txt</code>, <code>agentnet-catalog.json</code> and the capability pages; humans browse by category.</li>
          <li><strong>They buy over x402.</strong> The buyer's agent sends an HTTP request, receives a 402 payment requirement, signs a USDC payment on Base, resends — and receives your data. You are paid directly; we deduct a small platform commission.</li>
        </ol>
        <p class="dim">No accounts, no API-key handoff. One wallet is the whole setup.</p>
      </div>
      <div class="adv-card">
        <h2 class="adv-h1">Submit your services</h2>
        <form id="provider-form" action="/providers/submit" method="post" class="adv-form">
          <label>Your business / provider name <input name="business_name" required placeholder="Acme Data Inc."></label>
          <label>Provider slug <input name="provider_id" required placeholder="acme-data" pattern="[a-z0-9][a-z0-9-]*" title="lowercase, numbers, dashes"></label>
          <label>Website or contact email <input name="contact" required placeholder="https://acme.com or ops@acme.com"></label>
          <div class="adv-fieldset"><legend>Service(s) to list</legend>
            <label>Capability ID <input name="capability_id" required placeholder="acme.data_snapshot"></label>
            <label>Human title <input name="title" required placeholder="Live market snapshot"></label>
            <label>What it does <textarea name="description" required rows="3" placeholder="Returns the current …"></textarea></label>
            <label>Endpoint (optional for "coming soon") <input name="endpoint" placeholder="https://api.acme.com/v1/snapshot"></label>
            <label>HTTP method <select name="method"><option>GET</option><option>POST</option></select></label>
            <label>Starting price (USDC, 6-decimal) <input name="price_usdc" type="number" step="0.000001" min="0" required placeholder="0.001000"></label>
          </div>
          <label>Your x402 receiving wallet <input name="wallet" required placeholder="0x… (USDC on Base eip155:8453)" pattern="^0x[a-fA-F0-9]{40}$"></label>
          <label class="adv-check"><input type="checkbox" name="terms" required> I agree that AgentNet may take a small commission on x402 settlements and that my services will be publicly searchable.</label>
          <button class="btn btn-primary btn-lg" type="submit">Submit my provider listing</button>
          <p class="dim">After submitting, an operator verifies the wallet and endpoint (or your "coming soon" status) and publishes your store page. You'll be added to robots.txt, sitemap.xml, llms.txt and agentnet-catalog.json automatically.</p>
        </form>
      </div>
    </div>
  </section>

  <section class="adv-section container">
    <h2 class="adv-h1">What happens after you submit</h2>
    <div class="adv-grid adv-grid-3">
      <div class="adv-card"><h3>Store page</h3><p>Your provider page goes live with your capabilities, machine contracts, and prices — the same format every existing provider has.</p></div>
      <div class="adv-card"><h3>AEO + SEO indexing</h3><p>Your pages are added to the sitemap and to our robots/AEO surfaces so AI assistants and search engines can find and recommend your services.</p></div>
      <div class="adv-card"><h3>LLM discoverability</h3><p>Your capability appears in <code>llms.txt</code> and <code>agentnet-catalog.json</code>, so agents can discover and purchase your service directly.</p></div>
    </div>
  </section>
</main>
<footer class="adv-footer"><div class="container">
<p><strong>AgentNet / AdValorem</strong> — a single agentic commerce catalog. Payments settle over x402 in USDC on Base.</p>
<p class="dim">Machine surfaces: <a href="../../llms.txt">llms.txt</a> · <a href="../../llms-full.txt">llms-full.txt</a> · <a href="../../agentnet-catalog.json">agentnet-catalog.json</a> · <a href="../../agent/">agent guide</a> · <a href="../../robots.txt">robots.txt</a> · <a href="../../sitemap.xml">sitemap</a></p>
</div></footer>
</body></html>
'''
write("providers/submit/index.html", SUBMIT_PAGE)

# ---------------------------------------------------------------- research
RESEARCH_ARTICLES = [
    {
        "slug": "what-is-x402-machine-to-machine-payments",
        "title": "What Is x402? A Guide to Machine-to-Machine Payments",
        "lede": "HTTP 402 was reserved for payment but never used. x402 finally implements it: a machine can pay another machine in a single HTTP round trip, in USDC on Base, with no accounts or keys exchanged.",
        "sections": [
            ("The origins of HTTP 402 and the birth of x402", "HTTP has had a 402 Payment Required status code since 1997, but browsers never implemented it because no standard payment flow existed. x402 defines that flow: a client receives a 402 with payment requirements, signs a small on-chain payment, and retries with the payment attached."),
            ("How the x402 payment flow works", "A facilitating agent (facilitator) sits between buyer and seller. It verifies the seller's payment request, settles the buyer's signed USDC transfer on Base, and returns the paid response. The whole handshake is two HTTP calls."),
            ("Comparing x402 to API keys, accounts, and credit cards", "x402 needs no account, no API key, and no billing relationship. The payment itself is the credential. That makes it ideal for agent-to-agent commerce where neither party wants to onboard the other."),
            ("Integrating x402 with AgentNet primitives", "Every AgentNet capability declares a machine contract and an x402 price. Agents discover capabilities in llms.txt or agentnet-catalog.json, then call the endpoint and pay inline."),
            ("Pricing the services you can pay for with x402", "Prices are per-call in USDC (6 decimal places). Typical data reads cost fractions of a cent; composed outcomes cost more. The price is declared on the capability page and in the catalog."),
            ("How this maps to AgentNet", "AgentNet is the catalog layer: canonical capability records, provider stores, category hubs, and the machine surfaces (llms.txt, catalog JSON, robots, sitemap) that let agents find and pay for work."),
        ],
        "faq": [
            ("Does the buyer need a wallet?", "Yes — the buyer (or its agent) must control a wallet holding USDC on Base. The seller gets paid directly; AgentNet deducts a small commission."),
            ("Is this live on mainnet?", "Yes. x402 v1 settles on Base (eip155:8453) in USDC via a facilitator."),
        ],
    },
    {
        "slug": "agentnet-capability-discovery",
        "title": "How AI Agents Discover and Buy Capabilities on AgentNet",
        "lede": "AgentNet is built so an autonomous agent can find a capability, verify its machine contract, and pay for it over x402 — without a human in the loop.",
        "sections": [
            ("The discovery surfaces", "Three machine-readable surfaces: llms.txt (compact), agentnet-catalog.json (full JSON), and the canonical capability HTML pages (each with JSON-LD Service schema). Any of these is enough for an agent to build a shopping list."),
            ("The machine contract", "Every capability record declares its provider, availability (sellable now vs. planned), HTTP endpoint, method, and x402 price in USDC. That is the whole contract — no hidden terms."),
            ("Paying over x402", "The agent calls the endpoint, receives a 402 payment requirement, signs the USDC payment on Base, resends, and receives the payload. The tx hash plus the response is durable proof of purchase."),
            ("Why one catalog", "A single canonical catalog means every provider, capability, price, and state agrees. Agents don't reconcile multiple sources; they read the one source of truth."),
        ],
        "faq": [
            ("Which agents can use AgentNet today?", "Any HTTP client with a Base wallet. GPT-style, Perplexity, Claude, and custom agents all work with the same x402 handshake."),
        ],
    },
]

def build_research_index():
    cards = "".join(
        f'''<a class="adv-cap-card" href="{a['slug']}/">
  <h3 class="adv-card-title">{esc(a['title'])}</h3>
  <p class="adv-card-desc">{esc(a['lede'][:200])}</p>
</a>''' for a in RESEARCH_ARTICLES
    )
    body = f'''
  <section class="adv-page-head container"><h1 class="adv-h1">Research &amp; guides</h1>
    <p class="adv-lede">Practical explainers on x402, agent-native commerce, and how AgentNet works.</p></section>
  <section class="adv-section container"><div class="adv-grid adv-grid-2">{cards}</div></section>
'''
    write("research/index.html", page("Research — AgentNet", "Guides on x402 and agent-native capability commerce.", 1, body, active="research"))

def build_research_article(a):
    body = f'''
  <section class="adv-page-head container"><p class="adv-eyebrow">research</p>
    <h1 class="adv-h1">{esc(a['title'])}</h1>
    <p class="adv-lede">{esc(a['lede'])}</p></section>
  <article class="adv-article container">
''' + "".join(f"<h2>{esc(h)}</h2>\n<p>{esc(p)}</p>\n" for h, p in a["sections"]) + '''
  <h2>Frequently asked questions</h2>
  <dl class="adv-dl">
''' + "".join(f"<dt>{esc(q)}</dt><dd>{esc(ans)}</dd>" for q, ans in a["faq"]) + '''
  </dl>
  <p class="dim">Regenerated ''' + GEN_HUMAN + f'''. For the live catalog, see <a href="../../">the AgentNet home</a>.</p>
  </article>
'''
    ld = {"@type": "Article", "headline": a["title"], "description": a["lede"],
          "datePublished": "2026-09-16", "author": {"@type": "Organization", "name": "AdValorem"}}
    write(f"research/{a['slug']}/index.html", page(a["title"], a["lede"][:200], 2, body, active="research", url=f"{BASE}/research/{a['slug']}/", extra_ld=ld))

# ---------------------------------------------------------------- agent guide
AGENT_GUIDE = '''<!doctype html>
<html lang="en" data-domain="agentic">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Agent purchasing guide — buy AgentNet capabilities over x402</title>
<meta name="description" content="Step-by-step guide for AI agents: discover an AgentNet capability, pay over x402 in USDC on Base, and verify the result.">
<link rel="canonical" href="https://agentic.advalorem.io/agent/">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap">
<link rel="stylesheet" href="../_shell/tokens.css">
<link rel="stylesheet" href="../_shell/base.css">
<link rel="stylesheet" href="../_shell/shell.css">
<link rel="stylesheet" href="../_shell/propagation.css">
</head>
<body data-domain="agentic">
<a class="skip-link" href="#main">Skip to main content</a>
<header class="adv-nav"><div class="adv-nav-inner container"><a class="adv-brand" href="../"><span class="brand-name">AdValorem</span></a><nav class="adv-nav-links" aria-label="Section"><a href="../capabilities/">capabilities</a><a href="../categories/">categories</a><a href="../providers/">providers</a><a href="../providers/submit/">become a provider</a><a href="../research/">research</a></nav></div></header>
<main id="main" class="adv-main">
  <section class="adv-page-head container"><p class="adv-eyebrow">for autonomous agents</p>
    <h1 class="adv-h1">Buying on AgentNet, end to end</h1>
    <p class="adv-lede">This page is for you if you are an HTTP agent with a Base wallet. No accounts, no API keys — just discovery, an x402 payment handshake, and a payload.</p></section>
  <section class="adv-section container">
    <h2>1 · Discover</h2>
    <ul class="adv-ul">
      <li><code>GET https://agentic.advalorem.io/llms.txt</code> — compact catalog of every capability (URL, provider, state).</li>
      <li><code>GET https://agentic.advalorem.io/agentnet-catalog.json</code> — full JSON catalog with prices and canonical states.</li>
      <li>Any capability page (e.g. <code>/capabilities/search.web/</code>) carries a JSON-LD <code>Service</code> block with the machine contract.</li>
    </ul>
    <h2>2 · Choose &amp; inspect the contract</h2>
    <p>Each record lists <code>capability_id</code>, <code>provider</code>, <code>endpoint</code>, <code>method</code>, <code>availability</code>, and <code>price</code> (USDC, 6-decimal). Only records marked <em>Available Now</em> settle over x402 today.</p>
    <h2>3 · Pay over x402</h2>
    <ol class="adv-ol">
      <li>Send the request to the endpoint (no payment yet).</li>
      <li>Receive <code>402 Payment Required</code> with an x402 payment requirement: USDC on Base (eip155:8453), the payTo treasury, and the amount in 6-decimal USDC.</li>
      <li>Sign the payment from your wallet and attach it to the retry.</li>
      <li>The facilitator settles on Base; the response returns <code>200</code> with the payload.</li>
    </ol>
    <h2>4 · Verify</h2>
    <p>Keep the Base tx hash and the response body. Together they are durable evidence of the purchase. Retrying with the same signed payment is idempotent — you will not be charged twice.</p>
  </section>
</main>
</body></html>
'''
write("agent/index.html", AGENT_GUIDE)

# ---------------------------------------------------------------- llms.txt / llms-full / robots / sitemap
def build_llms_txt():
    lines = ["# AdValorem AgentNet — capability catalog", ""]
    lines.append(f"> {len(CAPS)} canonical capabilities · {len(PROVIDERS)} providers · payments: x402 v1 · Base (eip155:8453) · USDC · payTo 0x467032Df0e31198ccAC0EF4457B08C65e74C49Db · facilitator https://facilitator.heurist.xyz")
    lines.append(f"> Regenerated {GEN_TS}. Canonical source: agentnet_marketplace.public.capabilities.")
    lines.append("")
    lines.append("## Capabilities")
    lines.append("")
    for cid, title, provider, avail, price in CAPS:
        pr = money(CAP_PRICE.get(cid))
        lines.append(f"- [{title}]({BASE}/capabilities/{cid}/): {cid} · {provider} · {avail}" + (f" · {pr} USDC" if pr else ""))
    lines.append("")
    lines.append("## Machine surfaces")
    lines.append(f"- Full catalog JSON: {BASE}/agentnet-catalog.json")
    lines.append(f"- Agent purchasing guide: {BASE}/agent/")
    lines.append(f"- Provider onboarding: {BASE}/providers/submit/")
    lines.append(f"- API: {BASE}/api/v1/capabilities")
    write("llms.txt", "\n".join(lines) + "\n")

def build_llms_full():
    out = ["# AdValorem AgentNet — full capability catalog", "", f"Regenerated {GEN_TS}."]
    out.append("")
    for cid, title, provider, avail, price in CAPS:
        out.append(f"## {title}")
        out.append(f"capability_id: {cid}")
        out.append(f"provider: {provider}")
        out.append(f"availability: {avail}")
        out.append(f"canonical_state: {CAP_STATE.get(cid,'')}")
        out.append(f"endpoint: {CAP_ENDPOINT.get(cid) or 'no endpoint yet'}")
        out.append(f"method: {CAP_METHOD.get(cid) or 'POST'}")
        pr = money(CAP_PRICE.get(cid))
        out.append(f"price: {pr or 'on wire'} USDC")
        out.append(f"url: {BASE}/capabilities/{cid}/")
        out.append(f"description: {CAP_DESC.get(cid,'')[:500]}")
        out.append("")
    write("llms-full.txt", "\n".join(out) + "\n")

def build_robots():
    robots = f'''# AgentNet / AdValorem — agent-friendly robots
# Humans and AI agents are both welcome. Machine surfaces are explicit below.

User-agent: *
Allow: /

# Explicit machine-readable surfaces (for AI agents / LLMs)
# llms.txt: compact catalog. llms-full.txt: verbose catalog.
# agentnet-catalog.json: full JSON catalog. agent/: purchasing guide.
Sitemap: {BASE}/sitemap.xml

# Machine entry points
Allow: /llms.txt
Allow: /llms-full.txt
Allow: /agentnet-catalog.json
Allow: /agent/
Allow: /api/
'''
    write("robots.txt", robots)

def build_sitemap():
    urls = [
        (f"{BASE}/", 1.0, "weekly"),
        (f"{BASE}/capabilities/", 0.9, "weekly"),
        (f"{BASE}/categories/", 0.9, "weekly"),
        (f"{BASE}/providers/", 0.9, "weekly"),
        (f"{BASE}/providers/submit/", 0.9, "monthly"),
        (f"{BASE}/research/", 0.8, "monthly"),
        (f"{BASE}/agent/", 0.8, "monthly"),
        (f"{BASE}/llms.txt", 0.6, "weekly"),
        (f"{BASE}/llms-full.txt", 0.5, "weekly"),
        (f"{BASE}/agentnet-catalog.json", 0.5, "weekly"),
    ]
    for c in CATEGORIES:
        urls.append((f"{BASE}/categories/{c}/", 0.7, "weekly"))
    for p in PROVIDERS:
        urls.append((f"{BASE}/providers/{p}/", 0.7, "weekly"))
    for cid, _, _, avail, _ in CAPS:
        urls.append((f"{BASE}/capabilities/{cid}/", 0.8 if avail == SELLABLE else 0.2, "daily" if avail == SELLABLE else "monthly"))
    for a in RESEARCH_ARTICLES:
        urls.append((f"{BASE}/research/{a['slug']}/", 0.7, "monthly"))
    body = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, prio, freq in urls:
        body.append(f"  <url><loc>{loc}</loc><priority>{prio}</priority><changefreq>{freq}</changefreq></url>")
    body.append("</urlset>")
    write("sitemap.xml", "\n".join(body) + "\n")

# ---------------------------------------------------------------- build all
build_index()
build_capabilities_index()
for cid, title, provider, avail, price in CAPS:
    build_capability_detail(cid, title, provider, avail, price)
build_categories()
for c in CATEGORIES:
    build_category_detail(c)
build_providers_index()
for p in PROVIDERS:
    build_provider_detail(p)
build_research_index()
for a in RESEARCH_ARTICLES:
    build_research_article(a)
build_llms_txt()
build_llms_full()
build_robots()
build_sitemap()

# copy catalog into .well-known
os.makedirs(os.path.join(ROOT, ".well-known"), exist_ok=True)
import shutil
shutil.copy(os.path.join(ROOT, "agentnet-catalog.json"), os.path.join(ROOT, ".well-known", "agentnet-catalog.json"))

print("site built:", os.listdir(ROOT))
