# Job Tracker — Backlog
> v1.1 lançado · v1.2 em desenvolvimento · Abril 2026
> Última atualização: análise técnica completa do código

---

## ✅ v1.0 — Concluído
- Pipeline Gupy com cooldown, timeout, backup automático
- Dashboard 12 páginas com Plotly
- Score de fit com breakdown matches/gaps
- Diário de candidatura, preparação para entrevista
- Remuneração CLT/PJ/Exterior com benefícios
- Comparativo, tendências, funil, perfil candidato
- Refatoração modular database/ e dashboard/views/

---

## ✅ v1.1 — Concluído
- Stack extractor 80+ tecnologias em 8 categorias
- Filtros ação rápida, SLA, checklist de preparação
- playwright-stealth, anti-detecção, cooldown 48h
- Medallion Architecture Bronze/Silver/Gold
- Great Expectations — 6 validações de qualidade
- Greenhouse + Inhire + SmartRecruiters + URL unificada
- Descrições automáticas via API — stacks reais
- Filtros de localização país/cidade

---

## ✅ v1.2 (parcial) — Concluído
- Cards 4 colunas com st.dialog, badges de status
- Favicon inline, seletor de colunas, ordenação
- Métricas clicáveis Dashboard e Vagas
- render_vaga_card — componente único reutilizável
- utils.py — helpers safe_str, safe_bool, status_badge
- Cache Streamlit @st.cache_data nas funções principais
- Connection manager DuckDB com context manager
- Makefile + hot reload no start.sh
- Fila de inscrição com score e ações rápidas
- Página de Estudos com roadmap DE e tracker de livros
- Redesign Empresas, Pipeline e Configurações
- candidatura_status=nao_inscrito padrão no inserir_vaga
- fix: registrar_log com data_execucao — cooldown funcionando
- Tabs no dialog de detalhes (Score/Candidatura/Remuneração/Diário)

---

## 🔴 Sprint 1 — Refatoração técnica (ALTA PRIORIDADE)
> Base para tudo que vem depois. Resolve bugs latentes e melhora performance.

### 1.1 Mover imports para topo dos arquivos
- [ ] `main.py` — 35+ imports dentro de funções processar_empresa_*
- [ ] `dashboard/views/` — imports dentro de funções render()
- **Impacto:** performance (módulos recarregados a cada chamada) + legibilidade
- **Esforço:** 1 sessão

### 1.2 Substituir duckdb.connect() por db_connect()
- [ ] `main.py` — 5 conexões diretas
- [ ] `dashboard/components.py` — 2 conexões diretas
- [ ] `dashboard/views/configuracoes.py` — 2 conexões diretas
- [ ] `dashboard/views/pipeline.py` — 1 conexão direta
- **Impacto:** elimina ConnectionException, garante fechamento de conexões
- **Esforço:** 1 sessão

### 1.3 Centralizar DB_PATH
- [ ] Remover `"data/curated/jobs.duckdb"` hardcoded de 10 arquivos
- [ ] Usar `from database.connection import DB_PATH` em todos
- **Impacto:** facilita mudança de ambiente (dev/prod)
- **Esforço:** 30 min

### 1.4 Deletar db_manager.py
- [ ] Verificar se pipeline_runner.py ainda usa db_manager
- [ ] Migrar qualquer função única para os módulos corretos
- [ ] Deletar database/db_manager.py (459 linhas de duplicata)
- **Impacto:** elimina confusão sobre qual função usar
- **Esforço:** 1 sessão

### 1.5 Unificar 4 funções processar_empresa_*
- [ ] Criar `pipeline/processors/base.py` com classe base
- [ ] Criar `pipeline/processors/gupy.py`, `greenhouse.py`, `inhire.py`, `smartrecruiters.py`
- [ ] Substituir 4 funções por uma única com Factory Pattern
- **Impacto:** 80% menos código duplicado, fácil adicionar Lever
- **Esforço:** 2 sessões

### 1.6 Tratar except: genéricos (16 ocorrências)
- [ ] Substituir `except:` por exceções específicas com logging
- [ ] Adicionar `logging.getLogger()` em vez de `print()`
- **Impacto:** bugs não ficam mais silenciosos
- **Esforço:** 1 sessão

---

## 🟡 Sprint 2 — Separação de responsabilidades
> Alinha com padrões de mercado DE. Facilita manutenção e testes.

### 2.1 Separar dashboard/components.py (500 linhas)
- [ ] `dashboard/data_loaders.py` — carregar_vagas, carregar_empresas, calcular_scores
- [ ] `dashboard/ui_components.py` — render_stacks, render_score_breakdown, render_vaga_card
- [ ] `dashboard/charts.py` — grafico_stacks, extrair_stacks_flat
- **Impacto:** cada arquivo tem responsabilidade única (SRP)
- **Esforço:** 2 sessões

### 2.2 Repository Pattern no database/
- [ ] `database/repositories/vagas_repo.py`
- [ ] `database/repositories/empresas_repo.py`
- [ ] `database/repositories/candidaturas_repo.py`
- **Impacto:** SQL isolado das views, testável, padrão de mercado
- **Esforço:** 3 sessões

