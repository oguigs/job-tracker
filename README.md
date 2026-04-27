# Job Tracker — Data Engineering

> Sistema de inteligência de mercado para profissionais de dados. Coleta vagas automaticamente de 37 empresas, extrai stacks, calcula scores ATS e exibe tudo em um dashboard interativo.

---

## Sobre o projeto

Pipeline completo de engenharia de dados para acompanhar o mercado de trabalho em Data Engineering. O sistema coleta vagas de 7 plataformas de recrutamento, processa as descrições, extrai tecnologias exigidas, calcula um score ATS comparando a vaga com o currículo do usuário, e apresenta tudo em um dashboard Streamlit com análises visuais.

**Números atuais:** 37 empresas monitoradas · 7 plataformas de coleta · ~169 vagas indexadas · 4 agentes LLM locais

---

## Arquitetura

```
job-tracker/
├── scrapers/
│   ├── gupy_scraper.py            # Gupy — paginação via API JSON
│   ├── gupy_detalhes.py           # Coleta descrição individual por vaga (Playwright)
│   ├── greenhouse_scraper.py      # Greenhouse — boards-api.greenhouse.io
│   ├── inhire_scraper.py          # InHire — Playwright + networkidle
│   ├── smartrecruiters_scraper.py # SmartRecruiters — API pública
│   ├── amazon_scraper.py          # Amazon Jobs — search.json API, filtro country=BRA
│   ├── bcg_scraper.py             # BCG Careers (Phenom People) — Playwright
│   ├── doordash_scraper.py        # DoorDash — Greenhouse API (doordashinternational)
│   ├── uber_scraper.py            # Uber — POST /api/loadSearchJobsResults, filtro BRA
│   └── company_search.py          # Busca dados de empresa (DuckDuckGo)
├── transformers/
│   ├── stack_extractor.py         # Extração de stacks, nível, modalidade, urgência, salário
│   ├── ats_agents.py              # Agentes ANYA, VANELLOPE, ARYA, NEXUS (Ollama)
│   └── curriculo_parser.py        # Parser de PDF do currículo
├── database/
│   ├── connection.py              # Gerenciamento de conexão DuckDB (context manager)
│   ├── schemas.py                 # DDL de todas as tabelas + backup automático
│   ├── empresas.py                # CRUD de empresas
│   ├── vagas.py                   # Inserção e deduplicação de vagas
│   ├── candidaturas.py            # Gestão do funil de candidatura
│   ├── ats_score.py               # Score ATS por vaga
│   ├── candidato.py               # Perfil e currículo do candidato
│   ├── contatos.py                # Rede de contatos por empresa
│   ├── logs.py                    # Log de execuções do pipeline
│   ├── filtros.py                 # Filtros de interesse e localização
│   └── snapshots.py               # Snapshots semanais do mercado
├── dashboard/
│   ├── app.py                     # Entrada do Streamlit — roteamento de páginas
│   ├── ui_components.py           # Cards, badges e componentes visuais reutilizáveis
│   └── views/
│       ├── dashboard_page.py      # Análises gerais do mercado
│       ├── vagas.py               # Lista de vagas com filtros e modo compacto
│       ├── empresas.py            # Gestão de empresas monitoradas
│       ├── perfil_empresa.py      # Perfil detalhado por empresa
│       ├── analise_curriculo.py   # Análise ATS currículo × vaga (4 agentes)
│       ├── arquitetura.py         # Visualização do pipeline ETL ao vivo
│       ├── tendencias.py          # Ranking de stacks e tendências de mercado
│       ├── funil.py               # Funil de candidaturas e conversão
│       ├── pipeline.py            # Monitor de execuções do pipeline
│       ├── minha_performance.py   # Métricas pessoais de candidatura
│       ├── perfil_candidato.py    # Perfil e stacks do candidato
│       ├── cadastrar_vaga.py      # Cadastro manual de vagas
│       ├── comparar_ofertas.py    # Comparativo entre ofertas
│       ├── comparativo.py         # Comparativo entre empresas
│       ├── configuracoes.py       # Filtros, currículo e preferências
│       ├── fila_inscricao.py      # Fila de vagas para se inscrever
│       ├── vagas_negadas.py       # Vagas negadas / arquivadas
│       ├── contatos.py            # Rede de contatos
│       ├── qualidade.py           # Qualidade dos dados coletados
│       ├── estudos.py             # Plano de estudos e gaps
│       └── perguntas.py           # Perguntas de entrevista por empresa
├── dbt/
│   ├── models/
│   │   ├── staging/               # stg_vagas, stg_empresas, stg_log_coleta
│   │   └── marts/                 # fct_vagas, dim_empresa_stats, agg_stacks_mercado
│   └── profiles.yml               # Conexão DuckDB para o dbt
├── main.py                        # Orquestrador do pipeline
├── logger.py                      # Logger centralizado com rich
├── Makefile                       # Atalhos: run, pipeline, dbt-run, dbt-test
└── BACKLOG.md                     # Roadmap completo do projeto
```

