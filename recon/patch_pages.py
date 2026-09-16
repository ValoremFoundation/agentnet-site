import json, re, sys, os

DEMOTE = {
 "mev.accuracy_archive","mev.daily_report","mev.opportunity_feed",
 "mev.builder_recommendation","mev.liquidation_waves","mev.searcher_leaderboard",
 "builder.bundle_submission","builder.private_orderflow",
}

def patch(path, cid):
    h = open(path, encoding="utf-8").read()
    orig = h
    # JSON-LD canonical_state
    h = h.replace('"name": "canonical_state", "value": "GREEN"',
                  '"name": "canonical_state", "value": "NOT_SELLABLE"')
    # JSON-LD availability_label
    h = h.replace('"name": "availability_label", "value": "Available Now"',
                  '"name": "availability_label", "value": "Planned"')
    # schema.org availability
    h = h.replace('"availability": "https://schema.org/Available"',
                  '"availability": "https://schema.org/Discontinued"')
    # visible badge
    h = h.replace('<span class="dim"> · GREEN</span>',
                  '<span class="dim"> · NOT-SELLABLE</span>')
    if h == orig:
        return False
    open(path,"w",encoding="utf-8").write(h)
    return True

base = sys.argv[1]
n=0
for cid in DEMOTE:
    p=os.path.join(base,"capabilities",cid,"index.html")
    if os.path.exists(p) and patch(p,cid):
        n+=1
print(f"patched {n}/{len(DEMOTE)} demoted capability pages")
