# 3 Trabalhos Relacionados

Este capítulo revisa a literatura sobre co-evolução entre schema e código em aplicações de banco de dados. A Seção 3.1 apresenta os estudos empíricos que investigaram esse fenômeno. A Seção 3.2 discute abordagens de detecção e prevenção de inconsistências causadas por evolução de schema. A Seção 3.3 examina trabalhos sobre evolução de schema em larga escala. A Seção 3.4 apresenta estudos sobre práticas de acesso a banco de dados e ORM. Por fim, a Seção 3.5 posiciona este trabalho em relação à literatura existente por meio de uma tabela comparativa.

---

## 3.1 Estudos Empíricos de Co-evolução Schema-Código

### 3.1.1 Qiu, Li e Su (2013)

Qiu, Li e Su (2013) conduziram o primeiro estudo empírico em larga escala sobre a co-evolução entre schema de banco de dados e código de aplicação. Os autores analisaram dez aplicações open-source de grande porte baseadas em Java, totalizando mais de 160.000 revisões em repositórios de controle de versão. O estudo focou em aplicações que utilizam JDBC (Java Database Connectivity), onde as consultas SQL são escritas diretamente no código-fonte como strings.

As principais contribuições e achados do estudo foram:

- **Frequência de mudanças de schema:** os schemas dos projetos analisados evoluem com frequência ao longo do ciclo de vida da aplicação, com distribuições similares de tipos de mudança entre diferentes projetos.
- **Impacto no código:** mudanças de schema induzem modificações significativas no código da aplicação. Determinados tipos de mudança (como remoção de tabelas ou colunas) causam mais impacto do que outros (como adição de colunas).
- **Análise de co-change:** os autores demonstraram que a análise de co-mudança (identificação de arquivos frequentemente modificados juntos) pode ser uma abordagem viável para automatizar ou assistir a evolução de aplicações de banco de dados.

A metodologia de Qiu et al. baseou-se na extração de mudanças de schema diretamente dos scripts SQL e do histórico de commits dos repositórios. Essa abordagem, embora eficaz para aplicações com SQL embutido, apresenta limitações quando aplicada a projetos que utilizam ORM, onde as interações com o banco de dados são mediadas por uma camada de abstração e as mudanças de schema são formalizadas por mecanismos específicos do framework (como as migrations do Django).

### 3.1.2 Vassiliadis et al. (2023)

Vassiliadis et al. (2023) realizaram um estudo de co-evolução em maior escala, analisando 195 projetos FOSS (Free and Open Source Software) hospedados no GitHub. O trabalho focou na relação temporal entre evolução de schema e evolução do código-fonte, utilizando um dataset previamente construído de histórias de evolução de schema.

Os principais achados foram:

- **Comportamentos diversos:** os projetos exibem padrões variados de co-evolução, com apenas uma pequena fração demonstrando evolução sincronizada entre schema e código.
- **Avanço precoce do schema:** a grande maioria dos schemas demonstra concentração de mudanças no início do ciclo de vida do projeto, com atividade de evolução diminuindo gradualmente ao longo do tempo.
- **Ritmos diferentes:** schema e código-fonte tipicamente evoluem em ritmos distintos, com schemas tendendo a atrair mudanças precocemente e depois gravitando em direção à inatividade.

Esse estudo é relevante para o presente trabalho porque demonstra que a co-evolução schema-código não é um fenômeno uniforme — projetos diferentes exibem padrões distintos, o que motiva a investigação de fatores que possam explicar essa variação (como a natureza do projeto, conforme proposto na RQ3 deste trabalho).

---

## 3.2 Detecção de Inconsistências Schema-Código

### 3.2.1 Meurice, Nagy e Cleve (2016)

Meurice, Nagy e Cleve (2016) abordaram o problema da co-evolução schema-código sob a perspectiva da detecção e prevenção de inconsistências. Enquanto Qiu et al. (2013) focaram na caracterização empírica do fenômeno, Meurice et al. propuseram uma abordagem automatizada para identificar trechos de código que se tornam inconsistentes após uma mudança de schema.

