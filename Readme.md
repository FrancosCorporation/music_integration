# Music Integration (Streamlit)

## 🐳 Instalação e Execução (Docker) — recomendado

### Pré-requisitos
- [Docker](https://docs.docker.com/get-docker/) + Docker Compose

### Rodar com Docker
```bash
docker compose up --build
```
Já possui Dockerfile com Playwright. `docker build -t music-int . && docker run -p 8501:8501 music-int`

### Sem Docker (local)
```bash
pip install -r requirements.txt
streamlit run app.py
```

2. A Arquitetura do Novo Projeto em Python
Para atender aos seus requisitos de ter uma dashboard simples para monitoramento e gerenciar logins diretamente pelo navegador, podemos estruturar o projeto com as seguintes tecnologias:

Backend / Orquestrador: Python + FastAPI. É moderno, incrivelmente rápido e perfeito para lidar com as chamadas das APIs e agendar as postagens.

Dashboard de Monitoramento: Streamlit. É uma biblioteca Python fantástica que cria interfaces web bonitas e funcionais em minutos, sem precisar escrever HTML ou JavaScript. Você poderá abrir o painel para ver o status dos agentes, relatórios de postagens e gerenciar contas.

Autenticação e "Login no Navegador": Playwright (com Python). Para redes sociais que dificultam o uso de APIs puras (como o Instagram e o TikTok em alguns cenários), o Playwright permite que o sistema abra um navegador real, deixe você fazer o login manualmente na primeira vez, e então salve os cookies de sessão para que o robô faça as postagens automaticamente nas próximas vezes.

3. Plano de Ação Completo
Vamos dividir o desenvolvimento em 4 fases claras para garantir que tudo funcione perfeitamente.

Fase 1: Configuração da Base e Dashboard

Criar o ambiente virtual Python.

Levantar a interface básica com o Streamlit.

Criar a estrutura do banco de dados (pode ser SQLite para facilitar ou PostgreSQL) para salvar o status dos vídeos (pendente, postado, erro).

Fase 2: Módulo de Autenticação (O Login no Navegador)

Integrar o Playwright para gerenciar sessões.

Criar na dashboard um botão "Conectar Conta", que abre uma janela de navegador limpa para você colocar login e senha.

Salvar o estado do navegador (cookies/tokens) localmente de forma segura.

Fase 3: Integração das Redes Sociais

YouTube: Usaremos a API oficial do Google (OAuth2). É a forma mais estável.

Instagram & TikTok: Usaremos o método de sessão do Playwright para emular as postagens web ou bibliotecas não-oficiais robustas, já que as APIs oficiais para postagem direta de vídeo às vezes têm restrições chatas para contas não-comerciais.

Sugestões Extras: Recomendo adicionarmos Pinterest (excelente tráfego orgânico para vídeos curtos/ideias) e X (Twitter), que tem uma API bem documentada e aceita bem o reaproveitamento de vídeos curtos.

Fase 4: Agentes e Automação (O "Trabalho" nos Bastidores)

Criar os scripts Python que pegam o vídeo gerado, preparam o título, as hashtags (usando IA para gerar a copy) e enviam para as plataformas configuradas.

Ligar tudo à dashboard para você ver barras de progresso ou logs em tempo real ("Vídeo X postado com sucesso no TikTok").


Aqui está o planejamento completo e estruturado para você entregar diretamente para a IA começar a construir o ecossistema em Python. O projeto será focado em automação total, gestão via dashboard em Streamlit e sistema de login persistente via navegador (Playwright) e APIs oficiais.

Planejamento Completo: Sistema de Automação de Mídias Sociais em Python
1. Escopo das Plataformas de Destino
Para garantir o máximo de alcance, o sistema fará a distribuição automatizada para todas as principais plataformas de vídeos curtos e longos:

YouTube (Shorts e Vídeos Longos via API oficial do Google OAuth2)

Instagram (Reels via Automação de Sessão/Playwright e API Graph onde aplicável)

TikTok (Vídeos via Playwright/Sessão e API de Upload)

Pinterest (Idea Pins / Vídeos para tráfego orgânico)

X (Twitter) (Postagem de vídeos curtos)

LinkedIn (Vídeos corporativos/profissionais)

2. Stack Tecnológica
Linguagem: Python 3.10+

Interface / Dashboard: Streamlit (para visualização de status, logs, métricas e botões de controle)

Automação Web / Logins: Playwright (para simular interações de navegador reais, capturar e salvar cookies de sessão de plataformas que dificultam login via API)

APIs Oficiais: Google Client Library (YouTube), Requests / SDKs específicos para as demais.

Banco de Dados Local: SQLite (para gerenciar a fila de vídeos, status de postagem e credenciais/tokens criptografados)

Gerenciador de Tarefas: Background threads ou APScheduler (para rodar os agendamentos em segundo plano)

3. Arquitetura de Pastas Sugerida
Plaintext
social_automation/
│
├── app.py                # Dashboard principal (Streamlit)
├── database.py           # Configuração do SQLite e modelos de dados
├── requirements.txt      # Dependências do projeto
├── sessions/             # Armazenamento seguro de cookies/sessões do Playwright
├── modules/
│   ├── __init__.py
│   ├── youtube.py        # Integração YouTube
│   ├── instagram.py      # Automação Instagram (Playwright)
│   ├── tiktok.py         # Automação TikTok (Playwright)
│   ├── pinterest.py      # Automação Pinterest
│   ├── x_twitter.py      # Automação X
│   └── linkedin.py       # Automação LinkedIn
└── assets/               # Vídeos e mídias temporárias
4. Fases de Execução para a IA Desenvolver
Fase 1: Core e Banco de Dados (database.py e requirements.txt)
Definir as dependências no requirements.txt: streamlit, playwright, google-auth-oauthlib, requests, apscheduler.

Criar o banco SQLite com tabelas para:

videos: Caminho do arquivo, título, descrição, tags, status (Pendente, Postado, Erro).

logs: Histórico de execuções e erros por plataforma.

accounts: Status de conexão de cada rede social.

Fase 2: O Sistema de Login no Navegador (modules/ e Playwright)
Criar um script base usando Playwright com persistent_context para que, ao clicar em "Conectar Conta" na dashboard, o navegador abra na página de login da rede social (ex: TikTok ou Instagram).

Você faz o login manualmente uma única vez na janela que se abrir.

O sistema salva os cookies e dados de sessão na pasta sessions/. Nas execuções seguintes, o robô reutiliza essa sessão logada sem precisar de senha novamente.

Para o YouTube, implementar o fluxo padrão de arquivo client_secret.json via OAuth2.

Fase 3: Módulos de Postagem por Plataforma
Desenvolvimento individual dos scripts de envio para cada rede escolhida:

YouTube: Upload automatizado via API oficial com tratamento de metadados.

Instagram & TikTok: Robô em Playwright que navega até a página de criação/upload, preenche a legenda, carrega o arquivo de vídeo e clica em publicar.

Pinterest, X e LinkedIn: Integrações via APIs dedicadas ou automação web de suporte.

Fase 4: A Dashboard de Monitoramento (app.py)
Construção da interface em Streamlit contendo:

Página Inicial (Status Geral): Gráficos rápidos do volume de vídeos postados vs. falhas, e o status de conexão de cada uma das contas (Conectado / Desconectado).

Painel de Logins: Botões interativos para disparar a janela de login assistido de cada plataforma caso alguma sessão expire.

Fila de Publicação: Upload manual ou automático de um novo vídeo, seleção de quais redes vão receber o conteúdo, e botão de "Publicar Agora" ou "Agendar".

Logs em Tempo Real: Uma aba mostrando o terminal visual das ações que os robôs estão tomando nos bastidores.