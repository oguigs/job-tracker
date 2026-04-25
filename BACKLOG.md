# Job Tracker — Backlog Completo

> Última atualização: Abril 2026 · Total: 158 itens

---

## Bloco 1 — Estabilidade ✅ Concluído

- [x] Cooldown por empresa (12h entre execuções)
- [x] Timeout por empresa (5 minutos)
- [x] Backup automático do banco (7 últimos)
- [x] Testar pipeline com 10+ empresas

---

## Bloco 2 — Visual do Dashboard ⚡ Em andamento

- [x] Migrar gráficos para Plotly
- [x] Logo via favicon — salvo localmente
- [x] Página de perfil por empresa
- [x] Logos das stacks com link para roadmap.sh
- [x] Redesign do expander de vaga com badges coloridos

---

## Bloco 3 — Favicon (Débito Técnico)

- [ ] Upload manual de logo na página de empresas
- [ ] Extrair favicon via Playwright para sites que bloqueiam requests
- [ ] Fallback em cascata: local → Google → Clearbit → iniciais coloridas da empresa

---

## Bloco 4 — Melhorias Visuais nas Vagas

- [ ] Badge de urgência — detectar "início imediato", "urgente" na descrição
- [ ] Barra de progresso do score de fit por vaga
- [ ] Indicador de tempo desde a coleta — "coletada há 3 dias"
- [ ] Tag visual de origem — ícone para vagas manuais vs coletadas
- [ ] Ícones em cada fase da timeline de candidatura
- [ ] Data de entrada em cada fase da timeline
- [ ] Modo compacto vs modo detalhado na listagem
- [ ] Destaque visual para vagas novas (últimas 24h)
- [ ] Ordenação por score de fit, data, empresa ou status
- [ ] Agrupamento por empresa ou por fase de candidatura

---

## Bloco 5 — Novas Funcionalidades

### Cadastro manual de vagas
- [ ] Formulário de cadastro de vaga manual
- [ ] Busca de empresa existente no formulário
- [ ] Modal de cadastro rápido de empresa se não existir
- [ ] Campo de descrição livre para colar o texto da vaga
- [ ] **Extração automática de stacks da descrição colada via `stack_extractor`**
- [ ] **Detecção automática de nível (junior/pleno/sênior/especialista) do texto colado**
- [ ] **Detecção automática de modalidade (remoto/híbrido/presencial) do texto colado**
- [ ] **Preview das stacks extraídas antes de salvar — permitir edição manual**
- [ ] **Identificar escopo da vaga — responsabilidades, requisitos obrigatórios vs desejáveis**
- [ ] **Usar Claude API para análise semântica profunda da descrição — sinônimos, contexto e senioridade implícita**
- [ ] Campo de origem (headhunter/indicação/LinkedIn/site próprio)
- [ ] Campo de contato livre (ex: "João da XP me indicou")
- [ ] Testar fluxo completo

### Base de indicadores
- [ ] Criar tabela `dim_contato` no banco
- [ ] Formulário de cadastro de contato (nome, email, empresa, grau de intimidade)
- [ ] Listar contatos por empresa na página de perfil
- [ ] Exibir contatos ao visualizar vaga
- [ ] Destacar email corporativo para indicação

---

## Bloco 6 — Inteligência Acionável

### Score de fit
- [ ] Criar tabela `dim_perfil_usuario` com stacks e nível
- [ ] Formulário de cadastro de stacks do usuário
- [ ] Algoritmo de cálculo de match (interseção de stacks)
- [ ] Badge de percentual de match em cada vaga
- [ ] Ordenar vagas por score de fit

### Diário de candidatura
- [ ] Criar tabela `log_candidatura` com notas por data
- [ ] Campo de nova nota dentro de cada vaga
- [ ] Histórico cronológico de notas por vaga

### Preparação para entrevista
- [ ] Exibir stacks mais pedidas pela empresa ao avançar para entrevista
- [ ] Exibir nível médio das vagas da empresa
- [ ] Exibir contatos cadastrados na empresa
- [ ] Checklist de preparação por tecnologia

### Análise temporal de stacks
- [ ] Criar tabela `snapshot_mercado` com dados semanais
- [ ] Job semanal que salva snapshot do estado atual
- [ ] Gráfico de tendência de cada stack ao longo do tempo
- [ ] Destacar stacks em crescimento vs declínio

### Radar de salário
- [ ] Extrair faixa salarial da descrição com regex
- [ ] Salvar `salario_min` e `salario_max` na `fact_vaga`
- [ ] Gráfico de distribuição salarial por nível e empresa

### Comparativo entre empresas
- [ ] Seletor de duas empresas para comparar
- [ ] Side by side de stacks, nível médio, modalidade
- [ ] Tempo médio que vagas ficam abertas por empresa

