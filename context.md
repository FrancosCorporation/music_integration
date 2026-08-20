# Music Integration – Social Automation Project

## Visão Geral
Sistema de automação de postagem de vídeos em múltiplas plataformas (YouTube, Instagram Reels, TikTok, Pinterest, X/Twitter, LinkedIn) gerenciado via dashboard Streamlit. Inclui autenticação assistida via Playwright, fila de publicação, logs e banco SQLite.

## Estrutura de Pastas
```
music_integration/
├─ .env.example
├─ requirements.txt
├─ venv/                     # virtualenv (não versionado)
├─ social_automation/
│   ├─ app.py                # Dashboard Streamlit
│   ├─ database.py           # SQLite init & helpers
│   ├─ sessions/             # cookies/tokens por plataforma
│   │   ├─ youtube/
│   │   ├─ instagram/
│   │   ├─ tiktok/
│   │   ├─ pinterest/
│   │   ├─ x_twitter/
│   │   └─ linkedin/
│   ├─ assets/               # vídeos temporários para upload
│   ├─ modules/
│   │   ├─ __init__.py
│   │   ├─ base.py           # Classe abstrata SocialPlatform
│   │   ├─ youtube.py        # API oficial Google (OAuth2)
│   │   ├─ instagram.py      # Playwright login + post Reels
│   │   ├─ tiktok.py         # Playwright login + post
│   │   ├─ pinterest.py      # stub API Pinterest
│   │   ├─ x_twitter.py      # stub API X (Twitter)
│   │   └─ linkedin.py       # stub API LinkedIn
│   └─ database.py
└─ context.md
```

## Stack Tecnológica
| Camada | Tecnologia |
|--------|------------|
| Linguagem | Python 3.12 |
| Dashboard | Streamlit 1.60 |
| Automação Web | Playwright 1.62 (Chromium) |
| YouTube API | google-auth-oauthlib + googleapiclient |
| Agendamento | APScheduler 3.11 |
| Banco | SQLite (arquivo `data.db`) |
| Configuração | python-dotenv |

## Banco de Dados (SQLite)
Tabelas criadas automaticamente via `database.init_db()`:
- **videos**: fila de publicação (id, file_path, title, description, tags, status, created_at, posted_at)
- **logs**: histórico de execuções (video_id, platform, status, message, created_at)
- **accounts**: status de conexão por plataforma (platform, connected, session_data, updated_at)

## Fases de Implementação (conforme Readme)

### Fase 1 – Core e Banco de Dados ✅
- `requirements.txt` com dependências
- `database.py` com `init_db()`, helpers `get_db`, `load_videos`, `load_logs`, `load_accounts`
- Banco SQLite criado em `social_automation/data.db`

### Fase 2 – Autenticação via Navegador (Playwright) ✅
- Classe base `SocialPlatform` com `login_interactive` que abre Chromium headful, aguarda login manual, salva cookies em `sessions/<platform>/session.json`
- Implementado para **Instagram** e **TikTok** (abre página de login, aguarda URL de sucesso, salva cookies)
- YouTube usa OAuth2 oficial (`google-auth-oauthlib`) com `client_secret.json` em `sessions/youtube/`

### Fase 3 – Módulos de Postagem por Plataforma (parcial)
| Plataforma | Status |
|------------|--------|
| YouTube | ✅ Upload via API oficial (OAuth2) |
| Instagram | ✅ Upload via Playwright (Reels) |
| TikTok | ✅ Upload via Playwright |
| Pinterest | ⚠️ Stub – OAuth pendente |
| X (Twitter) | ⚠️ Stub – OAuth 2.0 pendente |
| LinkedIn | ⚠️ Stub – OAuth pendente |

### Fase 4 – Dashboard Streamlit ✅
Arquivo `app.py` com 4 abas:
1. **Home** – métricas (total, postados, pendentes, erros) + status de conexões
2. **Logins** – botão Conectar/Desconectar por plataforma (abre navegador Playwright quando necessário)
3. **Queue** – upload de múltiplos vídeos, título/descrição/tags, seleção de plataformas, botão "Adicionar à fila" + botão "Publicar pendentes"
4. **Logs** – tabela dos últimos 200 registros da tabela `logs`

## Como Executar
```bash
cd ~/Git/music_integration
source venv/bin/activate
streamlit run social_automation/app.py
```
Acesse `http://localhost:8501`.

## Variáveis de Ambiente (`.env`)
Copie `.env.example` para `.env` e preencha:
```dotenv
FRONTEND_URL=https://francoscorporation.ddns.net
# Google OAuth
# GOOGLE_CLIENT_ID=
# GOOGLE_CLIENT_SECRET=
# Resend (opcional)
RESEND_API_KEY=
RESEND_FROM_EMAIL=onboarding@francoscorp.com
RESEND_FROM_NAME=Francos Corp
```

## Próximos Passos (Roadmap)
1. Implementar OAuth para Pinterest, X, LinkedIn.
2. Adicionar agendamento via APScheduler (publicar em horário).
3. Gerar legendas/hashtags com IA (OpenAI / local LLM).
4. Suporte a múltiplos arquivos simultâneos e retentativas com backoff.
5. Testes automatizados (pytest) e CI/CD.

## Comandos Úteis
```bash
# Recriar banco
python -m social_automation.database

# Instalar navegadores Playwright
playwright install chromium

# Atualizar dependências
pip install -r requirements.txt --upgrade
```

---
*Documento gerado automaticamente – última atualização 2025-08-02.*
