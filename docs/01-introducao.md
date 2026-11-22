# 1 Introdução

Sistemas de software que utilizam bancos de dados relacionais dependem de um esquema (schema) que define a estrutura das tabelas, colunas, tipos de dados e restrições de integridade. Esse esquema não é estático: ao longo do ciclo de vida de uma aplicação, mudanças nos requisitos de negócio, correções de defeitos e otimizações de desempenho frequentemente exigem alterações na estrutura do banco de dados. Quando o schema muda — novas tabelas são criadas, campos são adicionados, colunas são removidas — o código da aplicação que interage com esses dados frequentemente precisa ser adaptado para refletir a nova estrutura. Esse fenômeno de modificação coordenada entre a estrutura do banco de dados e o código que a utiliza é denominado co-evolução schema-código (QIU; LI; SU, 2013).

A co-evolução schema-código é um problema relevante para a manutenção de software. Estudos anteriores demonstraram que a falta de sincronização entre mudanças de schema e adaptações no código é uma fonte significativa de defeitos em aplicações de banco de dados (MEURICE; NAGY; CLEVE, 2016). Quando um desenvolvedor modifica o schema sem atualizar todas as partes do código que dependem da estrutura anterior, o resultado pode ser erros em tempo de execução, perda de dados ou comportamento incorreto da aplicação. Liu, Mondal e Chen (2024) constataram que bugs relacionados a schema, consultas SQL e APIs de acesso a dados representam 84,2% dos defeitos de acesso a banco de dados em aplicações Java de grande porte.

Apesar da relevância desse problema, a literatura existente sobre co-evolução schema-código apresenta lacunas importantes. Os estudos empíricos de maior escala (QIU; LI; SU, 2013; VASSILIADIS et al., 2023) focaram predominantemente em sistemas que utilizam SQL explicitamente embutido no código-fonte, onde as consultas são escritas como strings dentro de classes Java via JDBC. Pouco se sabe sobre como a co-evolução se manifesta em frameworks que adotam o padrão ORM (Object-Relational Mapping), nos quais a interação com o banco de dados é mediada por uma camada de abstração e as mudanças de schema são formalizadas por mecanismos específicos do framework.

O ecossistema Django, um dos frameworks de desenvolvimento web mais adotados na linguagem Python, representa uma oportunidade particularmente favorável para o estudo empírico de co-evolução schema-código. Desde a versão 1.7, o Django disponibiliza um sistema de migrations: arquivos Python gerados automaticamente a partir de alterações nas definições de modelo (`models.py`) que descrevem, de forma estruturada e tipada, as operações de evolução do schema relacional. Essa padronização confere três propriedades que viabilizam a análise sistemática em larga escala. Primeiro, as mudanças de schema são rastreáveis como arquivos versionados no sistema de controle de versão (Git), o que permite associar cada migration ao commit que a introduziu. Segundo, as operações de schema são estruturadas e passíveis de extração automatizada via parsing da Abstract Syntax Tree (AST) do Python, sem necessidade de executar o código ou instalar dependências do projeto. Terceiro, o fluxo causal é bem definido: o desenvolvedor altera `models.py`, o comando `makemigrations` gera a migration, e o commit registra ambas as mudanças junto com eventuais adaptações no restante do código.

Além disso, a arquitetura do Django organiza o código da aplicação em camadas com responsabilidades bem definidas — models, views, admin, serializers, forms, templates, URLs e testes — cada uma com um grau distinto de acoplamento com o schema do banco de dados. Essa separação arquitetural permite uma análise mais granular do que a oferecida por estudos anteriores, que trataram o código da aplicação como uma massa homogênea: é possível identificar não apenas se o código foi co-modificado com o schema, mas especificamente quais camadas da arquitetura foram afetadas.

## 1.1 Objetivo

