# 2 Fundamentação Teórica

Este capítulo apresenta os conceitos fundamentais que sustentam a investigação proposta. A Seção 2.1 discute a evolução de schemas de banco de dados e seus desafios. A Seção 2.2 detalha o framework Django e seu sistema de migrations, que constitui o objeto de análise deste trabalho. A Seção 2.3 introduz a Mineração de Repositórios de Software como abordagem metodológica. Por fim, a Seção 2.4 define co-evolução schema-código e situa o conceito na literatura.

---

## 2.1 Evolução de Schema de Banco de Dados

Sistemas de software que utilizam bancos de dados relacionais dependem de um esquema (schema) que define a estrutura das tabelas, colunas, tipos de dados, restrições de integridade e índices. Esse esquema não é estático: ao longo do ciclo de vida de uma aplicação, mudanças nos requisitos de negócio, correções de bugs e otimizações de desempenho frequentemente exigem alterações na estrutura do banco de dados (RODDICK, 1992).

A evolução de schema refere-se ao processo de modificar o esquema de um banco de dados enquanto se preserva a integridade dos dados existentes e a compatibilidade com o código da aplicação que o utiliza (CURINO; MOON; ZANIOLO, 2008). Esse processo envolve operações como criação e remoção de tabelas, adição e remoção de colunas, alteração de tipos de dados e modificação de restrições de integridade.

A importância da evolução de schema para a engenharia de software reside no fato de que o esquema do banco de dados serve como um contrato implícito entre a camada de persistência e as demais camadas da aplicação. Quando esse contrato é alterado — por exemplo, ao renomear uma coluna ou remover uma tabela — todo o código que depende da estrutura anterior pode ser afetado. Se essas dependências não forem atualizadas de forma coordenada, o resultado são inconsistências que podem se manifestar como erros em tempo de execução, perda de dados ou comportamento incorreto da aplicação (MEURICE; NAGY; CLEVE, 2016).

Curino, Moon e Zaniolo (2008) classificam as operações de evolução de schema em categorias de acordo com seu impacto:

- **Operações aditivas:** criam novos elementos no schema sem afetar os existentes (ex.: adicionar uma nova tabela ou coluna). Essas operações geralmente são retrocompatíveis.
- **Operações destrutivas:** removem elementos do schema (ex.: remover uma coluna ou tabela). Essas operações podem causar inconsistências no código que referenciava os elementos removidos.
- **Operações de modificação:** alteram propriedades de elementos existentes (ex.: mudar o tipo de uma coluna, renomear uma tabela). O impacto depende da natureza da modificação.

Em sistemas tradicionais, a evolução de schema era frequentemente gerenciada por meio de scripts SQL executados manualmente pelos administradores de banco de dados. Essa abordagem é propensa a erros e dificulta a rastreabilidade das mudanças. Frameworks modernos de desenvolvimento web, como Django, Ruby on Rails e Laravel, introduziram sistemas de migrations que formalizam e automatizam esse processo, tornando as mudanças de schema versionáveis e reprodutíveis.

---

## 2.2 Django e o Sistema de Migrations

### 2.2.1 O framework Django

Django é um framework de desenvolvimento web em Python que segue o padrão arquitetural Model-View-Template (MVT), uma variação do Model-View-Controller (MVC). Lançado em 2005 e mantido pela Django Software Foundation, o framework é amplamente adotado tanto em projetos open-source quanto em aplicações comerciais, sendo utilizado por organizações como Mozilla, Instagram e The Washington Post (DJANGO SOFTWARE FOUNDATION, 2024).

A arquitetura de uma aplicação Django é organizada em camadas com responsabilidades bem definidas:

- **Models (`models.py`):** definem a estrutura dos dados como classes Python. Cada classe de modelo corresponde a uma tabela no banco de dados, e cada atributo da classe corresponde a uma coluna. O ORM (Object-Relational Mapping) do Django traduz essas definições declarativas em operações SQL.
- **Views (`views.py`):** contêm a lógica de negócio que processa requisições HTTP e retorna respostas. Views acessam os dados através dos models.
- **Templates (`.html`):** definem a apresentação visual dos dados ao usuário.
- **Admin (`admin.py`):** fornece uma interface administrativa gerada automaticamente para gerenciar os dados dos models.
- **Forms (`forms.py`):** definem a validação e o processamento de formulários, frequentemente vinculados a models específicos.
- **Serializers (`serializers.py`):** utilizados em APIs REST (via Django REST Framework), convertem objetos de modelo em representações JSON e vice-versa.
- **URLs (`urls.py`):** mapeiam URLs para views.

Essa separação em camadas é relevante para este estudo porque cada camada possui um grau diferente de acoplamento com o schema do banco de dados. Models são diretamente vinculados ao schema; views, admin e serializers dependem dos models e, portanto, são indiretamente afetados por mudanças de schema; templates e URLs tipicamente têm acoplamento mais fraco.

