# 5 Resultados

Este capítulo apresenta os resultados obtidos pela aplicação da pipeline de análise descrita na Seção 4 ao corpus de 124 projetos Django open-source. A análise processou 11.624 pares migration-commit extraídos de 122 repositórios. Dos 124 repositórios do corpus, dois não produziram pares válidos devido a históricos Git incompatíveis com a extração. A diferença entre o total de 12.173 arquivos de migration identificados e os 11.624 pares analisados deve-se a migrations cujo commit de introdução não pôde ser determinado (migrations adicionadas via merge, squash ou importação de histórico externo). Os resultados são organizados pelas três perguntas de pesquisa.

---

## 5.1 RQ1: Grau de Acoplamento Schema-Código

*Qual o grau de acoplamento entre mudanças de schema e mudanças no código de aplicação nos commits de projetos Django open-source?*

### 5.1.1 Co-evolution ratio

Dos 11.624 commits que introduziram migrations, 9.616 (82,7%) também alteraram pelo menos um arquivo de código fora do diretório de migrations. Apenas 2.008 commits (17,3%) foram migration-only — ou seja, contêm exclusivamente arquivos de migration sem nenhuma modificação no código da aplicação.

A análise por repositório revela que o acoplamento é ainda mais pronunciado quando medido individualmente: a mediana do co-evolution ratio por repositório é de 90,3%, com intervalo interquartil de 81,6% a 96,9%. A média por repositório é de 86,0% (desvio padrão 17,4%), variando de 3,2% (mínimo) a 100,0% (máximo).

| Métrica | Valor |
|---------|-------|
| Pares migration-commit analisados | 11.624 |
| Commits com co-evolução (código alterado) | 9.616 (82,7%) |
| Commits migration-only | 2.008 (17,3%) |
| Co-evolution ratio por repo (mediana) | 90,3% |
| Co-evolution ratio por repo (IQR) | 81,6% – 96,9% |

Esses resultados indicam que, na grande maioria dos casos, desenvolvedores Django modificam o código da aplicação no mesmo commit em que introduzem uma migration, sugerindo que a co-evolução schema-código é a norma, não a exceção, neste ecossistema.

### 5.1.2 Spread e code churn

Para os 9.616 commits co-evoluídos, a mediana do spread (número de arquivos de código alterados) é de 7,0 arquivos, com intervalo interquartil de 3,0 a 16,0. A média é consideravelmente mais alta (33,9 arquivos), indicando a presença de outliers — commits com centenas de arquivos alterados (kitchen-sink commits).

O code churn (linhas adicionadas + removidas) apresenta padrão similar: mediana de 120 LOC e média de 5.681 LOC, com intervalo interquartil de 30 a 531 LOC.

| Métrica | Mediana | IQR | Média |
|---------|---------|-----|-------|
| Spread (arquivos) | 7,0 | 3,0 – 16,0 | 33,9 |
| Code churn (LOC) | 120,0 | 30,0 – 531,0 | 5.681,2 |

### 5.1.3 Efeito do filtro de outliers

Ao aplicar o filtro de outliers (commits com no máximo 50 arquivos alterados), 1.514 commits são removidos (13,0%), restando 10.110 pares. O co-evolution ratio sobe ligeiramente para 84,3%, a mediana do spread cai para 6,0 arquivos e a mediana do churn para 94 LOC. Esses valores filtrados representam melhor o commit típico de co-evolução schema-código: uma mudança que afeta 6 arquivos e modifica aproximadamente 100 linhas de código.

### 5.1.4 Discussão

O co-evolution ratio de 82,7% (mediana per-repo 90,3%) é consideravelmente mais alto do que o observado por Vassiliadis et al. (2023), que reportaram que evolução sincronizada entre schema e código é "relativamente incomum" em projetos FOSS genéricos. Essa discrepância pode ser explicada pelo fluxo de trabalho do Django: o comando `makemigrations` é tipicamente executado imediatamente após a alteração de `models.py`, e ambos os arquivos são commitados juntos. Esse fluxo cria uma tendência natural ao acoplamento temporal que não existe em projetos com SQL embutido, onde mudanças de schema podem ser aplicadas independentemente do código.

A diferença entre mediana e média no spread (7,0 vs 33,9) e no churn (120 vs 5.681) evidencia a presença de commits atípicos com alta amplitude. Esses outliers correspondem tipicamente a releases, refactorings massivos ou reorganizações de código que incluem migrations junto com centenas de outras mudanças. O uso da mediana como medida de tendência central é mais representativo do comportamento típico.

---

## 5.2 RQ2: Propagação por Camada e Tipo de Operação

*Quais camadas da arquitetura Django são mais frequentemente co-modificadas em resposta a evoluções de schema, e como essa distribuição se relaciona com o tipo de operação de migration realizada?*

### 5.2.1 Distribuição por camada arquitetural

A Tabela a seguir apresenta a distribuição dos arquivos co-modificados por camada arquitetural Django, excluindo os próprios arquivos de migration.

