"""
gerar_dados.py - Fase 1 do CasaNova 2 (Pricing & Planejamento)

O QUE ESTE SCRIPT FAZ
---------------------
Constroi a "realidade" da CasaNova: 24 meses de historico de uma rede de varejo
(casa, ferramentas e utilidades) com 12 lojas fisicas + e-commerce, ~600 produtos,
precos, custos, promocoes, concorrencia e estoque.

Os dados nascem LIMPOS dentro do script (simulacao) e so depois recebem
problemas de qualidade de proposito (duplicidades, precos zerados, datas
invalidas...). Alem disso, o script PLANTA cenarios de pricing para voce
descobrir na analise (produto caro demais, promocao que deu prejuizo, etc).

Tudo que foi plantado e salvo em docs/gabarito.md e docs/gabarito_produtos.csv.
REGRA DO JOGO: so abra o gabarito DEPOIS de fazer sua analise.

COMO RODAR (na raiz do projeto, com o .venv ativo)
--------------------------------------------------
    python src/gerar_dados.py

Opcoes:
    --seed 42          muda a "semente" (dados diferentes, mesma logica)
    --produtos 600     quantidade de produtos (use 120 para um teste rapido)

SAIDAS (data/raw/, CSV com separador ';' e decimal ',', abre direto no Excel pt-BR)
    dim_produto, dim_loja, dim_calendario, fato_vendas, hist_precos,
    promocoes, preco_concorrente, estoque, fato_vendas_amostra
"""

import argparse
import time
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------------------
# 1. PARAMETROS DO CENARIO (mexa aqui para mudar a empresa)
# ---------------------------------------------------------------------------
DATA_INI = pd.Timestamp("2024-10-01")
DATA_FIM = pd.Timestamp("2026-09-30")          # 24 meses = 730 dias
ID_PRODUTO_BASE = 1001                          # primeiro id_produto
PRAZO_REPOSICAO = 7                             # dias entre pedir e receber estoque
ESCALA_DEMANDA = 1.0                            # multiplica toda a demanda (volume de linhas)

# Cada categoria tem: custo tipico, markup (preco = custo x markup), elasticidade
# VERDADEIRA (o que a Fase 5 deve tentar recuperar), sazonalidade e tipos de produto.
CATEGORIAS = {
    "Ferramentas Manuais": dict(cod="FM", custo_med=28, sigma=0.6, markup=1.90, elast=-0.6,
        amp=0.05, pico=6, tipos=["Martelo", "Chave de Fenda", "Alicate", "Trena", "Serra Manual", "Jogo de Chaves"]),
    "Ferramentas Elétricas": dict(cod="FE", custo_med=180, sigma=0.6, markup=1.55, elast=-0.8,
        amp=0.05, pico=6, tipos=["Furadeira", "Parafusadeira", "Esmerilhadeira", "Serra Tico-Tico", "Lixadeira", "Soprador"]),
    "Utilidades Domésticas": dict(cod="UD", custo_med=16, sigma=0.5, markup=1.75, elast=-1.9,
        amp=0.08, pico=12, tipos=["Jogo de Panelas", "Garrafa Térmica", "Pote Hermético", "Balde", "Vassoura", "Escorredor"]),
    "Organização e Armazenagem": dict(cod="OA", custo_med=30, sigma=0.5, markup=1.80, elast=-1.5,
        amp=0.08, pico=1, tipos=["Caixa Organizadora", "Prateleira", "Cabideiro", "Gaveteiro", "Sapateira", "Armário Multiuso"]),
    "Cama, Mesa e Banho": dict(cod="CM", custo_med=45, sigma=0.5, markup=1.90, elast=-1.3,
        amp=0.25, pico=7, tipos=["Toalha de Banho", "Jogo de Lençol", "Edredom", "Toalha de Mesa", "Tapete de Banheiro", "Travesseiro"]),
    "Iluminação": dict(cod="IL", custo_med=25, sigma=0.6, markup=1.70, elast=-1.1,
        amp=0.08, pico=11, tipos=["Lâmpada LED", "Luminária de Mesa", "Pendente", "Fita LED", "Refletor", "Abajur"]),
    "Jardim e Churrasco": dict(cod="JC", custo_med=60, sigma=0.7, markup=1.75, elast=-1.4,
        amp=0.35, pico=12, tipos=["Mangueira", "Churrasqueira", "Kit Churrasco", "Regador", "Vaso", "Cortador de Grama"]),
    "Decoração": dict(cod="DC", custo_med=35, sigma=0.6, markup=2.00, elast=-1.7,
        amp=0.25, pico=12, tipos=["Quadro", "Espelho", "Vaso Decorativo", "Relógio de Parede", "Almofada", "Cortina"]),
}

MARCAS = ["Casalar", "FerroForte", "LuzVida", "TecnoLar", "Verdecor",
          "PratoFino", "Domus", "ForteMax", "Arteca", "Brisa"]
VARIACOES = ["Pro", "Plus", "Basic", "Premium", "Compacto", "Max", "Slim", "Classic", "Home", "Top"]

# Lojas: (nome, cidade, uf, regiao, peso de tamanho). A ultima e o e-commerce (estoque do CD).
LOJAS = [
    ("CasaNova Barra da Tijuca", "Rio de Janeiro", "RJ", "Sudeste", 1.5, "fisica"),
    ("CasaNova Tijuca", "Rio de Janeiro", "RJ", "Sudeste", 1.1, "fisica"),
    ("CasaNova Campo Grande", "Rio de Janeiro", "RJ", "Sudeste", 0.9, "fisica"),
    ("CasaNova Icaraí", "Niterói", "RJ", "Sudeste", 0.8, "fisica"),
    ("CasaNova Paulista", "São Paulo", "SP", "Sudeste", 1.4, "fisica"),
    ("CasaNova Tatuapé", "São Paulo", "SP", "Sudeste", 1.2, "fisica"),
    ("CasaNova Campinas", "Campinas", "SP", "Sudeste", 1.0, "fisica"),
    ("CasaNova Savassi", "Belo Horizonte", "MG", "Sudeste", 1.0, "fisica"),
    ("CasaNova Vitória", "Vitória", "ES", "Sudeste", 0.8, "fisica"),
    ("CasaNova Curitiba", "Curitiba", "PR", "Sul", 0.9, "fisica"),
    ("CasaNova Salvador", "Salvador", "BA", "Nordeste", 0.8, "fisica"),
    ("CasaNova Brasília", "Brasília", "DF", "Centro-Oeste", 0.9, "fisica"),
    ("CasaNova E-commerce", "Rio de Janeiro", "RJ", "Nacional", 2.5, "ecommerce"),
]