O trabalho parte da observação de que, em muitos projetos, mudanças de schema e adaptações no código não ocorrem de forma sincronizada, gerando janelas de inconsistência onde o código referencia elementos do schema que foram removidos, renomeados ou modificados. Os autores desenvolveram uma abordagem baseada em análise estática que:

- Extrai as dependências entre o código da aplicação e o schema do banco de dados.
- Detecta automaticamente quando uma mudança de schema quebra uma dessas dependências.
- Sugere adaptações necessárias no código para restaurar a consistência.

A contribuição principal é demonstrar que a detecção automatizada de inconsistências schema-código é viável e pode ser integrada ao fluxo de desenvolvimento para prevenir bugs relacionados à evolução de schema. No entanto, a abordagem foi avaliada em aplicações Java com SQL embutido, e sua aplicabilidade a frameworks ORM como Django não foi investigada.

### 3.2.2 Meurice e Cleve (2014) — DAHLIA

Meurice e Cleve (2014) desenvolveram DAHLIA (Database ScHema EvoLutIon Analysis), uma ferramenta de análise visual que minera o histórico de evolução de schema a partir de repositórios de software e permite sua análise interativa. DAHLIA reconstrói a história de mudanças do schema commit a commit, identificando operações como criação de tabelas, adição de colunas e alteração de restrições.

A ferramenta é relevante para este trabalho porque demonstra a viabilidade da extração automatizada de operações de schema a partir do histórico de commits — a mesma abordagem fundamental utilizada neste estudo, embora aplicada a um contexto diferente (SQL embutido vs. migrations Django).

---

## 3.3 Evolução de Schema em Larga Escala

### 3.3.1 Cleve et al. (2015)

Cleve et al. (2015) conduziram um estudo de caso detalhado sobre evolução de schema de banco de dados, examinando como mudanças de requisitos são propagadas para schemas, dados e programas. O trabalho analisou o sistema de gestão acadêmica da Universidade de Namur ao longo de 18 anos de evolução, documentando 320 mudanças de schema.

Os autores identificaram padrões recorrentes de evolução, como:

- Mudanças de schema motivadas por novas funcionalidades versus mudanças motivadas por refatoração.
- Cascatas de propagação: como uma mudança em uma tabela pode exigir ajustes em múltiplas partes do sistema.
- A importância da documentação e rastreabilidade das mudanças de schema para a manutenção de longo prazo.

Embora o estudo seja focado em um único sistema, suas observações sobre padrões de propagação de mudanças são diretamente relevantes para a RQ2 deste trabalho, que investiga quais camadas da arquitetura Django são mais frequentemente afetadas por mudanças de schema.

### 3.3.2 Curino, Moon e Zaniolo (2008) — PRISM

Curino, Moon e Zaniolo (2008) desenvolveram o PRISM workbench, um sistema para gerenciar a evolução de schema de forma controlada e reprodutível. Embora o foco de PRISM seja na gestão (e não na análise empírica) da evolução de schema, o trabalho é relevante porque introduziu uma taxonomia de operações de evolução de schema que influenciou estudos posteriores, incluindo a categorização utilizada no ecossistema Django.

PRISM demonstrou que a evolução de schema pode ser tratada como uma sequência de operações atômicas bem definidas — uma abordagem que o Django adotou posteriormente com seu sistema de migrations, onde cada migration contém uma lista explícita de operações tipadas (CreateModel, AddField, etc.).

---

## 3.4 Acesso a Banco de Dados e ORM

### 3.4.1 Yang, Li e Bhatt (2016)

Yang, Li e Bhatt (2016) realizaram um estudo empírico sobre a prática de manutenção de código ORM (Object-Relational Mapping) em projetos open-source. Os autores analisaram a evolução de código ORM em projetos Java que utilizam Hibernate, medindo métricas como densidade de código ORM, frequência de mudanças e complexidade dos commits que modificam código ORM.

Os principais achados relevantes para este trabalho foram:

