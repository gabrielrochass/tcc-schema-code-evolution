# Decisoes e Limitacoes

## Decisao 1: Parsing AST (nao MigrationLoader do Django)

**Escolha:** Extrair operacoes via `ast.parse()` dos arquivos .py de migration.

**Alternativa descartada:** Usar `django.db.migrations.loader.MigrationLoader` — precisaria instalar Django + dependencias de cada projeto, configurar DJANGO_SETTINGS_MODULE. Fragilidade operacional inaceitavel para TCC.

**Justificativa:** Migrations Django tem estrutura canonica e padronizada. O parser AST funciona com 100% de precisao nos casos testados. Zero dependencias externas.

## Decisao 2: Same-commit como definicao de co-evolucao

**Escolha:** Considerar que uma migration e seu codigo coevoluem se estao no mesmo commit.

**Alternativa descartada:** Janela temporal de N commits antes/depois — arbitraria, muito ruido.

**Limitacoes conhecidas:**
- Commits "kitchen-sink" inflam metricas (muitas mudancas nao-relacionadas no mesmo commit)
- Mitigacao: filtro de outliers (--max-commit-files 50)
- Migration pode ser criada em commit separado do codigo que a motivou
- Codigo pode ser adaptado em commits posteriores

**Justificativa:** E a hipotese operacional mais simples, reprodutivel e nao-arbitraria. Discutir as limitacoes explicitamente como ameaca a validade.

## Decisao 3: Causalidade migration <- models.py

Em Django, o fluxo tipico e:

```
Desenvolvedor edita models.py
    -> python manage.py makemigrations (gera migration automaticamente)
    -> git commit (ambos juntos)
```

Portanto, a migration e **consequencia** da mudanca em models.py, nao causa. Isso e uma distincao importante: nao estamos medindo "impacto da migration no codigo", e sim "extensao das mudancas de codigo que acompanham uma evolucao de schema".

## Decisao 4: Clone parcial (blob:none)

**Escolha:** `git clone --filter=blob:none` em vez de clone completo ou shallow.

**Justificativa:** Preserva todo o historico de commits (necessario para git log) sem baixar todos os blobs (economia de banda/disco). Git busca blobs sob demanda quando necessario.

## Decisao 5: Filtro de outliers

**Escolha:** Opcionalmente descartar commits com >50 arquivos alterados.

**Justificativa:** Commits com centenas de arquivos geralmente sao merges, refactorings massivos, ou atualizacoes de dependencias — nao representam uma evolucao pontual de schema.

**Risco:** Pode descartar commits legitimos de grandes features. Por isso e opcional (--max-commit-files).

## Problemas metodologicos identificados

| Problema | Severidade | Tratamento |
|----------|------------|------------|
| Migration em commit separado do codigo | Media | Ameaca a validade; medir % de migration-only commits |
| Multiplas migrations no mesmo commit | Baixa | Agrupar operacoes por commit |
| Migrations squashed | Baixa | Detectavel pelo nome do arquivo |
| Commits kitchen-sink | Alta | Filtro de outliers (>50 files) |
| Branches/merges | Baixa | Usar --first-parent se necessario |
| SQL raw fora das migrations | Baixa | Fora do escopo — focamos no ORM Django |
| Libs externas com migrations proprias | Baixa | Filtrar por diretorio do projeto |