### Fluxo do pipeline

```
dim_empresa (banco)
      │  37 empresas ativas, cooldown 12h por empresa
      ▼
Scrapers (7 plataformas)
  Gupy · Greenhouse · InHire · SmartRecruiters
  Amazon Jobs · BCG · DoorDash · Uber
      │  título, link, localização, descrição
      ▼
Stack Extractor (regex + dicionário)
      │  stacks por categoria, nível, modalidade, urgência, salário
      ▼
ANYA (agente ATS — Ollama local)
      │  score ATS: keywords + formatação + seções + impacto
      ▼
DuckDB — fact_vaga
      │  deduplicação por hash, vagas encerradas detectadas
      ▼
dbt (staging → marts)
      │  stg_vagas · fct_vagas · dim_empresa_stats · agg_stacks_mercado
      ▼
Dashboard Streamlit
```

---

## Plataformas de coleta

| Plataforma | Abordagem | Empresas |
|---|---|---|
| Gupy | API JSON pública (`/v1/jobs`) | 24 empresas |
| Greenhouse | API REST (`boards-api.greenhouse.io`) | Nubank, iFood, C6 Bank, Jusbrasil, Ai Inbev, DoorDash |
| InHire | Playwright + `networkidle` | Magalu Cloud, Pra Valer |
| SmartRecruiters | API REST pública | Visa, Serasa |
| Amazon Jobs | API JSON + filtro `country=BRA` | Amazon AWS |
| BCG Careers | Playwright (Phenom People) | BCG |
| Uber Careers | POST `/api/loadSearchJobsResults` + filtro BRA | Uber |

---

## Agentes ATS (Ollama — local, gratuito)

Quatro agentes LLM analisam o currículo em relação a cada vaga:

| Agente | Função | Score |
|---|---|---|
| ANYA | Analisa match de keywords entre currículo e vaga | 0–100 |
| VANELLOPE | Analisa formatação ATS-friendly do currículo | 0–100 |
| ARYA | Verifica seções obrigatórias (experiência, skills, educação) | 0–100 |
| NEXUS | Gera sugestões de otimização com before/after | — |

Score final = ANYA × 0,40 + VANELLOPE × 0,25 + ARYA × 0,20 + Impacto × 0,15

---

## Modelo de dados

### `fact_vaga`
| Campo | Tipo | Descrição |
|---|---|---|
| id | INTEGER | Chave primária |
| hash | VARCHAR | MD5(título + empresa + link) — unicidade |
| titulo | VARCHAR | Título da vaga |
| nivel | VARCHAR | junior / pleno / senior / especialista / lead |
| modalidade | VARCHAR | remoto / hibrido / presencial |
| stacks | JSON | Stacks por categoria (linguagens, cloud, etc.) |
| link | VARCHAR | URL da vaga |
| fonte | VARCHAR | gupy / greenhouse / inhire / smartrecruiters / amazon / bcg / desconhecida |
| id_empresa | INTEGER | FK → dim_empresa |
| data_coleta | DATE | Data da coleta |
| ativa | BOOLEAN | Vaga ainda no ar |
| urgente | BOOLEAN | Detectado "urgente" / "início imediato" |
| salario_min / max | INTEGER | Faixa salarial extraída da descrição |
| candidatura_status | VARCHAR | nao_inscrito → inscrito → chamado → aprovado / reprovado |

### `dim_empresa`
| Campo | Tipo | Descrição |
|---|---|---|
| id | INTEGER | Chave primária |
| nome | VARCHAR | Nome da empresa |
| url_vagas | VARCHAR | URL do portal de vagas |
| favicon_url | VARCHAR | URL do ícone da empresa |
| ramo / cidade / estado | VARCHAR | Dados cadastrais |
| ativa | BOOLEAN | Monitoramento ativo |

