"""Phone-sized end-to-end run: setup, preview, swap, play (fast-forwarded), summary, history, moves."""
import os, sys
from _common import sync_playwright, launch, page, OUT
def wait_kind(pg,kind,speed=60):
    pg.evaluate(f'KB.setSpeed({speed})')
    for _ in range(400):
        if pg.evaluate('KB.PL.seq[KB.PL.i].k')==kind: break
        pg.wait_for_timeout(50)
    pg.evaluate('KB.setSpeed(1)'); pg.wait_for_timeout(500)
with sync_playwright() as p:
    b=launch(p); pg,errs=page(b,viewport={'width':390,'height':844},device_scale_factor=2)
    shot=lambda n:pg.screenshot(path=os.path.join(OUT,n+'.png'))
    shot('1_setup')
    pg.click('text=30 min'); pg.click('text=Legs'); pg.click('#b-build'); shot('2_preview')
    pg.click('.swap >> nth=0'); pg.click('#b-start'); pg.wait_for_timeout(800); shot('3_ready')
    wait_kind(pg,'work'); shot('4_work')
    wait_kind(pg,'rest'); shot('5_rest')
    pg.evaluate('KB.setSpeed(400)'); pg.wait_for_selector('#v-done:not(.hide)',timeout=90000); shot('6_done')
    pg.click('#b-done'); pg.wait_for_timeout(300); shot('7_history')
    n=pg.evaluate("JSON.parse(localStorage.getItem('kb_history')||'[]').length")
    pg.click('nav >> text=Moves'); pg.click('#m-list .mrow >> nth=4'); pg.wait_for_timeout(500); shot('8_move')
    print('history entries:',n,'| JS errors:',errs or 'none','| screenshots in',OUT)
    b.close(); sys.exit(1 if errs or n<1 else 0)
