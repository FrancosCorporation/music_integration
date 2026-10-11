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
- [x] Atualizar instalação, limites, segurança e contexto do projeto.
- [x] Adicionar validação estática no CI.

## Pendências conhecidas

- [ ] Validar a configuração real do OAuth no Google Cloud e autorizar a conta do projeto.
- [ ] Executar uma publicação privada com um vídeo de baixo risco em conta de homologação; requer credenciais e cota do projeto.
- [ ] Implementar integração oficial por plataforma apenas após obter permissões, aprovação de API e requisitos de conta.
- [ ] Adicionar limpeza configurável e segura de mídia local, respeitando retenção e falhas de upload.
- [ ] Migrar registros de uma cópia externa do banco legado caso ela exista; o arquivo rastreado neste repositório estava vazio.

Não execute automações de publicação sem autorização manual no painel. Testes automatizados e publicação em produção não fazem parte desta entrega.