# Eventos sazonais: (nome, multiplicador padrao, {categoria: multiplicador}, [(inicio, fim)])
# A ORDEM define a prioridade do rotulo no calendario (primeiro = mais importante).
EVENTOS = [
    ("Black Friday", 1.7, {}, [("2024-11-25", "2024-12-02"), ("2025-11-24", "2025-12-01")]),
    ("Natal", 1.2, {"Decoração": 1.5, "Iluminação": 1.4},
        [("2024-12-01", "2024-12-24"), ("2025-12-01", "2025-12-24")]),
    ("Dia das Mães", 1.1, {"Cama, Mesa e Banho": 1.4, "Utilidades Domésticas": 1.3, "Decoração": 1.3},
        [("2025-05-04", "2025-05-11"), ("2026-05-03", "2026-05-10")]),
    ("Dia dos Pais", 1.05, {"Ferramentas Manuais": 1.4, "Ferramentas Elétricas": 1.5},
        [("2025-08-03", "2025-08-10"), ("2026-08-02", "2026-08-09")]),
    ("Dia do Consumidor", 1.2, {}, [("2025-03-12", "2025-03-15"), ("2026-03-12", "2026-03-15")]),
]

FERIADOS = {
    "2024-10-12": "Nossa Sra. Aparecida", "2024-11-02": "Finados", "2024-11-15": "Proclamação da República",
    "2024-11-20": "Consciência Negra", "2024-12-25": "Natal",
    "2025-01-01": "Confraternização Universal", "2025-03-03": "Carnaval", "2025-03-04": "Carnaval",
    "2025-04-18": "Sexta-feira Santa", "2025-04-21": "Tiradentes", "2025-05-01": "Dia do Trabalho",
    "2025-06-19": "Corpus Christi", "2025-09-07": "Independência", "2025-10-12": "Nossa Sra. Aparecida",
    "2025-11-02": "Finados", "2025-11-15": "Proclamação da República", "2025-11-20": "Consciência Negra",
    "2025-12-25": "Natal",
    "2026-01-01": "Confraternização Universal", "2026-02-16": "Carnaval", "2026-02-17": "Carnaval",
    "2026-04-03": "Sexta-feira Santa", "2026-04-21": "Tiradentes", "2026-05-01": "Dia do Trabalho",
    "2026-06-04": "Corpus Christi", "2026-09-07": "Independência",
}

# Choques de CUSTO (cambio, materia-prima) e a reacao do MERCADO (concorrentes reajustam ~1 mes depois).
CHOQUES_CUSTO = [("Ferramentas Elétricas", "2026-03-01", 1.14), ("Cama, Mesa e Banho", "2025-09-01", 1.08)]
CHOQUES_MERCADO = [("Ferramentas Elétricas", "2026-04-01", 1.10), ("Cama, Mesa e Banho", "2025-10-01", 1.06)]

# Datas em que a CasaNova revisa precos de tabela.
REVISOES = ["2025-01-01", "2025-04-01", "2025-06-01", "2025-07-01",
            "2025-10-01", "2026-01-01", "2026-04-01", "2026-07-01"]
DATA_REPOSICIONAMENTO = "2025-06-01"   # quando "caro demais" e "barato demais" nascem
REVISAO_PULADA_FE = "2026-04-01"       # revisao que esqueceram de fazer em Ferr. Eletricas (vazamento de margem)
DATA_RUPTURA_LIDERES = "2025-08-01"    # a partir daqui o reabastecimento dos lideres falha

PROMOCOES = [
    # nome, inicio, fim, tipo, desconto, categoria alvo, prob. de o produto participar
    ("Black Friday 2024", "2024-11-25", "2024-12-02", "sazonal", 0.22, "Todas", 0.6),
    ("Natal Decoração 2024", "2024-12-05", "2024-12-24", "sazonal", 0.12, "Decoração", 0.8),
    ("Liquidação de Verão 2025", "2025-01-13", "2025-01-26", "liquidacao", 0.20, "Jardim e Churrasco", 0.8),
    ("Dia do Consumidor 2025", "2025-03-10", "2025-03-16", "sazonal", 0.15, "Todas", 0.6),
    ("Dia das Mães 2025", "2025-05-02", "2025-05-11", "sazonal", 0.15, "Cama, Mesa e Banho", 0.8),
    ("Semana Casa Arrumada", "2025-06-16", "2025-06-29", "categoria", 0.15, "Organização e Armazenagem", 0.8),
    ("Dia dos Pais 2025 Elétricas", "2025-08-01", "2025-08-10", "sazonal", 0.18, "Ferramentas Elétricas", 0.8),
    ("Mega Utilidades", "2025-08-18", "2025-09-07", "queima", 0.42, "Utilidades Domésticas", 0.9),
    ("Black Friday 2025", "2025-11-24", "2025-12-01", "sazonal", 0.25, "Todas", 0.6),
    ("Natal Decoração 2025", "2025-12-05", "2025-12-24", "sazonal", 0.12, "Decoração", 0.8),
    ("Liquidação de Verão 2026", "2026-01-12", "2026-01-25", "liquidacao", 0.20, "Jardim e Churrasco", 0.8),
    ("Dia do Consumidor 2026", "2026-03-09", "2026-03-15", "sazonal", 0.15, "Todas", 0.6),
    ("Dia das Mães 2026", "2026-05-01", "2026-05-10", "sazonal", 0.15, "Cama, Mesa e Banho", 0.8),
    ("Semana do Cliente", "2026-07-13", "2026-07-19", "sazonal", 0.10, "Todas", 0.6),
    ("Dia dos Pais 2026 Manuais", "2026-07-31", "2026-08-09", "sazonal", 0.18, "Ferramentas Manuais", 0.8),
]
ID_PROMO_PREJUIZO = 8                  # "Mega Utilidades"

