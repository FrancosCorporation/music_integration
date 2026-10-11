# Segurança

- Mantenha o painel em `127.0.0.1`. O Docker Compose já publica somente nessa interface. Para acesso remoto, use VPN ou um proxy com TLS e autenticação adicional.
- Configure uma senha exclusiva com pelo menos 16 caracteres em `.env`. O valor de exemplo não serve para produção.
- Restrinja as permissões de `data/` e `sessions/`. Eles contêm vídeos, o banco e credenciais OAuth.
- Nunca versione `.env`, `client_secret.json`, `token.json`, vídeos, banco local ou cookies de navegador.
- O token OAuth solicita apenas o escopo `youtube.upload`. Revogue-o na conta Google se o acesso não for mais necessário.
- O painel não publica sem uma ação manual. Uploads públicos exigem seleção e confirmação explícitas; uploads privados são o padrão.
- As outras integrações estão desativadas. Não use automação de navegador para fornecer senhas a este painel.
- Faça cópias de segurança criptografadas e limite o acesso a quem administra a conta.
- Para remover os dados, pare o serviço e apague `data/` e `sessions/` conscientemente; essa ação remove uploads em espera e tokens locais.
