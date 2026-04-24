# Job Tracker — Data Engineering

> Pipeline de coleta, processamento e análise de vagas de Data Engineering com dashboard interativo.

---

## Sobre o projeto

Sistema de inteligência de mercado para profissionais de dados. Coleta automaticamente vagas de empresas monitoradas, extrai as stacks exigidas, detecta vagas novas e encerradas, e exibe tudo em um dashboard para direcionar estudos e candidaturas.

---

## Arquitetura

```
job-tracker/
├── scrapers/
│   ├── gupy_scraper.py       # Coleta vagas de qualquer empresa no Gupy
│   ├── gupy_detalhes.py      # Coleta descrição completa de cada vaga
│   └── company_search.py     # Busca automática de dados da empresa (DuckDuckGo)
├── transformers/
│   └── stack_extractor.py    # Extração de stacks, nível e modalidade
├── database/
│   └── db_manager.py         # Gerenciamento do DuckDB (CRUD + deduplicação)
├── dashboard/
│   └── app.py                # Dashboard Streamlit
├── data/
│   ├── raw/                  # JSONs brutos coletados
│   └── curated/              # Banco DuckDB processado
├── main.py                   # Orquestrador do pipeline completo
├── .env                      # Variáveis de ambiente (não versionado)
├── .gitignore
└── requirements.txt
```

### Fluxo do pipeline

```
Empresas no banco
      │
      ▼
Gupy Scraper (Playwright)
      │  coleta título, link, modalidade
      ▼
Gupy Detalhes (Playwright)
      │  coleta descrição completa de cada vaga
      ▼
Stack Extractor
      │  extrai stacks, nível, modalidade
      ▼
DuckDB
      │  deduplicação por hash, detecta vagas encerradas
      ▼
Dashboard Streamlit
```

---

## Modelo de dados

### `dim_empresa`
Cadastro das empresas monitoradas.

| Campo | Tipo | Descrição |
|---|---|---|
| id | INTEGER | Chave primária |
| nome | VARCHAR | Nome da empresa |
| ramo | VARCHAR | Setor de atuação |
| cidade | VARCHAR | Cidade principal |
| estado | VARCHAR | Estado |
| url_gupy | VARCHAR | URL do portal Gupy |
| url_linkedin | VARCHAR | URL do LinkedIn |
| url_site_vagas | VARCHAR | URL do site de vagas |
| ativa | BOOLEAN | Monitoramento ativo |
| data_cadastro | DATE | Data do cadastro |

### `dim_empresa_endereco`
Polos e escritórios por empresa (1 empresa → N endereços).

| Campo | Tipo | Descrição |
|---|---|---|
| id | INTEGER | Chave primária |
| id_empresa | INTEGER | FK para dim_empresa |
| cidade | VARCHAR | Cidade do polo |
| bairro | VARCHAR | Bairro do polo |

### `fact_vaga`
Vagas coletadas com stacks extraídas.

| Campo | Tipo | Descrição |
|---|---|---|
| id | INTEGER | Chave primária |
| hash | VARCHAR | Hash único (título + empresa + link) |
| titulo | VARCHAR | Título da vaga |
| nivel | VARCHAR | junior / pleno / senior / especialista |
| modalidade | VARCHAR | remoto / hibrido / presencial |
| stacks | JSON | Stacks por categoria |
| link | VARCHAR | URL da vaga |
| fonte | VARCHAR | Portal de origem |
| id_empresa | INTEGER | FK para dim_empresa |
| data_coleta | DATE | Data da coleta |
| ativa | BOOLEAN | Vaga ainda no ar |
| data_encerramento | DATE | Data que saiu do site |

### `log_coleta`
Histórico de execuções do pipeline.

