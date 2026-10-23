#!/usr/bin/env python3
"""Gera a base de roteiros da Lielu para o agente de IA da Clint.

Lê as páginas de saída do site lieluturismo.com.br e escreve um HTML de texto puro
por destino, sem abas, fotos ou scripts, com todas as seções de cada saída abertas.

Uso:
    python3 gerar.py china            # saídas cujo endereço começa com "china"
    python3 gerar.py china --cache    # reaproveita as páginas já baixadas hoje
"""
import datetime
import html
import os
import re
import sys
import time
import urllib.request

SITE = "https://lieluturismo.com.br"
LISTA = SITE + "/viagens-lielu-turismo/"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/128 Safari/537.36"
AQUI = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(AQUI, "cache")
SAIDA = os.path.join(AQUI, "saida")

# Seções da página de saída, na ordem em que aparecem (âncoras do menu interno do site).
SECOES = ["home", "roteiro", "inclui", "diferenciais", "detalhes", "bloqueio", "valor", "contato"]

MESES = {"JANEIRO": 1, "FEVEREIRO": 2, "MARÇO": 3, "MARCO": 3, "ABRIL": 4, "MAIO": 5, "JUNHO": 6,
         "JULHO": 7, "AGOSTO": 8, "SETEMBRO": 9, "OUTUBRO": 10, "NOVEMBRO": 11, "DEZEMBRO": 12}
MES_ABREV = {"JAN": 1, "FEV": 2, "MAR": 3, "ABR": 4, "MAI": 5, "JUN": 6,
             "JUL": 7, "AGO": 8, "SET": 9, "OUT": 10, "NOV": 11, "DEZ": 12}


def reais(v):
    return "R$ " + f"{v:,}".replace(",", ".")


def preco(t):
    """'Entrada de R$ 8.327 + 12 x iguais de R$ 2.776 cada' -> texto com o total somado."""
    m = re.search(r"Entrada de R\$\s*([\d.]+)\s*\+\s*(\d+)\s*x iguais de R\$\s*([\d.]+)", t)
    if not m:
        return "sob consulta" if "consulta" in t.lower() else t
    entrada, n, parcela = int(m.group(1).replace(".", "")), int(m.group(2)), int(m.group(3).replace(".", ""))
    return f"entrada {reais(entrada)} + {n}× {reais(parcela)} (total {reais(entrada + n * parcela)})"


# Arquivo de cada destino: (nome do arquivo, nome exibido, regex no endereço da saída).
# O endereço nem sempre bate com o roteiro (ex.: "italia-do-norte-abr2027" é a Itália Clássica), por isso o
# agrupamento é por destino, do jeito que o cliente pergunta, e não por roteiro.
DESTINOS = [
    ("6-paises-alpes", "6 Países – Alpes Europeus", r"6paises"),
    ("africa-do-sul", "África do Sul", r"africa-do-sul"),
    ("aurora-boreal", "Aurora Boreal na Noruega", r"aurora-boreal"),
    ("bulgaria-e-romenia", "Bulgária e Romênia", r"bulgaria"),
    ("china", "China", r"china"),
    ("coreia-do-sul", "Coreia do Sul", r"coreia"),
    ("croacia-e-balcas", "Croácia e Bálcãs (De Veneza a Dubrovnik; Croácia, Eslovênia e Bósnia)", r"(croacia|de-veneza-a-dubrovnik)"),
    ("egito", "Egito", r"egito"),
    ("emirados-arabes", "Emirados Árabes (Dubai, Sharjah e Abu Dhabi)", r"dubai"),
    ("escandinavia", "Escandinávia", r"escandinavia"),
    ("espanha", "Espanha (inclui Espanha do Sul e Marrocos)", r"espanha"),
    ("europa-do-leste", "Europa do Leste", r"europa-do-leste"),
    ("franca", "França (De Bordeaux a Paris)", r"de-bordeaux"),
    ("grecia", "Grécia", r"grecia"),
    ("india-e-nepal", "Índia e Nepal", r"india"),
    ("italia", "Itália", r"(italia|encantos-da-italia|sul-da-italia)"),
    ("japao", "Japão", r"japao"),
    ("keukenhof-e-benelux", "Keukenhof – Holanda, Bélgica, Luxemburgo, França e Alemanha", r"(keukenhof|hol-ale-fra-lux-bel)"),
    ("marrocos", "Marrocos", r"marrocos"),
    ("portugal", "Portugal (inclui Portugal, Espanha, França e Andorra)", r"portugal"),
    ("reino-unido", "Reino Unido – Inglaterra, Escócia e País de Gales", r"(reino-unido|inglaterra)"),
    ("suica", "Suíça (inclui Suíça e Itália)", r"suica"),
    ("tailandia", "Tailândia", r"tailandia"),
    ("tunisia", "Tunísia", r"tunisia"),
    ("turquia", "Turquia com Ilha Grega Chios", r"turquia"),
]

# ---------------------------------------------------------------- download

def baixar(url, arquivo, usar_cache):
    if usar_cache and os.path.exists(arquivo):
        return open(arquivo, encoding="utf-8", errors="ignore").read()
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        s = r.read().decode("utf-8", errors="ignore")
    os.makedirs(os.path.dirname(arquivo), exist_ok=True)
    open(arquivo, "w", encoding="utf-8").write(s)
    time.sleep(1)
    return s


# ---------------------------------------------------------------- html -> texto

