# Fábrica diária (30/10/2026): lista do dia do funil "China" (promosdeviagem.com.br/china/).
# uso: python3 fabrica/saidas_china.py dados/site_hoje.json publico   → publico/saidas_china.json (+ china_pendencias.json)
# Base fixa: fabrica/china_base.json (brief do funil: 6 roteiros, ordem 6.1, tetos, mapa id_site → roteiro_id).
# Todo dia: só fica saída que existe no site HOJE, com parcela/entrada 12x e dias do site. O roteiro vem SEMPRE do mapa
# (id_site → roteiro_id), nunca do slug nem do título. Saída da China no site que não está no mapa NÃO entra: vai para
# china_pendencias.json (o Bruno mapeia). Saída sem preço no site = "sob consulta" (parcelas null).
import json, os, sys, datetime
SITE, PUB = sys.argv[1], sys.argv[2]
AQUI = os.path.dirname(os.path.abspath(__file__))
base = json.load(open(os.path.join(AQUI, 'china_base.json')))
site = json.load(open(SITE))
por_id = {}
for r in site:
    if r.get('id') is not None: por_id[int(r['id'])] = r
mapa = {int(k): v for k, v in base['mapa_id_site_roteiro'].items()}
rot_nome = {r['roteiro_id']: r for r in base['roteiros']}

saidas, fora, avisos = [], [], []
for s in base['saidas']:
    r = por_id.get(s['id_site'])
    if not r:
        fora.append({'id_site': s['id_site'], 'slug': s['slug'], 'motivo': 'saiu do site'}); continue
    if mapa.get(s['id_site']) != s['roteiro_id']:
        raise SystemExit('base inconsistente com o mapa: %s' % s['slug'])
    n = dict(s)
    n['slug'] = r['slug']
    if r.get('url') and r['url'].startswith('https://lieluturismo.com.br/'): n['link'] = r['url']
    da = r.get('dias_aereo') or s['dias_aereo']; dt = r.get('dias_terrestre') or s['dias_terrestre']
    n['dias_aereo'] = int(da); n['dias_terrestre'] = int(dt)
    t, c = r.get('terrestre'), r.get('completo')
    if t and c:
        n.update(sob_consulta=False, parcela_12x_terrestre=t['parcela'], parcela_12x_aereo=c['parcela'],
                 entrada_terrestre=t['entrada'], entrada_aereo=c['entrada'])
    else:
        if not s['sob_consulta']: avisos.append('perdeu o preço no site (virou sob consulta): ' + s['slug'])
        n.update(sob_consulta=True, parcela_12x_terrestre=None, parcela_12x_aereo=None, entrada_terrestre=None, entrada_aereo=None)
    saidas.append(n)

# saída da China no site que não está no mapa → pendência para o Bruno (não entra no funil)
pend = []
vistos = {s['id_site'] for s in base['saidas']}
for i, r in por_id.items():
    if i in vistos: continue
    if i in mapa or (r.get('slug') or '').startswith('china') or 'china' in (r.get('nome') or '').lower():
        pend.append({'id_site': i, 'slug': r.get('slug'), 'nome': r.get('nome'), 'data': r.get('data')})

assert len(saidas) >= 6, 'menos de 6 saídas da China no site: lista não publicada (a página usa a embutida)'
ids = [s['id_site'] for s in saidas]; assert len(ids) == len(set(ids))
for s in saidas:
    assert s['link'].startswith('https://lieluturismo.com.br/'), s['slug']
    if not s['sob_consulta']:
        assert s['parcela_12x_terrestre'] > 0 and s['parcela_12x_aereo'] > 0, s['slug']
saidas.sort(key=lambda s: (s['ano'], s['mes'], s['dia'] or 99, s['id_site']))
roteiros = []
for r in base['roteiros']:
    n = dict(r); n['saidas'] = [s['id_site'] for s in saidas if s['roteiro_id'] == r['roteiro_id']]
    roteiros.append(n)
out = {'versao': 1, 'gerado_em': datetime.date.today().isoformat(), 'faixas': base['faixas'], 'ordem': base['ordem'],
       'mapa_id_site_roteiro': base['mapa_id_site_roteiro'], 'roteiros': roteiros, 'saidas': saidas}
os.makedirs(PUB, exist_ok=True)
json.dump(out, open(os.path.join(PUB, 'saidas_china.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
json.dump({'gerado_em': out['gerado_em'], 'fora_do_funil': fora, 'sem_mapa': pend, 'avisos': avisos},
          open(os.path.join(PUB, 'china_pendencias.json'), 'w'), ensure_ascii=False, indent=1)
print('saidas_china.json:', len(saidas), 'saídas;', sum(1 for s in saidas if s['sob_consulta']), 'sob consulta; fora:', len(fora), '; sem mapa:', len(pend), avisos)
