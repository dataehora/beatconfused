"""Etapa 3: Freerouting 2.5.0 (linha de comando) sobre a placa com o par USB e o fan-out (etapas 1 e 2).
Idempotente: parte de uma placa base (padrao: a roteada depois da etapa 2; ou BASE=caminho, p. ex. uma placa em que so as redes ruins foram
arrancadas) e grava build/fr_<tag>.kicad_pcb; a roteada so muda na etapa 6.
Uso: python etapa3_fr.py [tag] [passes]   env: BASE (placa base), CORR_W (largura da classe Corrente no DSN, mm), FRW (largura padrao, mm).
Tudo o que ja existe na base e fixo para o Freerouting (travado). O ImportSpecctraSES apaga o que o pcbnew exportou como fixo: lib.reaplica devolve."""
import re, shutil, sys
from lib import *
import pcbnew

NL = chr(10)

def _bloco(t, k):
    d = 0; m = k
    while True:
        if t[m] == '(': d += 1
        elif t[m] == ')':
            d -= 1
            if d == 0: return t[k:m+1], m + 1
        m += 1

def filtra_redes(t, manter):
    """Deixa no (network) so as redes de `manter` (as outras viram obstaculo sem ligacao a fazer): roteamento por estagios."""
    i = t.index('(network'); k = i + len('(network'); filhos = []
    while True:
        while t[k].isspace(): k += 1
        if t[k] == ')': k += 1; break
        bl, k = _bloco(t, k); filhos.append(bl)
    keep = []
    for bl in filhos:
        if bl.startswith('(net '):
            nome = bl[5:].split()[0].strip('"')
            if nome not in manter: continue
        keep.append(bl)
    return t[:i] + '(network' + NL + NL.join('    ' + x for x in keep) + NL + '  )' + t[k:]

def dsn_ajusta(t, furos=()):
    if os.environ.get('NETS'):
        t = filtra_redes(t, set(os.environ['NETS'].split(',')))
    # o rule area do cartao MicroMod (so afirma altura de peca) nao proibe trilha: tira o keepout dele
    t = re.sub(r'\n    \(keepout "" \(polygon B\.Cu 0\s+24700 -7000[^\n]*\)\)', '', t)
    # classe Out: OUT_Rk a 0,3 mm de tudo (regra do .kicad_dru: CLK/DATA/I2S/MCLK); o Freerouting nao conhece regra por rede
    t = t.replace('OUT_R1 OUT_R2 OUT_R3 OUT_R4' + NL, NL, 1)
    t = t.replace('    (class Corrente', '    (class Out OUT_R1 OUT_R2 OUT_R3 OUT_R4' + NL + '      (circuit (use_via "Via[0-3]_500:300_um"))' + NL +
                  '      (rule (width 200) (clearance 300))' + NL + '    )' + NL + '    (class Corrente', 1)
    # faixa de 0,45 mm junto a borda (cobre a 0,3 mm da borda) e quadrados de 3,2 mm nos cantos arredondados
    x0, y0, x1, y1 = 2450, -2450, 77500, -97550; f = 450; q = 3200
    def poly(a, b, c, d): return '    (keepout "" (polygon signal 0  %d %d  %d %d  %d %d  %d %d  %d %d))' % (a, b, c, b, c, d, a, d, a, b) + NL
    faixas = poly(x0-100, y0+100, x1+100, y0-f) + poly(x0-100, y1+f, x1+100, y1-100) + poly(x0-100, y0+100, x0+f, y1-100) + poly(x1-f, y0+100, x1+100, y1-100)
    # fenda do cabo da tela (recorte em Edge.Cuts: x 44,45..51,45; y 18,175..20,675): cobre a 0,3 mm do recorte + meia trilha
    faixas += poly(43850, -17575, 52050, -21275)
    faixas += poly(x0, y0, x0+q, y0-q) + poly(x1-q, y0, x1, y0-q) + poly(x0, y1+q, x0+q, y1) + poly(x1-q, y1+q, x1, y1)
    t = t.replace('    (via "Via[0-3]_500:300_um")' + NL, faixas + '    (via "Via[0-3]_500:300_um")' + NL, 1)
    for (hx, hy, hr) in furos:      # furos nao metalizados (NPTH): cobre a 0,2 mm do furo + meia trilha
        faixas_ = '    (keepout "" (circle signal %d %d %d))' % (round(hr*1000), round(hx*1000), round(-hy*1000)) + NL
        t = t.replace('    (via "Via[0-3]_500:300_um")' + NL, faixas_ + '    (via "Via[0-3]_500:300_um")' + NL, 1)
    if os.environ.get('CORR_W'): t = t.replace('(width 800)', '(width %d)' % round(float(os.environ['CORR_W']) * 1000))
    if os.environ.get('FRW'): t = t.replace('(width 200)', '(width %d)' % round(float(os.environ['FRW']) * 1000))
    return t

def roda(tag, passes, base):
    work = os.path.join(BUILD, 'base_%s.kicad_pcb' % tag)
    shutil.copy(base, work); companions(work)
    b = pcbnew.LoadBoard(work)
    for t in b.GetTracks(): t.SetLocked(True)
    b.SetLayerType(pcbnew.In1_Cu, pcbnew.LT_POWER); b.SetLayerType(pcbnew.In2_Cu, pcbnew.LT_POWER)
    dsn = os.path.join(BUILD, 'fr_%s.dsn' % tag); ses = os.path.join(BUILD, 'fr_%s.ses' % tag)
    pcbnew.ExportSpecctraDSN(b, dsn)
    furos = []
    for f_ in b.GetFootprints():
        for p_ in f_.Pads():
            if p_.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                q_ = p_.GetPosition(); furos.append((q_.x/1e6, q_.y/1e6, max(p_.GetDrillSize().x, p_.GetDrillSize().y)/2e6 + 0.35))
    txt = dsn_ajusta(open(dsn, encoding='utf-8').read(), furos)
    open(dsn, 'w', encoding='utf-8').write(txt)
    t0 = time.time(); log("freerouting %s: passes %s" % (tag, passes))
    r = subprocess.run([FR, '-de', dsn, '-do', ses, '-mp', str(passes)], capture_output=True, text=True)
    open(os.path.join(BUILD, 'fr_%s.log' % tag), 'w', encoding='utf-8').write(r.stdout + r.stderr)
    log("freerouting %.0fs" % (time.time() - t0))
    b = pcbnew.LoadBoard(work)
    log("ses: %s" % pcbnew.ImportSpecctraSES(b, ses))
    reaplica(b, pcbnew.LoadBoard(work))
    for t in b.GetTracks(): t.SetLocked(False)
    fill(b)
    out = os.path.join(BUILD, 'fr_%s.kicad_pcb' % tag)
    pcbnew.SaveBoard(out, b); companions(out)
    r_, d = drc(out, os.path.join(BUILD, 'drc_fr_%s.json' % tag)); log("DRC fr_%s: %s" % (tag, r_))
    marca('3_freerouting_' + tag, status='feito', s=round(time.time() - t0), drc=r_)
    return out

if __name__ == '__main__':
    tag = sys.argv[1] if len(sys.argv) > 1 else 'a'; passes = sys.argv[2] if len(sys.argv) > 2 else '40'
    roda(tag, passes, os.environ.get('BASE', BOARD))
