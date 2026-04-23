# Job Tracker — Data Engineering Intelligence

> Pipeline pessoal de inteligência de mercado para vagas de Data Engineering. Stack 100% gratuita e open source — projeto de portfólio que ensina ferramentas mainstream do mercado de DE enquanto automatiza a busca de emprego.

---

## 🚀 O que faz

- **Coleta automática** de vagas em Gupy, Greenhouse, Inhire e SmartRecruiters via Playwright e APIs REST
- **Extração de stacks** via NLP — 80+ tecnologias em 8 categorias
- **Score de fit** — compatibilidade entre seu perfil e cada vaga, com breakdown de matches e gaps
- **Funil de candidaturas** — rastreia cada vaga do "não inscrito" até "aprovado"
- **Dashboard interativo** com 14 páginas — métricas, gráficos, filtros, dialogs de detalhe
- **Fila de inscrição** — vagas ordenadas por score para processar sequencialmente
- **Roadmap de estudos** com tracker de progresso e livros
- **Remuneração CLT/PJ** com cálculo automático de total mensal e anual

---

## 🏗 Arquitetura

```
job-tracker/
├── main.py                      # Orquestração do pipeline
├── utils.py                     # Helpers globais (safe_str, safe_bool, etc.)
├── Makefile                     # make run | make pipeline | make backup
├── start.sh                     # Hot reload
├── database/
│   ├── connection.py            # DB_PATH + context manager db_connect()
│   ├── schemas.py               # DDL completo + TIMELINE + backup automático
│   ├── migrations.py            # Migrações idempotentes para bancos existentes
│   ├── vagas.py                 # CRUD de vagas
│   ├── empresas.py              # CRUD de empresas
│   ├── candidaturas.py          # Atualização de candidatura e remuneração
│   ├── logs.py                  # Execuções e cooldown
│   ├── filtros.py               # Filtros de título e localização
│   ├── candidato.py             # Perfil e stacks do candidato
│   ├── score.py                 # Cálculo de fit
│   ├── diario.py                # Notas de candidatura
│   ├── contatos.py              # Contatos por empresa
│   ├── medallion.py             # Views Bronze/Silver/Gold
│   ├── quality.py               # Great Expectations
│   └── snapshots.py             # Histórico de stacks do mercado
├── scrapers/
│   ├── gupy_scraper.py          # Playwright + stealth
│   ├── gupy_detalhes.py         # Coleta de descrições em lote
│   ├── greenhouse_scraper.py    # API REST
│   ├── inhire_scraper.py        # Playwright
│   └── smartrecruiters_scraper.py  # API REST
├── transformers/
│   └── stack_extractor.py       # NLP para extração de stacks e nível
└── dashboard/
    ├── app.py                   # Roteamento com navegação agrupada
    ├── theme.py                 # Paleta de cores centralizada
    ├── data_loaders.py          # Queries e carregamento de dados
    ├── charts.py                # Gráficos Plotly
    ├── ui_components.py         # Componentes reutilizáveis
    ├── components.py            # Re-exporta tudo (compatibilidade)
    └── views/                   # 14 páginas do dashboard
        ├── dashboard_page.py
        ├── vagas.py
        ├── fila_inscricao.py
        ├── estudos.py
        ├── empresas.py
        ├── pipeline.py
        ├── configuracoes.py
        ├── comparativo.py
        ├── tendencias.py
        ├── funil.py
        ├── qualidade.py
        ├── perfil_candidato.py
        ├── contatos.py
        ├── cadastrar_vaga.py
        └── vagas_negadas.py
```

### Padrões implementados