- Commits que modificam código ORM são mais complexos que commits que modificam outros tipos de código.
- A configuração do mapeamento objeto-relacional evolui com frequência e é uma fonte significativa de mudanças.
- A camada de acesso a dados (equivalente aos models no Django) concentra a maioria das mudanças relacionadas ao ORM.

Esse estudo complementa a perspectiva deste trabalho ao examinar a evolução sob a ótica do ORM (em vez do SQL embutido), embora em um ecossistema diferente (Java/Hibernate vs. Python/Django).

### 3.4.2 Chen et al. (2024)

Chen et al. (2024) conduziram um estudo empírico sobre as características de bugs de acesso a banco de dados em aplicações Java. Os autores analisaram 423 bugs em sete aplicações open-source de grande porte, classificando-os em categorias de causa raiz.

Um achado relevante é que bugs relacionados ao schema (como referências a colunas ou tabelas que foram removidas ou renomeadas) representam uma parcela significativa dos bugs de acesso a banco de dados. Isso reforça a motivação deste trabalho: a falta de coordenação entre evolução de schema e adaptação do código é uma fonte real e mensurável de defeitos de software.

---

## 3.5 Posicionamento deste Trabalho

A tabela a seguir posiciona este trabalho em relação à literatura revisada, destacando as diferenças em contexto, escala, metodologia e foco.

| Aspecto | Qiu et al. (2013) | Meurice et al. (2016) | Vassiliadis et al. (2023) | Cleve et al. (2015) | Yang et al. (2016) | **Este trabalho** |
|---------|-------------------|----------------------|--------------------------|--------------------|--------------------|-------------------|
| **Contexto** | Java/JDBC | Java/JDBC | Misto (SQL) | Sistema único | Java/Hibernate | **Python/Django** |
| **Mecanismo de schema** | SQL embutido | SQL embutido | Scripts SQL | Scripts SQL | ORM (Hibernate) | **Migrations Django** |
| **Escala** | 10 projetos | 3 projetos | 195 projetos | 1 projeto | 7 projetos | **124 projetos** |
| **Foco** | Co-evolução empírica | Detecção inconsistências | Padrões temporais | Estudo de caso | Manutenção ORM | **Co-evolução por camada** |
| **Extração schema** | Parsing SQL | Análise estática | Parsing SQL | Manual | Parsing config ORM | **AST de migrations** |
| **Classificação arquitetural** | Não | Não | Não | Parcial | Não | **Sim (8 camadas)** |
| **Apps vs Libs** | Não | Não | Não | Não | Não | **Sim (RQ3)** |
| **Tipo de operação** | Categorias genéricas | Categorias genéricas | Categorias genéricas | Categorias manuais | Não | **Operações Django tipadas** |

### 3.5.1 Contribuições diferenciais

Este trabalho se diferencia da literatura existente em quatro aspectos:

1. **Ecossistema Django.** Nenhum estudo anterior investigou co-evolução schema-código especificamente no ecossistema Django, onde o ORM impõe uma estrutura canônica que viabiliza extração automatizada via AST. Estudos anteriores focaram predominantemente em Java com SQL embutido (Qiu et al., 2013; Meurice et al., 2016) ou em datasets heterogêneos com scripts SQL (Vassiliadis et al., 2023).

2. **Classificação por camada arquitetural.** Este é o primeiro estudo a classificar os arquivos co-modificados por seu papel na arquitetura do framework (model, view, admin, serializer, form, template, test, URL), permitindo uma análise mais granular de como mudanças de schema propagam pela aplicação. Estudos anteriores trataram o código da aplicação como uma massa homogênea.

3. **Cruzamento operação × camada.** A análise cruza o tipo de operação de migration (CreateModel, AddField, RemoveField, etc.) com a camada afetada, investigando se diferentes tipos de mudança de schema impactam diferentes partes da arquitetura. Essa dimensão não foi explorada na literatura.

4. **Comparação apps vs bibliotecas.** A segmentação do corpus em aplicações full-stack e bibliotecas reutilizáveis permite investigar se a natureza do projeto influencia os padrões de co-evolução — uma questão inédita na literatura.
