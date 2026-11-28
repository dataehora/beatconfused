import math
S=16.0
W,H=1700,860
o=[]
def R(x,y,w,h,f,s='#333',sw=1,ex=''):o.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{f}" stroke="{s}" stroke-width="{sw}" {ex}/>')
def T(x,y,t,sz=13,a='middle',w='normal',c='#222'):o.append(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{sz}" text-anchor="{a}" font-weight="{w}" fill="{c}" font-family="Helvetica,Arial">{t}</text>')
def L(x1,y1,x2,y2,c='#999',sw=1,d=''):o.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{c}" stroke-width="{sw}" {"stroke-dasharray=\""+d+"\"" if d else ""}/>')
def P(d,f,s='#222',sw=1):o.append(f'<path d="{d}" fill="{f}" stroke="{s}" stroke-width="{sw}"/>')
o.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><rect width="{W}" height="{H}" fill="#fbfaf6"/>')
T(W/2,32,'eTutti Slim · botão estilo acordeon (proposta do Chat para decisão) · corte pelo eixo, fileira 1 · mm (z a partir do fundo do case)',18,w='bold')
T(W/2,54,'switch KS‑33D medida no STEP da Gateron · tampo na fileira 1: superfície 14,0, espessura 2,85 · inclinação 7,1° · a mesma peça serve as 4 fileiras (tudo sobe junto com o degrau)',12,c='#555')
# geometry row1
CT=10.85; SEAT=5.0; STEM_REST=CT+3.5; TRAV=3.5
LID_S=14.0; LID_T=2.85; SLOPE=math.tan(math.radians(7.1))
HOLE=11.0; SHANK=10.0; HEAD_D=15.0; HEAD_H=7.5; DOME=1.0; G=2.0
RIM=LID_S+SLOPE*HOLE/2
UND_REST=RIM+G+TRAV
def panel(px,label,press):
    zoff=-TRAV if press else 0
    zero=780; X0=px+300
    Z=lambda z: zero-(z-2)*S*1.55
    K=S*1.55
    xs=lambda x: X0+x*K
    T(px+300,90,label,16,w='bold')
    # grade + ruler
    R(xs(-9),Z(SEAT),18*K,1.2*K,'#3c7d4a','#244')
    R(xs(-9),Z(SEAT+2.5),18*K,1.2*K,'#c9b98f','#776')  # grade
    # switch housing
    R(xs(-7),Z(CT),14*K,(CT-SEAT-1.2)*K,'#e9e9e9','#666')
    # switch stem (moves)
    st=STEM_REST+zoff
    R(xs(-4.7),Z(st),9.4*K,(st-CT+0.8)*K,'#d8d0e8','#665')
    R(xs(-2.83),Z(st),5.67*K,3.3*K,'#fbfaf6','#665')  # pocket
    R(xs(-0.55),Z(st),1.1*K,3.3*K,'#d8d0e8','#665')    # male cross (section)
    # lid with sloped surface: left= front (lower)
    def lidpoly(x0,x1):
        z0s=LID_S+SLOPE*x0; z1s=LID_S+SLOPE*x1
        return f'M{xs(x0)},{Z(z0s-LID_T)} L{xs(x0)},{Z(z0s)} L{xs(x1)},{Z(z1s)} L{xs(x1)},{Z(z1s-LID_T)} Z'
    P(lidpoly(-11,-HOLE/2),'#ede4cf','#776'); P(lidpoly(HOLE/2,11),'#ede4cf','#776')
    # button
    und=UND_REST+zoff
    # pin
    R(xs(-2.7),Z(st+0.0)-0,5.4*K,0.001,'none','none')
    pin_top=st; pin_bot=st-3.0
    P(f'M{xs(-2.7)},{Z(pin_top)} L{xs(-2.7)},{Z(pin_bot)} L{xs(2.7)},{Z(pin_bot)} L{xs(2.7)},{Z(pin_top)} Z','#f6f1e4','#222')
    R(xs(-0.52),Z(pin_top),1.04*K,3.0*K,'#fbfaf6','#c0392b',0.8)
    # shank
    P(f'M{xs(-SHANK/2)},{Z(und)} L{xs(-SHANK/2)},{Z(st)} L{xs(SHANK/2)},{Z(st)} L{xs(SHANK/2)},{Z(und)} Z','#f6f1e4','#222')
    # head with dome
    r=HEAD_D/2; top=und+HEAD_H
    P(f'M{xs(-r)},{Z(und)} L{xs(-r)},{Z(top-DOME-0.8)} Q{xs(-r)},{Z(top-DOME)} {xs(-r+0.9)},{Z(top-DOME)} Q{xs(0)},{Z(top+DOME*0.95)} {xs(r-0.9)},{Z(top-DOME)} Q{xs(r)},{Z(top-DOME)} {xs(r)},{Z(top-DOME-0.8)} L{xs(r)},{Z(und)} Z','#f6f1e4','#222',1.3)
    # dims
    def dim(z,t,c='#1f5fa8',x=11.5):
        L(xs(x-1),Z(z),xs(x+4.5),Z(z),c,0.8,'4,3'); T(xs(x+4.7),Z(z)+4,t,11.5,a='start',c=c)
    dim(top,f'topo {top:.2f}'.replace('.',','))
    dim(und,f'base da cabeça {und:.2f}'.replace('.',','))
    dim(RIM,f'borda alta do furo {RIM:.2f}'.replace('.',','),'#8a6d1f')
    dim(st,f'topo da haste da switch {st:.2f}'.replace('.',','),'#6a4e9a')
    dim(CT,f'topo da switch {CT:.2f}'.replace('.',','),'#666')
    if press:
        L(xs(-9),Z(und),xs(-9),Z(RIM),'#c0392b',1.4); T(xs(-9.3),Z((und+RIM)/2)+4,f'{und-RIM:.1f} livre'.replace('.',','),12,a='end',w='bold',c='#c0392b')
    else:
        L(xs(-9),Z(und),xs(-9),Z(und-TRAV),'#555',1); T(xs(-9.3),Z(und-TRAV/2)+4,'curso 3,5',11,a='end',c='#555')
    T(xs(-10.5),Z(LID_S-SLOPE*10)+18,'frente',10,a='start',c='#777'); T(xs(10.5),Z(LID_S+SLOPE*10)+18,'trás',10,a='end',c='#777')
panel(20,'em repouso',False)
panel(850,'apertado (fim do curso)',True)
o.append('</svg>')
open('botao_acordeon.svg','w').write('\n'.join(o))
print('und rest',UND_REST,'top',UND_REST+HEAD_H,'rim',RIM, 'shank len', UND_REST-STEM_REST)