CONCORRENTES = [("Mercado Livre", 0.97), ("Amazon", 0.98), ("Concorrente Regional", 1.03)]


# ---------------------------------------------------------------------------
# 2. FUNCOES AUXILIARES
# ---------------------------------------------------------------------------
def idx(data):
    """Converte uma data (texto) no numero do dia dentro do periodo (0 = 01/10/2024)."""
    return (pd.Timestamp(data) - DATA_INI).days


def preco_90(x):
    """Preco 'de varejo': arredonda para baixo e termina em ,90 (ex.: 47,32 -> 46,90)."""
    return np.floor(x) + 0.90


def log_problema(log, tabela, problema, qtd):
    log.append({"tabela": tabela, "problema": problema, "linhas_afetadas": int(qtd)})


def passo(msg, t0):
    print(f"  [{time.time() - t0:6.1f}s] {msg}", flush=True)


# ---------------------------------------------------------------------------
# 3. DIMENSOES (quem vende, o que vende, quando)
# ---------------------------------------------------------------------------
def gerar_produtos(rng, n):
    """
    Cria os produtos. Para cada um sorteamos o custo (lognormal: poucos itens caros,
    muitos baratos), o preco inicial (custo x markup da categoria) e a popularidade
    (base_p = quantas unidades ele vende por dia por loja, em media).
    """
    cats = list(CATEGORIAS)
    linhas = []
    for ci, cat in enumerate(cats):
        c = CATEGORIAS[cat]
        k = n // len(cats) + (1 if ci < n % len(cats) else 0)
        for j in range(k):
            tipo = str(rng.choice(c["tipos"]))
            marca = str(rng.choice(MARCAS))
            custo = float(max(3.0, rng.lognormal(np.log(c["custo_med"]), c["sigma"])))
            preco = float(preco_90(custo * c["markup"] * rng.lognormal(0, 0.06)))
            linhas.append(dict(
                categoria=cat, subcategoria=tipo, marca=marca,
                nome=f"{tipo} {marca} {rng.choice(VARIACOES)} {int(rng.integers(10, 99))}",
                custo_ini=round(custo, 2), preco_ini=preco,
                elast=c["elast"] + float(rng.normal(0, 0.10)),
                base_p=float(np.clip(rng.lognormal(np.log(0.22), 1.1), 0.01, 6.0)),
                status="descontinuado" if rng.random() < 0.03 else "ativo",
            ))
    df = pd.DataFrame(linhas)
    df.insert(0, "id_produto", ID_PRODUTO_BASE + np.arange(len(df)))
    df.insert(1, "sku", [f"CN-{CATEGORIAS[c]['cod']}-{i:04d}" for i, c in enumerate(df["categoria"], 1)])
    df["markup"] = df["preco_ini"] / df["custo_ini"]
    return df


def gerar_calendario(datas):
    """Calendario com feriados e eventos sazonais (usado na analise e na simulacao)."""
    nomes_dia = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
    evento = pd.Series("", index=datas)
    for nome, _, _, janelas in reversed(EVENTOS):          # o de maior prioridade escreve por ultimo
        for ini, fim in janelas:
            evento.loc[ini:fim] = nome
    fer = pd.Series(datas.strftime("%Y-%m-%d"), index=datas).map(FERIADOS).fillna("")
    return pd.DataFrame({
        "data": datas.strftime("%Y-%m-%d"), "ano": datas.year, "mes": datas.month,
        "trimestre": datas.quarter, "semana_ano": datas.isocalendar().week.to_numpy(),
        "dia_semana": [nomes_dia[i] for i in datas.dayofweek],
        "fim_de_semana": (datas.dayofweek >= 5).astype(int),
        "feriado": (fer.to_numpy() != "").astype(int), "nome_feriado": fer.to_numpy(),
        "evento_sazonal": evento.to_numpy(),
    })


def fator_sazonal(datas, cats_produto):
    """
    Matriz [produto x dia] com a sazonalidade: onda anual da categoria (ex.: churrasco
    vende mais no verao) x multiplicador de eventos (Black Friday, Natal...) x tendencia.
    """
    D = len(datas)
    cats = list(CATEGORIAS)
    mes_frac = datas.month.to_numpy() + datas.day.to_numpy() / 31.0
    sazon_cat = np.zeros((len(cats), D))
    ev_cat = np.ones((len(cats), D))
    for ci, cat in enumerate(cats):
        c = CATEGORIAS[cat]
        sazon_cat[ci] = 1 + c["amp"] * np.cos(2 * np.pi * (mes_frac - c["pico"]) / 12)
        for nome, padrao, por_cat, janelas in EVENTOS:
            m = por_cat.get(cat, padrao)
            for ini, fim in janelas:
                a, b = idx(ini), idx(fim) + 1
                ev_cat[ci, a:b] = np.maximum(ev_cat[ci, a:b], m)
    tendencia = 1 + 0.08 * np.arange(D) / D                 # empresa em leve recuperacao
    ci_prod = np.array([cats.index(c) for c in cats_produto])
    return (sazon_cat * ev_cat)[ci_prod] * tendencia[None, :]


# ---------------------------------------------------------------------------
# 4. CUSTO, PRECO DE TABELA, MERCADO E PROMOCOES
# ---------------------------------------------------------------------------
def gerar_custo_e_mercado(prod, D):
    """
    custo[p, dia]  : custo do produto (inflaciona 0,5% ao mes + choques de cambio)
    mercado[p, dia]: preco 'justo' de mercado (inflaciona 0,45% ao mes; concorrentes
                     reagem aos choques com ~1 mes de atraso)
    """
    meses = np.arange(D) / 30.4
    cat = prod["categoria"].to_numpy()
    custo = prod["custo_ini"].to_numpy()[:, None] * (1.005 ** meses)[None, :]
    mercado = prod["preco_ini"].to_numpy()[:, None] * (1.0045 ** meses)[None, :]
    for c, data, fator in CHOQUES_CUSTO:
        custo[cat == c, idx(data):] *= fator
    for c, data, fator in CHOQUES_MERCADO:
        mercado[cat == c, idx(data):] *= fator
    return custo, mercado


