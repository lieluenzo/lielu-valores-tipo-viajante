# Fábrica das imagens de valores do funil "China" (30/10/2026). SÓ China, 1 pacote por imagem.
# Para cada saída com preço do saidas_china.json: publico/china/<slug>-t.png (TERRESTRE) e <slug>-a.png (TERRESTRE + AÉREO + SEGURO),
# com UM cartão (a saída) no mesmo visual das imagens "DATAS E VALORES". O n8n manda 4 imagens: a escolha e as 3 parecidas da página.
# Saída "sob consulta" não tem imagem. Dias: dias_terrestre no T, dias_aereo no A. Grava publico/china/index.json.
# uso: python3 fabrica/fabrica_china.py publico/saidas_china.json publico
import json, os, sys, subprocess, datetime, html as H, shutil, zoneinfo

CHROME = os.environ.get('CHROME') or next((c for c in [
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', shutil.which('google-chrome'),
    shutil.which('google-chrome-stable'), shutil.which('chromium')] if c and os.path.exists(c)), None)
LISTA, PUB = sys.argv[1], os.path.abspath(sys.argv[2])
OUT = os.path.join(PUB, 'china'); os.makedirs(OUT, exist_ok=True)
D = json.load(open(LISTA))
AGORA = datetime.datetime.now(zoneinfo.ZoneInfo('America/Sao_Paulo')); HOJE = AGORA.date()
f = lambda v: f"{v:,}".replace(',', '.'); e = H.escape
MES = ['', 'JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
nome_rot = {r['roteiro_id']: r for r in D['roteiros']}
HH = 760
CSS = f"""@import url('https://fonts.googleapis.com/css2?family=Arimo:wght@400;700&family=Poppins:wght@400;700&display=block');
*{{margin:0;padding:0;box-sizing:border-box}} html,body{{width:1080px;height:{HH}px;overflow:hidden}}
body{{background:linear-gradient(180deg,#0A2549 0%,#0D2F5E 100%);font-family:Arimo,Arial,sans-serif;position:relative;color:#fff}}
.hd{{position:absolute;left:40px;top:34px;font:700 26px Arimo;letter-spacing:4.2px;color:#F5B72B}}
.tt{{position:absolute;left:40px;top:70px;font:700 52px Arimo;color:#fff;white-space:nowrap}}
.st{{position:absolute;left:40px;top:132px;font:700 30px Arimo;color:#CFE0FB;white-space:nowrap}}
.card{{position:absolute;left:30px;top:214px;width:1020px;height:290px;border-radius:22px;background:#2D3E4F;border:4px solid #F5B72B}}
.dt{{position:absolute;left:16px;top:12px;font:700 44px Arimo;color:#fff;white-space:nowrap}}
.nt{{position:absolute;left:18px;top:66px;width:984px;font:700 23px/28px Arimo;color:#DBE7FB;white-space:nowrap}}
.box{{position:absolute;top:104px;left:16px;width:984px;height:170px;border-radius:14px;text-align:center}}
.bl{{background:#fff;color:#0A2447}} .br{{background:#07172E;border:3px solid #fff;color:#fff}}
.lb{{position:absolute;left:0;right:0;top:8px;font:700 20px/24px Poppins}} .bl .lb{{color:#47638F}} .br .lb{{color:#F5B72B}}
.pr{{position:absolute;left:0;right:0;top:60px;font:700 56px Arimo;white-space:nowrap}}
.en{{position:absolute;left:0;right:0;top:122px;font:700 30px Arimo;white-space:nowrap}}
.ft{{position:absolute;left:0;right:0;top:545px;white-space:nowrap;text-align:center;font:400 23.2px/31px Poppins;color:#CFE0FB}} .ft b{{color:#fff;font-weight:700}}"""
FIT = """<script>document.fonts.ready.then(()=>{for(const el of document.querySelectorAll('.tt,.dt')){let s=parseFloat(getComputedStyle(el).fontSize);
const cabe=()=>el.getBoundingClientRect().right<=1040;while(!cabe()&&s>16){s-=1;el.style.fontSize=s+'px'}}})</script>"""

def data_cartao(s):
    if s['dia']: return f"{s['dia']:02d} {MES[s['mes']]} {s['ano']}"
    return f"{MES[s['mes']]} {s['ano']}"

def imagem(s, pac):
    t = pac == 't'
    par, ent = (s['parcela_12x_terrestre'], s['entrada_terrestre']) if t else (s['parcela_12x_aereo'], s['entrada_aereo'])
    dias = s['dias_terrestre'] if t else s['dias_aereo']
    rot = nome_rot[s['roteiro_id']]
    titulo = rot['nome']
    rotulo = 'Pacote completo<br>' + ('TERRESTRE' if t else 'TERRESTRE + AÉREO + SEGURO')
    seguro = '' if t else ' Seguro incluso até 70 anos.'
    b = (f'<div class="hd">LIELU TURISMO · DATAS E VALORES</div><div class="tt">{e(titulo)}</div>'
         f'<div class="st">{e(rot["sub"])}</div>'
         f'<div class="card"><div class="dt">{e(data_cartao(s))}</div><div class="nt">{dias} dias</div>'
         f'<div class="box {"bl" if t else "br"}"><div class="lb">{rotulo}</div><div class="pr">12x R$ {f(par)}</div><div class="en">+ entrada R$ {f(ent)}</div></div></div>'
         f'<div class="ft"><b>Valores por pessoa, em apartamento duplo.</b> Parcelas sem juros, fixas em reais, sem<br>variação cambial.{seguro} '
         f'Valores de {HOJE:%d/%m/%Y},<br>sujeitos a alteração sem aviso prévio.</div>')
    assert ent + 12 * par > 0
    h = os.path.join(OUT, f"{s['slug']}-{pac}.html"); png = h[:-5] + '.png'
    open(h, 'w').write(f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>{b}{FIT}</body></html>')
    subprocess.run([CHROME, '--headless=new', '--no-sandbox', '--disable-gpu', '--hide-scrollbars', '--force-device-scale-factor=1',
                    f'--window-size=1080,{HH}', '--virtual-time-budget=10000', f'--screenshot={png}', 'file://' + h],
                   capture_output=True, check=True, timeout=120)
    os.remove(h)
    assert os.path.getsize(png) > 30_000, f'imagem vazia: {png}'

idx = {'gerado_em': AGORA.isoformat(timespec='seconds'), 'versao': AGORA.strftime('%Y%m%d%H%M'), 'saidas': {}}
for s in D['saidas']:
    if s['sob_consulta']: continue
    imagem(s, 't'); imagem(s, 'a')
    idx['saidas'][str(s['id_site'])] = dict(slug=s['slug'], roteiro=nome_rot[s['roteiro_id']]['nome'], saida=s['saida'], link=s['link'],
                                            t=s['slug'] + '-t.png', a=s['slug'] + '-a.png')
    print(s['id_site'], s['slug'], flush=True)
assert len(idx['saidas']) >= 4, 'poucas imagens da China: nada publicado'
json.dump(idx, open(os.path.join(OUT, 'index.json'), 'w'), ensure_ascii=False, indent=1)
print(len(idx['saidas']) * 2, 'imagens em', OUT)
