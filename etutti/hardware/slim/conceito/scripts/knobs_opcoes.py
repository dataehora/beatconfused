S=8.0  # px per mm
W,H=1500,1060
o=[]
def R(x,y,w,h,f,s='#333',sw=1,extra=''):o.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{f}" stroke="{s}" stroke-width="{sw}" {extra}/>')
def T(x,y,t,sz=13,a='middle',w='normal',c='#222'):o.append(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{sz}" text-anchor="{a}" font-weight="{w}" fill="{c}" font-family="Helvetica,Arial">{t}</text>')
def L(x1,y1,x2,y2,c='#999',sw=1,d=''):o.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{c}" stroke-width="{sw}" {"stroke-dasharray=\""+d+"\"" if d else ""}/>')
o.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><rect width="{W}" height="{H}" fill="#fbfaf6"/>')
T(W/2,32,'eTutti Slim · knobs: opções para decisão (corte vertical no eixo do knob, mm a partir do fundo da base)',19,w='bold')
T(W/2,54,'placa principal com topo em z 5,0 (proposta do Code; se a placa subir Δ para caber conectores/JST, as opções A e B sobem Δ)  ·  medidas marcadas * a conferir no datasheet/STEP',12,c='#555')
cols=[('A','Componente comum, eixo CORTADO','knob baixo sobre a porca'),('B','Componente comum, eixo INTEIRO','knob alto, sem cortar nada'),('C','Knob MAGNÉTICO, sem eixo','sensor de ângulo na placa, knob gira no tampo')]
rows=[('Registros — fileira 1 (tampo z 14,0)',14.0,18.55,'botão fil. 1: 18,55'),('Volume — fileira 4 (tampo z 21,0)',21.0,25.55,'botão fil. 4: 25,55')]
PW,PH=470,460; X0=30; Y0=80
ZB=5.0
for r,(rt,ls,bt,btl) in enumerate(rows):
  for c,(cid,ct,cs) in enumerate(cols):
    px=X0+c*(PW+10); py=Y0+r*(PH+20)
    R(px,py,PW,PH,'#fff','#ccc')
    T(px+10,py+20,f'{cid}{r+1} · {ct}',14,a='start',w='bold')
    T(px+10,py+38,rt+' · '+cs,11.5,a='start',c='#555')
    zmax=34; gy=py+PH-22
    Z=lambda z: gy-z*S*1.0
    cx=px+PW/2-30
    # grid
    for z in range(0,36,5):
      L(px+40,Z(z),px+PW-100,Z(z),'#eee'); T(px+34,Z(z)+4,str(z),10,a='end',c='#888')
    # floor
    R(px+45,Z(1.6),PW-150,1.6*S,'#d9d4c7','#888')
    # main board
    R(px+60,Z(ZB),PW-190,1.2*S,'#3c7d4a','#244')
    # lid
    th=2.85; lx0=px+45; lx1=px+PW-105
    pit = (cid=='C')
    if pit:
      hw=8.8
      R(lx0,Z(ls),(cx-hw*S)-lx0,th*S,'#e8e2d2','#777')
      R(cx+hw*S,Z(ls),lx1-(cx+hw*S),th*S,'#e8e2d2','#777')
      R(cx-hw*S,Z(ls-1.2),2*hw*S,(th-1.2)*S,'#e8e2d2','#777')
    else:
      hole=4.7 if cid!='C' else 0
      R(lx0,Z(ls),(cx-hole*S)-lx0,th*S,'#e8e2d2','#777')
      R(cx+hole*S,Z(ls),lx1-(cx+hole*S),th*S,'#e8e2d2','#777')
    # button-top ref
    L(px+45,Z(bt),px+PW-100,Z(bt),'#c0392b',1.2,'5,4'); T(px+PW-98,Z(bt)+4,btl,10.5,a='start',c='#c0392b')
    T(px+PW-98,Z(ls)+4,f'tampo {ls:.1f}'.replace('.',','),10.5,a='start',c='#777')
    info=[]
    if cid in 'AB':
      if r==0: body=7.5; bush=5.0; name='Alps SRBV170701 (L15)'
      else: body=10.0; bush=5.0; name='pot 9 mm c/ chave*'
      zt=ZB+1.2; bt0=zt+body
      R(cx-4.0*S,Z(bt0),8*S,body*S,'#5a6c86','#223')
      R(cx-4.5*S,Z(bt0+bush),9*S,bush*S,'#b9b9b9','#555')
      # pocket from below if body enters lid
      if bt0>ls-th: 
        R(cx-5*S,Z(bt0+0.3),10*S,(bt0+0.3-(ls-th))*S,'#fbfaf6','#777','0.8','stroke-dasharray="3,2"')
      nut0=max(ls,bt0+bush-2.0)
      R(cx-5.5*S,Z(ls+2.0),11*S,2.0*S,'#cfcfcf','#555')  # nut on lid
      sh0=bt0+bush
      tip = (sh0+6.0) if cid=='A' else (bt0+15.0)
      R(cx-3*S,Z(tip),6*S,(tip-sh0)*S,'#d0d0d0','#555')
      ktop=tip+1.5
      kb=ls+0.3
      o.append(f'<path d="M{cx-8*S:.1f},{Z(kb):.1f} L{cx-8*S:.1f},{Z(ktop-1):.1f} Q{cx-8*S:.1f},{Z(ktop):.1f} {cx-7*S:.1f},{Z(ktop):.1f} L{cx+7*S:.1f},{Z(ktop):.1f} Q{cx+8*S:.1f},{Z(ktop):.1f} {cx+8*S:.1f},{Z(ktop-1):.1f} L{cx+8*S:.1f},{Z(kb):.1f} Z" fill="#2b2b2b" fill-opacity="0.82" stroke="#111"/>')
      info=[name, f'topo do knob z {ktop:.1f}  ({ktop-ls:+.1f} sobre o tampo)', f'{ktop-bt:+.1f} mm em relação ao botão da fileira', 'eixo cortado a 6 mm da bucha' if cid=='A' else 'eixo de fábrica, nada cortado', 'peça de furo, soldada em casa; bucha M9 + porca no tampo']
      if r==1: info[4]='pot 9 mm com chave rotativa: sem peça vertical em estoque*'
    else:
      # sensor on board top
      R(cx-2*S,Z(ZB+1.2+0.9),4*S,0.9*S,'#222','#000')
      kb=ls-1.2+0.2; ktop=kb+5.8
      # stem with magnet
      stem_bot=ZB+1.2+0.9+3.0
      R(cx-3.2*S,Z(kb),6.4*S,(kb-stem_bot)*S,'#444','#111')
      R(cx-3*S,Z(stem_bot+2.0),6*S,2.0*S,'#b03a2e','#600')
      o.append(f'<path d="M{cx-8.2*S:.1f},{Z(kb):.1f} L{cx-8.2*S:.1f},{Z(ktop-1):.1f} Q{cx-8.2*S:.1f},{Z(ktop):.1f} {cx-7.2*S:.1f},{Z(ktop):.1f} L{cx+7.2*S:.1f},{Z(ktop):.1f} Q{cx+8.2*S:.1f},{Z(ktop):.1f} {cx+8.2*S:.1f},{Z(ktop-1):.1f} L{cx+8.2*S:.1f},{Z(kb):.1f} Z" fill="#2b2b2b" fill-opacity="0.82" stroke="#111"/>')
      gap=stem_bot-(ZB+1.2+0.9)
      info=['ímã diametral Ø6×2* na ponta da haste do knob', f'topo do knob z {ktop:.1f}  ({ktop-ls:+.1f} sobre o tampo, no poço)', f'{ktop-bt:+.1f} mm em relação ao botão da fileira', f'sensor de ângulo no topo da placa; folga ímã→sensor ≈ {gap:.1f} mm*', 'retenção por clique na haste; detentes moldados no poço']
      if r==1: info[4]='OFF = 2º ímã + chave Hall de µA (DRV5032*) → SYSOFF'
    for i,t in enumerate(info): T(px+12,py+58+i*15,t,11,a='start',c='#333' if i else '#000',w='bold' if i==1 else 'normal')
# legend
ly=Y0+2*(PH+20)+2
items=[('#5a6c86','corpo da chave/pot'),('#b9b9b9','bucha M9*'),('#cfcfcf','porca'),('#d0d0d0','eixo'),('#2b2b2b','knob'),('#b03a2e','ímã'),('#3c7d4a','placa principal'),('#e8e2d2','tampo')]
for i,(f,t) in enumerate(items):
  R(40+i*180,ly,14,14,f); T(60+i*180,ly+12,t,12,a='start')
o.append('</svg>')
open('knobs_opcoes.svg','w').write('\n'.join(o))