def gerar_precos_lista(prod, custo, cenarios):
    """
    Preco de tabela dia a dia. Em cada data de revisao a CasaNova recalcula o preco
    como custo x markup original e so muda se a diferenca passar de 2%.
    Plantamos 3 desvios: caro demais, barato demais e o vazamento em Ferr. Eletricas.
    """
    P, D = len(prod), custo.shape[1]
    cat = prod["categoria"].to_numpy()
    markup = prod["markup"].to_numpy()
    preco = prod["preco_ini"].to_numpy().copy()
    lista = np.repeat(preco[:, None], D, axis=1)
    hist = [(i, DATA_INI, preco[i], "preco_inicial") for i in range(P)]
    caro, barato = cenarios["caro_demais"], cenarios["barato_demais"]
    d_repos = idx(DATA_REPOSICIONAMENTO)
    for dstr in REVISOES:
        d = idx(dstr)
        mult = np.ones(P)
        if d >= d_repos:
            mult[caro], mult[barato] = 1.25, 0.85
        novo = preco_90(custo[:, d] * markup * mult)
        if dstr == DATA_REPOSICIONAMENTO:
            muda = caro | barato
        else:
            muda = np.abs(novo / preco - 1) > 0.02
            if dstr == REVISAO_PULADA_FE:
                muda &= ~(cat == "Ferramentas Elétricas")
        for i in np.where(muda)[0]:
            if dstr == DATA_REPOSICIONAMENTO:
                motivo = "reposicionamento" if caro[i] else "alinhamento_agressivo"
            else:
                motivo = "reajuste_custo"
            hist.append((i, pd.Timestamp(dstr), novo[i], motivo))
        preco[muda] = novo[muda]
        lista[muda, d:] = novo[muda][:, None]
    return lista, hist


def gerar_promocoes(rng, prod, D):
    """Aplica as promocoes: matrizes [produto x dia] de desconto e de id da promocao."""
    P = len(prod)
    cat = prod["categoria"].to_numpy()
    disc = np.zeros((P, D))
    pid = np.zeros((P, D), dtype=int)
    linhas = []
    for k, (nome, ini, fim, tipo, desc, alvo, prob) in enumerate(PROMOCOES, start=1):
        a, b = idx(ini), idx(fim) + 1
        elegivel = np.ones(P, bool) if alvo == "Todas" else (cat == alvo)
        part = elegivel & (rng.random(P) < prob)       # nem todo produto entra na promocao
        atual = disc[part, a:b]
        vence = desc > atual                            # se duas promocoes se sobrepoem, vale a maior
        disc[part, a:b] = np.where(vence, desc, atual)
        pid[part, a:b] = np.where(vence, k, pid[part, a:b])
        linhas.append(dict(id_promocao=k, nome=nome, data_inicio=ini, data_fim=fim, tipo=tipo,
                           desconto_pct=round(desc * 100, 1), categoria_alvo=alvo))
    return disc, pid, pd.DataFrame(linhas)


# ---------------------------------------------------------------------------
# 5. SIMULACAO DIARIA: DEMANDA + ESTOQUE
# ---------------------------------------------------------------------------
def simular(rng, prod, lojas, datas, sazon, peff, cenarios):
    """
    Para cada dia, para cada produto x loja:
      1) chega estoque que foi pedido ha 7 dias;
      2) sorteia a demanda (Poisson, com variacao extra de Gamma);
      3) vende o que tem em estoque (se faltar, e venda perdida = ruptura);
      4) se o estoque (+ o que ja esta a caminho) cair abaixo do ponto de pedido, repoe.

    Demanda esperada = popularidade x tamanho da loja x sazonalidade x dia da semana
                       x EFEITO-PRECO, onde efeito-preco = (preco praticado / preco do mercado) ^ elasticidade.
    E aqui que a elasticidade verdadeira entra nos dados.
    """
    P, S, D = len(prod), len(lojas), len(datas)
    L = PRAZO_REPOSICAO
    pesos = np.array([l[4] for l in lojas])
    eh_ecom = np.array([l[5] == "ecommerce" for l in lojas])
    fisica = np.array([0.90, 0.90, 0.95, 1.00, 1.10, 1.40, 1.20])     # seg..dom
    ecom = np.array([1.00, 1.00, 0.98, 1.00, 1.05, 1.00, 1.10])
    dow = datas.dayofweek.to_numpy()
    wk = np.where(eh_ecom[None, :], ecom[dow][:, None], fisica[dow][:, None])   # [dia x loja]

    lam_media = prod["base_p"].to_numpy()[:, None] * pesos[None, :] * ESCALA_DEMANDA

    # Politica de reposicao: ponto de pedido s = cobertura de (prazo + 3) dias;
    # nivel maximo S = cobertura de (prazo + 3 + 14) dias. Multiplicadores plantam os problemas.
    def politica(mult):
        s_pt = np.maximum(1, np.ceil(lam_media * (L + 3) * mult[:, None])).astype(np.int32)
        s_up = np.maximum(s_pt + 2, np.ceil(lam_media * (L + 3 + 14) * mult[:, None])).astype(np.int32)
        return s_pt, s_up

    mult_antes = np.ones(P)
    mult_antes[cenarios["excesso_estoque"]] = 9.0      # compram demais: estoque parado
    mult_depois = mult_antes.copy()
    mult_depois[cenarios["ruptura_lider"]] = 0.4       # lideres passam a ser reabastecidos de menos
    sp0, su0 = politica(mult_antes)
    sp1, su1 = politica(mult_depois)
    d_rup = idx(DATA_RUPTURA_LIDERES)

    estoque = su0.copy()
    a_caminho = np.zeros((P, S), dtype=np.int32)
    fila = np.zeros((L + 1, P, S), dtype=np.int32)
    vendas = np.zeros((D, P, S), dtype=np.int16)
    fim_estoque = np.zeros((D, P, S), dtype=np.int32)
    perdidas = np.zeros((D, P, S), dtype=np.int16)

    for d in range(D):
        slot = d % (L + 1)
        chegada = fila[slot]
        estoque += chegada
        a_caminho -= chegada
        fila[slot] = 0

        lam = lam_media * (sazon[:, d] * peff[:, d])[:, None] * wk[d][None, :]
        lam = lam * rng.gamma(5.0, 1 / 5.0, size=(P, S))
        demanda = rng.poisson(lam).astype(np.int32)
        venda = np.minimum(demanda, estoque)
        estoque -= venda

        sp, su = (sp1, su1) if d >= d_rup else (sp0, su0)
        posicao = estoque + a_caminho
        qtd = np.where(posicao <= sp, su - posicao, 0).astype(np.int32)
        a_caminho += qtd
        fila[(d + L) % (L + 1)] += qtd

        vendas[d] = venda
        fim_estoque[d] = estoque
        perdidas[d] = demanda - venda
    return vendas, fim_estoque, perdidas


