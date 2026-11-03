# 03/11/2026 — "imagens de período" do robô do Instagram "Comente 2027" (carrossel Calendário 2027, 1º semestre).
# Visual = PAINEL DE PARTIDAS do carrossel (aprovado pelo Bruno: "vai na 2... amei"), agora com o preço do dia.
# Feito para rodar na fábrica do GitHub (lieluenzo/lielu-valores-tipo-viajante) todo dia às 5h, como o fabrica.py:
# só Python + Chrome sem tela, fonte Inter do Google Fonts, nenhuma foto, altura cresce sozinha.
# uso: python3 calendario_2027.py dados/site_hoje.json publico   → publico/calendario-2027/<parte>.png + index.json
# Regras: preço do site (entrada + 12x = total, conferido); sem preço = "Valor com o consultor"; dias totais, nunca "noites";
#   nome curto = nomes_curtos.json da fábrica (ou a regra curto() do fabrica.py); mesmo nome no mesmo dia ganha a versão do site.
import json, os, re, sys, subprocess, datetime, html as H, shutil, zoneinfo

AQUI = os.path.dirname(os.path.abspath(__file__))
CHROME = os.environ.get('CHROME') or next((c for c in [
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', shutil.which('google-chrome'),
    shutil.which('google-chrome-stable'), shutil.which('chromium')] if c and os.path.exists(c)), None)
