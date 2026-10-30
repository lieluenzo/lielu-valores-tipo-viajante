# Fábrica diária (30/10/2026): lista do dia do funil "Data de Viagem" (promosdeviagem.com.br/datadeviagem/).
# uso: python3 fabrica/saidas_dv.py dados/site_hoje.json publico   → publico/saidas_dv.json
# Base fixa: fabrica/dv_base.json (95 saídas de 22/10, classificadas: destino, cat, multi, pool, selo, dias).
# Todo dia: só fica saída que existe no site HOJE (index.json da fábrica), com a parcela 12x do dia
# (terrestre e completo). Saída de 2027 nova no site que é do MESMO roteiro de uma da base herda a classificação.
# Fora: ano ≠ 2027, mês corrente e passadas (a página também filtra).
import json, os, re, sys, datetime
SITE, PUB = sys.argv[1], sys.argv[2]
AQUI = os.path.dirname(os.path.abspath(__file__))
idx = json.load(open(os.path.join(PUB, 'index.json')))['saidas']
base = json.load(open(os.path.join(AQUI, 'dv_base.json')))['saidas']
site = {}
try:
    for r in json.load(open(SITE)): site[r['slug']] = r
except Exception as e:
    print('site_hoje ilegível:', e)
MES = ['', 'jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
hoje = datetime.date.today()
def ok_data(ano, mes):
    return ano == 2027 and (ano, mes) > (hoje.year, hoje.month)

saidas, vistos = [], set()
for s in base:
    v = idx.get(s['slug'])
    if not v:
        print('saiu do site, fica fora:', s['slug']); continue
    if not ok_data(s['ano'], s['mes']): continue
    n = dict(s)
    n['parcela_12x_terrestre'] = v['terrestre']['parcela']
    n['parcela_12x_aereo'] = v['completo']['parcela']
    saidas.append(n); vistos.add(s['slug'])

# saídas novas de 2027 do mesmo roteiro de alguma da base (o índice dá o nome curto do roteiro)
familia = {}
for s in base:
    v = idx.get(s['slug'])
    if v: familia.setdefault(v['roteiro'], s)
# saída antiga que saiu do site: a família vem pelo nome do roteiro gravado na base
for s in base:
    familia.setdefault((s.get('nome_site') or '').split(' (')[0].strip(), s)
for slug, v in idx.items():
    if slug in vistos: continue
    m = re.match(r'(\d\d)/(\d\d)/(\d{4})$', v.get('data', ''))
    if not m: continue
    dia, mes, ano = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if not ok_data(ano, mes): continue
    mod = familia.get(v['roteiro'])
    pid = (site.get(slug) or {}).get('id')
    if not mod or not pid:
        print('nova sem classificação, fica fora:', slug, v['roteiro']); continue
    n = dict(mod)
    dif = (mod['dias_aereo'] or 0) - (mod['dias_terrestre'] or 0)
    st = site.get(slug) or {}
    da = int(st.get('dias_aereo') or v['dias'])
    dt = int(st['dias_terrestre']) if str(st.get('dias_terrestre') or '').isdigit() else max(1, da - dif)
    n.update(id_site=int(pid), slug=slug, link=v['link'], saida='%02d/%s/%d' % (dia, MES[mes], ano), ano=ano, mes=mes, dia=dia,
             dias_aereo=da, dias_terrestre=dt, nome_site=(site.get(slug) or {}).get('nome') or mod['nome_site'],
             parcela_12x_terrestre=v['terrestre']['parcela'], parcela_12x_aereo=v['completo']['parcela'], selo=None)
    print('nova incluída:', slug, 'como', mod['slug'])
    saidas.append(n)

ids = [s['id_site'] for s in saidas]
assert len(ids) == len(set(ids)), 'id_site repetido'
assert len(saidas) >= 10, 'lista curta demais'
for s in saidas:
    assert s['parcela_12x_terrestre'] > 0 and s['parcela_12x_aereo'] > 0, s['slug']
    assert s['link'].startswith('https://lieluturismo.com.br/'), s['slug']
saidas.sort(key=lambda s: (s['ano'], s['mes'], s['dia'] or 0, s['id_site']))
out = {'versao': 1, 'gerado_em': hoje.isoformat(), 'saidas': saidas}
json.dump(out, open(os.path.join(PUB, 'saidas_dv.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
print('saidas_dv.json:', len(saidas), 'saídas')