### Exportar checklist de candidatura
- [ ] Gerar PDF com stacks da vaga vs seu perfil
- [ ] Destacar gaps — o que estudar antes da entrevista
- [ ] Exportar histórico da candidatura

### Alertas
- [ ] Detectar "início imediato", "urgente", "processo rápido"
- [ ] Destacar vagas urgentes no topo da lista
- [ ] Notificação quando nova vaga relevante aparecer

### Histórico de mercado
- [ ] Snapshots semanais automáticos
- [ ] Dashboard de evolução do mercado ao longo do tempo
- [ ] Comparativo mês a mês de vagas por empresa

---

## Bloco 7 — Gestão de Candidatura Avançada

- [ ] SLA de resposta — alertar quando empresa não respondeu em X dias
- [ ] Mapa de calor de candidaturas — em qual fase você mais trava
- [ ] Taxa de conversão por empresa — candidaturas que viraram entrevista
- [ ] Comparativo do seu perfil com o mercado
- [ ] Detector de empresas em crescimento — mais vagas que o mês anterior
- [ ] Índice de senioridade do mercado — proporção sênior/pleno/júnior
- [ ] Sazonalidade de contratações — quando as empresas mais contratam
- [ ] Cronômetro de processo seletivo — há quantos dias em cada fase
- [ ] Gerador de carta de apresentação personalizada por vaga via IA

---

## Bloco 8 — Robô de Candidatura Automática

- [ ] Mapear campos do formulário Gupy (nome, email, telefone, LinkedIn, currículo)
- [ ] Criar perfil do usuário com dados pessoais para preenchimento
- [ ] Implementar preenchimento automático com Playwright
- [ ] Implementar pausa antes de submeter — revisão humana obrigatória
- [ ] Log de cada candidatura automatizada
- [ ] Tratar upload de currículo no formulário
- [ ] Tratar perguntas customizadas das empresas
- [ ] Detectar e tratar captcha

---

## Bloco 9 — Engenharia de Dados — Curto Prazo

### Camadas Bronze/Silver/Gold
- [ ] Criar schema `bronze` — dados brutos do scraper
- [ ] Criar schema `silver` — dados normalizados e deduplicados
- [ ] Criar schema `gold` — dados analíticos consumidos pelo dashboard
- [ ] Migrar pipeline para gravar em Bronze primeiro
- [ ] Criar transformações Bronze → Silver → Gold

### dbt
- [ ] Instalar e configurar dbt com DuckDB
- [ ] Criar modelo `stg_vagas` (staging)
- [ ] Criar modelo `dim_empresa` (dimensão)
- [ ] Criar modelo `fact_vaga` (fato)
- [ ] Criar testes de qualidade nos modelos
- [ ] Gerar documentação automática

### Great Expectations ou Soda
- [ ] Instalar e configurar
- [ ] Criar expectativa: título nunca nulo
- [ ] Criar expectativa: modalidade dentro de valores esperados
- [ ] Criar expectativa: hash único
- [ ] Integrar validação no pipeline

### Outros
- [ ] Data lineage — documentar origem e transformações de cada campo
- [ ] Schema versioning — controle de mudanças sem quebrar o pipeline

---

## Bloco 10 — Engenharia de Dados — Médio Prazo

### Docker
- [ ] Criar `Dockerfile` para o dashboard
- [ ] Criar `Dockerfile` para o pipeline
- [ ] Criar `docker-compose.yml` subindo tudo com um comando
- [ ] Testar em ambiente limpo

### Prefect
- [ ] Instalar e configurar Prefect
- [ ] Criar DAG do pipeline de coleta
- [ ] Configurar retry automático em caso de falha
- [ ] Configurar alertas de falha por email
- [ ] Migrar agendamento para Prefect

### GitHub Actions
- [ ] Criar workflow de CI — rodar testes a cada push
- [ ] Criar workflow de CD — pipeline diário na nuvem
- [ ] Criar workflow de backup — salvar banco no GitHub

### Outros
- [ ] Monitoramento — alertas, métricas de saúde, observabilidade
- [ ] Data catalog — documentação de datasets e linhagem visual

---

## Bloco 11 — Expansão da Ingestão

- [ ] Scraper para Inhire
- [ ] Scraper para Lever — Nubank, iFood, Rappi
- [ ] Scraper para Greenhouse — empresas internacionais
- [ ] Sites próprios — Itaú, XP, Globo
- [ ] Connector para API do LinkedIn Jobs

---

## Bloco 12 — Engenharia de Dados — Longo Prazo

- [ ] Apache Spark — reprocessar dados históricos com PySpark
- [ ] Apache Kafka — ingestão em streaming com múltiplas fontes
- [ ] Delta Lake ou Apache Iceberg — versionamento e time travel
- [ ] Apache Airflow — DAGs complexos quando escala justificar
- [ ] Cloud storage — S3 ou GCS + Parquet
- [ ] dbt Cloud — scheduler e documentação publicada

