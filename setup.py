"""
setup_projeto.py - Fase 0 do CasaNova 2 (Pricing & Planejamento)

Deixa o projeto pronto para uso:
  1. cria a estrutura de pastas
  2. cria README.md, .gitignore e requirements.txt (sem sobrescrever o que já existe)
  3. cria o ambiente virtual .venv
  4. instala as dependências
  5. confere se as bibliotecas importam

Como usar (na raiz do repositório, com o terminal do VSCode):
    python setup_projeto.py

Opções:
    --force         sobrescreve README.md, .gitignore e requirements.txt
    --skip-install  não cria o .venv nem instala dependências
"""

import argparse
import subprocess
import sys
import venv
from pathlib import Path

RAIZ = Path(__file__).resolve().parent

PASTAS = [
    "data/raw",
    "data/processed",
    "notebooks",
    "src",
    "sql",
    "excel",
    "powerbi",
    "docs",
]

REQUIREMENTS = """pandas
numpy
statsmodels
matplotlib
openpyxl
duckdb
ipykernel
"""

GITIGNORE = """# Ambiente virtual e caches
.venv/
__pycache__/
*.pyc
.ipynb_checkpoints/

# Dados gerados (são reproduzíveis pelo src/gerar_dados.py)
data/raw/*.csv
data/processed/*.csv
*.db
*.duckdb

# Arquivos temporários
~$*
.DS_Store
"""

README = """# CasaNova 2 — Pricing & Planejamento

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
"""

ARQUIVOS = {
    "requirements.txt": REQUIREMENTS,
    ".gitignore": GITIGNORE,
    "README.md": README,
}

IMPORTS_TESTE = ["pandas", "numpy", "statsmodels", "matplotlib", "openpyxl", "duckdb"]


def titulo(texto):
    print(f"\n=== {texto} ===")


def criar_pastas():
    titulo("1/5 Estrutura de pastas")
    for pasta in PASTAS:
        caminho = RAIZ / pasta
        caminho.mkdir(parents=True, exist_ok=True)
        (caminho / ".gitkeep").touch(exist_ok=True)
        print(f"  ok  {pasta}/")


def criar_arquivos(force):
    titulo("2/5 Arquivos base")
    for nome, conteudo in ARQUIVOS.items():
        caminho = RAIZ / nome
        if caminho.exists() and not force:
            print(f"  --  {nome} já existe (mantido; use --force para sobrescrever)")
            continue
        caminho.write_text(conteudo, encoding="utf-8")
        print(f"  ok  {nome}")


def python_do_venv():
    if sys.platform.startswith("win"):
        return RAIZ / ".venv" / "Scripts" / "python.exe"
    return RAIZ / ".venv" / "bin" / "python"


def criar_venv():
    titulo("3/5 Ambiente virtual")
    py = python_do_venv()
    if py.exists():
        print("  --  .venv já existe (mantido)")
        return
    venv.EnvBuilder(with_pip=True).create(RAIZ / ".venv")
    print("  ok  .venv criado")


def instalar_dependencias():
    titulo("4/5 Instalando dependências (pode demorar alguns minutos)")
    py = str(python_do_venv())
    subprocess.check_call([py, "-m", "pip", "install", "--upgrade", "pip"])
    subprocess.check_call([py, "-m", "pip", "install", "-r", str(RAIZ / "requirements.txt")])


def verificar():
    titulo("5/5 Verificação")
    py = str(python_do_venv())
    falhas = []
    for lib in IMPORTS_TESTE:
        r = subprocess.run([py, "-c", f"import {lib}"], capture_output=True, text=True)
        if r.returncode == 0:
            print(f"  ok  {lib}")
        else:
            print(f"  XX  {lib}")
            falhas.append(lib)
    return falhas


def proximos_passos(ativar_cmd):
    titulo("Próximos passos")
    print("  1. Ative o ambiente no terminal:")
    print(f"       {ativar_cmd}")
    print("  2. No VSCode, selecione o interpretador .venv")
    print("     (Ctrl+Shift+P -> Python: Select Interpreter).")
    print("  3. No GitHub Desktop, faça o commit com a mensagem:")
    print("       chore: estrutura inicial do projeto CasaNova Pricing")
    print("     e clique em Publish repository (desmarque 'Keep this code private').")
    print("  4. Fase 0 concluída. Próxima: Fase 1 (gerador de dados).")


def main():
    parser = argparse.ArgumentParser(description="Setup da Fase 0 - CasaNova Pricing")
    parser.add_argument("--force", action="store_true", help="sobrescreve arquivos base")
    parser.add_argument("--skip-install", action="store_true", help="não cria .venv nem instala")
    args = parser.parse_args()

    print(f"Projeto: {RAIZ}")
    criar_pastas()
    criar_arquivos(args.force)

    if args.skip_install:
        titulo("3/5 a 5/5 Ambiente virtual")
        print("  --  ignorado (--skip-install)")
    else:
        try:
            criar_venv()
            instalar_dependencias()
        except subprocess.CalledProcessError as e:
            print(f"\nERRO ao instalar dependências: {e}")
            print("Verifique sua conexão com a internet e rode o script de novo.")
            sys.exit(1)
        falhas = verificar()
        if falhas:
            print(f"\nBibliotecas com problema: {', '.join(falhas)}")
            sys.exit(1)

    ativar = (r".venv\Scripts\Activate.ps1" if sys.platform.startswith("win")
              else "source .venv/bin/activate")
    proximos_passos(ativar)


if __name__ == "__main__":
    main()