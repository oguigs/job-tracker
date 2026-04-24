# Job Tracker — Data Engineering Intelligence

> Pipeline pessoal de inteligência de mercado para vagas de Data Engineering. Stack 100% gratuita e open source — projeto de portfólio que ensina ferramentas mainstream do mercado de DE enquanto automatiza a busca de emprego.

---

## 🚀 O que faz

- **Coleta automática** de vagas em Gupy, Greenhouse, Inhire e SmartRecruiters via Playwright e APIs REST
- **Extração de stacks** via NLP — 80+ tecnologias em 8 categorias + tópicos customizados
- **Score de fit** — compatibilidade entre seu perfil e cada vaga com breakdown matches/gaps
- **Extração semântica** — tamanho de equipe, volume de dados, cultura, estágio da empresa
- **Detecção de salário** via regex nas descrições das vagas
- **Detecção de urgência** 🔥 automática
- **Funil de candidaturas** — timeline clicável do "não inscrito" até "aprovado"
- **Dashboard 15 páginas** organizadas em 4 grupos na sidebar
- **Fila de inscrição** — vagas ordenadas por score
- **Termômetro de empregabilidade** — % vagas com 70%+ de fit
- **Briefing automático** ao avançar para entrevista
- **Diff currículo × vaga** via pdfplumber + exportar como markdown
- **Banco de perguntas** de entrevista com stats de erros por stack
- **Retrospectiva de processo** ao encerrar candidatura
- **Comparador de ofertas** com score ponderado (fit + salário + afinidade)
- **Análise do processo seletivo** — Minha Performance
- **Radar de saúde** por empresa
- **Roadmap de estudos** com tópicos customizados, tracker de progresso e livros
- **Remuneração CLT/PJ** com cálculo automático (VR+VA+VT+PLR+Bônus+13º)
- **Diário de candidatura** com impressão subjetiva 😊😐😟
- **Prefect 2** — orquestração com @flow, @task e retry automático
- **Bronze layer** — JSONs crus antes de qualquer transformação
- **Logging estruturado** — get_logger() em todos os módulos
- **CI/CD** via GitHub Actions — py_compile + pytest a cada push

---

## 🏗 Arquitetura

```
job-tracker/
├── main.py                      # Orquestração do pipeline
├── pipeline_prefect.py          # Pipeline com Prefect 2 (@flow, @task)
├── pipeline_runner.py           # Entrypoint visual com Rich
├── logger.py                    # Logging centralizado get_logger()
├── utils.py                     # Helpers globais
├── Makefile                     # make run | pipeline | prefect | backup
├── .github/workflows/ci.yml     # CI GitHub Actions
├── database/
│   ├── connection.py            # DB_PATH + db_connect() context manager
│   ├── schemas.py               # DDL completo + TIMELINE + backup
│   ├── migrations.py            # Migrações idempotentes
│   ├── bronze.py                # Bronze layer — salvar/carregar JSONs crus
│   ├── vagas.py                 # CRUD vagas (urgente, descricao, salario)
│   ├── empresas.py              # CRUD + gerar_briefing_empresa()
│   ├── candidaturas.py          # Candidatura + remuneração automática
│   ├── perguntas.py             # Banco de perguntas de entrevista
│   ├── retrospectiva.py         # Retrospectiva de processo seletivo
│   ├── diario.py                # Notas com impressão subjetiva
│   ├── score.py                 # Cálculo de fit
│   ├── candidato.py             # Perfil e stacks do candidato
│   ├── contatos.py              # Contatos por empresa
│   ├── filtros.py               # Filtros de título e localização
│   ├── logs.py                  # Execuções e cooldown
│   ├── medallion.py             # Views Bronze/Silver/Gold
│   ├── quality.py               # Great Expectations
│   └── snapshots.py             # Histórico de stacks
├── scrapers/
│   ├── gupy_scraper.py          # Playwright + stealth
│   ├── gupy_detalhes.py         # Descrições em lote
│   ├── greenhouse_scraper.py    # API REST
│   ├── inhire_scraper.py        # Playwright
│   └── smartrecruiters_scraper.py
├── transformers/
│   ├── stack_extractor.py       # NLP: stacks, nível, urgência, salário, sinais
│   └── curriculo_parser.py      # pdfplumber + diff currículo × vaga
├── tests/
│   ├── test_utils.py            # 11 testes
│   └── test_stack_extractor.py  # 17 testes
└── dashboard/
    ├── app.py                   # Navegação agrupada em 4 grupos
    ├── theme.py                 # Paleta centralizada (WCAG AA)
    ├── data_loaders.py          # Queries e cache
    ├── ui_components.py         # Componentes reutilizáveis
    └── views/                   # 15 páginas
```

---

## ⚙️ Setup

```bash
git clone https://github.com/oguigs/job-tracker
cd job-tracker
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

## 🚀 Comandos

```bash
make run            # Dashboard Streamlit
make pipeline       # Pipeline de coleta
make prefect        # Pipeline com Prefect (uma vez)
make prefect-serve  # Pipeline agendado a cada 6h
make prefect-ui     # UI do Prefect
make backup         # Backup manual do banco
make test           # pytest
```

---

## 🗄 Banco de dados

**DuckDB** em `data/curated/jobs.duckdb`

| Tabela | Descrição |
|---|---|
| `dim_empresa` | Empresas monitoradas |
| `fact_vaga` | Vagas com candidatura, remuneração, stacks, sinais semânticos |
| `dim_candidato` | Perfil e stacks do candidato |
| `dim_candidato_stack` | Stacks com nível e experiência |
| `dim_contato` | Contatos por empresa |
| `log_coleta` | Histórico de execuções |
| `log_candidatura` | Diário com impressão subjetiva |
| `log_perguntas_entrevista` | Banco de perguntas técnicas |
| `log_retrospectiva` | Retrospectivas de processos encerrados |
| `config_filtros` | Filtros, estudos, livros e tópicos customizados |
| `snapshot_mercado` | Histórico de stacks do mercado |

Bronze layer em `data/raw/{plataforma}/{empresa}/{date}.json`

---

## 📊 Dashboard — 15 páginas

| Grupo | Páginas |
|---|---|
| 🎯 Trabalho diário | Dashboard, Fila de Inscrição, Vagas |
| 📚 Estudo | Estudos, Comparativo, Tendências, Minha Performance, Perguntas |
| 📋 Cadastros | Cadastrar Vaga, Empresas, Indicadores, Meu Perfil, Comparar Ofertas |
| ⚙️ Operações | Pipeline, Qualidade, Configurações, Funil, Vagas Negadas |

---

## 🛠 Stack técnica

| Camada | Tecnologia |
|---|---|
| Linguagem | Python 3.14 |
| Banco | DuckDB |
| Dashboard | Streamlit |
| Gráficos | Plotly |
| Scraping | Playwright + stealth |
| Orquestração | Prefect 2 |
| Qualidade | Great Expectations |
| Testes | pytest (28 testes) |
| CI/CD | GitHub Actions |
| Dados | Pandas |
| PDF | pdfplumber |

---

## 📋 Roadmap

| Onda | Foco | Status |
|---|---|---|
| 1-7 | Bugs, schema, UI, funcionalidades, DE | ✅ |
| 8 | Polimento UX (kanban, autocomplete) | 🔴 Próximo |
| 9 | Scrapers melhorados | 🟠 |
| 10 | Deploy (Docker, Raspberry Pi, Telegram) | 🟡 |
| 11 | Inteligência acumulada | 🔮 |

Ver [BACKLOG.md](BACKLOG.md) para detalhes.