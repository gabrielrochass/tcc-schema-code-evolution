# Papers de Referencia

Mapeamento dos papers citados no TCC, sua contribuicao e relacao com nosso trabalho.

---

## Visao Geral

```
NOSSO TCC usa cada paper assim:

  Motivacao (POR QUE importa)
  |-- Meurice et al. 2016 --- inconsistencias schema-codigo sao reais e detectaveis
  +-- Liu et al. 2024 ------ geram bugs mensuraveis (84% dos bugs de acesso a BD)

  Base conceitual (COMO pensar)
  |-- Curino et al. 2008 --- taxonomia de operacoes atomicas de schema
  +-- Cleve et al. 2015 ---- padroes de propagacao em cascata

  Precedente metodologico (COMO fazer)
  |-- Qiu et al. 2013 ------ co-evolucao empirica em larga escala (nosso "baseline")
  |-- Vassiliadis et al. 2023  escala + padroes temporais (195 projetos FOSS)
  +-- Meurice & Cleve 2014 - mineracao de schema via Git (DAHLIA)

  Contexto ORM (ONDE nos situamos)
  +-- Chen et al. 2016 ----- unico estudo empirico sobre manutencao ORM

  LACUNA --> Ninguem fez isso em Django, por camada arquitetural, apps vs libs
```

---

## Fichas Individuais

### 1. Qiu, Li e Su (2013) — Fundacao direta

| | |
|---|---|
| **Titulo** | An Empirical Analysis of the Co-evolution of Schema and Code in Database Applications |
| **Venue** | FSE 2013 |
| **Arquivo** | `An Empirical Analysis of the Co-evolution of Schema and Code in Database Applications.pdf` |
| **Contexto** | 10 apps Java/JDBC, 160K revisoes |
| **Metodo** | Parsing de SQL embutido no codigo + analise de commits |

**Achados-chave:**
- Schemas evoluem frequentemente ao longo do ciclo de vida
- Mudancas de schema induzem modificacoes significativas no codigo
- Remocao de tabelas/colunas causa mais impacto que adicao
- Analise de co-change e viavel para assistir evolucao de BD

**Relacao com nosso TCC:**
Trabalho mais proximo do nosso — fazemos o "mesmo estudo" em contexto diferente (Django/ORM vs Java/JDBC). Nossos diferenciais: classificacao por camada arquitetural, operacoes tipadas via AST, comparacao apps vs libs.

---

### 2. Meurice, Nagy e Cleve (2016) — Motivacao do problema

| | |
|---|---|
| **Titulo** | Detecting and Preventing Program Inconsistencies Under Database Schema Evolution |
| **Venue** | ICSME 2016 |
| **Arquivo** | `Detecting and Preventing Program Inconsistencies Under Database Schema Evolution.pdf` |
| **Contexto** | 3 apps Java/JDBC |
| **Metodo** | Analise estatica de dependencias codigo → schema |

**Achados-chave:**
- Inconsistencias schema-codigo sao comuns e detectaveis automaticamente
- Existem janelas de inconsistencia entre mudanca de schema e adaptacao do codigo
- Deteccao automatizada e viavel e integravel ao fluxo de desenvolvimento

**Relacao com nosso TCC:**
Reforca *por que* co-evolucao importa — falta de sincronia gera bugs. Nosso RQ1 (co-evolution ratio) mede exatamente esse fenomeno: quantos commits sincronizam vs. deixam pra depois.

---

### 3. Vassiliadis et al. (2023) — Escala e padroes temporais

| | |
|---|---|
| **Titulo** | Joint Source and Schema Evolution: Insights from a Study of 195 FOSS Projects |
| **Venue** | EDBT 2023 |
| **Arquivo** | `Joint Source and Schema Evolution - Vassiliadis et al 2023.pdf` |
| **Contexto** | 195 projetos FOSS, scripts SQL |
| **Metodo** | Analise temporal de historias de evolucao de schema |

**Achados-chave:**
- Poucos projetos evoluem schema e codigo em sincronia
- Schemas mudam mais no inicio do projeto e depois estabilizam
- Schema e codigo evoluem em ritmos distintos
- Comportamentos diversos entre projetos

**Relacao com nosso TCC:**
Corrobora que co-evolucao nao e uniforme — projetos diferentes = padroes diferentes. Motiva diretamente nossa RQ3 (apps vs libs podem ter padroes distintos). Escala similar (195 vs 124 projetos).

---

### 4. Curino, Moon e Zaniolo (2008) — Taxonomia de operacoes

| | |
|---|---|
| **Titulo** | Graceful Database Schema Evolution: the PRISM Workbench |
| **Venue** | VLDB 2008 |
| **Arquivo** | `The PRISM Workbench - Curino Moon Zaniolo 2008.pdf` |
| **Contexto** | Sistema PRISM para gestao de evolucao de schema |
| **Metodo** | Modelagem formal de operacoes de evolucao |

**Achados-chave:**
- Evolucao de schema pode ser modelada como sequencia de operacoes atomicas
- Taxonomia: operacoes aditivas, destrutivas e de modificacao
- Automatizacao da evolucao e viavel com operacoes bem definidas

