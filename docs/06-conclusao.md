# 6 Conclusão

Este trabalho investigou empiricamente os padrões de co-evolução entre schema de banco de dados e código de aplicação em 124 projetos Django open-source, analisando 11.624 pares migration-commit que contêm 34.345 operações de schema. A análise combinou parsing AST de migrations Django com dados de histórico Git para quantificar o grau de acoplamento, mapear a propagação por camada arquitetural e comparar aplicações full-stack com bibliotecas reutilizáveis. Esta seção resume as contribuições, discute as limitações e propõe direções para trabalhos futuros.

---

## 6.1 Contribuições

### 6.1.1 Co-evolução schema-código é a norma em Django (RQ1)

O estudo revelou que 82,7% dos commits que introduzem migrations também alteram código da aplicação, com mediana per-repo de 90,3%. Esse resultado é consideravelmente mais alto do que o observado por Vassiliadis et al. (2023) em projetos FOSS genéricos, onde a evolução sincronizada entre schema e código foi classificada como "relativamente incomum". A explicação reside no fluxo de trabalho do Django: o comando `makemigrations` gera migrations a partir de alterações em `models.py`, e ambos são tipicamente commitados juntos. Esse fluxo cria um acoplamento temporal natural que não existe em abordagens com SQL embutido.

O commit típico de co-evolução altera 7 arquivos e modifica 120 linhas de código (medianas), embora a presença de kitchen-sink commits eleve significativamente as médias. Esses números fornecem uma referência quantitativa inédita para o ecossistema Django.

### 6.1.2 Impacto além das camadas clássicas (RQ2)

A análise por camada arquitetural revelou que o impacto de mudanças de schema vai além das camadas tipicamente associadas ao ORM. As categorias `other_python` (21,1%) e `test` (16,3%) são mais frequentemente co-modificadas do que `model` (7,8%) e `view` (5,4%), indicando que configurações, utilitários e testes absorvem uma parcela substancial do esforço de co-evolução.

O cruzamento entre tipo de operação e camada revelou padrões distintos: operações destrutivas (`DeleteModel`, `RemoveField`) co-evoluem mais fortemente com testes do que operações aditivas, sugerindo que a remoção de funcionalidades exige maior esforço de atualização de testes. `CreateModel` gera o maior spread médio (53 arquivos), confirmando que a introdução de novos modelos tem impacto amplo na aplicação.

### 6.1.3 Bibliotecas têm acoplamento mais forte que aplicações (RQ3)

Contrariamente à hipótese inicial, bibliotecas Django apresentam co-evolution ratio mais alto (91,6%) do que aplicações full-stack (81,8%). A explicação é que o co-evolution ratio mede acoplamento *dentro do repositório*, e bibliotecas, por terem escopo mais restrito, são proporcionalmente mais impactadas por cada mudança de schema. Além disso, bibliotecas dedicam ~28% das mudanças co-evoluídas a testes (versus ~16% em apps), refletindo a importância de testes abrangentes para garantir compatibilidade com projetos consumidores.

Esse achado tem implicações práticas: mantenedores de bibliotecas Django devem planejar mudanças de schema com atenção particular à atualização de testes, pois o impacto relativo é significativamente maior do que em aplicações.

### 6.1.4 Pipeline reprodutível

O estudo disponibiliza uma pipeline completa e open-source para mineração, extração e análise de co-evolução schema-código em projetos Django, composta por scripts Python que podem ser executados de forma independente. A pipeline processa desde a busca de repositórios na GitHub API até a geração de métricas de co-evolução por camada e tipo de operação.

---

## 6.2 Limitações

As limitações deste estudo, discutidas em detalhe na Seção 4.5, são sintetizadas a seguir.

### 6.2.1 Definição de co-evolução

A definição same-commit utilizada neste estudo é a mais simples e reprodutível, mas possui limitações conhecidas. Commits com muitas alterações não relacionadas (kitchen-sink commits) podem inflar o co-evolution ratio, enquanto adaptações de código feitas em commits posteriores à migration não são capturadas. A análise com filtro de outliers (máximo 50 arquivos por commit) mostrou que o ratio se mantém em 84,3%, sugerindo que o efeito dos kitchen-sink commits é moderado.

### 6.2.2 Classificação heurística de camadas

A classificação de arquivos por camada é baseada em padrões de nomenclatura e pode ser imprecisa em projetos que não seguem as convenções padrão do Django. Arquivos em categorias como `other_python` (21,1% das ocorrências) não são classificados por camada específica, limitando a granularidade da análise.

### 6.2.3 Representatividade do corpus

O corpus é composto exclusivamente por projetos open-source hospedados no GitHub com pelo menos 20 estrelas e 15 migrations, o que introduz viés em favor de projetos mais populares e maduros. Os resultados podem não ser generalizáveis para projetos industriais, projetos pequenos ou projetos que utilizam outros frameworks ORM.

### 6.2.4 Causalidade

O estudo mede correlação temporal (co-ocorrência no mesmo commit), não causalidade. O fato de um arquivo ser alterado no mesmo commit que uma migration não prova que a alteração foi motivada pela mudança de schema. Essa limitação é compartilhada com estudos anteriores na área (QIU; LI; SU, 2013).

---

## 6.3 Trabalhos Futuros

Os resultados deste estudo abrem diversas direções para investigação futura:

1. **Análise temporal.** Investigar como o co-evolution ratio varia ao longo do ciclo de vida dos projetos — se a co-evolução é mais forte no início (quando o schema está em formação) e diminui à medida que o schema estabiliza, como sugerido por Vassiliadis et al. (2023).

2. **Janela temporal expandida.** Relaxar a definição same-commit para incluir adaptações de código em commits próximos (por exemplo, nos 3 commits seguintes à migration), quantificando a co-evolução tardia que a definição atual não captura.

3. **Análise qualitativa.** Complementar a análise quantitativa com inspeção manual de uma amostra de commits para classificar os tipos de adaptação de código (correção de referências, adição de funcionalidade, refactoring) e verificar a precisão da definição same-commit.

4. **Outros frameworks ORM.** Replicar o estudo em outros ecossistemas com mecanismos de migration estruturados, como Ruby on Rails (Active Record Migrations), Laravel (Eloquent Migrations) ou Alembic (SQLAlchemy), para verificar se os padrões observados são específicos do Django ou generalizáveis a frameworks ORM modernos.

5. **Ferramentas de suporte.** Utilizar os padrões identificados (como a forte co-evolução entre operações destrutivas e testes) para desenvolver ferramentas que alertem desenvolvedores quando uma mudança de schema pode exigir atualização em camadas específicas da aplicação.

6. **Análise de acoplamento total em bibliotecas.** Investigar o impacto de mudanças de schema de bibliotecas nos projetos que as consomem, medindo o acoplamento *total* (intra-repo + inter-repo) que este estudo captura apenas parcialmente.
