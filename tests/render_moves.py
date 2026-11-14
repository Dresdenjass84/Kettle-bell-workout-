"""Draws every move's keyframes into tests/out/moves.png for visual review."""
import os
from _common import sync_playwright, launch, page, OUT
with sync_playwright() as p:
    b=launch(p); pg,errs=page(b,viewport={'width':1400,'height':900})
    pg.evaluate('''()=>{document.body.innerHTML='<div id=g style="display:grid;grid-template-columns:repeat(7,1fr);gap:6px;padding:6px;background:#222"></div>';
      const g=document.getElementById('g');[...KB.MOVES,...KB.WARM,...KB.COOL].forEach(m=>{const d=document.createElement('div');d.style.cssText='background:#333;color:#fff;font:12px sans-serif;padding:3px';d.innerHTML='<div>'+m.id+'</div>';
        m.kf.slice(0,4).forEach(f=>{const s=document.createElementNS('http://www.w3.org/2000/svg','svg');s.setAttribute('viewBox','0 0 200 190');s.style.cssText='width:45%;background:#444;margin:1px';KB.makeFig(s,{})(f[0],m.view,m.cx);d.appendChild(s);});g.appendChild(d);});}''')
    pg.set_viewport_size({'width':1400,'height':pg.evaluate('document.body.scrollHeight')})
    path=os.path.join(OUT,'moves.png'); pg.screenshot(path=path,full_page=True); print('wrote',path)
    if errs: print('JS errors:',errs)
    b.close()
