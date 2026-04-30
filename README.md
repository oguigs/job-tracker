# Job Tracker

Sistema pessoal de inteligência de mercado para acompanhar vagas de dados. Coleta automaticamente de 10+ plataformas de recrutamento, extrai stacks, calcula score ATS e exibe tudo num dashboard local.

**Números atuais:** ~40 empresas monitoradas · 10 plataformas de coleta · ~170 vagas indexadas · 4 agentes LLM locais

---

## O que faz

O problema que esse projeto resolve é simples: acompanhar o mercado de dados manualmente é inviável. As vagas somem, as stacks mudam, e sem registro você perde padrões que só ficam óbvios com volume.

O sistema faz três coisas:

1. **Coleta vagas** de múltiplas plataformas automaticamente, com deduplicação por hash e detecção de vagas encerradas
2. **Analisa o fit** entre seu currículo e cada vaga, usando agentes LLM locais rodando no Ollama
3. **Exibe tudo** num dashboard Streamlit com filtros, funil de candidaturas, análise de stacks e histórico

---

## Arquitetura

```
dim_empresa (banco)
      │  empresas ativas, cooldown 12h por empresa
      ▼
Scrapers (10 plataformas)
  Gupy · Greenhouse · Lever · InHire · SmartRecruiters
  Amazon Jobs · BCG · DoorDash · Uber · Amaris (MeiliSearch)
      │  título, link, localização, descrição
      ▼
Stack Extractor (regex + dicionário por categoria)
      │  stacks, nível, modalidade, urgência, salário
      ▼
ANYA (agente ATS — Ollama local)
      │  score: keywords + formatação + seções + impacto
      ▼
DuckDB — fact_vaga
      │  deduplicação por hash, vagas encerradas detectadas
      ▼
dbt (staging → marts)
      │  stg_vagas · fct_vagas · dim_empresa_stats · agg_stacks_mercado
      ▼
Dashboard Streamlit
```

```
job-tracker/
├── scrapers/           # Um arquivo por plataforma
├── transformers/       # Stack extractor + agentes ATS (Ollama)
├── database/           # DuckDB: conexão, schemas, CRUD por entidade
├── dashboard/
│   ├── app.py          # Roteamento de páginas
│   ├── ui_components.py
│   └── views/          # Uma view por página do dashboard
├── dbt/
│   ├── models/staging/ # stg_vagas, stg_empresas, stg_log_coleta
│   └── models/marts/   # fct_vagas, dim_empresa_stats, agg_stacks_mercado
├── main.py             # Orquestrador do pipeline
└── pipeline_prefect.py # Orquestração com Prefect (opcional)
```

---

## Stacks e por que foram escolhidas

### DuckDB

Banco de dados analítico embedded. Sem servidor, sem configuração, arquivo único no disco.

Foi a escolha certa porque o projeto é OLAP puro: leituras analíticas em cima de um volume pequeno-médio de vagas. DuckDB é incrivelmente rápido nisso, roda dentro do processo Python e é compatível com dbt nativamente.

**O que poderia ter sido usado:**
- **SQLite** — mais familiar, mas sem suporte analítico decente. Sem funções de janela, sem JSON bem suportado, sem integração com dbt.
- **PostgreSQL** — seria exagero. Você ganha transações e escalabilidade que esse projeto nunca vai precisar, em troca de ter que rodar um servidor local.
- **Parquet + pandas** — simples de começar, mas perde a capacidade de query ad-hoc e não tem onde guardar estado (candidaturas, empresas, contatos).

---

### Streamlit

Dashboard sem frontend. Você escreve Python, o Streamlit vira interface.

A escolha foi pragmática: o objetivo era ter um dashboard funcional rápido, não construir uma aplicação web. Streamlit elimina HTML, CSS e JavaScript completamente. Para uso pessoal e local, funciona bem.

**O que poderia ter sido usado:**
- **Dash (Plotly)** — mais flexível que Streamlit para customização visual, mas requer estrutura de callbacks que aumenta a complexidade para pouco ganho aqui.
- **Grafana** — ótimo para séries temporais e monitoramento de infra. Inadequado para esse caso porque o dashboard mistura análise com ações (funil de candidaturas, edição de dados, geração de cartas).
- **Metabase** — bom para exploração SQL por não-devs. Não faria sentido aqui porque o projeto já é do desenvolvedor.
- **React + FastAPI** — seria o caminho se houvesse intenção de hospedar ou compartilhar. Para uso local pessoal, é muito overhead.