Este trabalho tem como objetivo investigar empiricamente os padrões de co-evolução entre schema de banco de dados e código de aplicação em projetos Django open-source, utilizando uma abordagem de Mineração de Repositórios de Software (MSR). Especificamente, o estudo busca caracterizar o grau de acoplamento entre mudanças de schema e mudanças no código, mapear como essas mudanças propagam pelas camadas da arquitetura Django e verificar se a natureza do projeto (aplicação full-stack versus biblioteca reutilizável) influencia os padrões observados.

## 1.2 Perguntas de Pesquisa

Três perguntas de pesquisa guiam a investigação, construindo uma narrativa progressiva que parte da quantificação do fenômeno, avança para sua decomposição por camada e tipo de operação, e conclui com a análise de fatores que podem explicar variações nos padrões observados:

**RQ1: Qual o grau de acoplamento entre mudanças de schema e mudanças no código de aplicação nos commits de projetos Django open-source?**

Esta pergunta mede o co-evolution ratio — a proporção de commits que introduzem migrations e que também alteram arquivos de código fora do diretório de migrations. A hipótese é que a maioria dos commits com migration também altera `models.py` (pois `makemigrations` parte de mudanças no modelo), mas uma parcela relevante não alcança camadas downstream como views, admin e testes, indicando acoplamento parcial.

**RQ2: Quais camadas da arquitetura Django são mais frequentemente co-modificadas em resposta a evoluções de schema, e como essa distribuição se relaciona com o tipo de operação de migration realizada?**

Esta pergunta cruza duas dimensões: a camada arquitetural afetada (model, view, admin, serializer, form, template, test, URL) e o tipo de operação de migration (CreateModel, AddField, RemoveField, AlterField, entre outros). A hipótese é que operações de ciclo de vida do modelo (CreateModel, DeleteModel) afetam mais camadas do que operações pontuais de campo (AddField, AlterField), pois a criação de um novo modelo frequentemente demanda views, URLs, admin e testes correspondentes.

**RQ3: Os padrões de co-evolução observados diferem entre aplicações Django full-stack e bibliotecas reutilizáveis?**

Esta pergunta compara as métricas de RQ1 e RQ2 entre dois grupos: aplicações full-stack (que possuem o ciclo completo de models, views, templates e admin) e bibliotecas reutilizáveis (que expõem models mas cujo código downstream reside em projetos de terceiros). A hipótese é que bibliotecas apresentam co-evolution ratio menor, pois mudanças de schema em libs propagam para código fora do repositório analisado.

## 1.3 Contribuições

Este trabalho oferece quatro contribuições:

1. **Caracterização empírica do acoplamento schema-código em Django.** Quantificação do co-evolution ratio, code churn e spread em 124 projetos Django open-source, fornecendo o primeiro retrato empírico desse fenômeno no ecossistema Django.

2. **Mapeamento da propagação por camada arquitetural.** Identificação de quais camadas da arquitetura Django (model, view, admin, serializer, form, template, test, URL) são mais frequentemente afetadas por mudanças de schema, cruzada com o tipo de operação de migration — uma dimensão de análise inédita na literatura.

3. **Comparação entre aplicações e bibliotecas.** Segmentação do corpus em 86 aplicações full-stack e 38 bibliotecas reutilizáveis para investigar se a natureza do projeto influencia os padrões de co-evolução — uma questão não explorada em trabalhos anteriores.

4. **Pipeline reprodutível.** Disponibilização de scripts open-source para mineração de repositórios Django, extração de operações de migration via AST e análise de co-evolução, permitindo reprodução e extensão dos resultados.

## 1.4 Estrutura do Documento

O restante deste documento está organizado da seguinte forma. A Seção 2 apresenta a fundamentação teórica, cobrindo evolução de schema, o sistema de migrations do Django, Mineração de Repositórios de Software e o conceito de co-evolução schema-código. A Seção 3 revisa os trabalhos relacionados e posiciona este estudo em relação à literatura existente. A Seção 4 detalha a metodologia, incluindo o processo de seleção do corpus, a pipeline de extração e análise, e as métricas utilizadas. A Seção 5 apresenta os resultados obtidos para cada pergunta de pesquisa. Por fim, a Seção 6 discute as conclusões, limitações e direções para trabalhos futuros.
