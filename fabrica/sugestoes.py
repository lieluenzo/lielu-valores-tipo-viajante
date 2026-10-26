# Fábrica diária (26/10/2026): sugestões da página do funil Tipo de Viajante, só com saídas que existem no site HOJE.
# Mesmas regras do gerar_ramificacoes_v2.py de 23/10 (Bruno). Saída que saiu do site fica fora; o ramo completa com a próxima.
# uso: python3 fabrica/sugestoes.py dados/site_hoje.json publico   → publico/sugestoes.json
# Faixas iguais para os 3 perfis:
#   Terrestre (preço terrestre duplo): Até 20 mil · 20 a 25 · 25 a 30 · Acima de 30
#   Terrestre + Aéreo + Seguro (preço completo duplo): Até 20 mil · 20 a 30 · 30 a 40 · Acima de 40
#   "Até 20 mil" com aéreo: nenhuma saída custa isso; mostra as 6 mais baratas (com aviso "um pouco acima").
# 6 cards por ramo, um por roteiro, do mais barato para o mais caro.
# Iniciante e Intermediário: posição 1 = Turquia mais barata, posição 2 = Europa do Leste mais barata,
#   sempre — se não houver dentro da faixa/período, entra a mais perto (com aviso).
# Experiente: só do mais barato para o mais caro. Perfil nunca é relaxado (só o pool do perfil).
# Preços: índice do dia da fábrica (https://lieluenzo.github.io/lielu-valores-tipo-viajante/index.json).
import csv, json, re, sys, urllib.request, datetime

import os
SITE, PUB = sys.argv[1], sys.argv[2]
IDX_URL = 'index.json do dia'
idx = json.load(open(os.path.join(PUB, 'index.json')))
links = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ref', 'ids_links.json')))
site = {r['slug']: r for r in json.load(open(SITE))}   # nome completo da página