### 2.2.2 O sistema de migrations do Django

O sistema de migrations do Django foi introduzido na versão 1.7 (2014) e constitui o mecanismo oficial para gerenciar a evolução do schema de banco de dados. O fluxo de trabalho típico segue três etapas:

1. O desenvolvedor altera as definições em `models.py` (adiciona um campo, cria um modelo, etc.).
2. O comando `python manage.py makemigrations` detecta automaticamente as diferenças entre os models e o estado atual do schema, gerando um arquivo de migration.
3. O comando `python manage.py migrate` aplica as migrations pendentes ao banco de dados.

Cada migration é um arquivo Python com uma estrutura canônica e padronizada:

```python
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('app_name', '0001_initial'),
    ]
    operations = [
        migrations.AddField(
            model_name='order',
            name='status',
            field=models.CharField(max_length=20, default='pending'),
        ),
    ]
```

A lista `operations` contém as operações de schema a serem aplicadas. O Django define um conjunto finito de tipos de operação, que podem ser agrupados em categorias:

| Categoria | Operações | Descrição |
|-----------|-----------|-----------|
| Ciclo de vida do modelo | `CreateModel`, `DeleteModel` | Criação e remoção de tabelas |
| Mudanças de campo | `AddField`, `RemoveField`, `AlterField`, `RenameField` | Adição, remoção e modificação de colunas |
| Índices e constraints | `AddIndex`, `RemoveIndex`, `AddConstraint`, `RemoveConstraint` | Gerenciamento de índices e restrições |
| Metadados | `AlterModelOptions`, `AlterModelTable`, `RenameModel`, `AlterUniqueTogether`, `AlterIndexTogether` | Propriedades do modelo que não alteram colunas diretamente |
| Customizadas | `RunSQL`, `RunPython`, `SeparateDatabaseAndState` | Operações arbitrárias definidas pelo desenvolvedor |

Essa estrutura padronizada é especialmente relevante para estudos empíricos porque permite a extração automatizada das operações de schema via parsing da Abstract Syntax Tree (AST) do Python, sem necessidade de executar o código ou instalar as dependências do projeto.

### 2.2.3 Migrations como artefatos de evolução de schema

As migrations do Django possuem propriedades que as tornam particularmente adequadas para o estudo de evolução de schema:

1. **Rastreabilidade:** como arquivos versionados no Git, cada migration tem um commit associado que registra quando foi introduzida e quais outros arquivos foram modificados no mesmo contexto.
2. **Parseabilidade:** a estrutura canônica do arquivo de migration permite a extração de operações via AST sem ambiguidade.
3. **Causalidade explícita:** o fluxo `models.py → makemigrations → migration` estabelece uma relação causal clara entre mudanças no modelo e operações de schema.
4. **Granularidade:** cada operação dentro de uma migration corresponde a uma mudança atômica no schema (um campo adicionado, uma tabela criada, etc.).

Essas propriedades distinguem as migrations do Django de abordagens anteriores baseadas em SQL embutido no código, onde a identificação de mudanças de schema exigia análise textual de strings SQL dispersas pelo código-fonte (QIU; LI; SU, 2013).

---

## 2.3 Mineração de Repositórios de Software

Mineração de Repositórios de Software (MSR — Mining Software Repositories) é uma área de pesquisa em engenharia de software que utiliza técnicas de análise de dados para extrair informações úteis dos artefatos produzidos durante o desenvolvimento de software (HASSAN, 2008). Esses artefatos incluem sistemas de controle de versão (como Git), rastreadores de bugs, listas de e-mail, revisões de código e documentação.

O objetivo da MSR é transformar repositórios de software — que são fundamentalmente registros históricos de decisões de desenvolvimento — em fontes de evidência empírica sobre práticas, padrões e problemas de engenharia de software. A área consolidou-se ao longo das últimas duas décadas, com uma conferência dedicada (MSR — Mining Software Repositories) desde 2004 e aplicações em diversas subáreas da engenharia de software.

### 2.3.1 Técnicas utilizadas neste trabalho

Este estudo emprega três técnicas de MSR que são aplicadas de forma combinada:

**Análise de commits via Git.** O histórico de commits de um repositório registra cada modificação feita ao longo do tempo, incluindo quais arquivos foram alterados, quantas linhas foram adicionadas e removidas, e a mensagem associada pelo desenvolvedor. Comandos como `git log --diff-filter=A` permitem identificar o commit que introduziu um arquivo específico (como uma migration), e `git diff-tree --numstat` permite listar todos os arquivos alterados em um dado commit com métricas de churn (linhas adicionadas e removidas).