| Camada | Ocorrências | Proporção |
|--------|-------------|-----------|
| other (não-Python) | 101.921 | 31,2% |
| other_python | 68.836 | 21,1% |
| test | 53.324 | 16,3% |
| template | 36.649 | 11,2% |
| model | 25.526 | 7,8% |
| view | 17.562 | 5,4% |
| serializer | 6.808 | 2,1% |
| admin | 5.501 | 1,7% |
| form | 5.457 | 1,7% |
| url | 4.584 | 1,4% |

Três observações destacam-se. Primeiro, as categorias `other` e `other_python` dominam a distribuição (52,3% combinadas), indicando que commits com migration frequentemente incluem mudanças em arquivos fora das camadas Django clássicas — como configurações, scripts de deploy, documentação e utilitários. Segundo, `test` é a terceira camada mais afetada (16,3%), evidenciando que testes são frequentemente atualizados em resposta a mudanças de schema. Terceiro, entre as camadas Django específicas, `template` (11,2%) é a mais afetada, seguida por `model` (7,8%), `view` (5,4%), `serializer` (2,1%), `admin` (1,7%), `form` (1,7%) e `url` (1,4%).

### 5.2.2 Co-evolution ratio por tipo de operação

Diferentes tipos de operação de migration apresentam graus distintos de co-evolução com o código da aplicação.

| Operação | Total | Co-evoluídos | Ratio | Spread médio |
|----------|-------|-------------|-------|-------------|
| DeleteModel | 264 | 231 | 87,5% | 35,6 |
| AddField | 4.086 | 3.549 | 86,9% | 39,2 |
| RemoveField | 823 | 715 | 86,9% | 25,3 |
| RenameField | 274 | 238 | 86,9% | 25,5 |
| RenameModel | 76 | 67 | 88,2% | 51,7 |
| RunPython | 1.246 | 1.065 | 85,5% | 36,1 |
| CreateModel | 2.355 | 1.937 | 82,3% | 53,1 |
| AlterField | 4.311 | 3.460 | 80,3% | 24,0 |
| AlterModelOptions | 496 | 383 | 77,2% | 40,1 |
| SeparateDatabaseAndState | 109 | 70 | 64,2% | 42,9 |

Operações destrutivas (`DeleteModel` 87,5%, `RemoveField` 86,9%) e operações que alteram o nome de elementos (`RenameModel` 88,2%, `RenameField` 86,9%) apresentam os maiores ratios de co-evolução, sugerindo que mudanças que quebram referências existentes exigem adaptação imediata do código. `AlterField` (80,3%) apresenta o menor ratio entre as operações comuns, possivelmente porque muitas alterações de campo (como mudanças em `max_length` ou `blank=True`) não exigem adaptação do código.

`CreateModel` tem o maior spread médio (53,1 arquivos), consistente com a hipótese de que a criação de um novo modelo frequentemente demanda views, URLs, admin, templates e testes correspondentes.

### 5.2.3 Cruzamento operação × camada

A tabela a seguir mostra a distribuição proporcional das camadas afetadas para cada tipo de operação (top 5), considerando apenas commits co-evoluídos. Os valores representam a proporção de cada camada no total de arquivos alterados por tipo de operação.

| Operação | model | view | admin | serial. | form | test | template | url | other_py | other |
|----------|-------|------|-------|---------|------|------|----------|-----|----------|-------|
| CreateModel | 6,2% | 6,5% | 1,8% | 1,2% | 1,6% | 10,8% | 13,3% | 1,7% | 19,6% | 37,3% |
| AddField | 6,9% | 5,6% | 1,5% | 2,2% | 1,8% | 14,9% | 11,8% | 1,3% | 18,8% | 35,2% |
| AlterField | 10,3% | 5,0% | 1,7% | 2,9% | 1,7% | 20,4% | 10,4% | 1,3% | 23,4% | 22,9% |
| RemoveField | 10,3% | 5,3% | 2,2% | 2,7% | 2,0% | 20,2% | 9,7% | 1,5% | 22,4% | 23,7% |
| DeleteModel | 9,4% | 4,6% | 1,5% | 3,0% | 1,8% | 21,4% | 8,0% | 1,5% | 22,9% | 25,8% |

Padrões observados:

- **`test` cresce com operações destrutivas:** a proporção de testes co-modificados aumenta de 10,8% em `CreateModel` para 21,4% em `DeleteModel`, sugerindo que a remoção de funcionalidades exige maior atualização de testes.
- **`template` é mais afetada por `CreateModel`** (13,3%) do que por operações de campo (~10%), consistente com a criação de novas páginas e interfaces para novos modelos.
- **`model` tem proporção menor em `CreateModel`** (6,2%) do que em operações de campo (~10%), o que é contra-intuitivo à primeira vista, mas se explica pelo fato de que `CreateModel` gera commits com mais arquivos de outras camadas (views, templates, URLs), diluindo a proporção relativa de models.
- **`serializer` é mais afetada por operações destrutivas** (2,7-3,0%) do que aditivas (1,2-2,2%), indicando que APIs REST requerem atualização quando campos ou modelos são removidos.

---

## 5.3 RQ3: Aplicações vs Bibliotecas