# ---------------------------------------------------------------------------
# 6. MONTAGEM DAS TABELAS
# ---------------------------------------------------------------------------
def montar_fato(vendas, prod, datas, praticado, disc, pid, custo):
    """Transforma a matriz de vendas em linhas (so onde houve venda)."""
    d_i, p_i, s_i = np.nonzero(vendas)
    q = vendas[d_i, p_i, s_i].astype(np.int64)
    ids_promo = pid[p_i, d_i]
    f = pd.DataFrame({
        "id_venda": np.arange(1, len(q) + 1),
        "data": datas.strftime("%Y-%m-%d").to_numpy()[d_i],
        "id_loja": s_i + 1,
        "id_produto": ID_PRODUTO_BASE + p_i,
        "quantidade": q,
        "preco_praticado": praticado[p_i, d_i],
        "desconto_pct": np.round(disc[p_i, d_i] * 100, 1),
        "id_promocao": pd.array(np.where(ids_promo == 0, pd.NA, ids_promo), dtype="Int64"),
        "custo_total": np.round(q * custo[p_i, d_i], 2),
    })
    return f


def montar_estoque(fim_estoque, custo, datas, S):
    """Foto semanal (todo domingo) do estoque, com os dias de ruptura da semana."""
    P = fim_estoque.shape[1]
    domingos = np.where(datas.dayofweek == 6)[0]
    partes = []
    for d in domingos:
        ini = max(0, d - 6)
        rupt = (fim_estoque[ini:d + 1] == 0).sum(axis=0)             # dias com estoque zero na semana
        qtd = fim_estoque[d]
        pp, ss = np.meshgrid(np.arange(P), np.arange(S), indexing="ij")
        partes.append(pd.DataFrame({
            "data": datas[d].strftime("%Y-%m-%d"), "id_loja": ss.ravel() + 1,
            "id_produto": ID_PRODUTO_BASE + pp.ravel(), "qtd_estoque": qtd.ravel(),
            "qtd_ruptura_dias": rupt.ravel(),
            "custo_estoque": np.round(qtd.ravel() * custo[pp.ravel(), d], 2),
        }))
    return pd.concat(partes, ignore_index=True)


def montar_concorrentes(rng, prod, mercado, datas, log_gab):
    """Coleta semanal (toda segunda) do preco de 3 concorrentes para cada produto."""
    P = len(prod)
    semanas = pd.date_range(DATA_INI, DATA_FIM, freq="W-MON")
    di = np.array([(s - DATA_INI).days for s in semanas])
    W = len(semanas)
    em_bf = np.zeros(W, bool)
    for ini, fim in EVENTOS[0][3]:
        em_bf |= (semanas >= pd.Timestamp(ini)) & (semanas <= pd.Timestamp(fim))
    precos = np.zeros((P, W, len(CONCORRENTES)))
    for c, (nome, fator) in enumerate(CONCORRENTES):
        p = mercado[:, di] * fator * rng.normal(1, 0.025, (P, W))
        if nome in ("Mercado Livre", "Amazon"):
            p[:, em_bf] *= 0.88                                      # agressivos na Black Friday
        precos[:, :, c] = p
    # Precos "congelados": 15% dos pares produto x concorrente ficam 8 semanas sem atualizar.
    n_cong = 0
    for i, c in zip(*np.where(rng.random((P, len(CONCORRENTES))) < 0.15)):
        w0 = int(rng.integers(1, W - 8))
        precos[i, w0:w0 + 8, c] = precos[i, w0 - 1, c]
        n_cong += 8
    log_gab["precos_congelados"] = n_cong
    disp = rng.random((P, W, len(CONCORRENTES))) > 0.03
    pp, ww, cc = np.meshgrid(np.arange(P), np.arange(W), np.arange(len(CONCORRENTES)), indexing="ij")
    nomes = np.array([c[0] for c in CONCORRENTES])
    df = pd.DataFrame({
        "id_produto": ID_PRODUTO_BASE + pp.ravel(), "concorrente": nomes[cc.ravel()],
        "data_coleta": semanas.strftime("%Y-%m-%d").to_numpy()[ww.ravel()],
        "preco": np.round(precos.ravel(), 2), "disponivel": disp.ravel().astype(int),
    })
    return df.sort_values(["data_coleta", "id_produto", "concorrente"], kind="stable").reset_index(drop=True)


