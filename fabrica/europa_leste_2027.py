# 04/11/2026 — imagens de preço do robô do Instagram "Comente LESTE" (carrossel "Vai para a Europa do Leste? Compare os 4 roteiros").
# Uma imagem POR ROTEIRO, no visual do painel de partidas aprovado no calendário 2027 (calendario_2027.py), com o preço do dia.
# Feito para a fábrica do GitHub (lieluenzo/lielu-valores-tipo-viajante), como o calendario_2027.py: só Python + Chrome sem tela,
# fonte Inter do Google Fonts, nenhuma foto, altura cresce sozinha. Endereço de cada imagem fixo (o robô nunca muda).
# uso: python3 europa_leste_2027.py dados/site_hoje.json publico → publico/europa-do-leste-2027/<roteiro>.png + index.json
# Regras: preço do site (entrada + 12x = total, conferido); sem preço = "Valor com o consultor"; dias totais, nunca "noites";
#   fora as saídas já passadas e as do mês corrente (Mercados de Natal 14/11/2026 sai sozinho); outubro sem dia = "dia a definir".
import json, os, re, sys, subprocess, datetime, html as H, shutil, zoneinfo

CHROME = os.environ.get('CHROME') or next((c for c in [
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', shutil.which('google-chrome'),
    shutil.which('google-chrome-stable'), shutil.which('chromium')] if c and os.path.exists(c)), None)
