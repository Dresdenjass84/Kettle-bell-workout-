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
    pg.click('#t-kg16'); assert pg.evaluate('KB.settings.kg16')
    pg.click('text=30 min'); pg.click('text=Legs'); pg.click('#b-build'); shot('2_preview')
    kg_shown=pg.locator('#pv-body small', has_text='16 kg').count()
    pg.click('.swap >> nth=0'); pg.click('#b-start'); pg.wait_for_timeout(800); shot('3_ready')
    wait_kind(pg,'work'); shot('4_work')
    wait_kind(pg,'rest'); shot('5_rest')
    pg.evaluate('KB.setSpeed(400)'); pg.wait_for_selector('#v-done:not(.hide)',timeout=90000); shot('6_done')
    fin_seen=pg.evaluate("KB.PL.seq.filter(s=>s.k==='fin').length")
    before=pg.evaluate("({d:KB.settings.diff,p:KB.settings.preset,rr:KB.settings.rr})")
    pg.click('#d-rate-btns >> text=Too easy'); pg.wait_for_timeout(200); shot('6b_rated')
    msg=pg.inner_text('#d-rate-msg'); after=pg.evaluate("({d:KB.settings.diff,p:KB.settings.preset,rr:KB.settings.rr})")
    pg.click('#d-undo'); undone=pg.evaluate("({d:KB.settings.diff,p:KB.settings.preset,rr:KB.settings.rr})")
    pg.click('#d-rate-btns >> text=About right')
    rated=pg.evaluate("JSON.parse(localStorage.getItem('kb_history'))[0].rating")
    rate_ok=fin_seen>=4 and after!=before and undone==before and rated=='right' and msg.startswith('Next time')
    print('finisher intervals:',fin_seen,'| too easy ->',msg.replace('Undo','').strip(),'| undo restores:',undone==before,'| saved rating:',rated,'|','ok' if rate_ok else 'FAIL')
    pg.click('#b-done'); pg.wait_for_timeout(300); shot('7_history')
    n=pg.evaluate("JSON.parse(localStorage.getItem('kb_history')||'[]').length")
    pg.click('nav >> text=Moves'); pg.click('#m-list .mrow >> nth=4'); pg.wait_for_timeout(500); shot('8_move')
    # --- complexes: Brutal workout, step chips on screen, voice in both modes
    pg.evaluate("""()=>{window.SPOKEN=[];const U=window.SpeechSynthesisUtterance;window.speechSynthesis.speak=u=>SPOKEN.push(u.text);}""")
    pg.click('#sheet-close'); pg.click('nav >> text=Workout'); pg.click('text=20 min'); pg.click('text=Full body'); pg.click('text=Brutal'); pg.click('text=Move by move'); shot('9_setup_brutal')
    pg.click('#b-build')
    has=lambda:pg.evaluate("(()=>{const q=KB.sequence(WK).filter(s=>s.k==='work'&&KB.ALL[s.id].calls);return new Set(q.map(s=>s.id)).size>=2&&q.some(s=>s.round===1)})()")
    for _ in range(40):
        if has(): break
        pg.click('#b-reshuffle')
    shot('10_preview_brutal')
    def to_complex():
        pg.evaluate('KB.setSpeed(40)')
        for _ in range(2000):
            if pg.evaluate("(()=>{const it=KB.PL.seq[KB.PL.i];return it.k==='work'&&!!KB.ALL[it.id].calls&&KB.PL.left>it.dur-8})()"): break
            pg.wait_for_timeout(20)
        pg.evaluate('KB.setSpeed(1);SPOKEN.length=0'); pg.wait_for_timeout(7000)
        m=pg.evaluate("KB.ALL[KB.PL.seq[KB.PL.i].id]"); words=[c[1] for c in m['calls']]
        return m['name'],words,pg.evaluate('SPOKEN.slice()'),pg.locator('#p-cues .steps span.on').count()
    pg.click('#b-start'); pg.wait_for_timeout(500)
    name1,words1,spoken1,on1=to_complex(); shot('11_complex')
    pg.evaluate("KB.settings.cxVoice='once'"); pg.click('#b-next'); pg.click('#b-next')
    name2,words2,spoken2,on2=to_complex()
    step_ok=len([t for t in spoken1 if t in words1])>=2 and on1==1
    once_ok=not [t for t in spoken2 if t in words2] and on2==1
    print('complex, move by move:',name1,'| spoken:',spoken1,'|','ok' if step_ok else 'FAIL')
    print('complex, name once:',name2,'| spoken:',spoken2,'|','ok' if once_ok else 'FAIL')
    print('16 kg labels in legs preview:',kg_shown,'|','ok' if kg_shown>0 else 'FAIL')
    print('history entries:',n,'| JS errors:',errs or 'none','| screenshots in',OUT)
    b.close(); sys.exit(1 if errs or n<1 or not step_ok or not once_ok or not rate_ok or kg_shown==0 else 0)