# ---------------------------------------------------------------------------
# 7. PROBLEMAS DE QUALIDADE (aplicados DEPOIS da simulacao limpa)
# ---------------------------------------------------------------------------
def problemas_fato(f, rng, log):
    f = f.copy()
    n = len(f)
    m = rng.random(n) < 0.003
    f.loc[m, "preco_praticado"] = 0.0
    log_problema(log, "fato_vendas", "preco_praticado igual a zero", m.sum())
    m = rng.random(n) < 0.001
    f.loc[m, "quantidade"] = -f.loc[m, "quantidade"]
    log_problema(log, "fato_vendas", "quantidade negativa", m.sum())
    m = rng.random(n) < 0.002
    f.loc[m, "data"] = np.where(rng.random(m.sum()) < 0.5, "2025-02-30", "2027-03-15")
    log_problema(log, "fato_vendas", "data invalida (30/02) ou no futuro (2027)", m.sum())
    m = rng.random(n) < 0.002
    f.loc[m, "id_produto"] = 99999
    log_problema(log, "fato_vendas", "id_produto inexistente (quebra de integridade)", m.sum())
    m = rng.random(n) < 0.005
    f.loc[m, "custo_total"] = np.nan
    log_problema(log, "fato_vendas", "custo_total ausente", m.sum())
    m = rng.random(n) < 0.001
    f.loc[m, "desconto_pct"] = 150.0
    log_problema(log, "fato_vendas", "desconto_pct fora do padrao (150%)", m.sum())
    m = rng.random(n) < 0.015
    f = pd.concat([f, f[m]]).sort_values("id_venda", kind="stable").reset_index(drop=True)
    log_problema(log, "fato_vendas", "linhas duplicadas (mesmo id_venda)", m.sum())
    return f


def problemas_produto(df, rng, log):
    df = df.copy()
    n = len(df)
    idx_c = rng.choice(n, 12, replace=False)
    df.loc[idx_c, "custo_unitario"] = np.round(df.loc[idx_c, "preco_lista"] * 1.15, 2)
    log_problema(log, "dim_produto", "custo_unitario maior que preco_lista", 12)
    idx_n = rng.choice(n, 10, replace=False)
    df.loc[idx_n, "categoria"] = np.nan
    log_problema(log, "dim_produto", "categoria ausente", 10)
    m = rng.random(n) < 0.03
    df.loc[m, "marca"] = [v.upper() if rng.random() < 0.5 else v.lower() + " " for v in df.loc[m, "marca"]]
    log_problema(log, "dim_produto", "marca com caixa/espaco inconsistente", m.sum())
    dup = df.sample(6, random_state=int(rng.integers(0, 1_000_000)))
    df = pd.concat([df, dup], ignore_index=True)
    log_problema(log, "dim_produto", "linhas duplicadas", 6)
    return df


def problemas_outros(lojas, hist, promo, estoque, conc, rng, log):
    lojas = lojas.copy()
    lojas.loc[lojas["cidade"] == "Campinas", "cidade"] = "campinas"
    lojas.loc[lojas["cidade"] == "Niterói", "uf"] = "rj"
    log_problema(log, "dim_loja", "cidade em minuscula / uf em minuscula", 2)

    hist = hist.copy()
    ids = rng.choice(len(hist), 5, replace=False)
    hist.loc[ids, "preco"] = 0.0
    log_problema(log, "hist_precos", "preco igual a zero", 5)
    cand = hist[hist["data_fim"].notna()].index.to_numpy()
    ids = rng.choice(cand, 5, replace=False)
    hist.loc[ids, ["data_inicio", "data_fim"]] = hist.loc[ids, ["data_fim", "data_inicio"]].to_numpy()
    log_problema(log, "hist_precos", "data_fim anterior a data_inicio", 5)

    promo = promo.copy()
    k = promo["nome"] == "Semana do Cliente"
    promo.loc[k, ["data_inicio", "data_fim"]] = promo.loc[k, ["data_fim", "data_inicio"]].to_numpy()
    log_problema(log, "promocoes", "data_fim anterior a data_inicio", 1)

    estoque = estoque.copy()
    n = len(estoque)
    m = rng.random(n) < 0.003
    estoque.loc[m, "qtd_estoque"] = -estoque.loc[m, "qtd_estoque"].abs() - 1
    log_problema(log, "estoque", "qtd_estoque negativa", m.sum())
    m = rng.random(n) < 0.005
    estoque = pd.concat([estoque, estoque[m]], ignore_index=True)
    log_problema(log, "estoque", "linhas duplicadas", m.sum())

    conc = conc.copy()
    n = len(conc)
    m = rng.random(n) < 0.005
    conc.loc[m, "preco"] = np.where(rng.random(m.sum()) < 0.5, 0.0, np.nan)
    log_problema(log, "preco_concorrente", "preco zerado ou ausente", m.sum())
    m = rng.random(n) < 0.003
    conc.loc[m, "preco"] = conc.loc[m, "preco"] * 10
    log_problema(log, "preco_concorrente", "outlier (preco multiplicado por 10)", m.sum())
    m = rng.random(n) < 0.01
    variantes = {"Mercado Livre": ["MERCADO LIVRE", "mercadolivre"], "Amazon": ["AMAZON", "amazon "],
                 "Concorrente Regional": ["CONCORRENTE REGIONAL", "concorrente regional "]}
    conc.loc[m, "concorrente"] = [variantes[c][int(rng.integers(0, 2))] for c in conc.loc[m, "concorrente"]]
    log_problema(log, "preco_concorrente", "nome do concorrente inconsistente", m.sum())
    m = rng.random(n) < 0.01
    conc = pd.concat([conc, conc[m]], ignore_index=True)
    log_problema(log, "preco_concorrente", "linhas duplicadas", m.sum())
    return lojas, hist, promo, estoque, conc


# ---------------------------------------------------------------------------
# 8. SAIDA
# ---------------------------------------------------------------------------
def salvar(df, nome, pasta):
    """CSV no padrao brasileiro: separador ';', decimal ',', UTF-8 com BOM (Excel le certo)."""
    caminho = pasta / f"{nome}.csv"
    df.to_csv(caminho, sep=";", decimal=",", index=False, encoding="utf-8-sig")
    print(f"      {nome + '.csv':<26} {len(df):>10,} linhas  {caminho.stat().st_size / 1e6:7.1f} MB".replace(",", "."))


