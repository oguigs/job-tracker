# Job Tracker — Backlog

> v1.1 lançado · v1.2 em desenvolvimento · Abril 2026

---

## ✅ v1.0 — Concluído

- Pipeline Gupy com cooldown, timeout, backup automático
- Dashboard 12 páginas com Plotly
- Score de fit com breakdown matches/gaps
- Diário de candidatura por data
- Preparação para entrevista com gaps
- Remuneração CLT/PJ/Exterior com benefícios completos
- Comparativo entre empresas
- Tendências com snapshots automáticos
- Perfil do candidato com stacks
- Base de indicadores e contatos
- Cadastro manual de vagas
- Alerta urgente 🔥
- Refatoração modular database/ e dashboard/views/

---

## ✅ v1.1 — Concluído

- Stack extractor 80+ tecnologias em 8 categorias
- Modo compacto na listagem
- Filtros ação rápida (novas 24h, não inscritas, SLA)
- Marcar inscrito direto no modo compacto
- Checklist de preparação interativo
- Funil de candidaturas com taxa de conversão
- playwright-stealth + delays humanizados
- Detecção de bloqueio 403/429/Cloudflare
- Cooldown 48h empresa bloqueada
- Coleta espaçada com intervalo configurável
- Medallion Architecture Bronze/Silver/Gold
- Great Expectations — 6 validações de qualidade
- Página de Qualidade no dashboard
- Scraper Greenhouse via API REST
- Scraper Inhire via Playwright
- Scraper SmartRecruiters via API REST
- URL de vagas unificada com auto-detecção de plataforma
- Descrições automáticas via API — stacks reais extraídas
- Filtros de localização país/cidade
- Botões ativar/pausar todas empresas
- Limpeza da base por filtros

---

## ✅ v1.2 (parcial) — Em andamento

- Cards 4 colunas com st.dialog para detalhes
- Badges de status (Novo/Não inscrito/Inscrito/Em processo)
- Favicon inline nos cards
- Seletor de colunas (2/3/4)
- Ordenação por score/data/empresa
- Métricas clicáveis Dashboard e Vagas
- Linha colorida de status nos cards
- Dashboard com mesmo padrão de cards

---

## ⚡ v1.2 — Pendente

### 🎯 Facilitar inscrições (Prioridade máxima)
- [ ] **Fila de inscrição** — lista ordenada por score para trabalhar sequencialmente
- [ ] **Abrir todas não inscritas** — botão que abre todas as vagas relevantes em abas
- [ ] **Exportar lista CSV** — para compartilhar com mentores/recrutadores
- [ ] **Follow-up automático** — lembrar de fazer follow-up após X dias inscrito
- [ ] **Prep kit por vaga** — resumo empresa + perguntas prováveis + gaps

### 🎨 UX/UI — Páginas pendentes
- [ ] **Empresas** — formulário mais limpo, feedback visual
- [ ] **Pipeline** — progresso visual, log menos técnico
- [ ] **Configurações** — preview do impacto dos filtros
- [ ] **Perfil Candidato** — atualizar visualmente
- [ ] **Comparativo** — mais interatividade
- [ ] **Tendências** — gráficos mais ricos

### ⚡ Performance — Revisão de código
- [ ] **Cache Streamlit** — `@st.cache_data` em `calcular_scores_vagas`, `carregar_vagas`, `get_favicon`
- [ ] **Connection pooling DuckDB** — uma conexão por sessão em vez de abrir/fechar em cada função
- [ ] **Loop de dialogs** — percorre todas as vagas a cada render, otimizar para 100+ vagas
- [ ] **Imports no topo** — remover `from main import...` dentro de funções
- [ ] **Tratamento de NA** — padronizar em um único helper em vez de repetir em todo lugar
- [ ] **Constantes** — criar arquivo constants.py para strings repetidas

### 🏗 Design patterns
- [ ] **Separar lógica de apresentação** — criar `services/` para candidatura, score, pipeline
- [ ] **Padronizar conexões DB** — context manager para DuckDB
- [ ] **Testes unitários** — cobertura básica dos scrapers e transformers

### 📊 Qualidade de dados (aprender)
- [ ] **Data contracts** — definir esquema esperado entre camadas Bronze/Silver/Gold
- [ ] **Data lineage** — rastrear origem de cada campo
- [ ] **SLAs de pipeline** — alertar quando pipeline não rodar em X horas
- [ ] **Anomaly detection** — detectar quando número de vagas cai muito
- [ ] **Reconciliação** — comparar contagem entre coleta e banco
- [ ] **dbt tests** — quando Python 3.14 for suportado

### 🔧 Scrapers
- [ ] **Scraper Lever** — jobs.lever.co
- [ ] **Notificação desktop** — quando novas vagas aparecerem
- [ ] **Reprocessar stacks** — vagas sem descrição

### 📝 Score e análise
- [ ] **Score ATS** — análise currículo vs vaga
- [ ] **Carta de apresentação** automática por vaga
- [ ] **Cronômetro** processo seletivo

---

## 🔮 v2 — Cloud

- [ ] Deploy Streamlit Cloud
- [ ] Storage S3
- [ ] Docker + docker-compose
- [ ] Prefect DAGs com retry e alertas
- [ ] GitHub Actions CI/CD
- [ ] Notificações por email
- [ ] Onboarding wizard

---

## 🔮 v3/v4 — Longo prazo

- [ ] Raspberry Pi 24/7
- [ ] Apache Spark / Kafka
- [ ] Delta Lake / Iceberg
- [ ] Robô de candidatura automática
- [ ] Analytics de mercado — tendências por stack

---

## 📋 Roadmap sugerido

