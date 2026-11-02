#!/usr/bin/env python3
"""Company announcements and news only. No holdings, quantities, costs or valuations."""
import json
import ssl
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from urllib.request import Request, urlopen
from urllib.parse import quote_plus

from pathlib import Path
HERE = Path(__file__).resolve().parent
IST = timezone(timedelta(hours=5, minutes=30))

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
CTX = ssl.create_default_context()

def get(url, timeout=25, accept="application/json, text/plain, */*"):
    req = Request(url, headers={
        "User-Agent": UA,
        "Accept": accept,
        "Accept-Language": "en-IN,en;q=0.9",
    })
    with urlopen(req, timeout=timeout, context=CTX) as r:
        return r.read().decode("utf-8", "replace")

def get_json(url, **kw):
    return json.loads(get(url, **kw))

# ---------------------------------------------------------------- NSE announcements
def nse_announcements(symbol, limit=15):
    url = ("https://www.nseindia.com/api/corporate-announcements"
           "?index=equities&symbol=" + quote_plus(symbol))
    try:
        rows = get_json(url)
    except Exception as e:
        print(f"  [warn] NSE announcements failed for {symbol}: {e}")
        raise
    out = []
    for a in rows[:limit]:
        out.append({
            "date": a.get("an_dt", ""),
            "category": a.get("desc", "Announcement"),
            "subject": a.get("attchmntText", "").strip(),
            "attachment": a.get("attchmntFile", ""),
        })
    return out

# ---------------------------------------------------------------- Google News RSS
def google_news(query, limit=6):
    url = ("https://news.google.com/rss/search?q=" + quote_plus(query)
           + "&hl=en-IN&gl=IN&ceid=IN:en")
    try:
        xml_text = get(url, accept="application/rss+xml, application/xml, */*")
    except Exception as e:
        print(f"  [warn] Google News failed for '{query}': {e}")
        raise
    items = []
    try:
        root = ET.fromstring(xml_text)
        for it in root.iter("item"):
            if len(items) >= limit:
                break
            pub = it.findtext("pubDate") or ""
            iso = ""
            try:
                dt = datetime.strptime(pub, "%a, %d %b %Y %H:%M:%S %Z") \
                       .replace(tzinfo=timezone.utc).astimezone(IST)
                iso = dt.isoformat()
            except ValueError:
                pass
            items.append({
                "title": it.findtext("title") or "",
                "link": it.findtext("link") or "",
                "source": (it.findtext("source") or "").strip(),
                "date": iso,
            })
    except ET.ParseError as e:
        print(f"  [warn] RSS parse failed for '{query}': {e}")
    return items

# ---------------------------------------------------------------- SEBI circulars
def sebi_feed(limit=15):
    try:
        xml_text = get("https://www.sebi.gov.in/sebirss.xml",
                       accept="application/rss+xml, application/xml, */*")
        root = ET.fromstring(xml_text)
        items = []
        for it in root.iter("item"):
            if len(items) >= limit:
                break
            pub = it.findtext("pubDate") or ""
            iso = ""
            try:
                dt = datetime.strptime(pub, "%a, %d %b %Y %H:%M:%S %z")
                iso = dt.astimezone(IST).isoformat()
            except ValueError:
                pass
            items.append({
                "title": it.findtext("title") or "",
                "link": it.findtext("link") or "",
                "source": "SEBI",
                "date": iso,
            })
        return items
    except Exception as e:
        print(f"  [warn] SEBI feed failed: {e}")
        raise


from concurrent.futures import ThreadPoolExecutor
from email.utils import parsedate_to_datetime
import re

def safe_url(value):
    from urllib.parse import urlsplit
    if not isinstance(value,str): return ''
    try:
        p=urlsplit(value)
        return value if p.scheme=='https' and p.hostname and not p.username and not p.password else ''
    except ValueError: return ''

def clean_items(rows,kind):
    result=[];seen=set()
    if not isinstance(rows,list): raise ValueError('Feed response is not a list')
    for r in rows:
        if not isinstance(r,dict): continue
        if kind=='announcements':
            item={k:str(r.get(k,'') or '')[:2000] for k in ('date','category','subject')}
            item['attachment']=safe_url(r.get('attachment',''))
            try:item['date']=datetime.strptime(item['date'],'%d-%b-%Y %H:%M:%S').replace(tzinfo=IST).isoformat()
            except ValueError:pass
            if not item['subject'] and not item['category']: continue
            key=(item['date'],item['subject'],item['attachment'])
        else:
            item={k:str(r.get(k,'') or '')[:2000] for k in ('title','source','date')}
            item['link']=safe_url(r.get('link',''))
            if not item['title'] or not item['link']:continue
            key=(item['title'],item['link'])
        if key not in seen: seen.add(key);result.append(item)
    return result[:30]

