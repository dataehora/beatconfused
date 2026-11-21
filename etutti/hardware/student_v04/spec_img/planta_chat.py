import json, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch
d=json.load(open('/home/claude/beatconfused/etutti/hardware/student_v04/pcb/posicao_v4.json'))
P=d['pecas']
blocos={
 'USB':(['J201','U201','D201'],'#378ADD'),
 'MicroMod (M.2)':(['J101','TP101','C101','C102'],'#7F77DD'),
 'Energia e carga':(['U202','U204','L201','Q203','D202','D203','D205','J202','D206'],'#D85A30'),
 'Áudio':(['U301','U302','J301','J302','U501','J501','FB301'],'#1D9E75'),
 'Interface':(['SW401','SW402','SW403','J401'],'#BA7517'),
 'Fileiras':(['J601','J602','J603','J604'],'#D4537E'),
}
nomes={'J201':'USB-C','J301':'OUT','J302':'IN','J202':'bateria','J401':'tela','J501':'alto-falante',
 'SW401':'knob vol.','SW402':'knob reg.','SW403':'botão','U301':'codec','U501':'amp','U202':'carregador',
 'U204':'conversor','J101':'M.2','J601':'fil. 1','J602':'fil. 2','J603':'fil. 3','J604':'fil. 4'}
def draw_board(ax, labels=True):
    x0,y0,x1,y1=d['contorno']
    ax.add_patch(FancyBboxPatch((x0,y0),x1-x0,y1-y0,boxstyle='round,pad=0,rounding_size=3',fc='#EAF3DE',ec='#3B6D11',lw=1.2))
    cz=d['zonas']['cartao']
    ax.add_patch(Rectangle((cz[0],cz[1]),cz[2]-cz[0],cz[3]-cz[1],fc='#CECBF6',ec='#534AB7',lw=.8,alpha=.6))
    if labels: ax.text((cz[0]+cz[2])/2,(cz[1]+cz[3])/2,'cartão\nMicroMod',ha='center',va='center',fontsize=7,color='#3C3489')
    for b,(refs,c) in blocos.items():
        for r in refs:
            if r not in P: continue
            a,b_,cc,dd=P[r]['patio']
            ax.add_patch(Rectangle((a,b_),cc-a,dd-b_,fc=c,ec=c,alpha=.55 if P[r]['lado']=='B' else .9,lw=.6))
            if labels and r in nomes: ax.text((a+cc)/2,(b_+dd)/2,nomes[r],ha='center',va='center',fontsize=6.5,color='black')
    for h in ['H1','H2','H3','H4','H101']:
        p=P[h]; ax.add_patch(Circle((p['x'],p['y']),1.1 if h!='H101' else 1.35,fc='white',ec='black',lw=.8))
        if labels: ax.text(p['x']+1.8,p['y'],h,fontsize=6,va='center')
    for r in ['SW401','SW402']:
        p=P[r]; ax.add_patch(Circle((p['x'],p['y']),5,fc='none',ec='#633806',lw=1,ls='--'))
    fz=d['metricas']['fenda_do_cabo']; ax.add_patch(Rectangle((fz[0],fz[1]),fz[2]-fz[0],fz[3]-fz[1],fc='white',ec='black',lw=.6,hatch='////'))
    if labels:
        ax.add_patch(Rectangle((25,15.5),24,13,fc='none',ec='black',lw=.8,ls=':'))
        ax.text(37,14.5,'janela da tela (provisória)',ha='center',fontsize=6)
# Figura 1: instrumento inteiro
fig,ax=plt.subplots(figsize=(13,6))
ax.add_patch(Rectangle((0,0),252,100,fc='#F1EFE8',ec='#444441',lw=1.5))
draw_board(ax,labels=False)
rows={1:(74.03,89.2,7),2:(58.01,79.95,8),3:(41.99,89.2,7),4:(25.97,98.45,6)}
for r,(yc,xs,n) in rows.items():
    for k in range(2):
        rx=xs+k*74.4
        ax.add_patch(Rectangle((rx,yc-7),74,14,fc='#9FE1CB',ec='#0F6E56',lw=.8))
        for i in range(4):
            idx=k*4+i; cx=rx+9.25+18.5*i
            if idx<n: ax.add_patch(Circle((cx,yc),7.0,fc='white',ec='#2C2C2A',lw=.8))
            else: ax.add_patch(Circle((cx,yc),7.0,fc='none',ec='#888780',lw=.6,ls=':'))
    ax.text(xs-1.5,yc,f'fileira {r}',ha='right',va='center',fontsize=7.5)
    # cabo
    mx=d['metricas']['mouth_x_fileiras'][str(r)]
    ax.plot([mx,xs],[yc,yc],color='#D4537E',lw=1.4)
ax.add_patch(Rectangle((19.5,56),50,34,fc='none',ec='#D85A30',lw=1,ls='--')); ax.text(44.5,88,'bateria 503450 (posição da V3, a confirmar)',ha='center',fontsize=6.5,color='#712B13')
ax.add_patch(Circle((37,73.1),14,fc='none',ec='#1D9E75',lw=1,ls='--')); ax.text(37,73.1,'alto-falante Ø28\n(V3, a confirmar)',ha='center',va='center',fontsize=6.5,color='#085041')
ax.text(40,50.5,'placa principal\n75 × 95 mm',ha='center',fontsize=8,color='#27500A')
ax.annotate('USB-C (y 10)',xy=(0,10),xytext=(-14,4),fontsize=7,arrowprops=dict(arrowstyle='->'),annotation_clip=False)
ax.annotate('OUT / IN',xy=(0,48),xytext=(-14,48),fontsize=7,arrowprops=dict(arrowstyle='->'),annotation_clip=False)
ax.set_xlim(-16,256); ax.set_ylim(103,-3); ax.set_aspect('equal')
ax.set_title('Student V4 (R3V4) — planta geral, vista de cima, 28 teclas (jogador embaixo)',fontsize=11)
ax.set_xlabel('x (mm)'); ax.set_ylabel('y (mm) → jogador')
fig.tight_layout(); fig.savefig('/home/claude/planta/planta_geral.png',dpi=150)
# Figura 2: placa
fig,ax=plt.subplots(figsize=(8,9.5))
draw_board(ax)
for b,(refs,c) in blocos.items(): ax.plot([],[],'s',color=c,alpha=.7,label=b)
ax.legend(loc='lower left',fontsize=7,bbox_to_anchor=(0,-.16),ncol=3,frameon=False)
ax.set_xlim(0,80); ax.set_ylim(100,0); ax.set_aspect('equal')
ax.set_title('Placa principal V4 (R3V4) — blocos e posições, vista de cima\n(cor clara = peça no fundo; forte = no topo; círculos tracejados = knobs)',fontsize=9)
fig.tight_layout(); fig.savefig('/home/claude/planta/placa_blocos.png',dpi=150)