def texto(seg):
    seg = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", "", seg, flags=re.S)
    seg = re.sub(r"<!--.*?-->", "", seg, flags=re.S)
    seg = re.sub(r"<br\s*/?>", "\n", seg)
    seg = re.sub(r"</(p|div|li|h[1-6]|tr|ul|ol|table)>", "\n", seg)
    seg = re.sub(r"<(td|th)[^>]*>", " | ", seg)
    seg = re.sub(r"<[^>]+>", "", seg)
    seg = html.unescape(seg).replace("\xa0", " ")
    linhas = []
    for l in seg.split("\n"):
        l = re.sub(r"[ \t]+", " ", l).strip()
        l = re.sub(r"^(\|\s*)+", "", l).strip()          # sobra das células de tabela
        if l and l != "|":
            linhas.append(l)
    return linhas


# Títulos que abrem cada seção no corpo da página, na ordem em que aparecem. A separação é feita pelo texto,
# e não pelas âncoras, porque há páginas com âncora faltando ou no lugar errado.
MARCAS = [
    ("selo", lambda l: l.startswith("Esta viagem é operada pela Lielu Turismo")),
    ("inclui", lambda l: l.startswith("Nosso pacote INCLUI")),
    ("diferenciais", lambda l: l.startswith("Diferenciais que incluímos")),
    ("detalhes", lambda l: l.startswith("Detalhes deste Roteiro")),
    ("nao_inclui", lambda l: l.startswith("Nosso pacote NÃO INCLUI")),
    ("observacoes", lambda l: l.rstrip(":") == "Observações"),
    ("bloqueio", lambda l: l.startswith("Bloqueio Aéreo")),
    ("valor", lambda l: l.startswith("VALORES")),
    ("fim", lambda l: l.startswith("Galeria de fotos")),
]

# Texto institucional do selo Lielu, igual em todas as páginas (fica de fora da base)
SELO = ("Esta viagem é operada pela Lielu Turismo", "Para quem já nos conhece", "O selo não indica",
        "Mas, sobretudo, esse selo")


def secoes(s):
    # No "Custo no Destino" o nível é marcado pela cor: os "$" em cinza são os que faltam até 5.
    s = re.sub(r'<span style="color:\s*#999999;?">(\$+)', lambda m: "⟨" + m.group(1) + "⟩", s)
    ini = s.find('id="roteiro"')
    if ini < 0:
        raise ValueError("seção 'roteiro' não encontrada")
    ini = s.rfind("<", 0, ini)
    fim = next((s.rfind("<", 0, p) for p in (s.find('id="contato"'), s.find('id="footer"')) if p > ini), len(s))
    S = {"home": texto(s[:ini])}
    corpo = texto(s[ini:fim])
    S["_corpo"] = corpo
    atual, S["roteiro"], k = "roteiro", [], 0
    for l in corpo:
        # Bloco de experiências em destaque: aparece depois do selo ou no fim da página, conforme a saída
        if l.startswith("Clique abaixo para ver as experiências"):
            atual = "destaques"
            S.setdefault(atual, []).append(l)
            continue
        if atual == "destaques" and l.startswith("Compartilhe este roteiro"):
            atual = "fim"
        prox = next((j for j in range(k, len(MARCAS)) if MARCAS[j][1](l)), None)
        if prox is not None:
            atual, k = MARCAS[prox][0], prox + 1
            S.setdefault(atual, [])
            if atual == "selo":
                S[atual].append(l)
            continue
        if atual == "selo" and not l.startswith(SELO):
            atual = "destaques"  # bloco "Clique abaixo para ver as experiências que incluímos..." depois do selo
        S.setdefault(atual, []).append(l)
    S.setdefault("destaques", [])
    for nome, _ in MARCAS:
        S.setdefault(nome, [])
    return S


def ate(linhas, marcador):
    for i, l in enumerate(linhas):
        if l.startswith(marcador):
            return linhas[:i]
    return linhas


def itens(linhas, marca):
    """Uma linha = um item, sem a marca (√ ou •). Linhas sem marca (ex.: "Ingressos:") viram item próprio."""
    return [re.sub("^" + re.escape(marca) + r"\s*", "", l) for l in linhas if l.strip() not in ("", marca)]


def refeicoes_do_dia(titulo):
    """Refeições além do café da manhã, pelo que está entre parênteses no título do dia.
    "+ 1 refeição, a definir" = 1 · "e jantar especial" = 1 · "almoço e jantar" = 2 · "pensão completa" = 2 · "meia pensão" = 1
    """
    m = re.search(r"\(([^()]*)\)\s*$", titulo)
    if not m:
        return 0
    p = m.group(1).lower()
    if "pensão completa" in p:
        return 2
    if "meia pensão" in p:
        return 1
    n = sum(int(x) for x in re.findall(r"(\d+)\s*refeiç", p))
    return n + p.count("almoço") + p.count("jantar")


# ---------------------------------------------------------------- leitura de uma saída

