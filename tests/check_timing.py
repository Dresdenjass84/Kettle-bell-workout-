"""Every length x focus x interval x round-rest combo must total exactly the chosen length."""
import sys
from _common import sync_playwright, launch, page
with sync_playwright() as p:
    b=launch(p); pg,errs=page(b)
    res=pg.evaluate('''()=>{const out=[];for(const mins of [10,15,20,30,45])for(const focus of ['full','legs','upper','core'])for(const [w,r] of [[30,30],[40,20],[45,15],[50,10],[20,40],[90,30],[15,5],[120,90]])for(const rr of [30,45,60,90,120]){
      const wk=KB.buildWorkout({mins,focus,work:w,rest:r,rr});const seq=KB.sequence(wk);const tot=seq.reduce((a,s)=>a+s.dur,0);
      const ids=wk.circuits.flatMap(c=>c.moves);const items=[...wk.warm,...wk.cool].map(x=>x.dur);
      out.push({mins,focus,w,r,rr,tot,c:wk.plan.c,rounds:wk.plan.r,dup:ids.length!==new Set(ids).size,empty:wk.circuits.some(c=>!c.moves.length),minItem:Math.min(...items)});}return out;}''')
    bad=[x for x in res if x['tot']!=x['mins']*60 or x['dup'] or x['empty'] or x['minItem']<10]
    print(f"{len(res)} combinations checked, {len(bad)} failing")
    for x in bad[:20]: print('  FAIL',x)
    if errs: print('JS errors:',errs)
    b.close(); sys.exit(1 if bad or errs else 0)
