# Gabarito CasaNova 2 (NAO ABRA ANTES DE FAZER A ANALISE)

Gerado com seed=42 e 600 produtos. Periodo: 2024-10-01 a 2026-09-30.

Este arquivo lista tudo o que foi plantado nos dados. Use-o para conferir, no fim,
se a sua analise encontrou cada cenario. A lista produto a produto esta em `docs/gabarito_produtos.csv`.

## 1. Cenarios de pricing e estoque

| Cenario | Quantidade | Como aparece nos dados |
|---|---|---|
| Caro demais | 60 produtos | A partir de 01/06/2025 o preco fica 25% acima do que seria; concorrentes seguem o preco normal; volume cai |
| Barato demais | 48 produtos | A partir de 01/06/2025 o preco fica 15% abaixo; vendem mais, margem some |
| Ruptura em lider | 20 produtos | Os 20 mais vendidos; a partir de 01/08/2025 o reabastecimento falha e o estoque zera com frequencia |
| Excesso de estoque | 40 produtos | Itens de baixa venda comprados em volume 9x maior: cobertura acima de 120 dias |
| Promocao que deu prejuizo | id_promocao = 8 (Mega Utilidades) | 42% de desconto em Utilidades Domesticas (18/08 a 07/09/2025): volume sobe, margem total cai |
| Vazamento de custo | Ferramentas Eletricas | Custo sobe 14% em 01/03/2026; revisao de 01/04/2026 nao foi feita e o preco so sobe em 01/07/2026 |
| Choque em Cama, Mesa e Banho | categoria inteira | Custo sobe 8% em 01/09/2025; preco acompanha na revisao de 01/10/2025 |

## 2. Elasticidades verdadeiras (media por categoria)

Efeito-preco na demanda = (preco praticado / preco do mercado) ^ elasticidade.
Por isso, na Fase 5, use ln(quantidade) contra ln(indice de preco vs. concorrencia), e nao contra o preco nominal.
Espere estimativas um pouco MENORES (em modulo) que as verdadeiras: rupturas limitam as vendas nos picos de promocao
e o preco do concorrente e coletado com ruido. Explicar esse vies faz parte da analise.

| Categoria | Elasticidade verdadeira |
|---|---|
| Ferramentas Manuais | -0.6 |
| Ferramentas Elétricas | -0.8 |
| Utilidades Domésticas | -1.9 |
| Organização e Armazenagem | -1.5 |
| Cama, Mesa e Banho | -1.3 |
| Iluminação | -1.1 |
| Jardim e Churrasco | -1.4 |
| Decoração | -1.7 |

Cada produto tem um pequeno desvio individual (desvio padrao 0,10) em torno desse valor.

## 3. Numeros de referencia (calculados nos dados LIMPOS)

Margem % por trimestre (empresa toda):

| Trimestre | Receita (R$) | Margem % |
|---|---|---|
| 2024-T4 | 35.572.383 | 40.5 |
| 2025-T1 | 31.708.996 | 40.2 |
| 2025-T2 | 30.654.282 | 41.6 |
| 2025-T3 | 32.360.924 | 40.9 |
| 2025-T4 | 35.648.066 | 41.3 |
| 2026-T1 | 32.043.191 | 40.0 |
| 2026-T2 | 32.430.784 | 38.2 |
| 2026-T3 | 35.804.931 | 41.6 |

Promocao Mega Utilidades (Utilidades Domesticas): 3 semanas antes = 8118 unidades, margem 44.2%, lucro R$ 117696; durante = 14347 unidades, margem 5.5%, lucro R$ 15533.

Venda perdida por ruptura nos 20 produtos lideres (nao aparece em nenhuma tabela): 126483 unidades.

## 4. Problemas de qualidade injetados

| Tabela | Problema | Linhas afetadas |
|---|---|---|
| fato_vendas | preco_praticado igual a zero | 4661 |
| fato_vendas | quantidade negativa | 1556 |
| fato_vendas | data invalida (30/02) ou no futuro (2027) | 3061 |
| fato_vendas | id_produto inexistente (quebra de integridade) | 3179 |
| fato_vendas | custo_total ausente | 7750 |
| fato_vendas | desconto_pct fora do padrao (150%) | 1486 |
| fato_vendas | linhas duplicadas (mesmo id_venda) | 23112 |
| dim_produto | custo_unitario maior que preco_lista | 12 |
| dim_produto | categoria ausente | 10 |
| dim_produto | marca com caixa/espaco inconsistente | 19 |
| dim_produto | linhas duplicadas | 6 |
| dim_loja | cidade em minuscula / uf em minuscula | 2 |
| hist_precos | preco igual a zero | 5 |
| hist_precos | data_fim anterior a data_inicio | 5 |
| promocoes | data_fim anterior a data_inicio | 1 |
| estoque | qtd_estoque negativa | 2446 |
| estoque | linhas duplicadas | 3983 |
| preco_concorrente | preco zerado ou ausente | 981 |
| preco_concorrente | outlier (preco multiplicado por 10) | 578 |
| preco_concorrente | nome do concorrente inconsistente | 1892 |
| preco_concorrente | linhas duplicadas | 1922 |

Observacao: em preco_concorrente existem ainda 2040 precos 'congelados' (repetidos por 8 semanas seguidas), que nao sao um erro de formato e exigem olhar a serie para descobrir.
