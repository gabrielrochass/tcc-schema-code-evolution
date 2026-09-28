# Perguntas de Pesquisa

## RQ1: Quais tipos de operacoes de schema estao associados a maior impacto no codigo?

**Medir:** Code churn (LOC adicionadas + removidas) e spread (arquivos afetados) por tipo de operacao (AddField, CreateModel, AlterField, etc.)

**Dados:** Extraidos via AST parsing das migrations + git diff-tree dos commits correspondentes.

**Hipotese:** CreateModel e DeleteModel devem ter maior impacto que AlterField, pois envolvem criacao/remocao de entidades inteiras.

## RQ2: Como a coevolucao entre migrations e codigo se manifesta em projetos Django?

**Medir:** Co-evolution ratio (proporcao de commits com migration que tambem alteram codigo nao-migration), distribuicao de categorias de arquivo afetadas.

**Dados:** Classificacao dos arquivos alterados por papel no Django (model, view, admin, test, serializer, form, template, url).

**Hipotese:** A maioria dos commits que incluem migrations tambem incluem mudancas em models.py e em pelo menos uma camada downstream (views, admin, tests).

## RQ3 (bonus): Qual a extensao de mudancas em cada camada da aplicacao quando o schema evolui?

**Medir:** Distribuicao detalhada por categoria de arquivo, agrupada por tipo de operacao.

**Dados:** Mesmos da RQ1/RQ2, com cruzamento tipo_operacao x categoria_arquivo.

**Hipotese:** Mudancas de schema propagam de forma desigual — models.py e admin.py sao mais frequentemente afetados que templates ou URLs.

---

## Notas

- Todas as RQs sao respondidas com a **mesma pipeline de dados**: migration AST -> git log -> git diff-tree -> metricas.
- A definicao operacional de "co-evolucao" e: **arquivos alterados no mesmo commit que introduziu a migration**.
- Essa definicao tem limitacoes conhecidas (ver docs/05-decisoes.md), mas e reprodutivel e automatizavel.