### `dim_ats_score`
| Campo | Tipo | Descrição |
|---|---|---|
| id_vaga | INTEGER | FK → fact_vaga |
| score_keywords / formatacao / secoes / impacto | FLOAT | Scores por dimensão |
| score_final | FLOAT | Score ponderado 0–100 |
| keywords_encontradas / ausentes | JSON | Detalhes do match |

### `log_coleta`
| Campo | Tipo | Descrição |
|---|---|---|
| empresa | VARCHAR | Empresa processada |
| status | VARCHAR | sucesso / erro / bloqueado |
| vagas_encontradas / novas | INTEGER | Métricas da execução |
| data_execucao | TIMESTAMP | Horário da execução |

### Modelos dbt
| Modelo | Camada | Descrição |
|---|---|---|
| `stg_vagas` | Staging | Vagas normalizadas, nulos tratados, negadas filtradas |
| `stg_empresas` | Staging | Empresas com plataforma detectada pela URL |
| `stg_log_coleta` | Staging | Log de execuções |
| `fct_vagas` | Mart | Tabela fato com empresa desnormalizada e flags analíticas |
| `dim_empresa_stats` | Mart | Empresa enriquecida com estatísticas de vagas e pipeline |
| `agg_stacks_mercado` | Mart | Stacks unnestadas — ranking por categoria e nível |

---

## Stack do projeto

| Camada | Ferramenta | Por quê |
|---|---|---|
| Scraping JS | Playwright + playwright-stealth | Sites React/Next.js com SPA |
| Scraping REST | requests | APIs JSON públicas (Gupy, Greenhouse, SmartRecruiters, Uber, Amazon) |
| NLP / extração | Regex + dicionário de stacks | Leve, customizável, zero custo |
| LLM local | Ollama (llama3.2 / qwen2.5) | Análise ATS sem custo, sem limite de tokens |
| Storage | DuckDB | OLAP local, zero infraestrutura, compatível com dbt |
| Transformação analytics | dbt-core + dbt-duckdb | Camada staging → marts com testes automáticos |
| Dashboard | Streamlit | Zero frontend, deploy simples |
| Logging | rich / loguru | Logs coloridos no terminal |

---

## Instalação

### Pré-requisitos
- Python 3.11+
- [Ollama](https://ollama.ai) (para os agentes ATS — opcional)

### Setup

```bash
git clone https://github.com/oguigs/job-tracker.git
cd job-tracker

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
python -m playwright install chromium
```

### Ollama (agentes ATS)

```bash
# instalar Ollama: https://ollama.ai
ollama pull llama3.2   # ou qwen2.5, mistral
```

### Rodar

```bash
# pipeline de coleta
make pipeline
# ou: python main.py

# dashboard
make run
# ou: streamlit run dashboard/app.py

# dbt (camada analytics)
make dbt-run
make dbt-test
```

---

## Funcionalidades

### Pipeline
- Scraper multi-plataforma: Gupy, Greenhouse, InHire, SmartRecruiters, Amazon, BCG, DoorDash, Uber
- Cooldown por empresa (12h) — evita coletas repetidas
- Bloqueio automático de 48h em caso de detecção de bot
- Deduplicação por hash MD5 — sem duplicatas
- Detecção automática de vagas encerradas
- Score ATS calculado automaticamente para cada nova vaga
- Extração de stacks por categoria, nível, modalidade, urgência e faixa salarial

### Dashboard
- **Vagas** — cards com badges 🆕/🔥, tempo relativo, scores com mini progress bars, modo compacto
- **Análise ATS** — 4 agentes LLM analisam currículo × vaga com score detalhado e sugestões
- **Arquitetura ETL** — visualização ao vivo do pipeline com métricas por empresa
- **Tendências** — ranking de stacks, comparativo de tecnologias, histórico temporal
- **Funil** — kanban de candidaturas com timeline de fases
- **Perfil da empresa** — stacks exigidas, nível médio, histórico de vagas
- **Filtros configuráveis** — por título, localização, nível e modalidade

---

## Licença

Projeto pessoal para estudo e uso próprio.
