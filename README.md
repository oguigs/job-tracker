# Job Tracker — Data Engineering Intelligence

> v1.0 · Pipeline de inteligência de mercado para profissionais de dados.

---

## Sobre o projeto

> ⚠️ **Princípio de custo zero:** todas as tecnologias são gratuitas e open source. Projeto para uso pessoal exclusivo.

O Job Tracker coleta vagas automaticamente de portais como o Gupy, extrai stacks tecnológicas, calcula score de fit com o perfil do candidato, detecta vagas urgentes e oferece inteligência acionável para a busca de emprego — tudo em um dashboard Streamlit local.

---

## Diário de desenvolvimento

### Dia 1 — Fundação
Setup, Playwright, extração de stacks, DuckDB, dashboard inicial.

### Dia 2 — Expansão
Paginação automática, gestão de empresas, timeline de candidatura, filtros de coleta, pipeline Rich.

### Dia 3 — Estabilidade e Visual
Cooldown/timeout, backup automático, Plotly, favicons, badges de stacks coloridos com links roadmap.sh.

### Dia 4 — Inteligência e v1.0
Refatoração completa em módulos, score de fit com breakdown, perfil do candidato, diário de candidatura, preparação para entrevista, base de indicadores, cadastro manual de vagas, alerta de urgência, remuneração CLT/PJ/Exterior, comparativo entre empresas, análise temporal de stacks, snapshot automático.

---

## Arquitetura

```
INGESTÃO: Playwright (Gupy) + DuckDuckGo + Cadastro manual
    ↓
FILTROS: Palavras de interesse e bloqueio
    ↓
TRANSFORMAÇÃO: stack_extractor — stacks, nível, modalidade, urgência
    ↓
STORAGE: DuckDB local
    ↓
CONSUMO: Dashboard Streamlit — 11 páginas
```

---

## Stack

| Tecnologia | Uso |
|---|---|
| Python 3.14 | Linguagem principal |
| Playwright | Scraping dinâmico (Next.js/SPA) |
| DuckDB | Storage analítico local |
| Streamlit | Dashboard web |
| Plotly | Gráficos interativos |
| Pandas | Transformação de dados |
| Rich | Pipeline visual no terminal |
| DuckDuckGo | Busca automática de empresas |

---

## Estrutura de pastas

```
job-tracker/
├── scrapers/           # Playwright, DuckDuckGo
├── transformers/       # stack_extractor
├── database/
│   ├── connection.py
│   ├── schemas.py      # tabelas, backup, TIMELINE
│   ├── empresas.py
│   ├── vagas.py
│   ├── candidaturas.py
│   ├── candidato.py
│   ├── contatos.py
│   ├── filtros.py
│   ├── logs.py
│   ├── score.py
│   ├── diario.py
│   └── snapshots.py
├── dashboard/
│   ├── app.py          # roteamento (30 linhas)
│   ├── components.py   # funções reutilizáveis
│   ├── stack_config.py # ícones e links
│   ├── static/favicons/
│   └── views/          # 11 páginas independentes
├── data/curated/       # jobs.duckdb + backups
├── main.py
└── start.sh
```

---

## Instalação

```bash
git clone https://github.com/oguigs/job-tracker.git
cd job-tracker
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
```

### Alias de terminal
```bash
echo "alias jobtracker='cd ~/job-tracker && ./start.sh'" >> ~/.zshrc
source ~/.zshrc
```

---

## Como usar

```bash
jobtracker  # ativa venv e abre o dashboard
```

1. **Empresas** → cadastrar com site oficial para favicon automático
2. **Configurações** → palavras de interesse e bloqueio
3. **Meu Perfil** → cadastrar suas stacks para score de fit
4. **Pipeline** → rodar coleta em background
5. **Vagas** → ver score, breakdown, diário e preparação
6. **Indicadores** → cadastrar contatos por empresa
7. **Cadastrar Vaga** → vagas de indicação ou headhunter
8. **Comparativo** → comparar duas empresas lado a lado
9. **Tendências** → evolução de stacks ao longo do tempo

---

## Dashboard — 11 páginas

| Página | Descrição |
|---|---|
| Dashboard | Gráficos Plotly de stacks, nível e modalidade |
| Vagas | Lista ordenada por score com filtros avançados |
| Comparativo | Side by side de duas empresas |
| Tendências | Evolução temporal de stacks |
| Cadastrar Vaga | Manual com extração automática de stacks |
| Empresas | Cadastro com favicon, polos e edição |
| Indicadores | Contatos por empresa com grau de intimidade |
| Pipeline | Disparo com log em tempo real |
| Configurações | Filtros de coleta |
| Meu Perfil | Dados pessoais e stacks do candidato |
| Vagas Negadas | Vagas descartadas com reativação |

---

## Funcionalidades de inteligência

- **Score de fit** — match entre suas stacks e as da vaga com breakdown detalhado
- **Diário** — notas por data dentro de cada vaga
- **Preparação** — gaps e contatos ao avançar para entrevista
- **Alerta urgente** — badge 🔥 para vagas com início imediato
- **Remuneração** — regime, moeda, salário, VR/VA/VT, benefícios
- **Comparativo** — stacks, nível e modalidade de duas empresas
- **Tendências** — snapshots semanais com evolução das stacks

---

## Modelo de dados

| Tabela | Descrição |
|---|---|
| `dim_empresa` | Empresas com favicon, URLs, status |
| `fact_vaga` | Vagas com stacks, score, urgência, remuneração |
| `dim_candidato` | Perfil do candidato |
| `dim_candidato_stack` | Stacks com nível e experiência |
| `dim_contato` | Indicadores por empresa |
| `dim_empresa_endereco` | Polos por empresa |
| `log_candidatura` | Diário de notas |
| `config_filtros` | Palavras de interesse e bloqueio |
| `log_coleta` | Histórico de execuções |
| `snapshot_mercado` | Snapshots semanais de stacks |

---

## Backlog

O backlog completo está em [BACKLOG.md](BACKLOG.md).

**Próximos itens (v1.1):**
- Expandir `stack_extractor` com mais tecnologias
- Score ATS do currículo
- Bloco 9 — Bronze/Silver/Gold + dbt

---

## Licença

Projeto pessoal para estudo e uso próprio.