---

### Playwright + playwright-stealth

Para os sites que carregam via JavaScript (React/Next.js SPAs), requests normais retornam HTML vazio ou de loading. Playwright abre um browser de verdade e espera a página renderizar.

playwright-stealth remove os fingerprints que sites de recrutamento usam para detectar automação (navigator.webdriver, inconsistências em Canvas, etc.).

**O que poderia ter sido usado:**
- **Selenium** — mais antigo, mais pesado, mais lento. Playwright tem API melhor e é mais confiável com páginas modernas.
- **Puppeteer** — só JavaScript/Node. Não faz sentido num projeto Python.
- **Splash** — proxy HTTP que renderiza JavaScript, mas requer um serviço Docker separado. Mais complexidade sem ganho claro.
- **undetected-chromedriver** — alternativa ao stealth para ChromeDriver. Playwright + stealth ficou mais robusto nos testes.

---

### requests

Para as plataformas que têm API pública (Gupy, Greenhouse, SmartRecruiters, Lever, Amazon Jobs, Uber), requests é o suficiente. Sem JavaScript, sem browser, só HTTP.

**O que poderia ter sido usado:**
- **httpx** — suporte a async e HTTP/2. Seria útil se os scrapers rodassem em paralelo com asyncio. Por ora o pipeline é síncrono e requests resolve.
- **aiohttp** — mesmo argumento. Vale migrar se o tempo de coleta virar gargalo.

---

### Ollama (llama3.2 / qwen2.5)

Quatro agentes LLM analisam currículo × vaga localmente. Sem API key, sem custo por token, sem limite de chamadas.

O modelo roda na máquina. A latência é maior que uma API cloud, mas para análise assíncrona de vagas isso não importa. O que importa é não ter custo recorrente e não mandar currículo para servidores externos.

| Agente | O que faz |
|---|---|
| ANYA | Match de keywords currículo × vaga (peso 40%) |
| VANELLOPE | Compatibilidade de carreira e posicionamento (peso 25%) |
| ARYA | Estratégia para o processo seletivo (peso 20%) |
| NEXUS | Reescreve título, resumo e bullets do currículo (peso 15%) |
| CARTA | Gera carta de apresentação personalizada por vaga |

**O que poderia ter sido usado:**
- **OpenAI API (GPT-4o)** — respostas melhores, especialmente em análise de contexto. Mas custa dinheiro por chamada e você manda dados pessoais para fora.
- **Groq** — API gratuita com Llama e Mixtral, rápida. Boa alternativa se o hardware local for fraco. Ainda depende de conexão e tem limite de rate.
- **HuggingFace Transformers** — rodar modelos localmente sem Ollama. Mais controle, muito mais complexidade de setup.
- **Regex puro** — suficiente para extração de keywords, mas não para análise contextual. ANYA já usa regex; os outros agentes precisam de raciocínio.

---

### dbt (dbt-core + dbt-duckdb)

Camada de transformação analítica. Os scrapers inserem dados brutos; o dbt produz as tabelas limpas que o dashboard usa.

O modelo staging → marts separa responsabilidades: os scrapers não precisam saber do schema analítico, e o dashboard não depende de tabelas brutas.

**O que poderia ter sido usado:**
- **pandas puro** — simples de começar, mas você perde documentação de linhagem, testes automáticos de dados e a separação clara entre ingestão e transformação.
- **SQLAlchemy** — para transformações em SQL dentro do Python. Sem a estrutura de DAG e sem os testes nativos do dbt.
- **Airflow** — orquestração pesada demais para um projeto local. Faz sentido quando você tem dezenas de pipelines com dependências complexas.

---

### Regex + dicionário de stacks

Stack extractor não usa LLM: é regex com dicionário categorizado de tecnologias. Mais de 400 termos mapeados por categoria (linguagens, cloud, bancos de dados, ferramentas de dados, etc.).

A escolha foi deliberada. LLM para extração de stacks seria lento e impreciso comparado a um dicionário curado. Regex não alucina "React" quando a vaga menciona "reação do cliente".

