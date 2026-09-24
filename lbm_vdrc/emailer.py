from __future__ import annotations
import smtplib,ssl
from email.message import EmailMessage
from .core import PATHS,load_json
from .secrets import SecretStore

def send(subject,body):
    settings=load_json(PATHS["settings"],{});mail=settings.get("email",{})
    if not mail.get("enabled"):return False
    sec=SecretStore().get(mail.get("credential",""));msg=EmailMessage();msg["Subject"]=subject;msg["From"]=mail["from"];msg["To"]=mail["to"];msg.set_content(body)
    host=mail["host"];port=int(mail.get("port",587));mode=mail.get("security","starttls").lower()
    if mode in ("ssl","tls"):
        with smtplib.SMTP_SSL(host,port,context=ssl.create_default_context(),timeout=30) as s:
            if sec.get("username"):s.login(sec["username"],sec.get("password",""))
            s.send_message(msg)
    else:
        with smtplib.SMTP(host,port,timeout=30) as s:
            s.ehlo()
            if mode=="starttls":s.starttls(context=ssl.create_default_context());s.ehlo()
            if sec.get("username"):s.login(sec["username"],sec.get("password",""))
            s.send_message(msg)
    return True
