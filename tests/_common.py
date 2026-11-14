import os, shutil
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL='file://'+os.path.join(ROOT,'index.html')
OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'out'); os.makedirs(OUT,exist_ok=True)
def launch(p):
    chrome=shutil.which('google-chrome') or shutil.which('chromium')
    return p.chromium.launch(executable_path=chrome,args=['--no-sandbox']) if os.environ.get('USE_SYSTEM_CHROME') and chrome else p.chromium.launch()
def page(b,**kw):
    pg=b.new_page(**kw); errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(URL); return pg,errs
