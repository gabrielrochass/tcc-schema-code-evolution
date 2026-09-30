# data/raw -- Dados Brutos da Mineracao

**Documentacao completa:** [docs/06-selecao-corpus.md](../../docs/06-selecao-corpus.md)

## Arquivos

| Arquivo | Script | Descricao |
|---------|--------|-----------|
| `candidates.csv` / `.json` | v1 (buckets) | 35 repos, 17 com >=15 mig. Amostra inicial. |
| `candidates_full.csv` / `.json` | v2 (full-scan) | 416 repos, 131 com >=15 mig. Corpus completo. |

## Numeros -- Full-scan (v2)

- 3.850 matches na busca GitHub
- 1.000 avaliados (10 paginas)
- **416 verificados como Django real**
- **131 com >= 15 migrations**
- Distribuicao: S=55, M=22, L=54

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
