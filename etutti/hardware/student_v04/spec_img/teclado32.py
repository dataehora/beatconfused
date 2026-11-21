import json, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch
d=json.load(open('/home/claude/beatconfused/etutti/hardware/student_v04/pcb/posicao_v4.json'))
N=['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
def nm(m): return f"{N[m%12]}{m//12-1}"
P=18.5
# row: (y centre, régua start x, first midi)
rows={1:(74.03,89.2,57),2:(58.01,79.95,55),3:(41.99,89.2,56),4:(25.97,79.95,54)}
old={1:7,2:8,3:7,4:6}
newkeys={(1,7),(3,7),(4,0),(4,7)}
fig,ax=plt.subplots(figsize=(15,6.6))
ax.add_patch(Rectangle((0,0),252,100,fc='#F1EFE8',ec='#444441',lw=1.5))
x0,y0,x1,y1=d['contorno']
ax.add_patch(FancyBboxPatch((x0,y0),x1-x0,y1-y0,boxstyle='round,pad=0,rounding_size=3',fc='#EAF3DE',ec='#3B6D11',lw=1))
ax.text(40,50,'placa principal\n(interface)',ha='center',va='center',fontsize=9,color='#27500A')
for r,(yc,xs,m0) in rows.items():
    for k in range(2):
        rx=xs+k*74.4
        ax.add_patch(Rectangle((rx,yc-7),74,14,fc='#9FE1CB',ec='#0F6E56',lw=.8))
        for i in range(4):
            idx=k*4+i; cx=rx+9.25+18.5*i; note=m0+3*idx
            nova=(r,idx) in newkeys
            ax.add_patch(Circle((cx,yc),7.0,fc='#FAC775' if nova else 'white',ec='#2C2C2A',lw=.8))
            ax.text(cx,yc,nm(note),ha='center',va='center',fontsize=8.5,weight='bold' if N[note%12] in('C','F') else 'normal')
    ax.text(xs+150,yc,f'fileira {r}\n{nm(m0)}–{nm(m0+21)}',ha='left',va='center',fontsize=7.5)
    # cabo placa -> 1a régua
    ax.plot([77.5,xs+3],[yc-4.5,yc-4.5],color='#D4537E',lw=2)
    # elo entre réguas
    ax.plot([xs+74-4,xs+74.4+4],[yc-4.5,yc-4.5],color='#534AB7',lw=3)
ax.plot([],[],color='#D4537E',lw=2,label='cabo placa → 1ª régua (4, ~25 mm)')
ax.plot([],[],color='#534AB7',lw=3,label='elo régua → régua na mesma fileira (4, mesma altura)')
ax.add_patch(Rectangle((0,0),0,0,fc='#FAC775',ec='k',label='teclas novas (4)'))
ax.legend(loc='lower center',bbox_to_anchor=(0.5,-0.2),ncol=3,fontsize=8,frameon=False)
ax.set_xlim(-2,262); ax.set_ylim(103,-3); ax.set_aspect('equal')
ax.set_title('Student V4 — teclado de 32 teclas (8 réguas cheias), vista de cima, jogador embaixo. Proposta do J, 21 nov',fontsize=10.5)
ax.set_xlabel('x (mm)'); ax.set_ylabel('y (mm)')
fig.tight_layout(); fig.savefig('/home/claude/planta/teclado_32.png',dpi=150)