**Parsing de AST (Abstract Syntax Tree).** A AST é uma representação estruturada do código-fonte que preserva sua semântica sintática. Em Python, o módulo `ast` da biblioteca padrão permite analisar arquivos `.py` e extrair informações estruturadas sem executar o código. No contexto deste trabalho, o parsing de AST é utilizado para extrair as operações de cada migration (tipo de operação, modelo afetado, campo quando aplicável) de forma confiável e automatizada.

**Classificação heurística de arquivos.** Os arquivos alterados em cada commit são classificados por seu papel na arquitetura Django com base em padrões de nomenclatura e caminho. Por exemplo, arquivos em diretórios `/migrations/` são classificados como migrations, arquivos nomeados `models.py` ou dentro de `/models/` são classificados como models, e assim por diante. Essa abordagem segue convenções amplamente adotadas no ecossistema Django.

### 2.3.2 Plataforma GitHub como fonte de dados

O GitHub é a maior plataforma de hospedagem de código-fonte do mundo, com mais de 100 milhões de repositórios públicos. Para estudos de MSR, o GitHub oferece uma API de busca que permite filtrar repositórios por linguagem, número de estrelas, data de atividade e outros critérios, além de APIs para acessar a árvore de arquivos e o conteúdo de repositórios sem necessidade de clone completo.

A utilização de projetos open-source hospedados no GitHub como corpus de estudo é uma prática consolidada na literatura de engenharia de software empírica, embora apresente ameaças à validade conhecidas, como o viés de seleção (projetos no GitHub podem não ser representativos de software industrial) e a presença de projetos inativos, acadêmicos ou de demonstração (KALLIAMVAKOU et al., 2014).

---

## 2.4 Co-evolução Schema-Código

### 2.4.1 Definição

Co-evolução schema-código refere-se ao fenômeno pelo qual mudanças na estrutura do banco de dados (schema) e mudanças no código da aplicação ocorrem de forma coordenada ao longo do tempo. Quando o schema evolui — por exemplo, com a adição de um novo campo em uma tabela — o código que interage com essa tabela frequentemente precisa ser adaptado para refletir a mudança: novos formulários, consultas atualizadas, interfaces administrativas modificadas, testes ajustados.

A coordenação entre schema e código é essencial para a manutenção da consistência do sistema. Qiu, Li e Su (2013) demonstraram que a falta de sincronização entre mudanças de schema e adaptações no código é uma fonte significativa de bugs em aplicações de banco de dados, particularmente em projetos de grande escala onde múltiplos desenvolvedores modificam o schema e o código de forma concorrente.

### 2.4.2 Dimensões da co-evolução

A co-evolução schema-código pode ser analisada sob múltiplas dimensões:

**Acoplamento temporal.** Mede se mudanças de schema e mudanças no código ocorrem no mesmo commit, na mesma janela temporal, ou de forma desacoplada. Um alto grau de acoplamento temporal sugere que os desenvolvedores reconhecem e tratam a dependência entre schema e código como parte de uma mesma unidade lógica de trabalho.

**Amplitude de propagação (spread).** Mede quantos arquivos de código são afetados por uma mudança de schema. Uma mudança que afeta apenas `models.py` tem spread baixo; uma que requer adaptações em views, admin, serializers e testes tem spread alto.

**Profundidade arquitetural.** Identifica quais camadas da arquitetura são afetadas por uma mudança de schema. Em uma aplicação Django, espera-se que `models.py` seja quase sempre co-modificado (pois é a origem causal da migration), mas o grau de propagação para camadas mais distantes (views, templates, testes) pode variar.

**Impacto por tipo de operação.** Diferentes tipos de operação de schema podem ter impactos distintos na aplicação. Intuitivamente, operações de ciclo de vida (como `CreateModel`) devem afetar mais camadas do que operações pontuais (como `AlterField`), pois a criação de um novo modelo frequentemente exige views, URLs, admin e testes correspondentes.

### 2.4.3 Operacionalização neste estudo

Neste trabalho, a co-evolução é operacionalizada da seguinte forma: uma migration e o código da aplicação são considerados co-evoluídos quando ambos são modificados no mesmo commit que introduziu a migration. Essa definição — denominada same-commit co-evolution — é a mais simples e reprodutível entre as alternativas possíveis, embora possua limitações reconhecidas: mudanças no código podem ocorrer em commits posteriores à migration, e commits com muitas alterações não relacionadas (kitchen-sink commits) podem inflar artificialmente as métricas de co-evolução. Essas limitações são discutidas como ameaças à validade na Seção 4 (Metodologia).

A métrica central derivada dessa operacionalização é o **co-evolution ratio**: a proporção de commits que introduzem migrations e que também alteram pelo menos um arquivo de código fora do diretório de migrations. Essa métrica quantifica o grau de acoplamento entre mudanças de schema e mudanças no código da aplicação.
