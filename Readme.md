# Music Integration

Painel privado em Streamlit para organizar vídeos e publicá-los manualmente no YouTube pela API oficial do Google. Instagram, TikTok, Pinterest, X e LinkedIn aparecem como integrações futuras e não recebem arquivos nem tentativas de login.

## Requisitos

- Python 3.12 ou Docker com Docker Compose.
- Um OAuth Client ID do tipo **aplicativo para computador** no Google Cloud, com a YouTube Data API v3 habilitada.
- Uma senha administrativa aleatória com pelo menos 16 caracteres.

## Execução local

```bash
cp .env.example .env
# Edite .env e defina DASHBOARD_PASSWORD com uma senha longa e exclusiva.
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
mkdir -p data sessions/youtube
chmod 700 data sessions sessions/youtube
streamlit run social_automation/app.py --server.address=127.0.0.1
```

Abra `http://127.0.0.1:8501` e entre com `DASHBOARD_PASSWORD`.

## Conectar a conta Google

1. Baixe o arquivo OAuth do Google Cloud e salve-o como `sessions/youtube/client_secret.json`.
2. Com o ambiente virtual ativo, execute `python -m social_automation.youtube_auth` no computador que tem um navegador.
3. Autorize a conta no Google. O token será salvo em `sessions/youtube/token.json` com acesso restrito ao usuário local.
4. Inicie ou atualize o painel. A credencial é renovada quando necessário.

O arquivo de cliente OAuth e o token são segredos locais. Não os envie ao Git ou a terceiros.

## Execução com Docker Compose

```bash
cp .env.example .env
# Edite .env: configure uma senha longa e PUID/PGID com os IDs do seu usuário.
mkdir -p data sessions/youtube
chmod 700 data sessions sessions/youtube
docker compose up --build -d
```

O painel fica disponível somente em `127.0.0.1:8501`. Os dados persistem em `data/` e `sessions/`. Para conectar pelo OAuth, execute o comando de autenticação no host e mantenha o diretório `sessions/` montado. Para parar: `docker compose down`.

## Uso e limites atuais

- Adicione vídeos MP4, MOV ou MKV. Cada arquivo pode ter até 200 MB, com limite combinado de 200 MB por envio. Cada item recebe um nome aleatório no armazenamento privado local.
- Informe o título ou deixe em branco para usar o nome do arquivo. Descrição e tags são opcionais.
- A fila nunca publica sozinha. Clique em **Publicar vídeos pendentes** para enviar.
- A privacidade padrão é **Privado**. Para vídeos públicos, selecione **Público** e confirme a publicação aberta.
- O estado e o identificador retornado pela API ficam registrados por vídeo. Falhas podem ser recolocadas manualmente na fila.
- Vídeos anteriores à fila por plataforma não são publicados automaticamente.
- Cada execução envia até 100 destinos pendentes. A API e as cotas do Google podem limitar uploads.
- Não há agendamento, postagem automática, nem integração habilitada para outras redes.

## Armazenamento e configuração

- `DASHBOARD_PASSWORD`: senha obrigatória do painel (mínimo de 16 caracteres).
- `MEDIA_RETENTION_DAYS`: `0` desativa a limpeza local. Um valor entre 1 e 36500 dias habilita uma ação manual no painel; ela remove somente o arquivo local de vídeos com todos os destinos publicados após o prazo. Falhas, itens parciais ou pendentes e registros do banco permanecem; vídeos remotos não são removidos.
- `DATA_DIR`: diretório de SQLite e vídeos recebidos; padrão `social_automation/data/`.
- `SESSION_DIR`: diretório de credenciais; padrão `social_automation/sessions/`.
- `DB_PATH`: opcional, caminho explícito para o SQLite.

Faça backup de `data/` e `sessions/` em local privado. Consulte [SECURITY.md](SECURITY.md) antes de expor o serviço fora do computador local.
