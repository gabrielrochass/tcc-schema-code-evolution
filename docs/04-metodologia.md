# Metodologia

## Visao Geral

Estudo empirico quantitativo baseado em mineracao de repositorios de software (MSR).

## Pipeline

```mermaid
flowchart TD
    subgraph "1. Coleta"
        A["GitHub Search API\nBusca por projetos Django"] --> B["Verificacao automatica\nmanage.py + Django em deps"]
        B --> C["Classificacao\nmodulos, models, views, migrations"]
    end

    subgraph "2. Filtragem e Classificacao"
        C --> D{"migrations >= 15?"}
        D -->|Sim| E["131 candidatos"]
        D -->|Nao| F["Descartado"]
        E --> CL["Classificacao manual\napp / lib / exclude"]
        CL --> CV["Cross-validation automatizada\nclassify_repos.py (kappa = 0,63)"]
        CV --> E2["Corpus final: 124 repos\n86 apps + 38 libs"]
    end

    subgraph "3. Extracao"
        E2 --> G["Clone parcial\ngit clone --filter=blob:none"]
        G --> H["Parsing AST\ndas migrations"]
        H --> I["Operacoes extraidas\ntipo, modelo, campo"]
    end

    subgraph "4. Correlacao"
        I --> J["git log --diff-filter=A\ncommit que introduziu cada migration"]
        J --> K["git diff-tree --numstat\narquivos e LOC alteradas"]
    end

    subgraph "5. Classificacao e Metricas"
        K --> L["Classificacao por camada\nDjango (model, view, admin...)"]
        L --> M["Calculo de metricas\nchurn, spread, co-evolution ratio"]
    end

    subgraph "6. Analise"
        M --> N["Agregacao por tipo\nde operacao e camada"]
        N --> O["Segmentacao\napps vs bibliotecas"]
        O --> P["Respostas as RQs"]
    end

    style A fill:#3498db,color:#fff
    style E2 fill:#27ae60,color:#fff
    style F fill:#95a5a6,color:#fff
    style P fill:#27ae60,color:#fff
    style CV fill:#8e44ad,color:#fff
```

### Scripts da pipeline

| Etapa | Script | Entrada | Saida |
|-------|--------|---------|-------|
| Coleta + Filtragem | `mine_repositories.py` / `mine_repositories_full.py` | GitHub API | `candidates.csv` |
| Classificacao | `classify_repos.py` | `candidates_full.json` + GitHub API | `corpus_classification_auto.json` |
| Extracao | `extract_migrations.py` | Repos clonados | `migrations.json` |
| Correlacao + Metricas | `analyze_coevolution.py` | Repos clonados | `coevolution.json` |

## Selecao do Corpus

### Criterios de inclusao

```mermaid
flowchart LR
    A["GitHub Search API"] --> B["language:Python\nfork:false\nstars >= 20\npush nos ultimos 2 anos"]
    B --> C["Verificacao:\nmanage.py +\nDjango em deps"]
    C --> D["Classificacao:\nmodulos, models,\nviews, migrations"]
    D --> E["Filtro:\nmigrations >= 15"]

    style E fill:#27ae60,color:#fff
```

1. Projeto Django real (verificado via manage.py + requirements.txt/pyproject.toml)
2. Linguagem principal: Python
3. Nao e fork
4. Push nos ultimos 2 anos
5. >= 20 stars
6. >= 15 arquivos de migration
7. >= 1 app Django com migrations

### Fonte

GitHub Search API, adaptando a infraestrutura do STAR-RG/django-smells.
Referencia: https://github.com/STAR-RG/django-smells

Detalhamento completo do processo de selecao em [06-selecao-corpus.md](06-selecao-corpus.md).

## Extracao de Dados

### Operacoes de migration (AST)

Django migrations seguem uma estrutura canonica:

```python
class Migration(migrations.Migration):
    operations = [
        migrations.AddField(model_name='Order', name='status', ...),
    ]
```

O parser AST extrai: tipo da operacao, modelo afetado, campo (quando aplicavel).

```mermaid
flowchart LR
    A["Arquivo .py\nde migration"] --> B["ast.parse()"]
    B --> C["Localizar classe\nMigration"]
    C --> D["Extrair lista\noperations = [...]"]
    D --> E["Para cada operacao:\ntipo, modelo, campo"]

    style A fill:#3498db,color:#fff
    style E fill:#27ae60,color:#fff
```

### Categorias de operacoes

| Categoria | Operacoes |
|-----------|-----------|
| Ciclo de vida do modelo | CreateModel, DeleteModel |
| Mudancas de campo | AddField, RemoveField, AlterField, RenameField |
| Indices e constraints | AddIndex, RemoveIndex, AddConstraint, RemoveConstraint |
| Metadados do modelo | AlterModelOptions, AlterModelTable, RenameModel, AlterUniqueTogether, AlterIndexTogether |
| Customizadas | RunSQL, RunPython, SeparateDatabaseAndState |

### Associacao migration -> codigo (Git)

Definicao operacional: **os arquivos alterados no mesmo commit que introduziu a migration**.

```mermaid
flowchart LR
    A["migration file"] --> B["git log\n--diff-filter=A\n--format=%H"]
    B --> C["SHA do commit\nque adicionou"]
    C --> D["git diff-tree\n--numstat SHA"]
    D --> E["Lista de arquivos\n+ LOC add/rem"]

    style A fill:#3498db,color:#fff
    style E fill:#27ae60,color:#fff
```

### Classificacao de arquivos

Cada arquivo alterado e classificado por seu papel na arquitetura Django:

| Categoria | Criterio |
|-----------|----------|
| migration | Dentro de /migrations/ |
| model | models.py ou /models/ |
| view | views.py ou /views/ |
| serializer | serializers.py ou /serializers/ |
| form | forms.py ou /forms/ |
| admin | admin.py |
| test | Contem 'test' no caminho |
| url | urls.py |
| template | Arquivo .html |
| other_python | Outros .py |
| other | Demais arquivos |

```mermaid
flowchart TD
    A["Arquivo alterado\nno commit"] --> B{"/migrations/?"}
    B -->|Sim| C["migration"]
    B -->|Nao| D{"models.py\nou /models/?"}
    D -->|Sim| E["model"]
    D -->|Nao| F{"views.py\nou /views/?"}
    F -->|Sim| G["view"]
    F -->|Nao| H{"admin.py?"}
    H -->|Sim| I["admin"]
    H -->|Nao| J{"Contem 'test'?"}
    J -->|Sim| K["test"]
    J -->|Nao| L["... demais\ncategorias"]

    style C fill:#e74c3c,color:#fff
    style E fill:#2980b9,color:#fff
    style G fill:#27ae60,color:#fff
    style I fill:#8e44ad,color:#fff
    style K fill:#f39c12,color:#fff
```

## Metricas

| Metrica | Descricao | RQ |
|---------|-----------|-----|
| **Co-evolution ratio** | Proporcao de migration commits que tambem alteram codigo | RQ1 |
| **Code churn** | LOC adicionadas + removidas (excluindo migrations) | RQ1, RQ2 |
| **Spread** | Numero de arquivos de codigo alterados por commit | RQ1, RQ2 |
| **Category distribution** | Frequencia de cada camada nos commits com migration | RQ2 |
| **Operation type distribution** | Frequencia e impacto de cada tipo de operacao | RQ2 |
| **Group comparison** | Metricas acima segmentadas por apps vs libs | RQ3 |

## Ameacas a Validade

Ver [05-decisoes.md](05-decisoes.md) para discussao detalhada de limitacoes e decisoes metodologicas.