---

## Bloco 13 — Encerramento v1.0

- [ ] README atualizado com diário do dia 3
- [ ] Tag v1.0 no GitHub

---

## Bloco 14 — Perfil do Candidato

- [ ] Criar página "Meu Perfil" no dashboard
- [ ] Criar tabela `dim_candidato` no banco
- [ ] Formulário de dados pessoais (nome, email, LinkedIn, cidade, nível, modalidade, pretensão salarial)
- [ ] Formulário de stacks com nível por tecnologia (básico/intermediário/avançado/especialista)
- [ ] Upload de PDF do currículo ou exportação do LinkedIn
- [ ] Extração automática de stacks do PDF com `pdfplumber`
- [ ] Salvar stacks extraídas no perfil para edição manual
- [ ] Exibir perfil resumido na sidebar do dashboard

---

## Bloco 15 — Score de Fit e ATS

- [ ] Algoritmo de match de stacks — perfil do candidato vs vaga
- [ ] Badge de percentual de match em cada vaga
- [ ] Ordenar vagas por score de fit

### Score ATS
- [ ] Análise de match de keywords — currículo vs descrição da vaga
- [ ] Análise de densidade de termos técnicos no currículo
- [ ] Análise de formato ATS-friendly do PDF
- [ ] Verificar seções obrigatórias no currículo (experiência, educação, skills, resumo)
- [ ] Score final 0-100 com breakdown por categoria
- [ ] Sugestões específicas do que adicionar no currículo para cada vaga
- [ ] Claude API para análise semântica — sinônimos e termos relacionados
- [ ] Relatório exportável de otimização do currículo por vaga

---

## v2 — Infraestrutura Cloud

- [ ] Deploy do dashboard no Streamlit Cloud
- [ ] Migrar storage para Google Drive ou S3 free tier
- [ ] Notificação de novas vagas por email
- [ ] Exportar relatório PDF para direcionar currículo
- [ ] Integração com LinkedIn — conexões de primeiro grau na empresa

---

## v3 — Raspberry Pi

- [ ] Configurar pipeline rodando automaticamente no Raspberry Pi
- [ ] Hospedar dashboard Streamlit no Pi 24/7
- [ ] Acesso remoto via Tailscale ou Cloudflare Tunnel
- [ ] Testar compatibilidade do Playwright com arquitetura ARM

---

## Resumo

| Bloco | Tema | Itens | Status |
|---|---|---|---|
| 1 | Estabilidade | 4 | ✅ Concluído |
| 2 | Visual do Dashboard | 5 | ⚡ Em andamento |
| 3 | Favicon (Débito) | 3 | ○ Pendente |
| 4 | Melhorias Visuais | 10 | ○ Pendente |
| 5 | Novas Funcionalidades | 18 | ○ Pendente |
| 6 | Inteligência Acionável | 23 | ○ Pendente |
| 7 | Candidatura Avançada | 9 | ○ Pendente |
| 8 | Robô de Candidatura | 8 | ○ v2 |
| 9 | DE Curto Prazo | 14 | ○ Pendente |
| 10 | DE Médio Prazo | 13 | ○ Pendente |
| 11 | Expansão Ingestão | 5 | ○ Pendente |
| 12 | DE Longo Prazo | 6 | ○ v2/v3 |
| 13 | Encerramento v1.0 | 2 | ○ Pendente |
| 14 | Perfil do Candidato | 8 | ○ Pendente |
| 15 | Score de Fit e ATS | 12 | ○ Pendente |
| v2 | Infraestrutura Cloud | 5 | ○ Futuro |
| v3 | Raspberry Pi | 4 | ○ Futuro |
| 16 | Anti-detecção Scraper | 10 | ○ Pendente |
| **Total** | | **158** | |

---

## Bloco 16 — Anti-detecção e Resiliência do Scraper
> ⚠️ Todas as soluções deste bloco são 100% gratuitas e open source.

- [ ] Delays humanizados aleatórios entre requisições (2-5 segundos)
- [ ] User-Agent e headers HTTP realistas no Playwright
- [ ] Integrar `playwright-stealth` — remove fingerprints de bot (pip install, zero custo)
- [ ] Rotação de viewport e resolução por execução
- [ ] Rotação de locale e timezone (pt-BR, America/Sao_Paulo)
- [ ] Detecção de bloqueio — identificar status 403/429/Cloudflare na resposta
- [ ] Tratamento diferenciado para empresa bloqueada — cooldown automático de 48h
- [ ] Log de status `bloqueado` separado de `erro` no log_coleta
- [ ] Modo de coleta espaçada — distribuir empresas ao longo do dia via agendamento
- [ ] Monitorar se plataformas como Gupy expõem API oficial gratuita

> 🚫 Fora do escopo por custo: proxy residencial, APIs pagas de terceiros.
