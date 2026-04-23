# Job Tracker — Backlog
> v1.2 em desenvolvimento · Abril 2026
> Última atualização: Ondas 1-4 concluídas

---

## ✅ Concluído — v1.0, v1.1, v1.2, Sprints 1-2

- Pipeline multi-plataforma (Gupy, Greenhouse, Inhire, SmartRecruiters)
- Dashboard 14 páginas com Plotly
- Score de fit com breakdown matches/gaps
- Medallion Architecture Bronze/Silver/Gold
- Great Expectations — validações de qualidade
- Fila de inscrição, Estudos com roadmap DE e tracker de livros
- Redesign completo UX — cards, badges, dialogs com tabs
- utils.py, theme.py, db_connect context manager
- Cache Streamlit, type hints, separação de responsabilidades
- render_vaga_card e render_dialog_vaga — componentes únicos

---

## ✅ Onda 1 — Estabilizar (concluída)
- B1 pipeline_runner indentação
- B2 main.py import conectar
- B3 cadastrar_vaga url_vagas
- B5 Makefile backup
- B6 great-expectations requirements
- A5 pasta fantasma removida
- A6 __pycache__ ignorado

## ✅ Onda 2 — Schema (concluída)
- B4 criar_tabelas() completo e fiel ao banco
- migrations.py com 4 migrações idempotentes
- Remuneração com sal13/PLR/bônus e cálculo automático

## ✅ Onda 3 — Padronizar acesso (concluída)
- B7 trailing comma SQL
- B8 con.close() duplo removido
- B9 pipeline_runner db_connect
- B10 quality.py chave results
- A2 pipeline_runner entrypoint fino
- A3 Playwright movido para gupy_detalhes
- A4 cache clear após pipeline

## ✅ Onda 4 — UI alta prioridade (parcialmente concluída)
- X1 navegação sidebar agrupada em expanders
- U2 render_dialog_vaga unificado
- U5 filtros persistentes na página Vagas
- U6 estado visual filtros rápidos (botão ativo destacado)
- X9 paleta centralizada em theme.py
- X6a botões de status em Estudos
- X4 estados vazios com instrução em 6 páginas

---

## 🔴 Onda 4 — UI restante (próxima sessão)

- [ ] **J6** — termômetro de empregabilidade no Dashboard — "X vagas com 70%+ de fit agora"
- [ ] **X5b** — timeline clicável no dialog — cada fase vira botão que atualiza status diretamente
- [ ] **X5c** — botão Negar com peso visual diferente — texto discreto com confirmação
- [ ] **X5d** — toast ao salvar candidatura — feedback visual após ação
- [ ] **U8** — verificar ícones roadmap.sh nas stacks
- [ ] **X3** — toast na Fila de Inscrição ao marcar inscrito

---

## 🟠 Onda 5 — Funcionalidades rápidas (1 sessão)

- [ ] **P1** — badge urgência nas vagas — `detectar_urgencia` já existe, falta chamar no pipeline
- [ ] **P2** — detecção de salário via regex nas descrições — salvar em `salario_min`/`salario_max`
- [ ] **P6** — dashboard saúde do pipeline — empresas falhando, taxa de sucesso por plataforma
- [ ] **P3** — snapshot semanal automático via cron/launchd

---

## 🟡 Onda 6 — Empregabilidade e inteligência dos dados (2-3 sessões)

### J — Job hunting (novas ideias — adicionar ao backlog antes de codar)
- [ ] **J2** — briefing automático ao avançar para entrevista — dados já existem, view nova
- [ ] **J1** — diff currículo × vaga — `pdfplumber` + cruzamento com `calcular_score()`
- [ ] **J3** — banco de perguntas de entrevista — tabela `log_perguntas_entrevista`
- [ ] **J4** — retrospectiva de processo seletivo — dialog ao mudar para aprovado/reprovado
- [ ] **J5** — heatmap de gaps → priorização automática de estudos
- [ ] **J6** — termômetro de empregabilidade — % vagas com 70%+ de fit
- [ ] **J7** — timer de preparação antes de entrevista — countdown + lista de estudos
- [ ] **J8** — alertas de janela de contratação por empresa (requer histórico)
- [ ] **J9** — curva de aprendizado estimada (requer histórico)

### I — Inteligência sobre os próprios dados (novas ideias)
- [ ] **I1** — análise do processo seletivo — em quais empresas você avançou mais?
- [ ] **I2** — radar de saúde por empresa — ritmo de abertura, tempo de vida das vagas
- [ ] **I3** — extração semântica das descrições — tamanho de equipe, volume de dados, cultura
- [ ] **I4** — classificador de senioridade via NLP — TF-IDF + regressão logística
- [ ] **I5** — impressão subjetiva no diário — campo positivo/neutro/negativo
- [ ] **I6** — comparador de ofertas concorrentes
- [ ] **I7** — exportar diff currículo × vaga como markdown/HTML
- [ ] **I8** — notificações Telegram/Discord webhook
- [ ] **I9** — similaridade semântica com sentence-transformers (alternativa Score ATS)

---

## 🔵 Onda 7 — Engenharia de dados pedagógica (4-6 sessões)

