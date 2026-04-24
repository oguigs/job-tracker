# Job Tracker — Backlog
> v1.3 em desenvolvimento · Abril 2026
> Última atualização: Ondas 1-7 parcialmente concluídas

---

## ✅ Ondas 1-5 — Concluídas

### Onda 1 — Estabilizar
- B1-B10 todos os bugs resolvidos
- A5 pasta fantasma, A6 __pycache__

### Onda 2 — Schema
- B4 criar_tabelas() completo, migrations.py, remuneração sal13/PLR/bônus

### Onda 3 — Padronizar acesso DB
- db_connect em todos os módulos, pipeline_runner entrypoint fino, Playwright para gupy_detalhes, cache clear

### Onda 4 — UI alta prioridade
- X1 navegação agrupada, U2 dialog unificado, U5 filtros persistentes, U6 filtros rápidos destacados
- X9 theme.py, X6a botões Estudos, X4 estados vazios, X5b timeline clicável, X5d toasts, X3 fila inscrição

### Onda 5 — Funcionalidades rápidas
- P1 urgência 🔥, P2 salário regex, P6 saúde pipeline

---

## ✅ Onda 6 — Empregabilidade (concluída)
- J6 termômetro de empregabilidade no Dashboard
- J2 briefing automático ao avançar para entrevista (tab 🎯 Briefing)
- J1 diff currículo × vaga via pdfplumber (tab 📄 Diff CV) + export markdown
- J3 banco de perguntas de entrevista (página Perguntas)
- J4 retrospectiva de processo ao mudar para aprovado/reprovado
- I1 página Minha Performance
- I2 radar de saúde no perfil empresa
- I3 extração semântica: tamanho equipe, volume dados, cultura, estágio
- I5 impressão subjetiva no diário 😊😐😟
- I6 comparador de ofertas com score ponderado
- I7 exportar diff como markdown

---

## ✅ Onda 7 — Engenharia DE (parcialmente concluída)
- E7 logging estruturado com get_logger() em main, scrapers e database
- E6 pytest: 28 testes passando (utils + stack_extractor)
- E5 GitHub Actions CI — py_compile + pytest + imports críticos
- E4 Prefect 2 — pipeline_prefect.py com @flow, @task, retry automático
- E1 Bronze layer — salvar_bronze(), carregar_bronze(), listar_bronze()

---

## 🔴 Onda 7 — Restante

- [ ] **E1b** — integrar `criar_views_medallion()` ao pipeline automaticamente
- [ ] **E1c** — migrar `carregar_vagas()` para usar view `gold_vagas`
- [ ] **E2** — dbt + DuckDB — aguardando compatibilidade Python 3.14
- [ ] **E3** — Great Expectations — expandir validações para todas as plataformas
- [ ] **E8** — scrapers — contexto Playwright reaproveitado entre vagas

---

## 🟠 Onda 8 — Polimento UX (2-3 sessões)

- [ ] **X2** — kanban de candidaturas — colunas por fase, cards clicáveis
- [ ] **X5a** — tab ativa por contexto no dialog
- [ ] **X7** — render_vaga_card para todas as telas — compact=True
- [ ] **X8a** — cadastro empresa — "Confirmar e salvar" direto
- [ ] **X8b** — cadastro vaga — autocomplete inline
- [ ] **X8c** — perfil candidato — selectbox de stacks com autocomplete
- [ ] **X10** — config.toml com tema explícito + contraste WCAG AA
- [ ] **X11** — mobile — detectar viewport estreito
- [ ] **X12** — micro-interações — contador no título, tooltip em badges
- [ ] **U3** — modo compacto padronizado
- [ ] **U4** — barra de progresso fina no score dos cards
- [ ] **U7** — render_stacks — categoria mais destacada
- [ ] **U10** — log pipeline incremental
- [ ] **U11** — confirmação ações destrutivas
- [ ] **U12** — Estudos conectado com stacks das vagas — contador dinâmico
- [ ] **U13** — acessibilidade — aria-label, contraste WCAG

---

## 🔵 Onda 9 — Scrapers melhorados (1-2 sessões)

- [ ] Gupy — extrair localização, regime, data de encerramento
- [ ] Greenhouse — modalidade, departamento
- [ ] Inhire — localização e nível
- [ ] SmartRecruiters — departamento e data de publicação
- [ ] Padronizar campos entre plataformas
- [ ] Detectar vagas duplicadas entre plataformas
- [ ] Scraper Lever — jobs.lever.co
- [ ] Amazon Jobs scraper (branch feature/amazon-scraper)
- [ ] BCG scraper (branch feature/bcg-scraper)

---

## 🔮 Onda 10 — Infraestrutura e deploy (3-5 sessões)

- [ ] Docker + docker-compose
- [ ] Deploy Streamlit Cloud
- [ ] Raspberry Pi 24/7 + Tailscale
- [ ] Prefect agendado a cada 6h (make prefect-serve)
- [ ] Notificações Telegram Bot — novas vagas com score alto
- [ ] GitHub Actions CI/CD completo com deploy
- [ ] Storage S3 para o banco DuckDB

---

## 🔮 Onda 11 — Inteligência acumulada

- [ ] **J5** — heatmap de gaps → priorização automática de estudos
- [ ] **J7** — timer de preparação antes de entrevista
- [ ] **J8** — alertas sazonais de contratação (requer histórico)
- [ ] **J9** — curva de aprendizado estimada
- [ ] **I4** — classificador de senioridade via NLP
- [ ] **I9** — sentence-transformers — similaridade semântica
- [ ] **E9** — Delta Lake / Iceberg
- [ ] **P3** — snapshot semanal automático via cron/launchd

---

## 🐛 Débitos técnicos

- dbt — incompatível Python 3.14
- salario_min/max = faixa anunciada / salario_mensal/total = negociado
- pipeline_runner.py ainda duplica parte da lógica de detecção de plataforma
- Favicon local vs URL — inconsistência entre empresas
- DuckDB read_only removido — todas as conexões são read/write

---

## 🏆 Padrões de mercado

| Padrão | Status |
|---|---|
| Medallion Architecture | ✅ |
| Repository Pattern | ✅ |
| Factory Pattern scrapers | ✅ |
| Context Manager DB | ✅ |
| Cache de dados | ✅ |
| Separação de responsabilidades | ✅ |
| Great Expectations | ✅ |
| Type hints | ✅ |
| Migrations idempotentes | ✅ |
| Paleta centralizada (theme.py) | ✅ |
| Estados vazios com instrução | ✅ |
| Logging estruturado | ✅ |
| Testes automatizados (pytest 28) | ✅ |
| CI/CD GitHub Actions | ✅ |
| Prefect orquestração | ✅ |
| Bronze layer | ✅ |
| dbt | ❌ Onda 7 (Python 3.14) |
| Docker | ❌ Onda 10 |

---

## 📋 Roadmap resumido

| Onda | Foco | Status | Sessões |
|---|---|---|---|
| 1-7 | Bugs, schema, UI, funcionalidades, DE | ✅ / ⚡ | — |
| 8 | Polimento UX | 🔴 Próximo | 2-3 |
| 9 | Scrapers melhorados | 🟠 | 1-2 |
| 10 | Deploy + Telegram | 🟡 | 3-5 |
| 11 | Inteligência acumulada | 🔮 | várias |
