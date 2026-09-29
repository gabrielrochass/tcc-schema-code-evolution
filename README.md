# TCC - Schema-Code Co-Evolution in Django Projects

Repositorio do Trabalho de Conclusao de Curso sobre co-evolucao entre esquemas de banco de dados e codigo de aplicacao em projetos Django.

## Objetivo

Investigar empiricamente como mudancas de schema (via Django migrations) se relacionam com mudancas no codigo de aplicacao em projetos open-source.

## Perguntas de Pesquisa

- **RQ1:** Qual o grau de acoplamento entre mudancas de schema e mudancas no codigo de aplicacao nos commits de projetos Django open-source?
- **RQ2:** Quais camadas da arquitetura Django sao mais frequentemente co-modificadas em resposta a evolucoes de schema, e como essa distribuicao se relaciona com o tipo de operacao de migration realizada?
- **RQ3:** Os padroes de co-evolucao observados diferem entre aplicacoes Django full-stack e bibliotecas reutilizaveis?

## Pipeline

```
GitHub Search API
    -> Encontrar projetos Django
    -> Filtrar por quantidade de migrations
    -> Clone parcial (preserva historico)
    -> Extrair operacoes das migrations (AST)
    -> Correlacionar com commits (git log)
    -> Medir impacto no codigo (git diff-tree)
    -> Agregar metricas por tipo de operacao
```

## Estrutura

```
tcc-schema-code-evolution/
├── docs/                   # Documentacao do TCC
│   ├── 01-tema.md
│   ├── 02-perguntas-pesquisa.md
│   ├── 03-trabalhos-relacionados.md
│   ├── 04-metodologia.md
│   ├── 05-decisoes.md
│   └── 06-selecao-corpus.md  # Processo de selecao com diagramas
├── papers/                 # Fichamentos de artigos
├── scripts/                # Scripts da pipeline
│   ├── mine_repositories.py      # Mineracao com buckets (v1)
│   ├── mine_repositories_full.py # Mineracao full-scan sem buckets (v2)
│   ├── extract_migrations.py     # Parser AST de migrations
│   └── analyze_coevolution.py    # Analise de co-evolucao
├── experiments/            # Experimentos intermediarios
├── data/
│   ├── raw/               # Dados brutos (candidates.csv)
│   └── processed/         # Dados processados (coevolution.json)
└── results/
    ├── figures/
    └── tables/
```

## Como usar

### Requisitos

```bash
pip install requests python-dotenv
```

Precisa de `GITHUB_TOKEN` no ambiente ou em `.env` (apenas para `mine_repositories.py`).

### 1. Minerar repositorios

```bash
# Dry run (estima chamadas API)
python scripts/mine_repositories.py --dry-run

# Mineracao completa
python scripts/mine_repositories.py --output data/raw/candidates.csv
```

### 2. Extrair migrations de um repo clonado

```bash
python scripts/extract_migrations.py /path/to/cloned/repo
python scripts/extract_migrations.py /path/to/repos/ --batch --output data/processed/migrations.json
```

### 3. Analisar co-evolucao

```bash
python scripts/analyze_coevolution.py /path/to/cloned/repo
python scripts/analyze_coevolution.py /path/to/repos/ --batch --output data/processed/coevolution.json

# Com filtro de outliers
python scripts/analyze_coevolution.py /path/to/repos/ --batch --max-commit-files 50
```

## Referencias

- Qiu, Li & Su (2013). *An Empirical Analysis of the Co-evolution of Schema and Code in Database Applications.*
- Meurice, Nagy & Cleve (2016). *Detecting and Preventing Program Inconsistencies under Database Schema Evolution.*
- STAR-RG/django-smells — infraestrutura base para mineracao de repos Django.
