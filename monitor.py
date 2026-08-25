#!/usr/bin/env python3
import json
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
import urllib.parse, urllib.request

API="https://backoffice.aarhus-posterlist.kommuneplatformen.dk/api/PosterListe/GetAllPosts"
DEPTS={"MBA-":"Borgmesterens Afdeling","MTM-":"Teknik og Miljø"}
DAYS=10
TZ=ZoneInfo("Europe/Copenhagen")
DATA=Path(__file__).resolve().parent/"data"
SEEN=DATA/"seen.json"
LATEST=DATA/"latest.json"
ALL=DATA/"all-current.json"

def fetch(url):
    req=urllib.request.Request(url,headers={
        "User-Agent":"Mozilla/5.0 (compatible; AarhusPostlisteMonitor/1.0)",
        "Accept":"application/json,text/plain,*/*",
        "Referer":"https://aarhus.dk/"
    })
    with urllib.request.urlopen(req,timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))

def key(x):
    if x.get("id") is not None: return f"id:{x['id']}"
    if x.get("dokumentnr"): return f"dokumentnr:{x['dokumentnr']}"
    return "ident:"+x.get("dokumentidentifikation","")

def main():
    DATA.mkdir(exist_ok=True)
    now=datetime.now(TZ); today=now.date()
    seen=json.loads(SEEN.read_text(encoding="utf-8")) if SEEN.exists() else {}
    rows=[]; errors=[]; checked=[]

    for i in range(DAYS):
        d=(today-timedelta(days=i)).isoformat()
        for dept,name in DEPTS.items():
            q=urllib.parse.urlencode({"department":dept,"datetime":d,"type":"indgaende-dokument"})
            url=f"{API}?{q}"
            try:
                items=fetch(url)
                if not isinstance(items,list): raise ValueError("Svar er ikke en liste")
                checked.append({"department":dept,"department_name":name,"date":d,"count":len(items)})
                for x in items:
                    x["_department"]=dept; x["_department_name"]=name; x["_queried_date"]=d
                    rows.append(x)
            except Exception as e:
                errors.append({"department":dept,"date":d,"error":repr(e),"url":url})

    uniq={key(x):x for x in rows}
    current=list(uniq.values())
    new=[]
    for x in current:
        k=key(x)
        fp={a:x.get(a) for a in ("dokumenttitel","journalDate","sagsnr","ansvarligEnhed")}
        old=seen.get(k)
        if old is None:
            x["_status"]="new"; new.append(x)
        elif old.get("fingerprint")!=fp:
            x["_status"]="changed"; new.append(x)
        seen[k]={
            "first_seen": old.get("first_seen") if old else now.isoformat(),
            "last_seen": now.isoformat(),
            "fingerprint": fp
        }

    latest={
        "generated_at":now.isoformat(),
        "timezone":"Europe/Copenhagen",
        "window_days":DAYS,
        "window_start":(today-timedelta(days=DAYS-1)).isoformat(),
        "window_end":today.isoformat(),
        "departments":{
            dept:{
                "name":name,
                "fetched_unique_posts_in_window":sum(1 for x in current if x.get("_department")==dept),
                "new_or_changed_posts":sum(1 for x in new if x.get("_department")==dept)
            } for dept,name in DEPTS.items()
        },
        "checked_dates":checked,
        "new_or_changed":sorted(new,key=lambda x:x.get("journalDate") or "",reverse=True),
        "errors":errors,
        "technical_status":"ok" if not errors else ("partial" if current else "failed")
    }

    LATEST.write_text(json.dumps(latest,ensure_ascii=False,indent=2),encoding="utf-8")
    ALL.write_text(json.dumps(current,ensure_ascii=False,indent=2),encoding="utf-8")
    SEEN.write_text(json.dumps(seen,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"technical_status":latest["technical_status"],"new_or_changed":len(new),"errors":len(errors)},ensure_ascii=False))
    if latest["technical_status"]=="failed": raise SystemExit(2)

if __name__=="__main__": main()