| Padrão | Status |
|---|---|
| Medallion Architecture (Bronze/Silver/Gold) | ✅ |
| Repository Pattern (database/) | ✅ |
| Factory Pattern (scrapers) | ✅ |
| Context Manager DB (`db_connect()`) | ✅ |
| Cache (`@st.cache_data`) | ✅ |
| Separação de responsabilidades (SRP) | ✅ |
| Great Expectations | ✅ |
| Type hints | ✅ |
| Migrations idempotentes | ✅ |
| Paleta centralizada (theme.py) | ✅ |
| Logging estruturado | 🔜 |
| Testes automatizados (pytest) | 🔜 |
| dbt + DuckDB | 🔜 |
| Prefect orquestração | 🔜 |
| CI/CD GitHub Actions | 🔜 |
| Docker | 🔜 |

---

## ⚙️ Setup

### Requisitos
- Python 3.14+
- Playwright (`playwright install chromium`)

### Instalação

```bash
git clone https://github.com/oguigs/job-tracker
cd job-tracker
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### Executar

```bash
# Dashboard
make run

# Pipeline de coleta
make pipeline

# Backup manual
make backup
```

---

## 🗄 Banco de dados

**DuckDB** em `data/curated/jobs.duckdb`

| Tabela | Descrição |
|---|---|
| `dim_empresa` | Empresas monitoradas |
| `fact_vaga` | Vagas com candidatura, remuneração e stacks |
| `dim_candidato` | Perfil e stacks do candidato |
| `dim_candidato_stack` | Stacks com nível e anos de experiência |
| `dim_contato` | Contatos por empresa |
| `log_coleta` | Histórico de execuções do pipeline |
| `log_candidatura` | Diário de notas por vaga |
| `config_filtros` | Filtros de título, localização e estudos |
| `snapshot_mercado` | Histórico de stacks ao longo do tempo |

Backups automáticos em `data/curated/backups/` (mantém últimos 7).

Migrations em `database/migrations.py` — seguras para rodar múltiplas vezes.

---

## 🏃 Pipeline

O pipeline coleta vagas das empresas ativas, filtra por título e localização, extrai stacks das descrições e insere no banco.

```
dim_empresa (ativas)
    → scraper por plataforma (Gupy/Greenhouse/Inhire/SmartRecruiters)
    → filtro título + localização
    → coletar_descricoes_lote() — Playwright
    → extrair_stacks() — NLP
    → inserir_vaga() — DuckDB
    → registrar_log()
    → salvar_snapshot()
```

**Cooldown:** 12h entre execuções por empresa, 48h se bloqueada.

---

## 📊 Dashboard

14 páginas organizadas em 4 grupos na sidebar:

| Grupo | Páginas |
|---|---|
| 🎯 Trabalho diário | Dashboard, Fila de Inscrição, Vagas |
| 📚 Estudo | Estudos, Comparativo, Tendências |
| 📋 Cadastros | Cadastrar Vaga, Empresas, Indicadores, Meu Perfil |
| ⚙️ Operações | Pipeline, Qualidade, Configurações, Funil, Vagas Negadas |

---

## 🔧 Variáveis de ambiente

```bash
JOB_TRACKER_DB=data/curated/jobs.duckdb  # caminho do banco (opcional)
```

---

## 📋 Roadmap

| Onda | Foco | Status |
|---|---|---|
| 1-3 | Bugs, schema, padronização DB | ✅ |
| 4 | UI alta prioridade | ⚡ Em andamento |
| 5 | Funcionalidades rápidas (urgência, salário, saúde pipeline) | 🔴 |
| 6 | Empregabilidade (briefing entrevista, diff currículo) | 🟠 |
| 7 | DE pedagógico (dbt, Prefect, testes, CI/CD) | 🟡 |
| 8 | Polimento UX (kanban, micro-interações) | 🔵 |
| 9 | Deploy (Docker, Raspberry Pi, Streamlit Cloud) | 🔮 |

Ver [BACKLOG.md](BACKLOG.md) para detalhes completos.

---

## 🛠 Stack técnica

| Camada | Tecnologia |
|---|---|
| Linguagem | Python 3.14 |
| Banco de dados | DuckDB |
| Dashboard | Streamlit |
| Gráficos | Plotly |
| Scraping | Playwright + playwright-stealth |
| Qualidade | Great Expectations |
| Dados | Pandas |
