from __future__ import annotations
import os,re,sys,shutil,termios,tty
from datetime import datetime
from .core import APP_NAME, AUTHOR

ESC="\033["; RESET=ESC+"0m"; BOLD=ESC+"1m"; DIM=ESC+"2m"
CYAN=ESC+"38;5;51m"; BLUE=ESC+"38;5;39m"; GREEN=ESC+"38;5;46m"
YELLOW=ESC+"38;5;220m"; RED=ESC+"38;5;196m"; PURPLE=ESC+"38;5;141m"
WHITE=ESC+"38;5;255m"; BG_SEL=ESC+"48;5;24m"; FG_SEL=ESC+"38;5;231m"
ANSI_RE=re.compile(r"\x1b\[[0-9;]*m")

def vlen(s): return len(ANSI_RE.sub("",str(s)))
def clip(s,width):
    s=str(s); raw=ANSI_RE.sub("",s)
    if len(raw)<=width: return s
    return raw[:max(0,width-1)]+("…" if width else "")
def pad(s,width,align="left"):
    s=clip(s,width); n=max(0,width-vlen(s))
    if align=="right": return " "*n+s
    if align=="center":
        l=n//2; return " "*l+s+" "*(n-l)
    return s+" "*n

class Screen:
    MIN_W=100; MAX_W=132
    def __init__(self):
        cols,rows=shutil.get_terminal_size((120,40))
        # Never render wider than the actual terminal. 100+ columns gets the full layout;
        # smaller terminals keep the frame aligned and rely on clipping instead of wrapping.
        self.width=max(60,min(cols,self.MAX_W)); self.inner=self.width-2; self.rows=rows
    def clear(self): sys.stdout.write("\033[2J\033[H"); sys.stdout.flush()
    def top(self): print(CYAN+"╔"+"═"*self.inner+"╗"+RESET)
    def bottom(self): print(CYAN+"╚"+"═"*self.inner+"╝"+RESET)
    def divider(self): print(CYAN+"╠"+"═"*self.inner+"╣"+RESET)
    def line(self,text=""):
        # Every line is padded to the same visible width before the right border.
        print(CYAN+"║"+RESET+pad(text,self.inner)+CYAN+"║"+RESET)
    def header(self,subtitle=""):
        self.top(); clock=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        title=" ◆ "+APP_NAME; gap=max(1,self.inner-vlen(title)-len(clock))
        self.line(BOLD+CYAN+title+RESET+" "*gap+DIM+clock+RESET)
        if subtitle:self.line("   "+DIM+subtitle+RESET)
        self.divider()
    def section(self,title):
        title=f" {title} "; rest=max(0,self.inner-len(title)-3)
        # Nested box is exactly self.inner characters wide, so both outer right borders
        # always land in the same terminal column.
        print(CYAN+"║┌─"+title+"─"*rest+"┐║"+RESET)
    def section_row(self,text=""):
        print(CYAN+"║│"+RESET+pad(text,self.inner-2)+CYAN+"│║"+RESET)
    def section_end(self): print(CYAN+"║└"+"─"*(self.inner-2)+"┘║"+RESET)
    def footer(self,status_text="● READY"):
        self.divider()
        left="  ↑/↓ Navigate   ENTER Select   ESC Back   F1 Help   F5 Refresh"
        self.line(left+" "*max(1,self.inner-vlen(left)-len(status_text)-2)+GREEN+status_text+RESET)
        self.line("  "+DIM+AUTHOR+RESET); self.bottom()

def status(text):
    t=str(text).upper()
    if t in {"ONLINE","RUNNING","SUCCESS","PASSED","ACTIVE","READY","OK"}: return GREEN+"● "+t+RESET
    if t in {"FAILED","OFFLINE","ERROR","STOPPED"}: return RED+"● "+t+RESET
    if t in {"WARNING","DEGRADED","WAITING"}: return YELLOW+"● "+t+RESET
    return BLUE+"● "+t+RESET

def table_row(values,widths,aligns=None):
    aligns=aligns or ["left"]*len(values)
    return "  "+"  ".join(pad(v,w,a) for v,w,a in zip(values,widths,aligns))

def read_key():
    if not sys.stdin.isatty(): return input().strip()
    fd=sys.stdin.fileno(); old=termios.tcgetattr(fd)
    try:
        tty.setraw(fd); ch=os.read(fd,1)
        if ch==b"\x1b":
            rest=os.read(fd,2)
            if rest==b"[A":return "UP"
            if rest==b"[B":return "DOWN"
            return "ESC"
        if ch in (b"\r",b"\n"):return "ENTER"
        if ch==b"\x03":raise KeyboardInterrupt
        return ch.decode(errors="ignore")
    finally: termios.tcsetattr(fd,termios.TCSADRAIN,old)

def menu(items,title="MAIN MENU",selected=0,subtitle="",dashboard_lines=None):
    s=Screen()
    while True:
        s.clear(); s.header(subtitle)
        if dashboard_lines:
            s.section("CONNECTED HYPERVISORS")
            for ln in dashboard_lines:s.section_row(ln)
            s.section_end(); s.line()
        s.section(title)
        for i,item in enumerate(items):
            label=f"  {'▶' if i==selected else ' '}  {item}"
            if i==selected: label=BG_SEL+FG_SEL+BOLD+pad(label,s.inner-2)+RESET
            s.section_row(label)
        s.section_end(); s.footer()
        key=read_key()
        if key=="UP":selected=(selected-1)%len(items)
        elif key=="DOWN":selected=(selected+1)%len(items)
        elif key=="ENTER":return selected
        elif key in ("ESC","q","Q"):return None
