"""Every length x focus x interval x round-rest x difficulty x finisher combo must total exactly the chosen length,
before and after swapping moves. Ladders (the harder versions used in later rounds) must never repeat a
move within a workout and must keep each slot's one-sided setting."""
import sys
from _common import sync_playwright, launch, page
with sync_playwright() as p:
    b=launch(p); pg,errs=page(b)
    lad=pg.evaluate('''()=>KB.MOVES.filter(m=>m.up).filter(m=>!KB.ALL[m.up]||KB.ALL[m.up].uni!==m.uni).map(m=>m.id)''')
    calls=pg.evaluate('''()=>KB.MOVES.filter(m=>m.calls).filter(m=>m.calls[0][0]!==0||m.calls.some(c=>c[0]>=m.kf.length)).map(m=>m.id)''')
    res=pg.evaluate('''()=>{const out=[];const tot=wk=>KB.sequence(wk).reduce((a,s)=>a+s.dur,0);
     for(const fin of [true,false])for(const diff of ['std','hard','max'])for(const mins of [10,15,20,30,45])for(const focus of ['full','legs','upper','core'])for(const [w,r] of [[30,30],[40,20],[45,15],[50,10],[20,40],[90,30],[15,5],[120,90]])for(const rr of [30,45,60,90,120]){
      const wk=KB.buildWorkout({mins,focus,work:w,rest:r,rr,diff,fin});const t0=tot(wk);const nfin=KB.sequence(wk).filter(s=>s.k==='fin').length;
      const all=wk.circuits.flatMap(c=>c.ladders.flatMap(l=>[...new Set(l)]));
      const uniBad=wk.circuits.some(c=>c.ladders.some(l=>l.some(id=>KB.ALL[id].uni!==KB.ALL[l[0]].uni)||l.length!==c.rounds));
      const climbs=wk.circuits.reduce((a,c)=>a+c.ladders.filter(l=>new Set(l).size>1).length,0);
      const items=[...wk.warm,...wk.cool].map(x=>x.dur);
      const warmcool=items.reduce((a,b)=>a+b,0);
      wk.circuits.forEach((c,ci)=>c.moves.forEach((_,i)=>KB.swapMove(wk,ci,i)));
      const all2=wk.circuits.flatMap(c=>c.ladders.flatMap(l=>[...new Set(l)]));
      out.push({fin,nfin,finBad:fin&&mins>10?nfin<4:nfin>0,finDup:!!wk.fin&&wk.circuits.some(c=>c.ladders.flat().includes(wk.fin.id))&&KB.MOVES.some(m=>(focus==='full'||m.areas.includes(focus))&&!m.calls&&!m.uni&&!wk.circuits.some(c=>c.ladders.flat().includes(m.id))),diff,mins,focus,w,r,rr,tot:t0,tot2:tot(wk),c:wk.plan.c,rounds:wk.plan.r,dup:all.length!==new Set(all).size,dup2:all2.length!==new Set(all2).size,uniBad,climbs,
        stdClimb:diff==='std'&&climbs>0,empty:wk.circuits.some(c=>!c.moves.length),minItem:Math.min(...items),warmcool});}return out;}''')
    bad=[x for x in res if x['tot']!=x['mins']*60 or x['finBad'] or x['finDup'] or x['tot2']!=x['mins']*60 or x['dup'] or x['dup2'] or x['uniBad'] or x['stdClimb'] or x['empty'] or x['minItem']<10]
    print(f"{len(res)} combinations checked, {len(bad)} failing")
    for x in bad[:20]: print('  FAIL',x)
    for d in ['std','hard','max']:
        rows=[x for x in res if x['diff']==d and x['w'] in (30,40,45,50) and x['fin']]
        print(f"  {d}: preset workouts {len(rows)}, average slots that climb {sum(x['climbs'] for x in rows)/len(rows):.1f}, worst warm-up+cool-down share {max(x['warmcool']/(x['mins']*60) for x in rows):.0%}")
    if lad: print('ladders that change the one-sided setting:',lad)
    if calls: print('complexes with bad call indexes:',calls)
    if errs: print('JS errors:',errs)
    b.close(); sys.exit(1 if bad or errs or lad or calls else 0)