*Os padrões de co-evolução observados diferem entre aplicações Django full-stack e bibliotecas reutilizáveis?*

### 5.3.1 Visão geral

O corpus original contém 86 aplicações e 38 bibliotecas (124 repositórios). Dos 122 que produziram pares válidos, 85 são aplicações (10.564 pares migration-commit) e 37 são bibliotecas (1.060 pares). A diferença de escala reflete a composição do corpus: aplicações concentram 90,9% dos pares, pois possuem significativamente mais migrations por repositório.

| Métrica | Apps (85 repos) | Libs (37 repos) |
|---------|----------------|----------------|
| Pares migration-commit | 10.564 | 1.060 |
| Co-evolution ratio | 81,8% | 91,6% |
| Co-evolution ratio per-repo (mediana) | 89,4% | 94,4% |
| Spread mediano | 7,0 | 7,0 |
| Churn mediano (LOC) | 117,0 | 177,0 |

### 5.3.2 Co-evolution ratio

Contrariamente à hipótese inicial — de que bibliotecas apresentariam co-evolution ratio menor por terem código downstream em repositórios de terceiros — as bibliotecas apresentam ratio significativamente mais alto (91,6%) do que as aplicações (81,8%). A mediana per-repo confirma essa tendência: 94,4% para libs versus 89,4% para apps.

Essa descoberta pode ser explicada por dois fatores. Primeiro, bibliotecas Django tipicamente possuem escopo mais restrito e schemas menores, o que significa que cada mudança de schema tem maior probabilidade de afetar uma proporção significativa do código do repositório. Segundo, bibliotecas frequentemente incluem testes extensivos como parte do pacote — mudanças no schema quase sempre exigem atualização dos testes, que residem no próprio repositório.

### 5.3.3 Diferenças na distribuição por camada

A distribuição por camada arquitetural revela diferenças relevantes entre os dois grupos:

| Camada | Apps | Libs | Diferença |
|--------|------|------|-----------|
| model | 7,4% | 14,4% | +7,0 pp |
| test | 15,7% | 27,6% | +11,9 pp |
| template | 11,6% | 5,6% | -6,0 pp |
| serializer | 2,2% | 0,6% | -1,6 pp |
| admin | 1,6% | 3,0% | +1,4 pp |
| other | 31,8% | 22,3% | -9,5 pp |

Três diferenças são particularmente expressivas:

1. **Testes (27,6% libs vs 15,7% apps):** bibliotecas dedicam uma proporção quase duas vezes maior de suas mudanças co-evoluídas a testes. Isso é consistente com a prática de desenvolvimento de bibliotecas, onde testes abrangentes são essenciais para garantir compatibilidade com projetos consumidores.

2. **Models (14,4% libs vs 7,4% apps):** bibliotecas têm maior proporção de mudanças em models, refletindo que seus repositórios são mais focados na camada de dados — o schema é o produto principal da lib.

3. **Templates (5,6% libs vs 11,6% apps):** aplicações têm o dobro da proporção de templates, o que é esperado — apps possuem interfaces de usuário completas, enquanto a maioria das bibliotecas não inclui templates ou inclui apenas templates minimalistas para admin.

### 5.3.4 Discussão

Os resultados da RQ3 refutam a hipótese inicial de que bibliotecas teriam menor acoplamento schema-código. Na prática, o oposto foi observado: bibliotecas apresentam acoplamento mais forte, com co-evolution ratio de 91,6% versus 81,8% das aplicações. Essa inversão sugere que a natureza do projeto influencia os padrões de co-evolução, mas em direção oposta à esperada.

A explicação mais provável é que o co-evolution ratio mede acoplamento *dentro do repositório*, não acoplamento total. Bibliotecas podem ter menor acoplamento *total* (considerando código em projetos consumidores), mas dentro de seus próprios repositórios, cada mudança de schema tem impacto proporcionalmente maior. Aplicações, por outro lado, são sistemas maiores onde uma mudança pontual de schema pode afetar apenas uma fração do código total.

Essa distinção tem implicações práticas: mantenedores de bibliotecas Django devem estar cientes de que mudanças de schema têm alto impacto relativo em seus repositórios, especialmente na camada de testes, e planejar mudanças de schema com atenção particular à atualização de testes.

---

## 5.4 Resumo dos Resultados

| RQ | Achado principal |
|----|-----------------|
| **RQ1** | O co-evolution ratio global é de 82,7% (mediana per-repo 90,3%). Commits com migration tipicamente alteram 7 arquivos e 120 LOC de código (medianas). Co-evolução é a norma em projetos Django. |
| **RQ2** | As camadas mais afetadas são `other_python` (21,1%), `test` (16,3%) e `template` (11,2%). Operações destrutivas (Delete/Remove) co-evoluem mais com testes; `CreateModel` gera maior spread (53 arquivos). |
| **RQ3** | Bibliotecas têm co-evolution ratio mais alto (91,6%) que aplicações (81,8%), contrariando a hipótese inicial. Libs dedicam ~28% das mudanças co-evoluídas a testes (vs 16% em apps). |
