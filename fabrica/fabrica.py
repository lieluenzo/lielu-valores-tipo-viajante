# Fábrica das imagens "4 preços" do funil Tipo de Viajante (Lielu Turismo).
# Para CADA saída com preço no site: 1º cartão = a saída escolhida (borda dourada, SUA ESCOLHA);
# embaixo, "COM VALOR PARECIDO" = 3 saídas de OUTROS destinos com o terrestre duplo mais perto.
# Mesmo visual das imagens "DATAS E VALORES" do Da Vinci. Grava publico/<slug>.png + publico/index.json.
# uso: python3 fabrica.py site_hoje.json publico
import json, os, re, sys, subprocess, datetime, html as H, shutil, zoneinfo

AQUI = os.path.dirname(os.path.abspath(__file__))
CHROME = os.environ.get('CHROME') or next((c for c in [
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', shutil.which('google-chrome'),
    shutil.which('google-chrome-stable'), shutil.which('chromium')] if c and os.path.exists(c)), None)
SAIDAS, OUT = sys.argv[1], os.path.abspath(sys.argv[2])
L = json.load(open(SAIDAS)); os.makedirs(OUT, exist_ok=True)
AGORA = datetime.datetime.now(zoneinfo.ZoneInfo('America/Sao_Paulo')); HOJE = AGORA.date()
MES = ['', 'JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
MESN = {n: i for i, n in enumerate(['', 'janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto',
                                    'setembro', 'outubro', 'novembro', 'dezembro'])}
f = lambda v: f"{v:,}".replace(',', '.'); e = H.escape

# nome curto = o nome do roteiro no funil; saída nova (fora da lista) usa o nome do site antes do "–"
CURTO = json.load(open(os.path.join(AQUI, 'nomes_curtos.json')))
curto = lambda r: CURTO.get(r['slug']) or re.split(r'\s+[–-]\s+', r['nome'])[0]
familia = lambda r: r['slug'].split('-')[0]          # china-..., reino-unido-..., suica-...: um destino por cartão

fixa = lambda r: re.match(r'\d\d/\d\d/\d{4}$', r['data'])
so_mes = lambda r: re.match(r'([a-zç]+)/(\d{4}) \(dia a definir\)$', r['data'])
def ymd(r):
    if fixa(r):
        d, m, a = r['data'].split('/'); return int(a), int(m), int(d)
    m = so_mes(r); return int(m.group(2)), MESN[m.group(1)], 99
futura = lambda r: ymd(r)[:2] > (HOJE.year, HOJE.month)
com_preco = lambda r: r['terrestre'] and r['completo']
escolhiveis = [r for r in L if com_preco(r) and (fixa(r) or so_mes(r)) and futura(r)]
comparaveis = [r for r in escolhiveis if fixa(r)]
assert len(escolhiveis) >= 60, f'só {len(escolhiveis)} saídas com preço: leitura do site incompleta, nada foi publicado'

FIT = """<script>document.fonts.ready.then(()=>{for(const el of document.querySelectorAll('.tt,.st,.nt,.dt')){let s=parseFloat(getComputedStyle(el).fontSize);
const lim=el.dataset.lim?parseFloat(el.dataset.lim):1040;
const cabe=()=>el.classList.contains('nt')?el.scrollWidth<=el.clientWidth:el.getBoundingClientRect().right<=lim;while(!cabe()&&s>16){s-=1;el.style.fontSize=s+'px'}}})</script>"""
def css(HH): return f"""@import url('https://fonts.googleapis.com/css2?family=Arimo:wght@400;700&family=Poppins:wght@400;700&display=block');
*{{margin:0;padding:0;box-sizing:border-box}} html,body{{width:1080px;height:{HH}px;overflow:hidden}}
body{{background:linear-gradient(180deg,#0A2549 0%,#0D2F5E 100%);font-family:Arimo,Arial,sans-serif;position:relative;color:#fff}}
.hd{{position:absolute;left:40px;top:34px;font:700 26px Arimo;letter-spacing:4.2px;color:#F5B72B}}
.tt{{position:absolute;left:40px;top:70px;font:700 52px Arimo;color:#fff;white-space:nowrap}}
.st{{position:absolute;left:40px;top:132px;font:700 30px Arimo;color:#CFE0FB;white-space:nowrap}}
.sec{{position:absolute;left:40px;font:700 26px Arimo;letter-spacing:4.2px;color:#F5B72B;white-space:nowrap}}
.card{{position:absolute;left:30px;width:1020px;border-radius:22px;background:#1E375A;border:2px solid #566983}}
.card.hl{{background:#2D3E4F;border:4px solid #F5B72B}}
.dt{{position:absolute;left:16px;top:12px;font:700 44px Arimo;color:#fff;white-space:nowrap}}
.nt{{position:absolute;left:18px;top:66px;width:984px;font:700 23px/28px Arimo;color:#DBE7FB;white-space:nowrap}}
.pill{{position:absolute;right:17px;top:15px;height:42px;border-radius:21px;padding:0 14px;font:700 21px/42px Poppins;white-space:nowrap;background:#F5B72B;color:#0A2447}}
.box{{position:absolute;top:104px;height:170px;border-radius:14px;text-align:center}}
.bl{{left:16px;width:483px;background:#fff;color:#0A2447}} .br{{left:511px;width:489px;background:#07172E;border:3px solid #fff;color:#fff}}
.lb{{position:absolute;left:0;right:0;top:8px;font:700 20px/24px Poppins}} .bl .lb{{color:#47638F}} .br .lb{{color:#F5B72B}}
.pr{{position:absolute;left:0;right:0;top:60px;font:700 48px Arimo;white-space:nowrap}}
.en{{position:absolute;left:0;right:0;top:120px;font:700 28px Arimo;white-space:nowrap}}
.ft{{position:absolute;left:0;right:0;white-space:nowrap;text-align:center;font:400 23.2px/31px Poppins;color:#CFE0FB}} .ft b{{color:#fff;font-weight:700}}"""

def data_cartao(r):
    a, m, d = ymd(r); return f"{d:02d} {MES[m]} {a}" if fixa(r) else f"{MES[m]} {a} · dia a definir"

def cartao(r, y, hl):
    t, c = r['terrestre'], r['completo']
    assert t['entrada'] + 12 * t['parcela'] == t['total'] and c['entrada'] + 12 * c['parcela'] == c['total'], r['slug']
    if hl:
        topo = f'<div class="dt" data-lim="800">{e(data_cartao(r))}</div><div class="pill">SUA ESCOLHA</div>'
        nota = f"{r['dias_aereo']} dias"
    else:
        topo = f'<div class="dt">{e(curto(r))}</div>'
        nota = f"{data_cartao(r)} · {r['dias_aereo']} dias"
    return (f'<div class="card{" hl" if hl else ""}" style="top:{y}px;height:290px">{topo}<div class="nt">{e(nota)}</div>'
            f'<div class="box bl"><div class="lb">Pacote completo<br>TERRESTRE</div><div class="pr">12x R$ {f(t["parcela"])}</div><div class="en">+ entrada R$ {f(t["entrada"])}</div></div>'
            f'<div class="box br"><div class="lb">Pacote completo<br>TERRESTRE + AÉREO + SEGURO</div><div class="pr">12x R$ {f(c["parcela"])}</div><div class="en">+ entrada R$ {f(c["entrada"])}</div></div></div>')

def parecidos_de(esc):
    base = esc['terrestre']['total']; vistos, P = set(), []
    for r in sorted((r for r in comparaveis if familia(r) != familia(esc)), key=lambda r: (abs(r['terrestre']['total'] - base), ymd(r))):
        if familia(r) in vistos: continue
        vistos.add(familia(r)); P.append(r)
        if len(P) == 3: break
    return P

def imagem(esc, P):
    y = 214
    b = (f'<div class="hd">LIELU TURISMO · DATAS E VALORES</div><div class="tt">{e(curto(esc))}</div>'
         f'<div class="st">A sua escolha e 3 viagens com valor parecido</div>')
    b += cartao(esc, y, True); y += 290 + 34
    b += f'<div class="sec" style="top:{y}px">COM VALOR PARECIDO</div>'; y += 50
    for r in P:
        b += cartao(r, y, False); y += 290 + 14
    y += 20
    b += (f'<div class="ft" style="top:{y}px"><b>Valores por pessoa, em apartamento duplo.</b> Parcelas sem juros, fixas em reais, sem<br>variação cambial. '
          f'Seguro incluso até 70 anos. Valores de {HOJE:%d/%m/%Y}, sujeitos a<br>alteração sem aviso prévio.</div>')
    HH = y + 3 * 31 + 44
    h = os.path.join(OUT, esc['slug'] + '.html'); png = h[:-5] + '.png'
    open(h, 'w').write(f'<!doctype html><html><head><meta charset="utf-8"><style>{css(HH)}</style></head><body>{b}{FIT}</body></html>')
    subprocess.run([CHROME, '--headless=new', '--no-sandbox', '--disable-gpu', '--hide-scrollbars', '--force-device-scale-factor=1',
                    f'--window-size=1080,{HH}', '--virtual-time-budget=10000', f'--screenshot={png}', 'file://' + h],
                   capture_output=True, check=True, timeout=120)
    os.remove(h)
    assert os.path.getsize(png) > 50_000, f'imagem vazia: {png}'

resumo = lambda r: dict(roteiro=curto(r), data=r['data'], dias=r['dias_aereo'], terrestre=r['terrestre'], completo=r['completo'], link=r['url'])
idx = {'gerado_em': AGORA.isoformat(timespec='seconds'), 'versao': AGORA.strftime('%Y%m%d%H%M'), 'saidas': {}}
for esc in sorted(escolhiveis, key=lambda r: r['slug']):
    P = parecidos_de(esc)
    imagem(esc, P)
    idx['saidas'][esc['slug']] = dict(resumo(esc), parecidos=[dict(resumo(r), slug=r['slug']) for r in P])
    print(f"{esc['slug']:48} T {esc['terrestre']['total']:>6}  ← " + ' | '.join(f"{r['slug']} {r['terrestre']['total'] - esc['terrestre']['total']:+}" for r in P), flush=True)
json.dump(idx, open(os.path.join(OUT, 'index.json'), 'w'), ensure_ascii=False, indent=1)
print(len(idx['saidas']), 'imagens em', OUT)