SAIDAS, OUT = sys.argv[1], os.path.join(os.path.abspath(sys.argv[2]), 'calendario-2027')
L = json.load(open(SAIDAS)); os.makedirs(OUT, exist_ok=True)
AGORA = datetime.datetime.now(zoneinfo.ZoneInfo('America/Sao_Paulo')); HOJE = AGORA.date()
MES = ['', 'JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
f = lambda v: f"{v:,}".replace(',', '.'); e = H.escape; NB = ' '

# as 6 partes têm corte FIXO por data: o endereço de cada imagem no robô nunca muda
PARTES = [('jan-mar', 'JAN A MAR', None, (1, 1), (3, 31)), ('abr-1', 'ABRIL', 'dias 1 a 15', (4, 1), (4, 15)),
          ('abr-2', 'ABRIL', 'dias 16 a 30', (4, 16), (4, 30)), ('mai-1', 'MAIO', 'dias 1 a 15', (5, 1), (5, 15)),
          ('mai-2', 'MAIO', 'dias 16 a 31', (5, 16), (5, 31)), ('jun', 'JUNHO', None, (6, 1), (6, 30))]
ANO = 2027

arq_curtos = next((p for p in [os.environ.get('NOMES_CURTOS'), os.path.join(AQUI, 'nomes_curtos.json')] if p and os.path.exists(p)), None)
CURTO = json.load(open(arq_curtos)) if arq_curtos else {}
def curto(r):
    n = CURTO.get(r['slug']) or re.split(r'\s+[–-]\s+', r['nome'])[0]
    n = re.sub(r'\s+e\s+\d+\s+noites?\b.*$', '', n)          # nunca "noites" (regra do Bruno)
    if 'Slower Travel' in r['nome'] and 'Slower' not in n: n += ' Slower Travel'   # Keukenhof Slower é outro roteiro
    return {'6 países': '6 Países dos Alpes'}.get(n, n)
VERSAO = {'café da manhã e refeições conforme roteiro': 'com refeições'}
def versao(r):                                                # o que diferencia 2 roteiros de mesmo nome no mesmo dia
    v = re.split(r'\s+[–-]\s+', r['nome'])[-1].strip()
    return VERSAO.get(v.lower(), v)

def dmy(r):
    m = re.match(r'(\d\d)/(\d\d)/(\d{4})$', r.get('data') or '')
    return (int(m[3]), int(m[2]), int(m[1])) if m else None
ok_preco = lambda p: p and p.get('total') and p['entrada'] + 12 * p['parcela'] == p['total']

AV = ('<svg width="54" height="54" viewBox="0 0 24 24"><path fill="#fabf21" d="M2.5 19h19v2h-19zm19.57-9.36c-.21-.8-1.04-1.28-1.84-1.06'
      'L14.92 10l-6.9-6.43-1.93.51 4.14 7.17-4.97 1.33-1.97-1.54-1.45.39 2.59 4.49L21 11.49c.81-.23 1.28-1.05 1.07-1.85z"/></svg>')
TOPO, CAB, RH, PE = 300, 64, 100, 190                         # alturas: topo, cabeçalho das colunas, linha, rodapé
CSS = """@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=block');
*{margin:0;padding:0;box-sizing:border-box} html,body{width:1080px;height:%dpx;overflow:hidden}
body{font-family:Inter,Arial,sans-serif;color:#fff;background:radial-gradient(120%% 60%% at 85%% 0%%,#3a3270 0%%,#221d44 45%%,#15122b 100%%);position:relative}
.sb{position:absolute;left:52px;top:44px;font:700 21px/1 Inter;letter-spacing:4px;color:#fabf21}
.tt{position:absolute;left:44px;top:84px;display:flex;align-items:center;gap:16px;font:800 66px/1 Inter;letter-spacing:7px;color:#fabf21}
.per{position:absolute;right:52px;top:88px;text-align:right}.per b{display:block;font:800 40px/1 Inter;letter-spacing:1px}
.per span{display:block;font:600 24px/1 Inter;color:#c8c2da;margin-top:10px}
.qt{position:absolute;left:52px;top:196px;font:500 25px/1.3 Inter;color:#dcd7ef}.qt b{font-weight:800;color:#fff}
.bd{position:absolute;left:30px;right:30px;top:%dpx;bottom:%dpx;background:rgba(18,15,38,.92);border:1px solid rgba(255,255,255,.14);border-radius:30px;padding:0 22px}
.hd,.rw{display:grid;grid-template-columns:86px 1fr 214px 226px;column-gap:16px;align-items:center}
.hd{height:%dpx;border-bottom:2px solid rgba(250,191,33,.55);font:700 15px/1.25 Inter;letter-spacing:2px;color:#9e97c4}
.hd .a{color:#fabf21}
.rw{height:%dpx;border-top:1px solid rgba(255,255,255,.09)} .rw:nth-child(odd){background:rgba(255,255,255,.025)} .hd+.rw{border-top:0}
.dd{display:flex;flex-direction:column;align-items:center;gap:5px}.fx{display:flex;gap:4px}
.fl{width:38px;height:48px;border-radius:6px;background:#2b2656;color:#fabf21;font:800 31px/48px Inter;font-variant-numeric:tabular-nums;text-align:center;position:relative}
.fl:after{content:'';position:absolute;left:0;right:0;top:50%%;height:1px;background:rgba(0,0,0,.5)}
.dd small{font:800 14px/1 Inter;letter-spacing:2px;color:#c8c2da}
.nm{font:700 27px/1.14 Inter;color:#fff;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.ds{font:500 19px/1 Inter;color:#b9b2d6;margin-top:7px;white-space:nowrap}
.pr b{display:block;font:800 29px/1 Inter;white-space:nowrap;font-variant-numeric:tabular-nums}.pr span{display:block;font:500 18px/1 Inter;color:#b9b2d6;margin-top:8px;white-space:nowrap}
.pr.a b{color:#fabf21}
.cs{grid-column:3 / span 2;justify-self:start;font:700 22px/1 Inter;color:#fabf21;border:2px solid #fabf21;border-radius:999px;padding:12px 20px}
.ft{position:absolute;left:60px;right:60px;bottom:44px;text-align:center;font:400 21px/1.45 Inter;color:#c8c2da}.ft b{color:#fff;font-weight:700}
"""
FIT = """<script>document.fonts.ready.then(()=>{for(const el of document.querySelectorAll('.nm')){let s=parseFloat(getComputedStyle(el).fontSize);
while(el.scrollHeight>el.clientHeight+1&&s>18){s-=0.5;el.style.fontSize=s+'px'}}})</script>"""

def linhas_da_parte(ini, fim):
    rs = sorted([r for r in L if dmy(r) and dmy(r)[0] == ANO and ini <= dmy(r)[1:] <= fim], key=lambda r: (dmy(r), curto(r)))
    nomes = {}
    for r in rs: nomes.setdefault((dmy(r), curto(r)), []).append(r)
    out = []
    for r in rs:
        n = curto(r)
        if len(nomes[(dmy(r), n)]) > 1 and len(versao(r)) <= 30: n = f'{n} ({versao(r)})'   # a outra versão fica com o nome curto
        out.append((r, n))
    return out

def linha(r, nome, mostra_mes):
    a, m, d = dmy(r)
    fl = ''.join(f'<span class="fl">{c}</span>' for c in f'{d:02d}')
    da, dt = str(r.get('dias_aereo') or r.get('dias') or ''), str(r.get('dias_terrestre') or '')
    dias = f'{da} dias' if (not dt or dt == da) else f'{da} dias com aéreo · {dt} no terrestre'
    t, c = r.get('terrestre'), r.get('completo')
    if ok_preco(t) and ok_preco(c):
        precos = (f'<div class="pr"><b>12x R$ {f(t["parcela"])}</b><span>+ entrada R$ {f(t["entrada"])}</span></div>'
                  f'<div class="pr a"><b>12x R$ {f(c["parcela"])}</b><span>+ entrada R$ {f(c["entrada"])}</span></div>')
        p = dict(terrestre=t, completo=c)
    else:
        precos = '<div class="cs">Valor com o consultor</div>'; p = None
    html = (f'<div class="rw"><div class="dd"><div class="fx">{fl}</div><small>{MES[m]}</small></div>'
            f'<div><div class="nm">{e(nome)}</div><div class="ds">{e(dias)}</div></div>{precos}</div>')
    return html, dict(data=r['data'], roteiro=nome, slug=r['slug'], dias_aereo=da, dias_terrestre=dt, precos=p, link=r.get('url'))

idx = {'gerado_em': AGORA.isoformat(timespec='seconds'), 'partes': {}}
total = 0
for parte, rotulo, sub, ini, fim in PARTES:
    ls = linhas_da_parte(ini, fim)
    assert ls, f'{parte}: nenhuma saída no site — nada foi publicado'
    rows, dados = zip(*(linha(r, n, True) for r, n in ls))
    n = len(rows); total += n
    HH = (TOPO - 30) + CAB + n * RH + 18 + (PE - 20)
    sem = sum(1 for x in dados if not x['precos'])
    qt = f'<b>{n} saídas</b> · valores por pessoa, em 12x sem juros' + (f' · {sem} com valor no consultor' if sem else '')
    corpo = (f'<div class="sb">LIELU TURISMO · CALENDÁRIO DE VIAGENS {ANO}</div><div class="tt">{AV}PARTIDAS</div>'
             f'<div class="per"><b>{rotulo} {ANO}</b>' + (f'<span>{sub}</span>' if sub else '') + f'</div><div class="qt">{qt}</div>'
             f'<div class="bd"><div class="hd"><span>DIA</span><span>DESTINO</span><span>TERRESTRE</span><span class="a">TERRESTRE + AÉREO<br>+ SEGURO</span></div>'
             + ''.join(rows) + '</div>'
             f'<div class="ft"><b>Valores por pessoa, em apartamento duplo.</b> Parcelas sem juros, fixas em reais, sem variação cambial. '
             f'Seguro incluso até 70 anos. Valores de {HOJE:%d/%m/%Y}, sujeitos a alteração sem{NB}aviso{NB}prévio.</div>')
    css = CSS % (HH, TOPO - 30, PE - 20, CAB, RH)
    h = os.path.join(OUT, parte + '.html'); png = h[:-5] + '.png'
    open(h, 'w').write(f'<!doctype html><html><head><meta charset="utf-8"><style>{css}</style></head><body>{corpo}{FIT}</body></html>')
    subprocess.run([CHROME, '--headless=new', '--no-sandbox', '--disable-gpu', '--hide-scrollbars', '--force-device-scale-factor=1',
                    f'--window-size=1080,{HH}', '--virtual-time-budget=10000', f'--screenshot={png}', 'file://' + h],
                   capture_output=True, check=True, timeout=120)
    os.remove(h)
    assert os.path.getsize(png) > 50_000, f'imagem vazia: {png}'
    idx['partes'][parte] = dict(arquivo=f'calendario-2027/{parte}.png', saidas=list(dados))
    print(f'{parte:8} {n:>2} saídas ({sem} sem preço)  {HH}px', flush=True)
assert total >= 60, f'só {total} saídas: leitura do site incompleta'
json.dump(idx, open(os.path.join(OUT, 'index.json'), 'w'), ensure_ascii=False, indent=1)
print(total, 'saídas em', OUT)