### 2.3 Limpar data/raw/
- [ ] Verificar se vagas_processadas.json, urls_validadas.json são usados
- [ ] Remover arquivos obsoletos
- [ ] Atualizar .gitignore
- **Esforço:** 30 min

### 2.4 Type hints em todas as funções públicas
- [ ] database/*.py
- [ ] scrapers/*.py
- [ ] transformers/stack_extractor.py
- **Impacto:** documentação automática + detecção de bugs pelo IDE
- **Esforço:** 2 sessões

---

## 🟢 Sprint 3 — Features pendentes
> Funcionalidades que melhoram a experiência de busca de emprego.

### 3.1 Melhorias de scrapers
- [ ] Gupy — extrair localização, regime, salário, data de encerramento
- [ ] Greenhouse — melhorar detecção de modalidade, extrair departamento
- [ ] Inhire — extrair localização e nível
- [ ] SmartRecruiters — extrair departamento e data de publicação
- [ ] Padronizar campos entre todas as plataformas
- [ ] Scraper Lever — jobs.lever.co

### 3.2 Facilitar inscrições
- [ ] Exportar lista CSV das vagas filtradas
- [ ] Follow-up automático após X dias inscrito
- [ ] Prep kit por vaga — resumo empresa + perguntas + gaps

### 3.3 Score e análise
- [ ] Score ATS do currículo vs vaga
- [ ] Carta de apresentação automática por vaga
- [ ] Cronômetro de processo seletivo

### 3.4 UX restante
- [ ] Perfil Candidato — atualizar visualmente
- [ ] Comparativo — mais interatividade
- [ ] Tendências — gráficos mais ricos

---

## 🔵 Sprint 4 — Qualidade de dados (aprender + implementar)

### 4.1 Expandir Great Expectations
- [ ] Validações para Greenhouse e SmartRecruiters
- [ ] Validação de stacks não vazias para vagas com descrição
- [ ] Alertas automáticos quando qualidade cai

### 4.2 Data Contracts
- [ ] Definir esquema esperado entre Bronze/Silver/Gold
- [ ] Documentar contrato de cada scraper

### 4.3 Observabilidade do pipeline
- [ ] SLA — alertar quando pipeline não rodar em 24h
- [ ] Anomaly detection — queda brusca no número de vagas
- [ ] Métricas de qualidade por plataforma (% com stacks, % com modalidade)
- [ ] Logging estruturado — substituir print() por logging

### 4.4 Reconciliação
- [ ] Comparar contagem entre coleta e banco
- [ ] Relatório diário de qualidade automático

### 4.5 dbt
- [ ] Aguardar compatibilidade com Python 3.14
- [ ] Implementar models Silver e Gold com testes

---

## 🔮 Sprint 5 — Testes automatizados

- [ ] pytest para scrapers (mock de responses HTTP)
- [ ] pytest para transformers (stack_extractor)
- [ ] pytest para database (operações CRUD)
- [ ] pre-commit hooks — ruff + mypy antes de cada commit
- [ ] GitHub Actions — CI rodando testes em cada PR

---

## 🔮 v2 — Cloud & Deploy

- [ ] Deploy Streamlit Cloud
- [ ] Storage S3 para o banco DuckDB
- [ ] Docker + docker-compose
- [ ] Prefect DAGs com retry e alertas
- [ ] GitHub Actions CI/CD
- [ ] Notificações por email/push
- [ ] Onboarding wizard para novos usuários

---

## 🔮 v3/v4 — Longo prazo

- [ ] Raspberry Pi 24/7
- [ ] Apache Spark / Kafka para processamento em escala
- [ ] Delta Lake / Iceberg
- [ ] Robô de candidatura automática
- [ ] Analytics de mercado — tendências por stack

---

## 🐛 Débitos técnicos conhecidos

- dbt — incompatível Python 3.14
- Favicon local vs URL — inconsistência entre empresas
- salario_min/max vs salario_mensal/anual_total — campos legados duplicados
- Sequences do banco podem dessincronizar após recriação manual
- data/raw/ com arquivos JSON obsoletos

---

## 📋 Roadmap resumido

| Sprint | Foco | Quando |
|---|---|---|
| Sprint 1 | Refatoração técnica — imports, conexões, duplicatas | Agora |
| Sprint 2 | Separação responsabilidades — SRP, Repository Pattern | Próximo |
| Sprint 3 | Features — scrapers, inscrições, score ATS | Em seguida |
| Sprint 4 | Qualidade dados — GE, contracts, observabilidade | Depois |
| Sprint 5 | Testes + CI/CD | Antes do v2 |
| v2 | Cloud, Docker, deploy | Futuro |

---

## 🏆 Padrões de mercado já implementados

| Padrão | Status |
|---|---|
| Medallion Architecture | ✅ |
| Great Expectations | ✅ |
| Context Manager DB | ✅ |
| Cache de dados | ✅ |
| Componentes reutilizáveis | ✅ |
| utils.py centralizado | ✅ |
| Backup automático | ✅ |
| Factory Pattern scrapers | ❌ Sprint 1 |
| Repository Pattern DB | ❌ Sprint 2 |
| Logging estruturado | ❌ Sprint 4 |
| Type hints | ❌ Sprint 2 |
| Testes automatizados | ❌ Sprint 5 |
| CI/CD | ❌ v2 |