MES = {m: i for i, m in enumerate(['', 'jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'])}
S = []
for b in csv.DictReader(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ref', 'saidas_2027_do_brief.csv'))):
    slug = links[b['id_site']].rstrip('/').split('/')[-1]
    v = idx['saidas'].get(slug)
    if not v:
        print('sem preço hoje, fica fora:', b['roteiro'], b['saida']); continue
    m = re.match(r'(?:\d\d/)?([a-z]{3})/(\d{4})$', b['saida'])
    S.append(dict(id_site=int(b['id_site']), roteiro=b['roteiro'], saida=b['saida'], dias=int(b['dias']), selo=b['selo'] or None,
                  nome_site=site.get(slug, {}).get('nome') or v['roteiro'], link=links[b['id_site']],
                  perfis=b['perfis'], mes=(int(m.group(2)), MES[m.group(1)]),
                  T=v['terrestre']['total'], A=v['completo']['total']))
# a mesma saída pode aparecer 2x no brief (Grã-Bretanha 06/jun): fica uma por link
S = list({s['link']: s for s in S}.values())

POOL = {'INI': 'I', 'INT': 'M', 'EXP': 'E'}
FAIXAS = {'T': [('Até R$ 20 mil', 0, 20000), ('De R$ 20 mil a R$ 25 mil', 20000, 25000),
                ('De R$ 25 mil a R$ 30 mil', 25000, 30000), ('Acima de R$ 30 mil', 30000, 10**9)],
          'A': [('Até R$ 20 mil', 0, 20000), ('De R$ 20 mil a R$ 30 mil', 20000, 30000),
                ('De R$ 30 mil a R$ 40 mil', 30000, 40000), ('Acima de R$ 40 mil', 40000, 10**9)]}
PERIODOS = {'JAN-MAR27': (1, 3), 'ABR-JUN27': (4, 6), 'JUL-SET27': (7, 9), 'OUT-DEZ27': (10, 12), 'FLEX': (1, 12)}
NOME_PER = {'JAN-MAR27': 'Jan–Mar/27', 'ABR-JUN27': 'Abr–Jun/27', 'JUL-SET27': 'Jul–Set/27', 'OUT-DEZ27': 'Out–Dez/27', 'FLEX': 'Flexível'}
TURQUIA = lambda s: s['roteiro'].startswith('Turquia')
LESTE = lambda s: s['roteiro'].startswith('Europa do Leste')
N = 6

def escolher(perfil, dentro, distancia, preco, aviso_fora):
    """6 cards: [Turquia, Europa do Leste] (INI/INT) + roteiros diferentes, do mais barato.
    dentro(s) = cabe no pedido; distancia(s) = quão longe está do pedido (0 = dentro)."""
    pool = [s for s in S if POOL[perfil] in s['perfis']]
    chave = lambda s: (distancia(s), preco(s), s['mes'])
    cards, usados = [], set()
    def por(s, fora):
        usados.add(s['roteiro'])
        c = {k: s[k] for k in ('id_site', 'roteiro', 'saida', 'dias', 'selo', 'nome_site', 'link')}
        c['fora_do_pedido'] = fora
        if fora: c['aviso'] = aviso_fora(s)
        cards.append(c)
    if perfil in ('INI', 'INT'):
        for fam in (TURQUIA, LESTE):
            cand = sorted((s for s in pool if fam(s)), key=chave)
            if cand: por(cand[0], not dentro(cand[0]))
    resto = [s for s in pool if not TURQUIA(s) and not LESTE(s)] if perfil in ('INI', 'INT') else pool
    for s in sorted([s for s in resto if dentro(s)], key=lambda s: (preco(s), s['mes'])) + \
             sorted([s for s in resto if not dentro(s)], key=chave):
        if len(cards) == N: break
        if s['roteiro'] in usados: continue
        por(s, not dentro(s))
    return cards

ramos = {}
for per in POOL:
    for cod, (m1, m2) in PERIODOS.items():
        if per == 'EXP' and cod == 'OUT-DEZ27': continue          # a página esconde Out–Dez para o Experiente
        ate = lambda s, m1=m1, m2=m2: m1 <= s['mes'][1] <= m2 and s['mes'][0] == 2027
        dist = lambda s, m1=m1, m2=m2: 0 if ate(s) else min(abs(s['mes'][1] - m1), abs(s['mes'][1] - m2)) + 12 * abs(s['mes'][0] - 2027)
        ramos[f'D-{per}-{cod}'] = {'caminho': 'data', 'perfil': per, 'periodo': NOME_PER[cod],
                                   'cards': escolher(per, ate, dist, lambda s: s['T'],
                                                     lambda s: 'Saída próxima ao período que você escolheu')}
    for pac, fx in FAIXAS.items():
        for k, (rot, lo, hi) in enumerate(fx, 1):
            dentro = lambda s, pac=pac, lo=lo, hi=hi: lo < s[pac] <= hi
            dist = lambda s, pac=pac, lo=lo, hi=hi: 0 if dentro(s) else (s[pac] - hi if s[pac] > hi else lo - s[pac])
            aviso = lambda s, pac=pac, hi=hi: ('Um pouco acima da faixa que você escolheu' if s[pac] > hi
                                               else 'Um pouco abaixo da faixa que você escolheu')
            ramos[f'V-{per}-{pac}{k}'] = {'caminho': 'valor', 'perfil': per, 'pacote': pac, 'faixa': rot,
                                          'cards': escolher(per, dentro, dist, lambda s, pac=pac: s[pac], aviso)}

assert all(len(r['cards']) == N for r in ramos.values()), [k for k, r in ramos.items() if len(r['cards']) != N]
out = {'versao': 2, 'gerado_em': datetime.date.today().isoformat(),
       'fonte': f"regras do Bruno 23/10 + preços do índice {idx['versao']} ({IDX_URL})",
       'regras': 'Ordem dos cards = ordem de exibição (1 Turquia, 2 Europa do Leste para Iniciante/Intermediário; depois do mais barato). '
                 'Card com fora_do_pedido=true traz o texto em "aviso". Só saídas com preço no site hoje.', 'versao_imagens': idx['versao'],
       'faixas': {f'{p}-{per}': [f[0] for f in FAIXAS[p]] for p in FAIXAS for per in POOL},
       'ramos': ramos}
json.dump(out, open(os.path.join(PUB, 'sugestoes.json'), 'w'), ensure_ascii=False, indent=1)
print('ramos', len(ramos), 'cards', sum(len(r['cards']) for r in ramos.values()))