**Relacao com nosso TCC:**
Base conceitual pra nossa categorizacao de operacoes Django (CreateModel, AddField, etc.). Migrations Django seguem essa mesma filosofia de operacoes atomicas tipadas. Citado na fundamentacao teorica.

---

### 5. Meurice e Cleve (2014) — DAHLIA — Precedente metodologico

| | |
|---|---|
| **Titulo** | DAHLIA: A Visual Analyzer of Database Schema Evolution |
| **Venue** | IEEE CSMR-WCRE 2014 |
| **Arquivo** | `DAHLIA - Meurice Cleve 2014.pdf` |
| **Contexto** | Ferramenta visual de analise de evolucao de schema |
| **Metodo** | Mineracao de historico Git + reconstrucao de schema commit a commit |

**Achados-chave:**
- Extracao automatizada de operacoes de schema do historico Git e viavel
- Visualizacao interativa auxilia compreensao de padroes de evolucao

**Relacao com nosso TCC:**
Valida nossa abordagem metodologica — tambem mineramos operacoes de schema do Git. Diferenca: eles parsam SQL, nos parsamos AST de migrations Django (mais estruturado e confiavel).

---

### 6. Cleve et al. (2015) — Padroes de propagacao

| | |
|---|---|
| **Titulo** | Understanding Database Schema Evolution: A Case Study |
| **Venue** | Science of Computer Programming, vol. 97 |
| **Arquivo** | `Understanding DB Schema Evolution - Cleve et al 2015.pdf` |
| **Contexto** | 1 sistema, 18 anos de evolucao, 320 mudancas de schema |
| **Metodo** | Estudo de caso longitudinal |

**Achados-chave:**
- Mudancas de schema causam cascatas de propagacao no codigo
- Diferentes motivacoes (feature vs refactoring) geram impactos distintos
- Rastreabilidade e crucial pra manutencao de longo prazo

**Relacao com nosso TCC:**
Diretamente relevante pra RQ2 — nos medimos propagacao por camada Django. Eles viram cascatas em 1 sistema; nos quantificamos em 124 projetos.

---

### 7. Chen et al. (2016) — ORM como contexto

| | |
|---|---|
| **Titulo** | An Empirical Study on the Practice of Maintaining Object-Relational Mapping Code in Java Systems |
| **Venue** | MSR 2016 |
| **Arquivo** | `Maintaining ORM Code - Chen et al 2016.pdf` |
| **Contexto** | 7 projetos Java/Hibernate |
| **Metodo** | Analise de metricas de churn e complexidade em codigo ORM |

**Achados-chave:**
- Commits ORM sao mais complexos que commits de outro tipo de codigo
- Camada de acesso a dados concentra a maioria das mudancas
- Configuracao ORM evolui com frequencia significativa

**Relacao com nosso TCC:**
Unico estudo anterior sobre ORM (nao SQL puro). Confirma que codigo ORM e especial — mais complexo, mais acoplado ao schema. Nos estendemos pra Django e adicionamos dimensao de camada arquitetural.

---

### 8. Liu, Mondal e Chen (2024) — Consequencias praticas

| | |
|---|---|
| **Titulo** | An Empirical Study on the Characteristics of Database Access Bugs in Java Applications |
| **Venue** | ACM TOSEM 2024 |
| **Arquivo** | `Database Access Bugs - Liu Mondal Chen 2024.pdf` |
| **Contexto** | 423 bugs em 7 apps Java |
| **Metodo** | Classificacao manual de bugs de acesso a BD por causa raiz |

**Achados-chave:**
- 84,2% dos bugs sao de SQL, schema ou API
- Bugs de schema (referencia a elementos removidos/renomeados) sao parcela significativa
- Configuracao incorreta de ORM e fonte comum de bugs

**Relacao com nosso TCC:**
Evidencia empirica de que falta de co-evolucao causa bugs reais. Fortalece motivacao: entender padroes de co-evolucao ajuda a prevenir defeitos.

---

## Tabela Comparativa

| Aspecto | Qiu+ 2013 | Meurice+ 2016 | Vassiliadis+ 2023 | Cleve+ 2015 | Chen+ 2016 | **Nosso TCC** |
|---------|-----------|---------------|-------------------|-------------|------------|---------------|
| **Linguagem** | Java | Java | Misto | N/A | Java | **Python** |
| **Mecanismo schema** | SQL embutido | SQL embutido | Scripts SQL | Scripts SQL | ORM (Hibernate) | **Migrations Django** |
| **Escala** | 10 projetos | 3 projetos | 195 projetos | 1 projeto | 7 projetos | **124 projetos** |
| **Foco** | Co-evolucao | Inconsistencias | Padroes temporais | Estudo de caso | Manutencao ORM | **Co-evolucao por camada** |
| **Extracao schema** | Parsing SQL | Analise estatica | Parsing SQL | Manual | Parsing config | **AST de migrations** |
| **Classif. arquitetural** | Nao | Nao | Nao | Parcial | Nao | **Sim (8 camadas)** |
| **Apps vs Libs** | Nao | Nao | Nao | Nao | Nao | **Sim (RQ3)** |
| **Operacao × camada** | Nao | Nao | Nao | Nao | Nao | **Sim (RQ2)** |
