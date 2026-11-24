import sys,math
sys.path.insert(0,'/home/claude/slim/gen')
from geo import P,D,RB,OFFS,INK,BLUE,rr_outline,keys
from board import T,R,Cc,BOT,TOP,PCB,svg,keys_faint
FRONT=-18.5; BACK=70.6; RIGHT=149
OUTLINE=[(-58,-16.5),(-34,-16.5),(-34,69),(-89,69),(-89,55),(-58,55)]
PARTS=[
 ('USB-C 16p mid-mount (parede de trás, centro x=-66)',-70.5,61,-61.5,70.8,TOP),
 ('P2 3,5 mm OUT (parede esquerda, centro y=59,5)',-91,56.5,-78,62.5,TOP),
 ('RT1062 BGA196',-54,26,-42,38,BOT),
 ('Flash 64 Mbit',-51,17,-45,22,BOT),
 ('MKL02',-43,17.5,-40,20.5,BOT),
 ('24 MHz',-57.1,20.75,-53.9,23.25,BOT),
 ('32k',-53,12.4,-51,13.6,BOT),
 ('L DCDC',-45.5,21.5,-42.5,24.5,BOT),
 ('BQ24075',-56.5,58,-53.5,61,BOT),
 ('LDO 3V3',-56.5,63,-53.5,66,BOT),
 ('ESD USB',-64.5,56,-61.5,59,BOT),
 ('PTC',-60.6,56.4,-58.4,58.0,BOT),
 ('Conector bateria',-76.5,55.3,-67.5,58.3,BOT),
 ('SGTL5000',-78.5,63,-75.5,66,BOT),
 ('Lógica SYSOFF',-52,65,-50,67,BOT),
 ('PROG (interno)',-57,10.5,-53,13.5,BOT),
 ('LED do knob',-54.3,47.6,-52.7,48.4,BOT),
]
FFCY=[0,D,2*D,3*D]
def board(detail=False):
    s=['<polygon points="'+' '.join(f'{x:.2f},{-y:.2f}' for x,y in OUTLINE)+f'" fill="{PCB}" stroke="#2F6B3A" stroke-width="0.45" stroke-linejoin="round"/>']
    # BGA escape zone + corridors
    s.append(R(-56.5,23.5,-39.5,40.5,'none',stroke='#7C3AED',sw=0.3,extra='stroke-dasharray="1 0.7"'))
    def arrow(x0,y0,x1,y1,lab,anc='middle',dx=0,dy=0):
        return (f'<line x1="{x0}" y1="{-y0}" x2="{x1}" y2="{-y1}" stroke="#7C3AED" stroke-width="0.9" stroke-opacity="0.35" stroke-linecap="round"/>'
                )
    s.append(arrow(-42,32,-38,32,'',''))
    s.append(arrow(-48,26,-48,22.5,'',''))
    s.append(arrow(-54,36,-66,60,'',''))
    s.append(arrow(-54,28,-56,23.5,'',''))
    for nm,x0,y0,x1,y1,col in PARTS: s.append(R(x0,y0,x1,y1,col,sw=0.2))
    for y in FFCY: s.append(R(-39.5,y-4,-35,y+4,BOT,sw=0.2))
    for (kx,ky),nm in (((-46,0),'REGISTROS'),((-46,3*D),'VOL + LIGA')):
        s.append(R(kx-6,ky-6.5,kx+6,ky+6.5,TOP,sw=0.25,extra='opacity="0.85"')); s.append(Cc(kx,ky,3.5,'none',sw=0.25))
        if not detail: s.append(T(kx,ky-9.5,nm,2.2,INK,'middle','700'))
    for hx,hy in ((-87,67),(-56,-14.5),(-36,-14.5)): s.append(Cc(hx,hy,1.1,'#fff',sw=0.3))
    if detail:
        for n,(nm,x0,y0,x1,y1,col) in enumerate(PARTS,1):
            cx=(x0+x1)/2; cy=(y0+y1)/2
            s.append(Cc(cx,cy,1.2,'#fff',sw=0.2)); s.append(T(cx,cy-0.5,str(n),1.4,INK,'middle','700'))
        for i,y in enumerate(FFCY): s.append(T(-35,y-5.6,f'R{i+1}',1.6,'#9C7A0F','end','700'))
    return s
def battery():
    s=[R(-88.5,-15,-59.5,54.5,'none',stroke=BLUE,sw=0.35,rx=2,extra='stroke-dasharray="2 1.2"')]
    s.append(R(-88,-14.5,-60,54,'#C9D6E8',stroke=INK,sw=0.3,rx=1.5))
    s.append(f'<text x="-74" y="-20" font-family="IBM Plex Sans, Arial" font-size="2.4" font-weight="700" fill="{INK}" text-anchor="middle" transform="rotate(-90 -74 -20)">LiPo 1000 mAh · 4,5 × 28 × 68 mm · NTC</text>')
    s.append(f'<path d="M-66,-54 L-66,-55.5" stroke="#B91C1C" stroke-width="0.6"/>')
    return s
def rulers():
    s=[]
    for r in range(4):
        off=OFFS[r]; y=r*D; x0=off-21.5; x1=off+7*P+9
        s.append(R(x0,y-7.5,x1,y+7.5,PCB,stroke='#2F6B3A',sw=0.35,rx=1))
        for c in range(8): s.append(R(off+c*P-1.5,y-1.5,off+c*P+1.5,y+1.5,BOT,sw=0.15))
        s.append(R(off-19,y-4,off-14.5,y+4,BOT,sw=0.2)); s.append(R(off-13,y-3.2,off-8.6,y+3.2,BOT,sw=0.2))
        s.append(T(x1-1,y-6,f'R{r+1}',2.4,'#2F6B3A','end','700'))
        xr=off-16.75
        s.append(R(-37.25,y-2.8,xr,y+2.8,'#F4C542',stroke='#9C7A0F',sw=0.2,extra='opacity="0.8"'))
    return s
o=rr_outline(-90,FRONT,RIGHT,BACK,6)
body=['<polygon points="'+' '.join(f'{x:.2f},{-y:.2f}' for x,y in o)+f'" fill="#F7F3EA" stroke="{INK}" stroke-width="0.5"/>']
body+=rulers()+board()+battery()+keys_faint()
body.append(T(-87,FRONT-4.5,'Bateria à esquerda, na frente · USB‑C na parede de trás (x −66) · OUT na parede esquerda (y 59,5) · 239 × 89 mm',2.5,BLUE,'start','600'))
svg('P1e_layout.svg',-96,RIGHT+5,FRONT-8,BACK+5,body,3.0)
svg('MB5_detail.svg',-93,-31,-19,72,board(detail=True),6.5)
print('ok')
