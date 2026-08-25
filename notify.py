#!/usr/bin/env python3
import json, os, smtplib, html
from email.message import EmailMessage
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

TZ=ZoneInfo("Europe/Copenhagen")
LATEST=Path(__file__).resolve().parent/"data"/"latest.json"

RED=[
("økonomi/penge",["sparekatalog","udgift","budget","fondsmidler","erstatning","million","mio.","økonomi"]),
("klage/juridisk konflikt",["klage","planklagenævn","advokat","erstatningskrav","retssag","påbud"]),
("større projekt/byudvikling",["lokalplan","vvm","motorvejshotel","marselistunnel","kystsikring","brandstation","parkeringskælder"]),
("trafik/infrastruktur",["letbane","tunnel","motorvej","trafik","parkering"]),
("miljø/sundhed",["asbest","pcb","forurening","støj","flagermus","overfladevand"]),
("aktindsigt",["aktindsigt"])
]
YELLOW=[
("borgerhenvendelse",["borgerhenvendelse","henvendelse","åbent brev","meningstilkendegivelse"]),
("uklar status/korrespondance",["status","opfølgning","dialog","spørgsmål","materiale fra bygherre","bemærkninger"]),
("plan/projekt",["servitut","byggemodning","bygherre","rådgiver","lokalplanudkast"])
]
WHITE=["invitation","udstillingsåbning","jubilæum","reception","besøg hos"]

def classify(item):
    title=(item.get("dokumenttitel") or "").lower()
    score=0; reasons=[]
    for label, words in RED:
        if any(w in title for w in words):
            score+=3; reasons.append(label)
    for label, words in YELLOW:
        if any(w in title for w in words):
            score+=1; reasons.append(label)
    if len(title.strip())<22:
        score=max(score,1); reasons.append("uklar/kryptisk titel")
    if any(w in title for w in WHITE) and score<3:
        score=0
    if score>=3: return "red", ", ".join(dict.fromkeys(reasons))
    if score>=1: return "yellow", ", ".join(dict.fromkeys(reasons))
    return "white", "ingen tydelig nyhedsværdi ud fra titlen alene"

def fmt(s):
    if not s: return ""
    try: return datetime.fromisoformat(s).astimezone(TZ).strftime("%d.%m.%Y %H:%M")
    except: return s

def next_step(item, cat):
    t=(item.get("dokumenttitel") or "").lower()
    s=item.get("sagsnr") or ""
    if "aktindsigt" in t: return f"Find ud af hvem der søger aktindsigt, og hvilke dokumenter/svar kommunen udleverer i {s}."
    if "planklagenævn" in t or "klage" in t: return f"Hent afgørelsen/klagen og se, om den ændrer eller forsinker sagen {s}."
    if "lokalplan" in t or "vvm" in t or "bygherre" in t: return f"Slå {s} op og identificér projekt, bygherre, omfang og konfliktpunkter."
    if cat=="yellow": return f"Bed om aktindsigt i dokumentet/sagen {s} for at afklare emnet."
    return ""

def section(title, items, cat):
    if not items: return ""
    parts=[f"<h2>{html.escape(title)}</h2>"]
    for item, reason in items:
        parts.append(f"<p><strong>{html.escape(item.get('dokumenttitel') or '(uden titel)')}</strong><br>")
        parts.append(f"Enhed: {html.escape(item.get('ansvarligEnhed') or '')}<br>")
        parts.append(f"Sagsnr.: {html.escape(item.get('sagsnr') or '')}<br>")
        parts.append(f"Journaliseret: {html.escape(fmt(item.get('journalDate')))}<br>")
        parts.append(f"<em>Hvorfor:</em> {html.escape(reason)}")
        step=next_step(item,cat)
        if step: parts.append(f"<br><em>Næste skridt:</em> {html.escape(step)}")
        parts.append("</p>")
    return "".join(parts)

data=json.loads(LATEST.read_text(encoding="utf-8"))
new=data.get("new_or_changed",[])
red=[]; yellow=[]; white=[]
for item in new:
    cat,reason=classify(item)
    (red if cat=="red" else yellow if cat=="yellow" else white).append((item,reason))

deps=data.get("departments",{})
mba=deps.get("MBA-",{}); mtm=deps.get("MTM-",{})
subject=f"Aarhus postlister: {len(red)} røde, {len(yellow)} gule, {len(white)} øvrige"

body=["<html><body><h1>Aarhus postliste-briefing</h1>"]
body.append(f"<p>Kørsel: {html.escape(fmt(data.get('generated_at')))}<br>")
body.append(f"Vindue: {data.get('window_start','')} – {data.get('window_end','')}<br>")
body.append(f"MBA: {mba.get('fetched_unique_posts_in_window',0)} poster, {mba.get('new_or_changed_posts',0)} nye/ændrede<br>")
body.append(f"MTM: {mtm.get('fetched_unique_posts_in_window',0)} poster, {mtm.get('new_or_changed_posts',0)} nye/ændrede</p>")

if not new:
    body.append("<p><strong>Ingen nye eller ændrede poster siden sidste kørsel.</strong></p>")
else:
    body.append(section("🔴 Bør undersøges",red,"red"))
    body.append(section("🟡 Kan være interessant",yellow,"yellow"))
    body.append(section("⚪ Øvrige nye poster",white,"white"))
body.append("<hr><p><small>Automatisk prioritering ud fra titler og metadata. Ingen poster skjules.</small></p></body></html>")

msg=EmailMessage()
msg["Subject"]=subject
msg["From"]=os.environ.get("MAIL_FROM",os.environ["SMTP_USER"])
msg["To"]=os.environ["MAIL_TO"]
msg.set_content("Se HTML-versionen af denne mail.")
msg.add_alternative("".join(body),subtype="html")

with smtplib.SMTP(os.environ["SMTP_HOST"],int(os.environ.get("SMTP_PORT","587")),timeout=30) as smtp:
    smtp.starttls()
    smtp.login(os.environ["SMTP_USER"],os.environ["SMTP_PASSWORD"])
    smtp.send_message(msg)
print("Mail sendt")
