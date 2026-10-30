# Faixas de imagem do funil "China" (30/10/2026). O n8n junta as faixas NA HORA numa imagem só:
# cabeçalho + "SUA ESCOLHA" + "COM VALOR PARECIDO" + 3 cartões + rodapé, como nas imagens dos outros funis, mas SÓ China e 1 pacote.
# uso: python3 fabrica/fabrica_china_faixas.py publico/saidas_china.json publico   → publico/china/faixas/*.png + index.json
# Fundo SÓLIDO (#0B2A52) para as faixas emendarem sem costura. Altura fixa: cabeçalho 214, escolha 324, rótulo 60, parecido 304, rodapé 140.
import json, os, sys, subprocess, datetime, html as H, shutil, zoneinfo

CHROME = os.environ.get('CHROME') or next((c for c in [
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', shutil.which('google-chrome'),
    shutil.which('google-chrome-stable'), shutil.which('chromium')] if c and os.path.exists(c)), None)
LISTA, PUB = sys.argv[1], os.path.abspath(sys.argv[2])
OUT = os.path.join(PUB, 'china', 'faixas'); os.makedirs(OUT, exist_ok=True)
D = json.load(open(LISTA))
AGORA = datetime.datetime.now(zoneinfo.ZoneInfo('America/Sao_Paulo')); HOJE = AGORA.date()
f = lambda v: f"{v:,}".replace(',', '.'); e = H.escape
MES = ['', 'JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
rot = {r['roteiro_id']: r for r in D['roteiros']}
BG = '#0B2A52'
ALT = dict(h=214, hl=324, sec=60, n=304, f=140)
CSS = """@import url('https://fonts.googleapis.com/css2?family=Arimo:wght@400;700&family=Poppins:wght@400;700&display=block');
*{margin:0;padding:0;box-sizing:border-box} html,body{width:1080px;overflow:hidden}
body{background:%s;font-family:Arimo,Arial,sans-serif;position:relative;color:#fff}
.hd{position:absolute;left:40px;top:34px;font:700 26px Arimo;letter-spacing:4.2px;color:#F5B72B}
.tt{position:absolute;left:40px;top:70px;font:700 52px Arimo;color:#fff;white-space:nowrap}
.st{position:absolute;left:40px;top:132px;font:700 30px Arimo;color:#CFE0FB;white-space:nowrap}
.sec{position:absolute;left:40px;top:6px;font:700 26px Arimo;letter-spacing:4.2px;color:#F5B72B;white-space:nowrap}
.card{position:absolute;left:30px;top:0;width:1020px;height:290px;border-radius:22px;background:#1E375A;border:2px solid #566983}
.card.hl{background:#2D3E4F;border:4px solid #F5B72B}
.dt{position:absolute;left:16px;top:12px;font:700 44px Arimo;color:#fff;white-space:nowrap}
.nt{position:absolute;left:18px;top:66px;width:984px;font:700 23px/28px Arimo;color:#DBE7FB;white-space:nowrap}
.pill{position:absolute;right:17px;top:15px;height:42px;border-radius:21px;padding:0 14px;font:700 21px/42px Poppins;white-space:nowrap;background:#F5B72B;color:#0A2447}
.box{position:absolute;top:104px;left:16px;width:984px;height:170px;border-radius:14px;text-align:center}
.bl{background:#fff;color:#0A2447} .br{background:#07172E;border:3px solid #fff;color:#fff}
.lb{position:absolute;left:0;right:0;top:8px;font:700 20px/24px Poppins} .bl .lb{color:#47638F} .br .lb{color:#F5B72B}
.pr{position:absolute;left:0;right:0;top:60px;font:700 56px Arimo;white-space:nowrap}
.en{position:absolute;left:0;right:0;top:122px;font:700 30px Arimo;white-space:nowrap}
.ft{position:absolute;left:0;right:0;top:20px;white-space:nowrap;text-align:center;font:400 23.2px/31px Poppins;color:#CFE0FB} .ft b{color:#fff;font-weight:700}""" % BG
FIT = """<script>document.fonts.ready.then(()=>{for(const el of document.querySelectorAll('.tt,.dt')){let s=parseFloat(getComputedStyle(el).fontSize);
const cabe=()=>el.getBoundingClientRect().right<=1040;while(!cabe()&&s>16){s-=1;el.style.fontSize=s+'px'}}})</script>"""

def render(nome, body, alt):
    h = os.path.join(OUT, nome + '.html'); png = h[:-5] + '.png'
    open(h, 'w').write(f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS} html,body{{height:{alt}px}}</style></head><body>{body}{FIT}</body></html>')
    subprocess.run([CHROME, '--headless=new', '--no-sandbox', '--disable-gpu', '--hide-scrollbars', '--force-device-scale-factor=1',
                    f'--window-size=1080,{alt}', '--virtual-time-budget=10000', f'--screenshot={png}', 'file://' + h],
                   capture_output=True, check=True, timeout=120)
    os.remove(h)
    assert os.path.getsize(png) > 2_000, f'faixa vazia: {png}'

def data_cartao(s):
    return f"{s['dia']:02d} {MES[s['mes']]} {s['ano']}" if s['dia'] else f"{MES[s['mes']]} {s['ano']}"

def cartao(s, pac, hl):
    t = pac == 't'
    par, ent = (s['parcela_12x_terrestre'], s['entrada_terrestre']) if t else (s['parcela_12x_aereo'], s['entrada_aereo'])
    dias = s['dias_terrestre'] if t else s['dias_aereo']
    rotulo = 'Pacote completo<br>' + ('TERRESTRE' if t else 'TERRESTRE + AÉREO + SEGURO')
    box = f'<div class="box {"bl" if t else "br"}"><div class="lb">{rotulo}</div><div class="pr">12x R$ {f(par)}</div><div class="en">+ entrada R$ {f(ent)}</div></div>'
    if hl:
        topo = f'<div class="dt" data-lim="800">{e(data_cartao(s))}</div><div class="pill">SUA ESCOLHA</div>'; nota = f'{dias} dias'
    else:
        topo = f'<div class="dt">{e(rot[s["roteiro_id"]]["nome"])}</div>'; nota = f'{data_cartao(s)} · {dias} dias'
    return f'<div class="card{" hl" if hl else ""}">{topo}<div class="nt">{e(nota)}</div>{box}</div>'

idx = {'gerado_em': AGORA.isoformat(timespec='seconds'), 'versao': AGORA.strftime('%Y%m%d%H%M'), 'altura': ALT, 'saidas': {}, 'roteiros': []}
for rid, r in rot.items():
    render('h-' + rid, f'<div class="hd">LIELU TURISMO · DATAS E VALORES</div><div class="tt">{e(r["nome"])}</div>'
           f'<div class="st">A sua escolha e 3 viagens da China com valor parecido</div>', ALT['h'])
    idx['roteiros'].append(rid)
render('sec', '<div class="sec">COM VALOR PARECIDO</div>', ALT['sec'])
for pac, seg in (('t', ''), ('a', ' Seguro incluso até 70 anos.')):
    render('f-' + pac, f'<div class="ft"><b>Valores por pessoa, em apartamento duplo.</b> Parcelas sem juros, fixas em reais, sem<br>variação cambial.{seg} '
           f'Valores de {HOJE:%d/%m/%Y},<br>sujeitos a alteração sem aviso prévio.</div>', ALT['f'])
for s in D['saidas']:
    if s['sob_consulta']: continue
    for pac in ('t', 'a'):
        render(f"hl-{s['id_site']}-{pac}", cartao(s, pac, True), ALT['hl'])
        render(f"n-{s['id_site']}-{pac}", cartao(s, pac, False), ALT['n'])
    idx['saidas'][str(s['id_site'])] = dict(roteiro_id=s['roteiro_id'], slug=s['slug'], saida=s['saida'])
    print(s['id_site'], s['slug'], flush=True)
assert len(idx['saidas']) >= 4, 'poucas faixas da China: nada publicado'
json.dump(idx, open(os.path.join(OUT, 'index.json'), 'w'), ensure_ascii=False, indent=1)
print(len(idx['saidas']) * 4 + len(idx['roteiros']) + 3, 'faixas em', OUT)