def escrever_gabarito(caminho, args, prod, cenarios, log, extras, n_cong):
    cats = list(CATEGORIAS)
    linhas = [
        "# Gabarito CasaNova 2 (NAO ABRA ANTES DE FAZER A ANALISE)", "",
        f"Gerado com seed={args.seed} e {len(prod)} produtos. Periodo: {DATA_INI.date()} a {DATA_FIM.date()}.", "",
        "Este arquivo lista tudo o que foi plantado nos dados. Use-o para conferir, no fim,",
        "se a sua analise encontrou cada cenario. A lista produto a produto esta em `docs/gabarito_produtos.csv`.", "",
        "## 1. Cenarios de pricing e estoque", "",
        "| Cenario | Quantidade | Como aparece nos dados |", "|---|---|---|",
        f"| Caro demais | {int(cenarios['caro_demais'].sum())} produtos | A partir de 01/06/2025 o preco fica 25% acima do que seria; concorrentes seguem o preco normal; volume cai |",
        f"| Barato demais | {int(cenarios['barato_demais'].sum())} produtos | A partir de 01/06/2025 o preco fica 15% abaixo; vendem mais, margem some |",
        f"| Ruptura em lider | {int(cenarios['ruptura_lider'].sum())} produtos | Os 20 mais vendidos; a partir de 01/08/2025 o reabastecimento falha e o estoque zera com frequencia |",
        f"| Excesso de estoque | {int(cenarios['excesso_estoque'].sum())} produtos | Itens de baixa venda comprados em volume 9x maior: cobertura acima de 120 dias |",
        f"| Promocao que deu prejuizo | id_promocao = {ID_PROMO_PREJUIZO} (Mega Utilidades) | 42% de desconto em Utilidades Domesticas (18/08 a 07/09/2025): volume sobe, margem total cai |",
        "| Vazamento de custo | Ferramentas Eletricas | Custo sobe 14% em 01/03/2026; revisao de 01/04/2026 nao foi feita e o preco so sobe em 01/07/2026 |",
        "| Choque em Cama, Mesa e Banho | categoria inteira | Custo sobe 8% em 01/09/2025; preco acompanha na revisao de 01/10/2025 |", "",
        "## 2. Elasticidades verdadeiras (media por categoria)", "",
        "Efeito-preco na demanda = (preco praticado / preco do mercado) ^ elasticidade.",
        "Por isso, na Fase 5, use ln(quantidade) contra ln(indice de preco vs. concorrencia), e nao contra o preco nominal.",
        "Espere estimativas um pouco MENORES (em modulo) que as verdadeiras: rupturas limitam as vendas nos picos de promocao",
        "e o preco do concorrente e coletado com ruido. Explicar esse vies faz parte da analise.", "",
        "| Categoria | Elasticidade verdadeira |", "|---|---|",
    ]
    for c in cats:
        linhas.append(f"| {c} | {CATEGORIAS[c]['elast']} |")
    linhas += ["", "Cada produto tem um pequeno desvio individual (desvio padrao 0,10) em torno desse valor.", "",
               "## 3. Numeros de referencia (calculados nos dados LIMPOS)", ""]
    linhas += extras
    linhas += ["", "## 4. Problemas de qualidade injetados", "",
               "| Tabela | Problema | Linhas afetadas |", "|---|---|---|"]
    for r in log:
        linhas.append(f"| {r['tabela']} | {r['problema']} | {r['linhas_afetadas']} |")
    linhas += ["", f"Observacao: em preco_concorrente existem ainda {n_cong} precos 'congelados' "
                   "(repetidos por 8 semanas seguidas), que nao sao um erro de formato e exigem olhar a serie para descobrir.", ""]
    caminho.write_text("\n".join(linhas), encoding="utf-8")