| Sprint | Foco | Itens |
|---|---|---|
| Sprint 1 | Inscrição fácil | Fila de inscrição, abrir todas, exportar CSV |
| Sprint 2 | Performance | Cache Streamlit, connection pooling, refactor |
| Sprint 3 | Qualidade dados | Data contracts, SLAs, anomaly detection |
| Sprint 4 | UX restante | Empresas, Pipeline, Configurações |
| Sprint 5 | v2 | Deploy, Docker, CI/CD |

---

## 🐛 Débitos técnicos

- dbt — incompatível Python 3.14
- Favicon local vs URL — inconsistência
- Vagas novas nascem com ativa=NULL em alguns scrapers
- Sequences do banco resetadas após recriação
- `salario_min/max` vs `salario_mensal/anual_total` — campos duplicados legados

---

## 🛠 Boas práticas de desenvolvimento

### Alta prioridade (baixo esforço)
- [ ] **Cache Streamlit** — `@st.cache_data` em carregar_vagas, calcular_scores_vagas, get_favicon
- [ ] **utils.py** — helper `safe_bool`, `safe_str` para eliminar repetição de tratamento NA
- [ ] **Makefile** — comandos `make run`, `make pipeline`, `make backup`
- [ ] **hot reload** — `--server.runOnSave true` no start.sh

### Média prioridade (médio esforço)
- [ ] **render_vaga_card** — componente único reutilizado em vagas.py e dashboard_page.py
- [ ] **Connection manager DuckDB** — context manager `with db_connect() as con:`
- [ ] **config.py** — variáveis de ambiente DB_PATH, DEBUG

### Baixa prioridade (alto esforço)
- [ ] **services/** — separar lógica de negócio das views
- [ ] **tests/** — testes unitários básicos scrapers e transformers
- [ ] **Convenção de commits** — feat/fix/refactor/perf/docs

### Página de Estudos — Data Engineering
- [ ] Fundamentos — SQL avançado, Python, Git
- [ ] Cloud — AWS (S3, Glue, Athena, Lambda, EMR), Azure (Data Factory, Synapse, Databricks), GCP (BigQuery, Dataflow)
- [ ] Processing — Spark, PySpark, Kafka, Flink, dbt
- [ ] Orchestration — Airflow, Prefect, Dagster
- [ ] Storage — Delta Lake, Iceberg, Hudi, Data Lakehouse
- [ ] Quality — Great Expectations, data contracts, data lineage, SLAs
- [ ] Architecture — Medallion, Data Mesh, Lambda, Kappa
- [ ] ML/AI — MLflow, Feature Store, MLOps básico
- [ ] Status por tópico — Para estudar / Estudando / Concluído
- [ ] Conexão com vagas — "esse tópico aparece em X vagas da sua base"
- [ ] Prioridade baseada nas stacks mais exigidas nas suas vagas

---

## 🕷 Melhorias de Scrapers

### Gupy
- [ ] Extrair localização (cidade/estado) da vaga
- [ ] Extrair regime de contratação (CLT/PJ)
- [ ] Extrair salário quando disponível
- [ ] Extrair data de encerramento da vaga
- [ ] Detectar vagas encerradas e marcar no banco

### Greenhouse
- [ ] Extrair departamento/área da vaga
- [ ] Extrair localização completa (cidade, estado, país)
- [ ] Melhorar detecção de modalidade (remoto/híbrido/presencial)
- [ ] Paginação — verificar se há mais de 500 vagas

### Inhire
- [ ] Extrair localização da vaga
- [ ] Extrair nível da vaga
- [ ] Extrair regime de contratação

### SmartRecruiters
- [ ] Extrair departamento/área
- [ ] Melhorar detecção de modalidade via campos da API
- [ ] Extrair data de publicação

### Geral
- [ ] Padronizar campos extraídos entre todas as plataformas
- [ ] Detectar vagas duplicadas entre plataformas
- [ ] Alertar quando scraper falha repetidamente
- [ ] Métricas de qualidade da coleta por plataforma
- [ ] Scraper Lever — jobs.lever.co

---

## ✅ Concluído recentemente (v1.2 em andamento)

- Cache Streamlit `@st.cache_data` em funções principais
- utils.py — helpers safe_bool, safe_str, safe_int, nivel_fmt, modal_fmt, status_badge
- render_vaga_card — componente único reutilizado em vagas.py e dashboard_page.py
- Connection manager DuckDB com context manager
- Makefile com make run, make pipeline, make backup
- hot reload no start.sh
- Fila de inscrição com score, checklist e ações rápidas
- candidatura_status=nao_inscrito padrão no inserir_vaga

---

## 📋 Sprint atual — Prioridades definidas

### 1. 🎯 Detalhes da vaga com tabs (Alta prioridade)
- [ ] Tabs no dialog: 📊 Score / 📋 Candidatura / 💰 Remuneração / 📓 Diário
- [ ] Botão "Ver vaga" no topo do dialog
- [ ] Score e checklist visíveis sem scroll
- [ ] Ação rápida — inscrever/negar com um clique no topo

### 2. 🎯 Fila de inscrição — ajustes finais
- [ ] Botão "Estou com sorte" — vaga aleatória
- [ ] Corrigir contagem de vagas na fila
- [ ] Mostrar progresso visual da fila

### 3. 📚 Página de Estudos — Data Engineering
- [ ] Roadmap por categoria com status
- [ ] Prioridade baseada nas stacks das vagas
- [ ] Links para recursos e documentação
- [ ] Conexão com vagas da base

### 4. 🎨 UX outras páginas
- [ ] Empresas — formulário mais limpo
- [ ] Pipeline — progresso visual
- [ ] Configurações — preview de impacto