def ler_saida(url, s):
    S = secoes(s)
    d = {"url": url, "slug": url.rstrip("/").split("/")[-1]}

    # Cabeçalho: depois do menu interno ("Mais informações") até "Galeria de Fotos"
    h = S["home"]
    i = max(k for k, l in enumerate(h) if l == "Mais informações")
    cab = ate(h[i + 1:], "Galeria de Fotos")
    d["nome"] = cab[0]
    resto = cab[1:]
    d["pais"] = resto.pop(0).strip("()") if resto and resto[0].startswith("(") else ""
    d["visitando"] = d["dias"] = d["data_saida"] = ""
    desc = []
    for l in resto:
        m = re.match(r"(\d+)\s*dias\s*[–-]\s*saída:\s*(.+)", l, re.I)
        if l.startswith("Visitando:"):
            d["visitando"] = l.split(":", 1)[1].strip()
        elif m:
            d["dias"], d["data_saida"] = m.group(1), m.group(2).strip()
        else:
            desc.append(l)
    d["descricao"] = desc
    # Linha interna do site com o nome, a data e o ID da viagem (logo antes das 6 abas do menu)
    titulo = h[i - 6] if i >= 6 else ""
    m = re.search(r"\bID\s*(\d+)", titulo)
    d["id"] = m.group(1) if m else ""
    m = re.search(r'class="updated[^"]*">(\d{4})-(\d{2})-(\d{2})', s)
    d["atualizado_site"] = f"{m.group(3)}/{m.group(2)}/{m.group(1)}" if m else ""

    m = re.match(r"(?:(\d{1,2})/)?([A-ZÇ]+)/(\d{4})", d["data_saida"].upper())
    if m and m.group(1):
        d["ordem"] = (int(m.group(3)), MESES.get(m.group(2), 0), int(m.group(1)))
        d["data_curta"] = f"{int(m.group(1)):02d}/{MESES.get(m.group(2), 0):02d}/{m.group(3)}"
    elif m:  # só mês e ano: o dia ainda não foi definido no site
        d["ordem"] = (int(m.group(3)), MESES.get(m.group(2), 0), 99)
        d["data_curta"] = f"{m.group(2).lower()}/{m.group(3)} (dia a definir)"
    else:
        d["ordem"], d["data_curta"] = (9999, 0, 0), d["data_saida"]

    # Dia a dia
    rot = S["roteiro"]
    dias, aviso, intro = [], None, []
    for l in rot:
        if re.match(r"^(\d{1,2}º?/[A-ZÇ]{3,}|\d{1,2}º\s*DIA)\s*[–-]", l):
            dias.append({"titulo": l, "aviso": aviso, "texto": []})
            aviso = None
        elif l.startswith("CONSIDERAR ") and l.isupper():
            aviso = l
        elif dias:
            dias[-1]["texto"].append(l)
        else:
            intro.append(l)
    d["dias_roteiro"], d["intro_roteiro"] = dias, intro

    # Inclui e diferenciais
    d["inclui"] = itens(S["inclui"], "√")
    d["diferenciais"] = [x for x in itens(S["diferenciais"], "√")
                         if not x.startswith("além das muitas atividades que não necessitam de ingressos")]
    d["destaques"] = [x for x in S["destaques"]
                      if not x.startswith(("Clique abaixo para ver as experiências", "Veja mais experiências"))]
    d["dias_aereo"] = d["dias_terrestre"] = ""
    for it in d["diferenciais"]:
        m = re.match(r"(\d+) dias de viagem para pacote (com parte aérea|somente da parte terrestre)", it)
        if m:
            d["dias_aereo" if "aérea" in m.group(2) else "dias_terrestre"] = m.group(1)

    # Detalhes: clima/custo, não inclui, observações
    escala, info = {}, []
    for l in S["detalhes"]:
        m = re.match(r"^(\$+)(?:⟨(\$+)⟩)?\s*[–-]\s*(.+)$", l)
        if m:
            escala[len(m.group(1))] = m.group(3)
        elif l.startswith("Escala"):
            continue
        else:
            info.append(l)
    detalhes = []
    for l in info:  # cada linha é um item: os "•" e as linhas soltas ("Aconselhamos levar...", "Observações Gerais...")
        l = re.sub(r"^•\s*", "", l)
        m = re.match(r"Custo no Destino:\s*(\$+)(?:⟨(\$+)⟩)?", l)
        if m:
            nivel = len(m.group(1))
            faixa = escala.get(nivel, "")
            l = (f"Custo no destino (gastos pessoais por dia): nível {nivel} de 5" + (f" – {faixa}" if faixa else "")
                 + " " + l[m.end():].strip())
        detalhes.append(l.strip())
    d["detalhes"] = detalhes
    d["nao_inclui"] = itens(S["nao_inclui"], "•")
    d["observacoes"] = itens(S["observacoes"], "•")

    # Aéreo e hotéis
    bl = S["bloqueio"]
    d["cia"] = next((l.split(":", 1)[1].strip() for l in bl if l.startswith("Companhia")), "")
    k_cia = next((k for k, l in enumerate(bl) if l.startswith("Companhia")), 0)
    k_fim = next((k for k, l in enumerate(bl) if l.startswith("Bloqueios aéreos contratados")), len(bl))
    d["voos"] = [l for l in bl[k_cia + 1:k_fim] if l != "Voos"]
    d["aviso_voos"] = bl[k_fim] if k_fim < len(bl) else ""
    # Hotéis: há página com duas listas ("Hotéis Previstos" repetido) e com o título escrito "Hotéis Pevistos"
    listas = []
    for k_hot in [k for k, l in enumerate(bl) if l.startswith("Hotéis P")]:
        hot = ate(bl[k_hot + 1:], "Reserva-se o direito")
        listas.append([l for l in hot if l.replace(" ", "") != "Data|Hotel|Cidade|País"])
    d["hoteis"] = listas[0] if listas else []
    d["hoteis_outras"] = [x for x in listas[1:] if x != d["hoteis"]]
    d["aviso_hoteis"] = next((l for l in bl if l.startswith("Reserva-se o direito")), "")

    # Valores: junta "Duplo:" + "Entrada de ..." + "+ 12 x ..."
    val = S["valor"]
    out, k = [], 0
    while k < len(val):
        l = val[k]
        if l.endswith(":") and k + 1 < len(val) and val[k + 1].startswith("Entrada"):
            linha = f"{l} {val[k + 1]}"
            if k + 2 < len(val) and val[k + 2].startswith("+"):
                linha += " " + val[k + 2]
                k += 1
            if "SOB CONSULTA" in linha:
                linha = f"{l} sob consulta"
            out.append(linha)
            k += 2
        else:
            out.append(l)
            k += 1
    d["valores"] = out

    # Preços por pacote e tipo de quarto, para o quadro geral
    d["precos"], pacote = {}, None
    for l in out:
        # "Preço por pessoa SEM/COM parte aérea" aparece em todas as páginas; o título "PACOTE COMPLETO" nem sempre
        if l.startswith("Preço por pessoa SEM parte aérea"):
            pacote = "terrestre"
        elif l.startswith("Preço por pessoa COM parte aérea"):
            pacote = "aereo"
        m = re.match(r"(Duplo|Individual|Triplo):\s*(.*)", l)
        if pacote and m:
            d["precos"][(pacote, m.group(1))] = preco(m.group(2))

    # Retorno ao Brasil = saída + dias do pacote com aéreo - 1 (conferido com o último dia do roteiro)
    d["retorno"] = d["retorno_roteiro"] = ""
    if m_data := re.match(r"(\d{2})/(\d{2})/(\d{4})$", d["data_curta"]):
        ini = datetime.date(int(m_data.group(3)), int(m_data.group(2)), int(m_data.group(1)))
        fim = ini + datetime.timedelta(days=int(d["dias_aereo"] or d["dias"]) - 1)
        d["retorno"] = fim.strftime("%d/%m/%Y")
    d["inicio_roteiro"] = ""
    if dias and d["retorno"] and (m := re.match(r"(\d{1,2})/([A-ZÇ]{3})", dias[0]["titulo"])):
        ini_rot = f"{int(m.group(1)):02d}/{MES_ABREV.get(m.group(2), 0):02d}"
        if ini_rot != d["data_curta"][:5]:
            d["inicio_roteiro"] = ini_rot
    if dias and (m := re.match(r"(\d{1,2})/([A-ZÇ]{3})", dias[-1]["titulo"])):
        d["retorno_roteiro"] = f"{int(m.group(1)):02d}/{MES_ABREV.get(m.group(2), 0):02d}"

    # Conferência: refeições do dia a dia × número do "inclui"
    d["ref_dias"] = sum(refeicoes_do_dia(x["titulo"]) for x in dias)
    m = next((re.search(r"(\d+)\s*refeiç", it) for it in d["inclui"] if re.search(r"\d+\s*refeiç", it)), None)
    d["ref_inclui"] = int(m.group(1)) if m else None
    cafe = next((x for x in d["inclui"] if x.lower().startswith("café da manhã")), "café da manhã")
    if d["ref_inclui"] is not None:
        d["refeicoes"] = f"{cafe} + {d['ref_inclui']} refeições, conforme o roteiro"
    elif d["ref_dias"]:
        d["refeicoes"] = (f"{cafe} + {d['ref_dias']} refeições (o site não informa o total; "
                          f"contagem dos dias com refeição no roteiro dia a dia)")
    else:
        d["refeicoes"] = f"{cafe}; demais refeições conforme o roteiro"
    return d