**O que poderia ter sido usado:**
- **spaCy com NER customizado** — mais sofisticado, reconhece entidades no contexto. Vale considerar quando o dicionário ficar difícil de manter.
- **GPT para extração** — funciona, mas traz o custo e latência de uma chamada de API para cada vaga. O dicionário cobre 95% dos casos com custo zero.

---

### Prefect (opcional)

Orquestração do pipeline com retry, logging estruturado e UI de monitoramento. O pipeline funciona sem Prefect (basta `python main.py`), mas com `pipeline_prefect.py` você ganha observabilidade e scheduling.

**O que poderia ter sido usado:**
- **cron** — suficiente para scheduling. Sem observabilidade, sem retry automático.
- **APScheduler** — scheduler dentro do processo Python. Mais simples que Prefect, menos recursos.
- **Dagster** — alternativa moderna ao Airflow/Prefect. Boa para equipes; overhead alto para uso pessoal.

---

### pdfplumber

Lê PDF do currículo e extrai texto para os agentes LLM processarem.

**O que poderia ter sido usado:**
- **PyMuPDF (fitz)** — mais rápido e melhor com PDFs complexos. pdfplumber é mais simples de usar para extração de texto simples.
- **python-docx** — já está no requirements para arquivos .docx.

---

### MeiliSearch (externo, via Amaris)

O site careers.amaris.com usa MeiliSearch como motor de busca. Em vez de scraping com Playwright, o scraper da Amaris chama a API REST do MeiliSearch diretamente, com a chave pública exposta no bundle JavaScript do site.

---

## Modelo de dados

### `fact_vaga`
| Campo | Descrição |
|---|---|
| `hash` | MD5(título + empresa + link) — deduplicação |
| `titulo`, `nivel`, `modalidade` | Dados básicos da vaga |
| `stacks` | JSON com tecnologias por categoria |
| `fonte` | gupy / greenhouse / lever / smartrecruiters / amazon / bcg / amaris / ... |
| `ativa` | False quando a vaga sai do ar |
| `urgente` | True quando detecta "urgente" / "início imediato" na descrição |
| `salario_min`, `salario_max` | Faixa salarial extraída da descrição |
| `candidatura_status` | nao_inscrito → inscrito → chamado → aprovado / reprovado |

### Modelos dbt
| Modelo | Camada | O que faz |
|---|---|---|
| `stg_vagas` | Staging | Vagas normalizadas, nulos tratados, negadas filtradas |
| `stg_empresas` | Staging | Empresas com plataforma detectada pela URL |
| `fct_vagas` | Mart | Tabela fato com empresa desnormalizada e flags analíticas |
| `dim_empresa_stats` | Mart | Empresa com estatísticas de vagas e pipeline de candidatura |
| `agg_stacks_mercado` | Mart | Stacks unnestadas para ranking por categoria e nível |

---

## Instalação

**Pré-requisitos:** Python 3.11+, [Ollama](https://ollama.ai) (opcional, para agentes ATS)

```bash
git clone https://github.com/oguigs/job-tracker.git
cd job-tracker

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
```

```bash
# Ollama — agentes ATS
ollama pull llama3.2
```

```bash
make pipeline   # coleta vagas
make run        # dashboard
make dbt-run    # camada analytics
make dbt-test   # testes de qualidade
```

---

## Plataformas de coleta

| Plataforma | Abordagem | Notas |
|---|---|---|
| Gupy | API JSON (`/v1/jobs`) | 24+ empresas |
| Greenhouse | API REST (`boards-api.greenhouse.io`) | iFood, Nubank, C6, Ai Inbev |
| Lever | API REST pública | CloudWalk, dLocal |
| InHire | Playwright + networkidle | Magalu Cloud |
| SmartRecruiters | API REST pública | Visa, Serasa |
| Amazon Jobs | API JSON + filtro country=BRA | |
| BCG Careers | Playwright (Phenom People) | |
| Uber Careers | POST `/api/loadSearchJobsResults` | filtro BRA |
| DoorDash | Greenhouse API (doordashinternational) | |
| Amaris | MeiliSearch REST direto | chave pública no bundle JS |

---

## Licença

Projeto pessoal. Use, fork, adapte.
