# Metodologia

## Visao Geral

Estudo empirico quantitativo baseado em mineracao de repositorios de software (MSR).

### Pipeline

```
1. Mineracao de repos Django no GitHub
   (scripts/mine_repositories.py)
        |
2. Filtragem: repos com >= 15 migrations
        |
3. Clone parcial (--filter=blob:none)
   preserva historico git completo
        |
4. Extracao de operacoes das migrations
   (scripts/extract_migrations.py)
   metodo: parsing AST dos arquivos .py
        |
5. Correlacao migration -> commit
   (scripts/analyze_coevolution.py)
   metodo: git log --diff-filter=A
        |
6. Medicao de impacto no codigo
   metodo: git diff-tree --numstat
        |
7. Agregacao e analise
```

## Selecao do Corpus

### Criterios de inclusao

1. Projeto Django real (verificado via manage.py + requirements.txt)
2. Linguagem principal: Python
3. Nao e fork
4. Push nos ultimos 2 anos
5. >= 20 stars
6. >= 15 arquivos de migration
7. >= 1 app Django com migrations

### Fonte

GitHub Search API, adaptando a infraestrutura do STAR-RG/django-smells.
Referencia: https://github.com/STAR-RG/django-smells

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

### Associacao migration -> codigo (Git)

Definicao operacional: **os arquivos alterados no mesmo commit que introduziu a migration**.

- `git log --diff-filter=A` para encontrar o commit que adicionou cada migration
- `git diff-tree --numstat` para listar arquivos e LOC alteradas nesse commit

### Classificacao de arquivos

Cada arquivo alterado e classificado por seu papel no Django:

| Categoria | Criterio |
|-----------|----------|
| migration | Dentro de /migrations/ |
| model | models.py ou /models/ |
| view | views.py ou /views/ |
| serializer | serializers.py ou /serializers/ |
| form | forms.py ou /forms/ |
| admin | admin.py |
| test | Contém 'test' no caminho |
| url | urls.py |
| template | Arquivo .html |
| other_python | Outros .py |
| other | Demais arquivos |

## Metricas

1. **Code churn**: LOC adicionadas + removidas (excluindo migrations)
2. **Spread**: Numero de arquivos de codigo alterados
3. **Co-evolution ratio**: Proporcao de migration commits com mudancas de codigo
4. **Category distribution**: Quais camadas sao afetadas
5. **Operation type distribution**: Frequencia de cada tipo de operacao

## Ameacas a Validade

Ver [05-decisoes.md](05-decisoes.md) para discussao detalhada de limitacoes e decisoes metodologicas.