# ---------------------------------------------------------------- formato WhatsApp (o robô copia estes blocos)

BANDEIRA = {
    "África do Sul": "🇿🇦", "Alemanha": "🇩🇪", "Andorra": "🇦🇩", "Áustria": "🇦🇹", "Bélgica": "🇧🇪", "Bósnia": "🇧🇦",
    "Bulgária": "🇧🇬", "China": "🇨🇳", "Coreia do Sul": "🇰🇷", "Croácia": "🇭🇷", "Dinamarca": "🇩🇰",
    "Dubai": "🇦🇪", "Sharjah": "🇦🇪", "Abu Dhabi": "🇦🇪", "Egito": "🇪🇬", "Escócia": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "Eslováquia": "🇸🇰",
    "Eslovênia": "🇸🇮", "Espanha": "🇪🇸", "Finlândia": "🇫🇮", "França": "🇫🇷", "Grécia": "🇬🇷", "Holanda": "🇳🇱",
    "Hungria": "🇭🇺", "Índia": "🇮🇳", "Inglaterra": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "Itália": "🇮🇹", "Japão": "🇯🇵", "Liechtenstein": "🇱🇮",
    "Luxemburgo": "🇱🇺", "Marrocos": "🇲🇦", "Nepal": "🇳🇵", "Noruega": "🇳🇴", "País de Gales": "🏴󠁧󠁢󠁷󠁬󠁳󠁿",
    "Polônia": "🇵🇱", "Portugal": "🇵🇹", "República Tcheca": "🇨🇿", "Romênia": "🇷🇴", "Suécia": "🇸🇪", "Suíça": "🇨🇭",
    "Tailândia": "🇹🇭", "Tunísia": "🇹🇳", "Turquia": "🇹🇷",
}
# Para páginas sem a linha do país: bandeiras do destino
BANDEIRA_DESTINO = {"croacia-e-balcas": "🇭🇷🇸🇮🇧🇦", "marrocos": "🇲🇦"}

MESES_NOME = ["", "janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro",
              "outubro", "novembro", "dezembro"]


def bandeiras(d, arq=""):
    achados = sorted((m.start(), v) for k, v in BANDEIRA.items()
                     for m in [re.search(r"\b" + re.escape(k) + r"\b", d["pais"])] if m)  # na ordem do nome
    b = "".join(v for _, v in achados)
    b = "".join(dict.fromkeys(re.findall(r"🏴[^🏴🇦-🇿]*|[🇦-🇿]{2}", b)))  # sem repetir (Dubai/Sharjah/Abu Dhabi)
    return b or BANDEIRA_DESTINO.get(arq, "")


def data_extenso(d):
    m = re.match(r"(\d{2})/(\d{2})/(\d{4})$", d["data_curta"])
    if m:
        return f"{int(m.group(1))} de {MESES_NOME[int(m.group(2))]} de {m.group(3)}"
    m = re.match(r"(\w+)/(\d{4})", d["data_curta"])
    return f"{m.group(1)} de {m.group(2)} (dia a definir)" if m else d["data_curta"]


