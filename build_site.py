import json
from pathlib import Path
R=Path(__file__).resolve().parent

def build():
    from fetch_updates import validate_watchlist
    cfg=validate_watchlist(json.loads((R/'watchlist.json').read_text()))
    data=json.loads((R/'research.json').read_text())
    # Strict schema: the published payload never accepts arbitrary portfolio fields.
    assert set(data)=={'schemaVersion','updated','companies','policy','sebi','coverage'}
    from fetch_updates import clean_items
    def section(x,kind):
        return {k:x.get(k) for k in ('status','checkedAt','lastSuccessAt','error')}|{'items':clean_items(x.get('items',[]),kind)}
    allowed={c['symbol']:c for c in cfg['companies']}
    companies=[]
    for c in data['companies']:
        if c['symbol'] not in allowed:continue
        companies.append(allowed[c['symbol']]|{'announcements':section(c['announcements'],'announcements'),'news':section(c['news'],'news')})
    clean={'updated':data['updated'],'companies':companies,'policy':section(data['policy'],'news'),'sebi':section(data['sebi'],'news'),'coverage':data['coverage']}
    blob=json.dumps(clean,ensure_ascii=False).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    html=(R/'template.html').read_text().replace('/*__CSS__*/',(R/'style.css').read_text()).replace('/*__DATA__*/',blob).replace('/*__APP__*/',(R/'app.js').read_text())
    (R/'site.html').write_text(html)
    print('Bundled company research with strict field allowlists.')
if __name__=='__main__':build()
