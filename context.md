# Contexto do projeto

## Objetivo atual

O projeto oferece uma fila local para organizar vídeos e, quando solicitado manualmente no painel, publicá-los no YouTube pela API oficial. A senha do painel é obrigatória, o upload usa arquivos locais privados e a privacidade inicial no YouTube é `private`.

## Estado das plataformas

- YouTube: upload pela YouTube Data API v3 com OAuth de aplicativo instalado.
- Instagram, TikTok, Pinterest, X e LinkedIn: indisponíveis. Os antigos fluxos de navegador e stubs OAuth não constituíam integrações utilizáveis e foram desabilitados.

## Componentes

- `social_automation/app.py`: painel autenticado, fila de upload, publicação manual e registros.
- `social_automation/database.py`: SQLite com resultado por destino e reivindicação atômica antes do upload.
- `social_automation/modules/youtube.py`: credenciais e upload pela API oficial.
- `social_automation/youtube_auth.py`: autorização OAuth executada no host com navegador.
- `data/`: banco e arquivos enviados, fora do Git.
- `sessions/youtube/`: client secret e token OAuth, fora do Git.

## Limites conhecidos

Não há agendamento, postagem automática, publicação nas outras redes, limpeza automática de vídeos enviados, suporte a contas múltiplas ou métricas de audiência. O app envia no máximo cem destinos pendentes por ação; limites da API e da quota do Google também se aplicam.

Consulte [Readme.md](Readme.md) para instalação e [SECURITY.md](SECURITY.md) para o tratamento dos segredos e arquivos locais.