def blocos_preco(d):
    """Os 4 blocos de preço no modelo do Bruno, com os números desta saída."""
    out = []
    for pacote, nome_pac in (("aereo", "completo"), ("terrestre", "terrestre")):
        dias = d["dias_aereo"] or d["dias"] if pacote == "aereo" else (d["dias_terrestre"] or d["dias"])
        for quarto, nome_q in (("Duplo", "duplo"), ("Individual", "single")):
            p = d["precos"].get((pacote, quarto))
            if p is None:
                continue
            titulo = f"Preço por pessoa pacote {nome_pac} {nome_q}"
            if p == "sob consulta":
                out.append(f"{titulo}\n{bandeiras(d)} *{d['nome']}*\n📅 Saída: {data_extenso(d)} | {dias} dias\n💰 Valor: sob consulta")
                continue
            m = re.match(r"entrada (R\$ [\d.]+) \+ (\d+)× (R\$ [\d.]+) \(total (R\$ [\d.]+)\)", p)
            out.append(f"{titulo}\n{bandeiras(d)} *{d['nome']}*\n📅 Saída: {data_extenso(d)} | {dias} dias\n"
                       f"💰 Valor: {m.group(4)}\n🧾 Entrada de {m.group(1)} + ➕ {m.group(2)}× de {m.group(3)}")
    return out


def titulo_dia(n, dia):
    """'09/MAR – HONG KONG (café da manhã + 1 refeição, a definir)' -> '📍 *Dia 4 | 09/03 | Hong Kong* 🍽️ café...'"""
    t = dia["titulo"]
    m = re.match(r"^(?:(\d{1,2})º?/([A-ZÇ]{3})[A-ZÇ]*|\d{1,2}º\s*DIA)\s*[–-]\s*(.*)$", t)
    data = f"{int(m.group(1)):02d}/{MES_ABREV.get(m.group(2), 0):02d}" if m and m.group(1) else ""
    resto = m.group(3) if m else t
    ref = re.search(r"\(([^()]*)\)\s*$", resto)
    cidades = resto[:ref.start()].strip() if ref else resto.strip()
    pequenas = {"De", "Do", "Da", "Dos", "Das", "E", "A", "O", "Em", "No", "Na"}
    cidades = " ".join(w.lower() if w in pequenas else w for w in cidades.title().split())
    icone = "✈️" if re.search(r"\bVOO\b|SÃO PAULO", resto.upper()) else "📍"
    partes = [f"Dia {n}"] + ([data] if data else []) + [cidades]
    return f"{icone} *{' | '.join(partes)}*" + (f" 🍽️ {ref.group(1)}" if ref else "")


def linha_lista(d):
    return f"📅 {data_extenso(d)} | *{d['nome']}* | {d['dias_aereo'] or d['dias']} dias"


def html_por_destino(grupos):
    """Todas as saídas de cada destino juntas, já no formato de lista para o WhatsApp."""
    blocos = []
    for arq, nome, ss in grupos:
        linhas = [f"{bandeiras(ss[0], arq)} *{nome} — {len(ss)} {'saída' if len(ss) == 1 else 'saídas'}*"]
        linhas += [linha_lista(d) for d in ss]
        blocos.append(f'<p id="lista-{e(arq)}">' + "<br>\n".join(e(x) for x in linhas) + "</p>\n")
    return ('<h2 id="saidas-por-destino">Saídas por destino — lista completa de cada destino</h2>\n'
            "<p>Para responder \"quais saídas vocês têm para X\", copie o bloco inteiro do destino: "
            "ele traz todas as saídas daquele destino, em ordem de data.</p>\n" + "".join(blocos))


# ---------------------------------------------------------------- saída em HTML

def e(t):
    return html.escape(t, quote=False)


def lista(itens_):
    return "<ul>\n" + "".join(f"<li>{e(x)}</li>\n" for x in itens_) + "</ul>\n" if itens_ else "<p>—</p>\n"


