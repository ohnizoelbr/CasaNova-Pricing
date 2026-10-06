# CasaNova 2 — Pricing & Planejamento

Segunda fase do case **CasaNova Data Analytics**. Na primeira fase, a CasaNova voltou ao mercado e precisou recuperar competitividade. Agora ela precisa decidir **qual preço praticar sem destruir margem**.

> Projeto em construção.

## O problema

A CasaNova (casa, ferramentas e utilidades; lojas físicas, e-commerce e centro de distribuição) perdeu margem nos últimos 12 meses enquanto tentava acompanhar os preços dos grandes players.

## Perguntas de negócio

1. Quais produtos estão caros ou baratos demais em relação à concorrência?
2. Onde estamos perdendo margem: mix, desconto, custo ou preço?
3. Qual o impacto de mudar o preço no volume (elasticidade)?
4. Como está o estoque frente à demanda (ruptura e excesso)?
5. Qual a projeção de vendas dos próximos 3 meses em três cenários?
6. Quais ações de preço funcionaram e quais destruíram margem?

## Stack

Python (pandas, numpy, statsmodels) · SQL compatível com BigQuery · Excel · Power BI + DAX · Git/GitHub

## Estrutura

```
data/raw/         dados gerados (brutos, com problemas)
data/processed/   dados tratados (saída do ETL)
notebooks/        EDA, qualidade, elasticidade, projeção
src/              gerador, validações, ETL, pipeline
sql/              modelo e consultas analíticas
excel/            simulador de cenários
powerbi/          dashboard (.pbix) e prints
docs/             dicionário de dados, regras de negócio, apresentação
```

## Como rodar

_A completar ao final do projeto._

## Resultados

_A completar ao final do projeto._
