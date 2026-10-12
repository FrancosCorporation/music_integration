# Melhorias e estado atual

## Entrega atual

- [x] Proteger o painel com senha administrativa e comparação de tempo constante.
- [x] Limitar uploads a arquivos de vídeo aceitos, 200 MB por arquivo e por envio; armazenar com UUID e permissões privadas.
- [x] Separar destinos por plataforma, registrar estados/logs e reivindicar itens atomicamente.
- [x] Fazer o botão de publicar executar a API oficial do YouTube e registrar o ID remoto ou a falha.
- [x] Usar OAuth renovável com arquivos locais de acesso restrito.
- [x] Tornar `private` a privacidade padrão e exigir confirmação para publicação pública.
- [x] Desativar integrações incompletas de Instagram, TikTok, Pinterest, X e LinkedIn.
- [x] Ignorar arquivos locais e segredos; adicionar Docker Compose preso a loopback.
- [x] Adicionar retenção local desativada por padrão; ação manual limitada a uploads totalmente confirmados.
- [x] Atualizar instalação, limites, segurança e contexto do projeto.
- [x] Adicionar validação estática no CI.
- [x] Fixar Ubuntu 24.04 e atualizar checkout/Python Actions para v7.

## Pendências conhecidas

- [ ] Validar a configuração real do OAuth no Google Cloud e autorizar a conta do projeto.
- [ ] Executar uma publicação privada com um vídeo de baixo risco em conta de homologação; requer credenciais e cota do projeto.
- [ ] Implementar integração oficial por plataforma apenas após obter permissões, aprovação de API e requisitos de conta.
- [ ] Migrar registros de uma cópia externa do banco legado caso ela exista; o arquivo rastreado neste repositório estava vazio.

Não execute automações de publicação sem autorização manual no painel. Testes automatizados e publicação em produção não fazem parte desta entrega.

## Reauditoria de retenção e CI

A limpeza é desativada por `MEDIA_RETENTION_DAYS=0`. Com prazo positivo, um
operador autenticado também precisa confirmar a ação no painel. A rotina só
considera `videos.status='posted'`, data vencida e todos os destinos em `posted`;
preserva caminhos fora de `data/assets`, symlinks, arquivos ausentes, itens
parciais/falhos/pendentes e registra o resultado no banco. Não apaga uploads do
YouTube. A CI estática agora fixa Ubuntu 24.04 e usa checkout/setup-python v7.
Commit `3334535` passou na CI `38195921225`. AST de 12 Python, parse de 2 JSON,
YAML/TOML, Compose config e `git diff --check` passaram; nenhum teste, OAuth,
publicação ou ação de limpeza foi executado.