def html_saida(d):
    rot = f"{d['nome']} — saída {d['data_curta']}"
    p = [f'<section id="{e(d["slug"])}">\n<h2>{e(rot)}</h2>\n']
    campos = [
        ("Roteiro", d["nome"]),
        ("País", d["pais"]),
        ("Data de saída do Brasil (pacote com aéreo)", d["data_saida"]),
        *([("Atenção", f"o roteiro começa em {d['inicio_roteiro']} com a apresentação no aeroporto; "
                        f"o voo sai em {d['data_curta']} (veja o horário em Voos)")] if d["inicio_roteiro"] else []),
        ("Duração com aéreo", f"{d['dias_aereo'] or d['dias']} dias"),
        ("Duração só parte terrestre", f"{d['dias_terrestre']} dias" if d["dias_terrestre"] else "—"),
        ("Visitando", d["visitando"]),
        ("Bandeiras", bandeiras(d, d.get("_arq", "")) or "—"),
        ("Companhia aérea", d["cia"] or "—"),
        ("Refeições", d["refeicoes"]),
        ("Código da viagem no site", f"ID {d['id']}" if d["id"] else "—"),
        ("Página atualizada no site em", d["atualizado_site"] or "—"),
        ("Página oficial", d["url"]),
    ]
    p.append("<ul>\n" + "".join(f"<li><b>{e(k)}:</b> {e(v)}</li>\n" for k, v in campos) + "</ul>\n")
    if d["descricao"]:
        p.append(f"<h3>Apresentação — {e(rot)}</h3>\n" + "".join(f"<p>{e(x)}</p>\n" for x in d["descricao"]))
    p.append(f"<h3>Voos — {e(rot)}</h3>\n<p><b>Companhia aérea:</b> {e(d['cia'] or '—')}</p>\n" + lista(d["voos"]))
    if d["aviso_voos"]:
        p.append(f"<p>{e(d['aviso_voos'])}</p>\n")
    p.append(f"<h3>Hotéis previstos — {e(rot)}</h3>\n" + lista(d["hoteis"]))
    for outra in d["hoteis_outras"]:
        p.append("<p><b>Atenção:</b> a página desta saída no site traz outra lista de hotéis, diferente da acima. "
                 "Confirme com o consultor qual vale.</p>\n" + lista(outra))
    if d["aviso_hoteis"]:
        p.append(f"<p>{e(d['aviso_hoteis'])}</p>\n")
    p.append(f"<h3>O pacote inclui — {e(rot)}</h3>\n" + lista(d["inclui"]))
    p.append(f"<h3>Passeios e diferenciais incluídos — {e(rot)}</h3>\n" + lista(d["diferenciais"]))
    if d["destaques"]:
        p.append(f"<h3>Experiências em destaque — {e(rot)}</h3>\n" + lista(d["destaques"]))
    p.append(f"<h3>O pacote NÃO inclui — {e(rot)}</h3>\n" + lista(d["nao_inclui"]))
    p.append(f"<h3>Roteiro dia a dia — {e(rot)}</h3>\n")
    p.extend(f"<p>{e(x)}</p>\n" for x in d["intro_roteiro"])
    for n, dia in enumerate(d["dias_roteiro"], 1):
        if dia["aviso"]:
            p.append(f"<p><i>{e(dia['aviso'])}</i></p>\n")
        p.append(f"<h4>{e(titulo_dia(n, dia))}</h4>\n" + "".join(f"<p>{e(x)}</p>\n" for x in dia["texto"]))
    p.append(f"<h3>Clima, distâncias e custo no destino — {e(rot)}</h3>\n" + lista(d["detalhes"]))
    p.append(f"<h3>Observações — {e(rot)}</h3>\n" + lista(d["observacoes"]))
    p.append(f"<h3>Valores por pessoa — {e(rot)}</h3>\n" + lista(d["valores"]))
    blocos = blocos_preco(d)
    if blocos:
        p.append(f"<h3>Preços prontos para enviar ao cliente — {e(rot)}</h3>\n"
                 + "".join(f"<p>{'<br>'.join(e(x) for x in b.split(chr(10)))}</p>\n" for b in blocos)
                 + "<p>✅ Parcelamento sem juros, em reais.</p>\n")
    p.append("</section>\n<hr>\n")
    return "".join(p)


def precos_txt(d, pacote, rotulo):
    tipos = [t for t in ("Duplo", "Individual", "Triplo") if (pacote, t) in d["precos"]]
    if not tipos:
        return f"{rotulo}: —"
    return f"{rotulo} — " + " · ".join(f"{t}: {d['precos'][(pacote, t)]}" for t in tipos)


def celulas_quadro(d):
    """Uma linha do quadro geral; cada célula leva o próprio rótulo para ser entendida sozinha."""
    dias = f"{d['dias_aereo'] or d['dias']} dias com aéreo"
    if d["dias_terrestre"]:
        dias += f"; {d['dias_terrestre']} dias só terrestre"
    datas = f"Saída {d['data_curta']}" + (f", retorno {d['retorno']}" if d["retorno"] else "") + f". {dias}."
    n_ref = d["ref_inclui"] if d["ref_inclui"] is not None else d["ref_dias"]
    ref = f"Refeições: café da manhã + {n_ref} refeições" + ("" if d["ref_inclui"] is not None else " (contadas no dia a dia)")
    return [
        f"{d['nome']} — saída {d['data_curta']}" + (f" (ID {d['id']})" if d["id"] else ""),
        datas,
        f"Companhia aérea: {d['cia'] or '—'}",
        ref,
        precos_txt(d, "aereo", "Com aéreo e seguro"),
        precos_txt(d, "terrestre", "Só parte terrestre"),
    ]


CABECALHO_QUADRO = ("<th>Roteiro e saída</th><th>Datas e duração</th><th>Companhia aérea</th><th>Refeições</th>"
                    "<th>Preço com aéreo e seguro</th><th>Preço só parte terrestre</th>")

NOTA_VALORES = ("Valores por pessoa, em reais, parcelados sem juros e em parcelas fixas. "
                "O total é a soma da entrada com as parcelas. O retorno é a data de chegada ao Brasil no pacote com aéreo.")


def html_quadro(nome, saidas):
    """Quadro geral no fim da página de um destino."""
    linhas = "".join("<tr>" + "".join(f"<td>{e(c)}</td>" for c in celulas_quadro(d)) + "</tr>\n" for d in saidas)
    return f"""<h2 id="quadro-geral">Todas as saídas de {e(nome)} — datas, dias, companhia aérea, refeições e preços</h2>
<p>Uma linha por saída, em ordem de data. {NOTA_VALORES}
Os detalhes de cada saída estão na ficha dela, mais acima nesta página.</p>
<div style="overflow-x:auto">
<table>
<tr>{CABECALHO_QUADRO}</tr>
{linhas}</table>
</div>
"""