def fetch_section(fn,previous,kind,now):
    try:
        items=clean_items(fn(),kind)
        return {'status':'ok','checkedAt':now,'lastSuccessAt':now,'items':items,'error':None}
    except Exception as e:
        return {'status':'stale' if previous and previous.get('lastSuccessAt') else 'unavailable',
                'checkedAt':now,'lastSuccessAt':(previous or {}).get('lastSuccessAt'),
                'items':clean_items((previous or {}).get('items',[]),kind),'error':type(e).__name__}

def filter_company_news(name,rows):
    token=name.split()[0].casefold()
    finance=r'\b(stock|shares?|results?|earnings|profit|revenue|orders?|dividend|guidance|margin|NSE|BSE|investment|investors?|debt|board|quarter|Q[1-4]|governance|acquisition|business|capex|buyback|pledge|forecast|estimates?|target|rating|buy|sell|hold|penalty|regulat)'
    cutoff=datetime.now(IST)-timedelta(days=14)
    out=[]
    for r in rows:
        title=r['title'].casefold()
        if not re.search(r'\b'+re.escape(token)+r'\b',title):continue
        if not re.search(finance,title,re.IGNORECASE):continue
        if name=='INOX India' and 'pvr' in title:continue
        try:
            if datetime.fromisoformat(r['date'])<cutoff:continue
        except (ValueError,KeyError,TypeError):continue
        out.append(r)
    return sorted(out,key=lambda r:r['date'],reverse=True)[:6]

def company_news(name):
    rows=google_news('"'+name+'" (results OR earnings OR announcement) when:14d',limit=12)
    return filter_company_news(name,rows)

def validate_watchlist(cfg):
    if set(cfg)-{'companies','policy_queries'}:raise ValueError('Only company metadata and policy queries are accepted')
    seen=set()
    for c in cfg['companies']:
        if set(c)-{'symbol','name','isin','yahoo','sector'}:raise ValueError('Unexpected company field')
        if not re.fullmatch(r'[A-Z0-9&_-]{1,25}',c['symbol']) or c['symbol'] in seen:raise ValueError('Invalid/duplicate symbol')
        if not c['name'].strip():raise ValueError('Name required')
        seen.add(c['symbol'])
    if not seen:raise ValueError('Empty company list')
    return cfg

def main():
    cfg=validate_watchlist(json.loads((HERE/'watchlist.json').read_text()))
    path=HERE/'research.json'
    old=json.loads(path.read_text()) if path.exists() else {}
    old_companies={c['symbol']:c for c in old.get('companies',[])}
    now=datetime.now(IST).isoformat(timespec='seconds')
    def one(c):
        previous=old_companies.get(c['symbol'],{})
        ann=fetch_section(lambda:nse_announcements(c['symbol']),previous.get('announcements'),'announcements',now)
        news=fetch_section(lambda:company_news(c['name']),previous.get('news'),'news',now)
        print(c['symbol']+': filings='+ann['status']+', news='+news['status'])
        return {**c,'announcements':ann,'news':news}
    with ThreadPoolExecutor(max_workers=4) as pool: companies=list(pool.map(one,cfg['companies']))
    def policy_news():
        return [n for q in cfg['policy_queries'] for n in google_news(q+' when:14d',limit=4)]
    policy=fetch_section(policy_news,old.get('policy'),'news',now)
    sebi=fetch_section(sebi_feed,old.get('sebi'),'news',now)
    successes=sum(s['status']=='ok' for c in companies for s in (c['announcements'],c['news']))
    if successes==0:raise SystemExit('No company source succeeded; prior saved research was left unchanged.')
    payload={'schemaVersion':1,'updated':now,'companies':companies,'policy':policy,'sebi':sebi,
             'coverage':{'successful':successes,'total':2*len(companies)}}
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(payload,ensure_ascii=False,indent=2));tmp.replace(path)
    print(f'Saved research: {successes}/{2*len(companies)} company source checks successful. Failures are explicitly flagged.')
if __name__=='__main__':main()
