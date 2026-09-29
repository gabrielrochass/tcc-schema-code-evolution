# data/raw — Dados Brutos da Mineracao

**Data:** 2026-09-29
**Documentacao completa:** [docs/06-selecao-corpus.md](../../docs/06-selecao-corpus.md)

## Arquivos

| Arquivo | Descricao |
|---------|-----------|
| `candidates.csv` | 35 repos Django verificados (formato tabular) |
| `candidates.json` | Mesmos dados em JSON (mais facil de processar em scripts) |

## Numeros Rapidos

- 3.850 matches na busca GitHub
- 300 avaliados (3 paginas)
- **35 verificados como Django real**
- **17 com >= 15 migrations** (corpus candidato)

## Campos no CSV/JSON

| Campo | Descricao |
|-------|-----------|
| `full_name` | owner/repo no GitHub |
| `url` | URL do repositorio |
| `stars` | Estrelas no GitHub |
| `pushed_at` | Data do ultimo push |
| `license` | Licenca |
| `default_branch` | Branch principal |
| `commit_sha` | SHA do HEAD no momento da mineracao |
| `modules` | Numero de modulos Django detectados |
| `models` | Numero de modelos (classes em models.py) |
| `views` | Numero de views detectadas |
| `migration_count` | Total de arquivos de migration |
| `migration_apps` | Numero de apps com migrations |
| `size_class` | Small / Medium / Large |
| `verification_reason` | Como foi verificado como projeto Django |