def pagina(titulo, corpo):
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>{e(titulo)}</title>
<style>
body{{font-family:Arial,Helvetica,sans-serif;max-width:900px;margin:0 auto;padding:16px;line-height:1.5;color:#222;background:#fff}}
table{{border-collapse:collapse;width:100%}} td,th{{border:1px solid #ccc;padding:4px 6px;text-align:left;font-size:14px;vertical-align:top}}
h2{{margin-top:40px;border-bottom:2px solid #222}} h4{{margin-bottom:4px}}
</style>
</head>
<body>
{corpo}
</body>
</html>
"""


def html_destino(nome, saidas, gerado):
    idx = "".join(
        f"<tr><td>{e(d['nome'])}</td><td>{e(d['data_curta'])}</td><td>{e(d['dias_aereo'] or d['dias'])}</td>"
        f"<td>{e(d['dias_terrestre'] or '—')}</td><td>{e(d['cia'] or '—')}</td>"
        f"<td><a href=\"#{e(d['slug'])}\">ver</a></td></tr>\n" for d in saidas)
    corpo = f"""<p><a href="index.html">← Todas as saídas e todos os destinos</a></p>
<h1>Roteiros Lielu Turismo — {e(nome)}</h1>
<p>Base de consulta com todas as saídas de {e(nome)} publicadas em lieluturismo.com.br.
Gerada em {e(gerado)} a partir do site oficial. {len(saidas)} saídas.</p>
<h2>Como ler esta página</h2>
<ul>
<li>Cada saída abaixo é completa e independente. Sempre confirme a data de saída antes de responder, porque voos, hotéis, preços e às vezes o roteiro mudam de uma data para outra.</li>
<li>"Pacote com aéreo" inclui voos, taxas e seguro e sai do Brasil na data de saída. "Só parte terrestre" começa no hotel do primeiro destino e tem menos dias.</li>
<li>Dias marcados com "CONSIDERAR ESTE(S) DIA(S) APENAS NO ROTEIRO DO PACOTE COM PARTE AÉREA INCLUÍDA" valem só para quem compra com aéreo.</li>
<li>Os valores são por pessoa, em reais, parcelados sem juros e em parcelas fixas.</li>
<li>No final da página está o quadro "Todas as saídas de {e(nome)}", com datas, dias, companhia aérea, refeições e preços de todas as saídas juntos. Use esse quadro para comparar saídas ou responder rápido; use a ficha da saída para os detalhes.</li>
</ul>
<h2>Índice das saídas de {e(nome)}</h2>
<table>
<tr><th>Roteiro</th><th>Saída</th><th>Dias com aéreo</th><th>Dias só terrestre</th><th>Companhia aérea</th><th></th></tr>
{idx}</table>
<hr>
{"".join(html_saida(d) for d in saidas)}
{html_quadro(nome, saidas)}"""
    return pagina(f"Roteiros Lielu — {nome}", corpo)


def html_todas(grupos, gerado):
    """Página única com o quadro de todas as saídas do site, em ordem de data, com o destino e o arquivo da ficha."""
    todas = sorted(((d, nome, arq) for arq, nome, saidas in grupos for d in saidas), key=lambda x: x[0]["ordem"])
    linhas = "".join(
        f"<tr><td>{e('Destino: ' + nome)}</td>" + "".join(f"<td>{e(c)}</td>" for c in celulas_quadro(d))
        + f"<td><a href=\"{e(arq)}.html#{e(d['slug'])}\">{e(arq)}.html</a></td></tr>\n"
        for d, nome, arq in todas)
    lista_dest = "".join(f"<li><a href=\"{e(arq)}.html\">{e(nome)}</a>: {len(s)} saídas — página {e(arq)}.html</li>\n"
                         for arq, nome, s in grupos)
    corpo = f"""<h1>Roteiros Lielu Turismo — todas as saídas</h1>
<p>Quadro com todas as {len(todas)} saídas publicadas em lieluturismo.com.br, em ordem de data.
Gerado em {e(gerado)} a partir do site oficial.</p>
<h2>Como ler esta página</h2>
<ul>
<li>Uma linha por saída, com destino, roteiro, datas, dias, companhia aérea, refeições e preços. Use para responder perguntas como "o que tem em maio?" ou "qual a viagem mais curta?".</li>
<li>Os detalhes de cada saída (voos, hotéis, dia a dia, o que inclui e o que não inclui) estão na página do destino indicada na última coluna e na lista de destinos abaixo.</li>
<li>{NOTA_VALORES}</li>
</ul>
<h2>Destinos</h2>
<ul>
{lista_dest}</ul>
<h2 id="quadro-geral">Todas as saídas — datas, dias, companhia aérea, refeições e preços</h2>
<div style="overflow-x:auto">
<table>
<tr><th>Destino</th>{CABECALHO_QUADRO}<th>Ficha completa</th></tr>
{linhas}</table>
</div>"""
    return pagina("Roteiros Lielu — todas as saídas", corpo)


def html_unico(grupos, gerado):
    """Um arquivo só com tudo: quadro de todas as saídas no topo e, embaixo, as fichas completas de cada destino."""
    todas = sorted(((d, nome) for arq, nome, saidas in grupos for d in saidas), key=lambda x: x[0]["ordem"])
    linhas = "".join(
        f"<tr><td>{e('Destino: ' + nome)}</td>" + "".join(f"<td>{e(c)}</td>" for c in celulas_quadro(d))
        + f"<td><a href=\"#{e(d['slug'])}\">ver ficha</a></td></tr>\n" for d, nome in todas)
    lista_dest = "".join(f"<li><a href=\"#destino-{e(arq)}\">{e(nome)}</a>: {len(s)} saídas</li>\n"
                         for arq, nome, s in grupos)
    fichas = "".join(
        f'<h1 id="destino-{e(arq)}">Destino: {e(nome)} — {len(ss)} saídas</h1>\n' + "".join(html_saida(d) for d in ss)
        for arq, nome, ss in grupos)
    corpo = f"""<h1>Roteiros Lielu Turismo — todas as saídas</h1>
<p>Base de consulta com todas as {len(todas)} saídas publicadas em lieluturismo.com.br.
Gerada em {e(gerado)} a partir do site oficial.</p>
<h2>Como ler esta página</h2>
<ul>
<li>Logo abaixo está a lista de saídas por destino (todas as saídas de cada destino juntas) e depois o quadro com todas as saídas, em ordem de data: destino, roteiro, datas, dias, companhia aérea, refeições e preços. Use para responder rápido e comparar saídas.</li>
<li>Depois do quadro vêm as fichas completas, agrupadas por destino: voos, hotéis, o que inclui, o que não inclui, roteiro dia a dia, clima, observações e valores.</li>
<li>Cada saída é completa e independente. Sempre confirme a data de saída antes de responder, porque voos, hotéis, preços e às vezes o roteiro mudam de uma data para outra.</li>
<li>"Pacote com aéreo" inclui voos, taxas e seguro e sai do Brasil na data de saída. "Só parte terrestre" começa no hotel do primeiro destino e tem menos dias.</li>
<li>Dias marcados com "CONSIDERAR ESTE(S) DIA(S) APENAS NO ROTEIRO DO PACOTE COM PARTE AÉREA INCLUÍDA" valem só para quem compra com aéreo.</li>
<li>{NOTA_VALORES}</li>
</ul>
<h2>Destinos</h2>
<ul>
{lista_dest}</ul>
{html_por_destino(grupos)}
<h2 id="quadro-geral">Todas as saídas — datas, dias, companhia aérea, refeições e preços</h2>
<div style="overflow-x:auto">
<table>
<tr><th>Destino</th>{CABECALHO_QUADRO}<th>Ficha</th></tr>
{linhas}</table>
</div>
<hr>
{fichas}"""
    return pagina("Roteiros Lielu — todas as saídas", corpo)


def urls_de_saida(usar_cache):
    """Todos os links de saída do conteúdo da página de viagens (sem o menu e o rodapé)."""
    s = baixar(LISTA, os.path.join(CACHE, "_lista.html"), usar_cache)
    corpo = s[s.find('id="content"'):s.find('id="footer"')]
    return sorted(set(re.findall(r'href="(' + re.escape(SITE) + r'/[^"#?]+/)"', corpo)))


def destino_de(slug):
    for arq, nome, padrao in DESTINOS:
        if re.match(padrao + r"(-|\d|$)", slug):
            return arq, nome
    return None, None


def ler_todas(urls, usar_cache):
    saidas = []
    for u in urls:
        slug = u.rstrip("/").split("/")[-1]
        s = baixar(u, os.path.join(CACHE, slug + ".html"), usar_cache)
        if 'id="roteiro"' not in s:
            print(f"ignorada (não é página de saída): {u}")
            continue
        d = ler_saida(u, s)
        d["_html"] = s
        saidas.append(d)
    return saidas


def gravar(arq, conteudo):
    os.makedirs(SAIDA, exist_ok=True)
    caminho = os.path.join(SAIDA, arq + ".html")
    open(caminho, "w", encoding="utf-8").write(conteudo)
    return caminho


def main():
    import auditar
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    usar_cache = "--cache" in sys.argv
    alvo = args[0] if args else "todos"
    gerado = datetime.datetime.now().strftime("%d/%m/%Y")

    urls = urls_de_saida(usar_cache)
    if alvo != "todos":
        urls = [u for u in urls if u.rstrip("/").split("/")[-1].startswith(alvo)]
    saidas = ler_todas(urls, usar_cache)
    if not saidas:
        sys.exit(f"Nenhuma saída encontrada para '{alvo}'.")

    if alvo == "todos":  # apaga as páginas antigas: destino que sumiu do site não pode continuar publicado
        for f in os.listdir(SAIDA) if os.path.isdir(SAIDA) else []:
            if f.endswith(".html"):
                os.remove(os.path.join(SAIDA, f))

    grupos = {}
    for d in saidas:
        arq, nome = destino_de(d["slug"])
        if not arq:
            print(f"SEM DESTINO DEFINIDO: {d['slug']} ({d['pais']}) — entra em 'outros'")
            arq, nome = "outros", "Outros roteiros"
        d["_arq"] = arq
        grupos.setdefault(arq, (nome, []))[1].append(d)
    ordem = [(arq, nome, sorted(ss, key=lambda d: d["ordem"])) for arq, (nome, ss) in sorted(grupos.items())]

    total_prob = 0
    for arq, nome, ss in ordem:
        caminho = gravar(arq, html_destino(nome, ss, gerado))
        print(f"\n{caminho}  ({os.path.getsize(caminho):,} bytes, {len(ss)} saídas)")
        for d in ss:
            prob = auditar.auditar(d, d["_html"])
            total_prob += len(prob)
            print(f"  {'OK ' if not prob else 'XX '}{d['slug']:<52}{d['data_curta']:<14}"
                  + ("" if not prob else " | " + " | ".join(prob)))
    if alvo == "todos":
        caminho = gravar("roteiros-lielu-completo", html_unico(ordem, gerado))
        print(f"\n{caminho}  ({os.path.getsize(caminho):,} bytes, {len(saidas)} saídas)")
        caminho = gravar("index", html_todas(ordem, gerado))  # página inicial do site publicado
        caminho_antigo = os.path.join(SAIDA, "todas-as-saidas.html")
        if os.path.exists(caminho_antigo):
            os.remove(caminho_antigo)
        print(f"\n{caminho}  ({os.path.getsize(caminho):,} bytes, {len(saidas)} saídas)")
    print(f"\n{len(saidas)} saídas, {len(ordem)} arquivos de destino, {total_prob} problema(s) na conferência.")


if __name__ == "__main__":
    main()