| Campo | Tipo | Descrição |
|---|---|---|
| id | INTEGER | Chave primária |
| data_execucao | TIMESTAMP | Data e hora da execução |
| empresa | VARCHAR | Empresa processada |
| vagas_encontradas | INTEGER | Total de vagas no site |
| vagas_novas | INTEGER | Vagas inseridas pela primeira vez |
| status | VARCHAR | sucesso / erro |
| erro | VARCHAR | Mensagem de erro se houver |

---

## Stack do projeto

| Camada | Ferramenta | Por quê |
|---|---|---|
| Scraping dinâmico | Playwright | Sites Next.js e React |
| Scraping estático | requests + BeautifulSoup4 | Sites HTML simples |
| Busca de empresas | DuckDuckGo Search (ddgs) | Gratuito, sem chave de API |
| NLP / extração | Regex + dicionário de stacks | Leve e customizável |
| Storage | DuckDB + Parquet | OLAP local, zero infraestrutura |
| Transformação | Pandas | Limpeza e normalização |
| Dashboard | Streamlit | Zero frontend, deploy simples |
| Orquestração | schedule / launchd | Execução diária automática |

---

## Instalação

### Pré-requisitos
- Python 3.11+
- Git

### Setup

```bash
# clone o repositório
git clone https://github.com/oguigs/job-tracker.git
cd job-tracker

# crie e ative o ambiente virtual
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# instale as dependências
pip install -r requirements.txt

# instale o navegador do Playwright
python -m playwright install chromium

# configure as variáveis de ambiente
cp .env.example .env
# edite o .env com suas credenciais
```

### Variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

```
GOOGLE_API_KEY=sua_chave_aqui
GOOGLE_SEARCH_ENGINE_ID=seu_id_aqui
```

---

## Como usar

### Rodar o pipeline manualmente

```bash
python main.py
```

### Cadastrar empresas

```bash
streamlit run dashboard/app.py
```

Acesse `http://localhost:8501`, vá em "Empresas" e cadastre as empresas que deseja monitorar com a URL do Gupy.

### Estrutura da URL Gupy

Toda empresa que usa o Gupy segue o padrão:
```
https://nomeempresa.gupy.io/
```

Exemplos:
```
https://compass.gupy.io/
https://dock.gupy.io/
https://picpay.gupy.io/
```

---

## Funcionalidades

- Scraper genérico para qualquer empresa no Gupy
- Filtro automático de cargos relevantes (Data Engineer, Analytics Engineer, Data Analyst, etc.)
- Extração de stacks por categoria: linguagens, cloud, orquestração, processamento, armazenamento, infraestrutura
- Detecção automática de nível (junior, pleno, senior, especialista)
- Detecção de modalidade (remoto, híbrido, presencial)
- Deduplicação por hash — sem duplicatas mesmo rodando todo dia
- Detecção de vagas encerradas com data de encerramento registrada
- Log completo de cada execução do pipeline
- Dashboard com filtros, gráficos de stacks e lista de vagas
- Cadastro de empresas com busca automática de informações
- Suporte a múltiplos polos/escritórios por empresa
- Edição de empresas já cadastradas
- Pausar/reativar monitoramento por empresa

---

## Dashboard

O dashboard tem duas páginas:

**Dashboard** — visão analítica das vagas coletadas com filtros por empresa, nível, modalidade e status. Gráficos de stacks mais exigidas por categoria e lista detalhada de vagas com links diretos.

**Empresas** — cadastro e gestão de empresas monitoradas. Busca automática de informações como LinkedIn, site de vagas e cidade. Suporte a múltiplos polos por empresa.

---

## Roadmap

- [ ] Agendamento automático diário via launchd (Mac)
- [ ] Scraper para Inhire
- [ ] Scraper para Lever
- [ ] Scraper para sites próprios de empresas
- [ ] Página de análise comparativa de stacks entre empresas
- [ ] Gráfico de tempo médio que uma vaga fica aberta
- [ ] Export de relatório PDF para direcionar currículo
- [ ] Notificação por email quando vaga relevante aparecer

---

## Licença

Projeto pessoal para estudo e uso próprio.