SAIDAS, OUT = sys.argv[1], os.path.join(os.path.abspath(sys.argv[2]), 'europa-do-leste-2027')
L = json.load(open(SAIDAS)); os.makedirs(OUT, exist_ok=True)
AGORA = datetime.datetime.now(zoneinfo.ZoneInfo('America/Sao_Paulo')); HOJE = AGORA.date()
MES = ['', 'JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
MESN = {'janeiro': 1, 'fevereiro': 2, 'março': 3, 'abril': 4, 'maio': 5, 'junho': 6, 'julho': 7, 'agosto': 8, 'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12}
f = lambda v: f"{v:,}".replace(',', '.'); e = H.escape; NB = ' '

# roteiro = nome exato da página da saída no site (o endereço nem sempre diz o roteiro)
ROT = [('classico', 'Europa do Leste', 'Europa do Leste', '#fabf21', 'Munique → Berlim'),
       ('imperiais', 'Europa do Leste pelas Cidades Imperiais', 'Cidades Imperiais', '#6ec1ff', 'Viena → Praga'),
       ('imperiais-alemanha', 'Europa do Leste pelas Cidades Imperiais e Alemanha', 'Cidades Imperiais e Alemanha', '#b49cff', 'Munique → Berlim'),
       ('rota-romantica', 'Europa do Leste - Da Rota Romântica ao Danúbio', 'Da Rota Romântica ao Danúbio', '#5fd3a8', 'Frankfurt → Munique')]
# saídas com desenho diferente (lido nas páginas em 04/11/2026)
NOTA = {'europa-do-leste-imperial-21abr2027': 'Chega por Munique, com Salzburg',
        'europa-do-leste-imperial-12mai2027': 'Com Neuschwanstein · termina em Praga'}

def quando(r):
    """(ano, mês, dia ou 0) — 'outubro/2027 (dia a definir)' vira dia 0"""
    d = r.get('data') or ''
    m = re.match(r'(\d\d)/(\d\d)/(\d{4})$', d)
    if m: return int(m[3]), int(m[2]), int(m[1])
    m = re.match(r'([a-zç]+)/(\d{4})', d.lower())
    return (int(m[2]), MESN[m[1]], 0) if m and m[1] in MESN else None
ok_preco = lambda p: p and p.get('total') and p['entrada'] + 12 * p['parcela'] == p['total']
futura = lambda q: q and (q[0], q[1]) > (HOJE.year, HOJE.month)          # nunca o mês corrente nem o passado

AV = ('<svg width="54" height="54" viewBox="0 0 24 24"><path fill="#fabf21" d="M2.5 19h19v2h-19zm19.57-9.36c-.21-.8-1.04-1.28-1.84-1.06'
      'L14.92 10l-6.9-6.43-1.93.51 4.14 7.17-4.97 1.33-1.97-1.54-1.45.39 2.59 4.49L21 11.49c.81-.23 1.28-1.05 1.07-1.85z"/></svg>')
TOPO, CAB, RH, PE = 340, 64, 104, 190
CSS = """@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=block');
*{margin:0;padding:0;box-sizing:border-box} html,body{width:1080px;height:%dpx;overflow:hidden}
body{font-family:Inter,Arial,sans-serif;color:#fff;background:radial-gradient(120%% 60%% at 85%% 0%%,#3a3270 0%%,#221d44 45%%,#15122b 100%%);position:relative}
.sb{position:absolute;left:52px;top:44px;font:700 21px/1 Inter;letter-spacing:4px;color:#fabf21}
.tt{position:absolute;left:44px;top:84px;display:flex;align-items:center;gap:16px;font:800 66px/1 Inter;letter-spacing:7px;color:#fabf21}
.ro{position:absolute;left:52px;right:52px;top:186px;display:flex;align-items:center;gap:16px;font:800 46px/1.05 Inter;letter-spacing:-.5px}
.ro i{width:26px;height:26px;border-radius:50%%;flex:none;box-shadow:0 0 0 5px rgba(255,255,255,.12)}
.qt{position:absolute;left:52px;top:254px;font:500 25px/1.3 Inter;color:#dcd7ef}.qt b{font-weight:800;color:#fff}
.bd{position:absolute;left:30px;right:30px;top:%dpx;bottom:%dpx;background:rgba(18,15,38,.92);border:1px solid rgba(255,255,255,.14);border-radius:30px;padding:0 22px}
.hd,.rw{display:grid;grid-template-columns:86px 1fr 214px 226px;column-gap:16px;align-items:center}
.hd{height:%dpx;border-bottom:2px solid rgba(250,191,33,.55);font:700 15px/1.25 Inter;letter-spacing:2px;color:#9e97c4}
.hd .a{color:#fabf21}
.rw{height:%dpx;border-top:1px solid rgba(255,255,255,.09)} .rw:nth-child(odd){background:rgba(255,255,255,.025)} .hd+.rw{border-top:0}
.dd{display:flex;flex-direction:column;align-items:center;gap:5px}.fx{display:flex;gap:4px}
.fl{width:38px;height:48px;border-radius:6px;background:#2b2656;color:#fabf21;font:800 31px/48px Inter;font-variant-numeric:tabular-nums;text-align:center;position:relative}
.fl:after{content:'';position:absolute;left:0;right:0;top:50%%;height:1px;background:rgba(0,0,0,.5)}
.dd small{font:800 14px/1 Inter;letter-spacing:2px;color:#c8c2da}
.nm{font:700 27px/1.14 Inter;color:#fff;white-space:nowrap}.ds{font:500 19px/1.25 Inter;color:#b9b2d6;margin-top:7px}.ds em{font-style:normal;color:#fabf21;font-weight:700}
.pr b{display:block;font:800 29px/1 Inter;white-space:nowrap;font-variant-numeric:tabular-nums}.pr span{display:block;font:500 18px/1 Inter;color:#b9b2d6;margin-top:8px;white-space:nowrap}
.pr.a b{color:#fabf21}
.cs{grid-column:3 / span 2;justify-self:start;font:700 22px/1 Inter;color:#fabf21;border:2px solid #fabf21;border-radius:999px;padding:12px 20px}
.ft{position:absolute;left:60px;right:60px;bottom:44px;text-align:center;font:400 21px/1.45 Inter;color:#c8c2da}.ft b{color:#fff;font-weight:700}
"""

def linha(r):
    a, m, d = quando(r)
    fl = ''.join(f'<span class="fl">{c}</span>' for c in (f'{d:02d}' if d else '––'))
    da, dt = str(r.get('dias_aereo') or r.get('dias') or ''), str(r.get('dias_terrestre') or '')
    nota = NOTA.get(r['slug']) or ('Dia a definir' if not d else '')
    sub = (f'{dt} dias no terrestre' if dt and dt != da else '') + (' · ' if dt and dt != da and nota else '') + (f'<em>{e(nota)}</em>' if nota else '')
    t, c = r.get('terrestre'), r.get('completo')
    if ok_preco(t) and ok_preco(c):
        precos = (f'<div class="pr"><b>12x R$ {f(t["parcela"])}</b><span>+ entrada R$ {f(t["entrada"])}</span></div>'
                  f'<div class="pr a"><b>12x R$ {f(c["parcela"])}</b><span>+ entrada R$ {f(c["entrada"])}</span></div>')
        p = dict(terrestre=t, completo=c)
    else:
        precos = '<div class="cs">Valor com o consultor</div>'; p = None
    html = (f'<div class="rw"><div class="dd"><div class="fx">{fl}</div><small>{MES[m]}</small></div>'
            f'<div><div class="nm">{da} dias com aéreo</div>' + (f'<div class="ds">{sub}</div>' if sub else '') + f'</div>{precos}</div>')
    return html, dict(data=r['data'], slug=r['slug'], dias_aereo=da, dias_terrestre=dt, nota=nota or None, precos=p, link=r.get('url'))

idx = {'gerado_em': AGORA.isoformat(timespec='seconds'), 'roteiros': {}}
total = 0
for chave, nome_site, nome, cor, rota in ROT:
    rs = sorted([r for r in L if (r.get('nome') or '').strip() == nome_site and futura(quando(r))], key=lambda r: (quando(r)[:2], quando(r)[2] or 99))
    assert rs, f'{chave}: nenhuma saída no site — nada foi publicado'
    rows, dados = zip(*(linha(r) for r in rs))
    n = len(rows); total += n
    HH = (TOPO - 30) + CAB + n * RH + 18 + (PE - 20)
    sem = sum(1 for x in dados if not x['precos'])
    anos = sorted({quando(r)[0] for r in rs})
    qt = f'{e(rota)} · <b>{n} saída{"s" if n > 1 else ""}</b> · valores por pessoa, em 12x sem juros'
    corpo = (f'<div class="sb">LIELU TURISMO · EUROPA DO LESTE {"–".join(map(str, anos))}</div><div class="tt">{AV}PARTIDAS</div>'
             f'<div class="ro"><i style="background:{cor}"></i>{e(nome)}</div><div class="qt">{qt}</div>'
             f'<div class="bd"><div class="hd"><span>DIA</span><span>DURAÇÃO</span><span>TERRESTRE</span><span class="a">TERRESTRE + AÉREO<br>+ SEGURO</span></div>'
             + ''.join(rows) + '</div>'
             f'<div class="ft"><b>Valores por pessoa, em apartamento duplo.</b> Parcelas sem juros, fixas em reais, sem variação cambial. '
             f'Seguro incluso até 70 anos. Valores de {HOJE:%d/%m/%Y}, sujeitos a alteração sem{NB}aviso{NB}prévio.</div>')
    css = CSS % (HH, TOPO - 30, PE - 20, CAB, RH)
    h = os.path.join(OUT, chave + '.html'); png = h[:-5] + '.png'
    open(h, 'w').write(f'<!doctype html><html><head><meta charset="utf-8"><style>{css}</style></head><body>{corpo}</body></html>')
    subprocess.run([CHROME, '--headless=new', '--no-sandbox', '--disable-gpu', '--hide-scrollbars', '--force-device-scale-factor=1',
                    f'--window-size=1080,{HH}', '--virtual-time-budget=10000', f'--screenshot={png}', 'file://' + h],
                   capture_output=True, check=True, timeout=120)
    os.remove(h)
    assert os.path.getsize(png) > 50_000, f'imagem vazia: {png}'
    idx['roteiros'][chave] = dict(arquivo=f'europa-do-leste-2027/{chave}.png', roteiro=nome, rota=rota, saidas=list(dados))
    print(f'{chave:19} {n:>2} saídas ({sem} sem preço)  {HH}px', flush=True)
assert total >= 15, f'só {total} saídas: leitura do site incompleta'
json.dump(idx, open(os.path.join(OUT, 'index.json'), 'w'), ensure_ascii=False, indent=1)
print(total, 'saídas em', OUT)
