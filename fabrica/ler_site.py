# Lê AGORA todas as saídas do site da Lielu (preço terrestre duplo e completo duplo) e grava um JSON.
# Página que demora é tentada de novo (o site às vezes fica lento). Só biblioteca padrão do Python.
# uso: python3 ler_site.py site_hoje.json
import json, os, re, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gerar

OUT = os.path.abspath(sys.argv[1])
gerar.CACHE = os.path.join(os.path.dirname(OUT), 'cache_site')


def parse(p):
    """'entrada R$ 7.584 + 12× R$ 2.528 (total R$ 37.920)' → {total, entrada, parcela}"""
    m = re.match(r"entrada R\$ ([\d.]+) \+ (\d+)× R\$ ([\d.]+) \(total R\$ ([\d.]+)\)", p or '')
    if not m:
        return None
    n = lambda v: int(v.replace('.', ''))
    t, e, k, pa = n(m.group(4)), n(m.group(1)), int(m.group(2)), n(m.group(3))
    assert k == 12 and e + 12 * pa == t, p
    return dict(total=t, entrada=e, parcela=pa)


def tentar(f, *a):
    for tent in range(4):
        try:
            return f(*a)
        except Exception as ex:
            print('tentando de novo:', ex, flush=True)
            time.sleep(5 * (tent + 1))
    raise RuntimeError('o site não respondeu')


urls = tentar(gerar.urls_de_saida, False)
L = []
for u in urls:
    for d in tentar(gerar.ler_todas, [u], False):
        L.append(dict(slug=d['slug'], url=d.get('url'), nome=d['nome'], data=d['data_curta'], dias=d['dias'],
                      dias_aereo=d['dias_aereo'] or d['dias'], atualizado=d['atualizado_site'],
                      terrestre=parse(d['precos'].get(('terrestre', 'Duplo'))),
                      completo=parse(d['precos'].get(('aereo', 'Duplo')))))
json.dump(L, open(OUT, 'w'), ensure_ascii=False, indent=1)
print(len(urls), 'páginas,', len(L), 'saídas →', OUT)