# ---------------------------------------------------------------------------
# 9. PROGRAMA PRINCIPAL
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Gerador de dados CasaNova 2")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--produtos", type=int, default=600)
    args = ap.parse_args()

    t0 = time.time()
    rng = np.random.default_rng(args.seed)
    pasta = RAIZ / "data" / "raw"
    docs = RAIZ / "docs"
    pasta.mkdir(parents=True, exist_ok=True)
    docs.mkdir(parents=True, exist_ok=True)
    log, log_gab = [], {}

    print("Gerando dados da CasaNova 2...")
    datas = pd.date_range(DATA_INI, DATA_FIM, freq="D")
    D = len(datas)

    # --- produtos e cenarios plantados ---
    prod = gerar_produtos(rng, args.produtos)
    P = len(prod)
    ordem = np.argsort(-prod["base_p"].to_numpy())
    lideres = ordem[:20]                                       # os 20 mais vendidos
    resto = np.setdiff1d(np.arange(P), lideres)
    rng.shuffle(resto)
    n_caro, n_barato = int(round(P * 0.10)), int(round(P * 0.08))
    caro_i, barato_i = resto[:n_caro], resto[n_caro:n_caro + n_barato]
    livres = np.setdiff1d(resto, np.concatenate([caro_i, barato_i]))
    livres_set = set(livres.tolist())
    cauda = [i for i in ordem[::-1] if i in livres_set][: int(P * 0.35)]   # 35% de menor venda
    excesso_i = rng.choice(cauda, 40 if P >= 300 else max(5, P // 15), replace=False)
    cenarios = {k: np.zeros(P, bool) for k in ("caro_demais", "barato_demais", "ruptura_lider", "excesso_estoque")}
    cenarios["caro_demais"][caro_i] = True
    cenarios["barato_demais"][barato_i] = True
    cenarios["ruptura_lider"][lideres] = True
    cenarios["excesso_estoque"][excesso_i] = True
    passo(f"{P} produtos criados e cenarios sorteados", t0)

    # --- calendario, custos, precos, promocoes ---
    cal = gerar_calendario(datas)
    sazon = fator_sazonal(datas, prod["categoria"])
    custo, mercado = gerar_custo_e_mercado(prod, D)
    lista, hist_raw = gerar_precos_lista(prod, custo, cenarios)
    disc, pid, promo = gerar_promocoes(rng, prod, D)
    praticado = np.round(lista * (1 - disc), 2)
    elast = prod["elast"].to_numpy()[:, None]
    peff = np.clip((praticado / mercado) ** elast, 0.2, 8.0)
    passo("custos, precos de tabela, mercado e promocoes prontos", t0)

    # --- lojas ---
    lojas = pd.DataFrame([dict(id_loja=i + 1, nome=l[0], tipo=l[5], cidade=l[1], uf=l[2], regiao=l[3])
                          for i, l in enumerate(LOJAS)])

    # --- simulacao de demanda e estoque ---
    vendas, fim_estoque, perdidas = simular(rng, prod, LOJAS, datas, sazon, peff, cenarios)
    passo("simulacao diaria de vendas e estoque concluida", t0)

    # --- tabelas limpas ---
    fato = montar_fato(vendas, prod, datas, praticado, disc, pid, custo)
    estoque = montar_estoque(fim_estoque, custo, datas, len(LOJAS))
    conc = montar_concorrentes(rng, prod, mercado, datas, log_gab)
    hist = pd.DataFrame(hist_raw, columns=["i", "data_inicio", "preco", "motivo_alteracao"])
    hist["id_produto"] = ID_PRODUTO_BASE + hist["i"]
    hist = hist.sort_values(["id_produto", "data_inicio"]).reset_index(drop=True)
    hist["data_fim"] = hist.groupby("id_produto")["data_inicio"].shift(-1) - pd.Timedelta(days=1)
    for c in ("data_inicio", "data_fim"):
        hist[c] = hist[c].dt.strftime("%Y-%m-%d")
    hist = hist[["id_produto", "data_inicio", "data_fim", "preco", "motivo_alteracao"]]
    hist["preco"] = hist["preco"].round(2)

    dim_prod = pd.DataFrame({
        "id_produto": prod["id_produto"], "sku": prod["sku"], "nome": prod["nome"],
        "categoria": prod["categoria"], "subcategoria": prod["subcategoria"], "marca": prod["marca"],
        "custo_unitario": np.round(custo[:, -1], 2), "preco_lista": np.round(lista[:, -1], 2),
        "status": prod["status"],
    })
    passo(f"tabelas limpas montadas ({len(fato):,} linhas em fato_vendas)".replace(",", "."), t0)

    # --- numeros de referencia (dados limpos) para o gabarito ---
    fato["receita"] = fato["quantidade"] * fato["preco_praticado"]
    fato["trim"] = fato["data"].str[:4] + "-T" + ((fato["data"].str[5:7].astype(int) - 1) // 3 + 1).astype(str)
    q = fato.groupby("trim")[["receita", "custo_total"]].sum()
    q["margem_pct"] = ((q["receita"] - q["custo_total"]) / q["receita"] * 100).round(1)
    extras = ["Margem % por trimestre (empresa toda):", "", "| Trimestre | Receita (R$) | Margem % |", "|---|---|---|"]
    for t, r in q.iterrows():
        extras.append(f"| {t} | {r['receita']:,.0f} | {r['margem_pct']} |".replace(",", "."))
    cat_por_id = dict(zip(prod["id_produto"], prod["categoria"]))
    fato["categoria"] = fato["id_produto"].map(cat_por_id)
    ud = fato[fato["categoria"] == "Utilidades Domésticas"]
    def resumo(df):
        r, c = df["receita"].sum(), df["custo_total"].sum()
        return int(df["quantidade"].sum()), round((r - c) / r * 100, 1), round(r - c)
    antes = ud[(ud["data"] >= "2025-07-28") & (ud["data"] <= "2025-08-17")]
    durante = ud[(ud["data"] >= "2025-08-18") & (ud["data"] <= "2025-09-07")]
    ua, ma, la = resumo(antes)
    ub, mb, lb = resumo(durante)
    extras += ["", f"Promocao Mega Utilidades (Utilidades Domesticas): 3 semanas antes = {ua} unidades, margem {ma}%, lucro R$ {la}; "
                   f"durante = {ub} unidades, margem {mb}%, lucro R$ {lb}.", "",
               f"Venda perdida por ruptura nos 20 produtos lideres (nao aparece em nenhuma tabela): {int(perdidas[:, lideres, :].sum())} unidades."]
    fato = fato[["id_venda", "data", "id_loja", "id_produto", "quantidade", "preco_praticado",
                 "desconto_pct", "id_promocao", "custo_total"]]

    # --- injecao de problemas ---
    fato = problemas_fato(fato, rng, log)
    dim_prod = problemas_produto(dim_prod, rng, log)
    lojas, hist, promo, estoque, conc = problemas_outros(lojas, hist, promo, estoque, conc, rng, log)
    passo("problemas de qualidade injetados", t0)

    # --- salvar ---
    print("  Salvando em data/raw/ ...")
    salvar(dim_prod, "dim_produto", pasta)
    salvar(lojas, "dim_loja", pasta)
    salvar(cal, "dim_calendario", pasta)
    salvar(fato, "fato_vendas", pasta)
    salvar(fato.sample(min(50_000, len(fato)), random_state=1).sort_values("id_venda", kind="stable"),
           "fato_vendas_amostra", pasta)
    salvar(hist, "hist_precos", pasta)
    salvar(promo, "promocoes", pasta)
    salvar(conc, "preco_concorrente", pasta)
    salvar(estoque, "estoque", pasta)

    gab = prod[["id_produto", "sku", "categoria", "elast"]].rename(columns={"elast": "elasticidade_real"}).copy()
    for k, v in cenarios.items():
        gab[k] = v.astype(int)
    gab["elasticidade_real"] = gab["elasticidade_real"].round(3)
    gab.to_csv(docs / "gabarito_produtos.csv", sep=";", decimal=",", index=False, encoding="utf-8-sig")
    escrever_gabarito(docs / "gabarito.md", args, prod, cenarios, log, extras, log_gab["precos_congelados"])
    print(f"\nPronto em {time.time() - t0:.0f}s. Gabarito em docs/ (nao abra antes de analisar!).")


if __name__ == "__main__":
    main()