### E — Ferramentas DE (valor de portfólio)
- [ ] **E1** — Bronze layer — salvar JSON cru em `data/raw/{platform}/{empresa}/{date}.json`
- [ ] **E1b** — integrar `criar_views_medallion()` ao pipeline automaticamente
- [ ] **E1c** — migrar `carregar_vagas()` para usar view `gold_vagas`
- [ ] **E2** — dbt + DuckDB — `pip install dbt-duckdb`, models stg_vagas/dim_empresa/fact_vaga
- [ ] **E3** — Great Expectations — expandir validações para todas as plataformas
- [ ] **E4** — Prefect 2 — `@flow`, `@task`, retry automático, schedule local
- [ ] **E5** — GitHub Actions CI — py_compile + pytest + pip install em container limpo
- [ ] **E6** — testes pytest — stack_extractor, gerar_hash, utils.py, integração DuckDB
- [ ] **E7** — logging estruturado — substituir print() por logging/loguru
- [ ] **E8** — scrapers — separar coleta de detalhe, contexto Playwright reaproveitado

---

## 🟣 Onda 8 — Polimento UX + preparação candidaturas (2-3 sessões)

### X — UX análise profunda (novas ideias)
- [ ] **X2** — kanban de candidaturas — colunas por fase, cards clicáveis
- [ ] **X5a** — tab ativa por contexto no dialog — score para nova, candidatura para em processo
- [ ] **X7** — render_vaga_card para todas as telas — modo compacto como argumento `compact=True`
- [ ] **X8a** — cadastro de empresa — botão "Confirmar e salvar" após busca
- [ ] **X8b** — cadastro de vaga — autocomplete inline ao invés de modal de empresa
- [ ] **X8c** — perfil candidato — selectbox de stacks com autocomplete
- [ ] **X10** — config.toml com tema explícito + contraste WCAG AA
- [ ] **X11** — mobile — detectar viewport estreito, reduzir colunas automaticamente
- [ ] **X12** — micro-interações — contador no título, tooltip em badges, atalhos de teclado na fila

### U — UX backlog original
- [ ] **U3** — modo compacto padronizado usando render_vaga_card
- [ ] **U4** — barra de progresso fina no score dos cards
- [ ] **U7** — render_stacks — categoria mais destacada, expander para 30+ stacks
- [ ] **U9** — modo escuro — centralizar paleta para suportar tema escuro
- [ ] **U10** — log do pipeline incremental — st.empty() em vez de rebuild completo
- [ ] **U11** — confirmação antes de "Pausar todas" / "Ativar todas"
- [ ] **U12** — Estudos conectado com stacks das vagas — contador dinâmico por tópico
- [ ] **U13** — acessibilidade — aria-label, contraste WCAG em todos os badges

---

## 🔮 Onda 9 — Infraestrutura e deploy (3-5 sessões)

- [ ] **E9** — Delta Lake / Iceberg — `pyiceberg` com catalog SQLite local
- [ ] **E10** — Docker — Dockerfile dashboard + pipeline, docker-compose
- [ ] Deploy Streamlit Cloud
- [ ] Raspberry Pi 24/7 + Tailscale para acesso remoto
- [ ] Storage S3 para o banco DuckDB
- [ ] Prefect DAGs com retry e alertas
- [ ] Notificações por email/push

---

## 🐛 Débitos técnicos conhecidos

- dbt — incompatível Python 3.14
- salario_min/max vs salario_mensal/anual_total — campos com semânticas diferentes (decidido: min/max = faixa anunciada, mensal/total = negociado)
- Sequences do banco podem dessincronizar após recriação manual
- pipeline_runner.py ainda duplica parte da lógica de detecção de plataforma

---

## 🏆 Padrões de mercado

| Padrão | Status |
|---|---|
| Medallion Architecture | ✅ |
| Great Expectations | ✅ |
| Context Manager DB | ✅ |
| Cache de dados | ✅ |
| Componentes reutilizáveis | ✅ |
| utils.py + theme.py centralizados | ✅ |
| Backup automático | ✅ |
| Type hints | ✅ |
| Separação de responsabilidades (SRP) | ✅ |
| Factory Pattern scrapers | ✅ |
| Repository Pattern DB | ✅ |
| Estados vazios com instrução | ✅ |
| Navegação agrupada | ✅ |
| Logging estruturado | ❌ Onda 7 |
| Testes automatizados | ❌ Onda 7 |
| dbt | ❌ Onda 7 |
| Prefect | ❌ Onda 7 |
| CI/CD | ❌ Onda 7 |
| Docker | ❌ Onda 9 |

---

## 📋 Roadmap resumido

| Onda | Foco | Status | Sessões |
|---|---|---|---|
| 1 | Estabilizar bugs críticos | ✅ | — |
| 2 | Schema e migrations | ✅ | — |
| 3 | Padronizar acesso DB | ✅ | — |
| 4 | UI alta prioridade | ⚡ Em andamento | ~1 restante |
| 5 | Funcionalidades rápidas | 🔴 Próximo | 1 |
| 6 | Empregabilidade + inteligência | 🟠 | 2-3 |
| 7 | Engenharia DE pedagógica | 🟡 | 4-6 |
| 8 | Polimento UX + preparação | 🔵 | 2-3 |
| 9 | Docker + deploy + infra | 🔮 | 3-5 |
