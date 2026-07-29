# Prompt de implementação: gestão de usuários e perfis

## Objetivo

Implementar no projeto DataSaúde uma área administrativa para gestão de usuários, perfis e permissões, integrada ao frontend `datasaude-app` e ao backend `datasaude-api`.

A implementação deve respeitar a arquitetura existente, preservar o login atual e ser feita com migração compatível. Antes de criar abstrações, leia os arquivos existentes e siga os padrões já utilizados nos dois repositórios.

## Contexto atual do projeto

### Frontend: `datasaude-app`

- React 17 com Create React App, Material UI e React Router 5.
- As rotas administrativas ficam em `src/routes.js` e usam `layout: "/admin"`.
- `src/layouts/Admin.js` atualmente verifica apenas se existe um JWT válido por meio de `isAuthenticated()`.
- O login é feito por `POST /api/v1/users/login` em `src/auth.js`.
- O token e o refresh token são armazenados em `localStorage`.
- O menu lateral é gerado a partir de `src/routes.js`.
- A interface deve seguir o padrão visual existente do Material UI e das telas administrativas.

### Backend: `datasaude-api`

- FastAPI, SQLAlchemy assíncrono, Alembic e Pydantic.
- O modelo atual `app/user/models/user.py` possui `id`, `email` único, `nickname` único, `password`, `is_admin` e timestamps herdados de `TimestampMixin`.
- A tabela existente é `users`.
- Já existe `PermissionDependency` com `IsAuthenticated` e `IsAdmin` em `core/fastapi/dependencies/permission.py`.
- `GET /api/v1/users` já exige `IsAdmin`.
- `POST /api/v1/users` atualmente não exige autenticação administrativa e deve ser revisado, pois não pode continuar permitindo criação pública de usuários.
- O login atual retorna apenas `token` e `refresh_token`, e o `CurrentUser` contém somente o `id` extraído do token.
- O serviço atual compara diretamente o valor do campo `password`; novas senhas nunca devem ser armazenadas em texto puro.
- Transações seguem o decorator `Transactional`; não inserir `commit()` manual onde o padrão existente não utiliza isso.

### Scripts e banco

- As migrations ficam em `datasaude-api/migrations/versions` e são geradas com Alembic.
- `datasaude-scripts` contém scripts auxiliares, mas a regra de negócio da API deve permanecer no `datasaude-api`.
- Criar a migration necessária, mas não executá-la automaticamente e não alterar o banco durante o desenvolvimento.

## Requisitos funcionais

### 1. Gestão de usuários

Criar uma tela administrativa com:

- listagem paginada;
- busca por `nickname`, e-mail, perfil e status;
- indicação clara de usuário ativo ou inativo;
- criação de usuário;
- edição de usuário;
- alteração de senha sem retornar ou exibir a senha atual;
- associação a um perfil;
- ativação e inativação do usuário;
- confirmação antes de inativar;
- prevenção de inativação do último administrador ativo;
- tratamento visual para e-mail e nickname duplicados.

Preferir inativação (`is_active = false`) em vez de exclusão física, preservando histórico e integridade referencial. Não remover fisicamente usuários pela interface.

### 2. Gestão de perfis e permissões

Criar uma tela administrativa própria para:

- listar perfis;
- criar e editar perfil;
- inativar perfil quando necessário;
- definir o nome do perfil;
- selecionar permissões por meio de uma matriz de checkboxes;
- visualizar quais usuários estão associados ao perfil antes de inativá-lo.

Usar identificadores estáveis de permissão, separados do texto exibido. Inicialmente considerar as áreas existentes no frontend:

- `dashboard.view`
- `previsao.view`
- `chat_ia.view`
- `indicadores.view`
- `table.view`
- `maps.view`
- `users.manage`
- `roles.manage`

Novas telas devem poder registrar novas permissões sem reescrever a regra de autorização.

### 3. Compatibilidade com o modelo atual

Não substituir silenciosamente o modelo legado. Definir uma estratégia de migração explícita:

- manter `is_admin` durante a transição ou migrar seus usuários para um perfil `Administrador` equivalente;
- usuários existentes com `is_admin = true` devem continuar administradores após a migration;
- criar o perfil `Administrador` inicial de forma idempotente;
- decidir e documentar como os usuários existentes serão associados a um perfil padrão;
- adicionar `is_active` com valor inicial compatível com os usuários atuais;
- manter `email` e `nickname` únicos;
- avaliar o campo legado `password` antes da migration. Novas senhas devem usar hash seguro, e a estratégia para senhas existentes deve ser definida sem expor credenciais nem quebrar o login durante a transição;
- atualizar o login para rejeitar usuários inativos;
- não retornar `password` ou `password_hash` em nenhuma resposta da API.

Usar uma biblioteca de hash segura e compatível com o ambiente Python atual, adicionando a dependência ao `pyproject.toml` se necessário. Nunca implementar hash manual ou armazenar senha em texto puro.

## Requisitos de autorização

A autorização deve existir no backend. Ocultar menu e rota no frontend é apenas uma camada de usabilidade, não uma proteção.

- Todas as operações de usuários e perfis devem exigir usuário autenticado.
- Criar permissões backend reutilizáveis, por exemplo `HasPermission("users.manage")` e `HasPermission("roles.manage")`, aproveitando a estrutura de `PermissionDependency` existente.
- A API deve verificar a permissão em cada endpoint de leitura e mutação.
- Um usuário sem permissão deve receber `401` quando não autenticado ou `403` quando autenticado sem autorização, conforme o padrão de exceções já existente.
- O frontend deve obter o usuário atual e suas permissões por endpoint autenticado, como `GET /api/v1/users/me`, ou por contrato equivalente definido no backend. Não confiar em valores de perfil editáveis no `localStorage`.
- O guard de rotas deve verificar autenticação e permissão necessária.
- O menu lateral deve ocultar itens sem a permissão correspondente.
- A tela de administração de usuários deve exigir `users.manage`.
- A tela de administração de perfis deve exigir `roles.manage`.
- O perfil `Administrador` deve continuar tendo acesso administrativo completo.

## API sugerida

Preservar `POST /api/v1/users/login` e o refresh token existentes. Para a administração, preferir endpoints claramente separados, sem quebrar contratos já usados pelo frontend:

- `GET /api/v1/admin/users`
- `POST /api/v1/admin/users`
- `GET /api/v1/admin/users/{user_id}`
- `PATCH /api/v1/admin/users/{user_id}`
- `POST /api/v1/admin/users/{user_id}/activate`
- `POST /api/v1/admin/users/{user_id}/deactivate`
- `GET /api/v1/admin/roles`
- `POST /api/v1/admin/roles`
- `GET /api/v1/admin/roles/{role_id}`
- `PATCH /api/v1/admin/roles/{role_id}`
- `POST /api/v1/admin/roles/{role_id}/deactivate`
- `GET /api/v1/users/me`

A estrutura exata pode seguir os padrões da API existente, mas deve garantir:

- schemas de request e response separados;
- paginação consistente, com busca e filtros;
- validação de e-mail, nickname, senha e IDs;
- respostas sem campos sensíveis;
- mensagens de erro consistentes com `ExceptionResponseSchema`;
- autorização declarada no endpoint ou dependency equivalente;
- atualização transacional do usuário e do perfil;
- prevenção de referências a perfis inativos.

## Frontend

Implementar no `datasaude-app`:

- serviços HTTP separados para usuários, perfis e usuário atual;
- estado de autenticação com permissões carregadas do backend;
- guard reutilizável para rotas protegidas por permissão;
- menu lateral condicionado às permissões;
- tela `/admin/users`;
- tela `/admin/roles`;
- paginação, busca, filtros e estados de loading, vazio e erro;
- diálogos ou páginas de criação e edição seguindo o padrão Material UI existente;
- validação no formulário antes do envio;
- feedback após criação, edição, ativação e inativação;
- limpeza correta do estado após logout e expiração do token.

Não duplicar a lista de permissões em vários componentes. Definir um catálogo único de permissões no frontend apenas para labels e navegação, mantendo a decisão final no backend.

## Testes obrigatórios

### Backend

Adicionar testes para:

- criação e edição de usuário;
- e-mail e nickname duplicados;
- hash e verificação de senha;
- bloqueio de login para usuário inativo;
- listagem com busca, filtros e paginação;
- criação e associação de perfil;
- autorização de cada endpoint administrativo;
- rejeição de usuário sem a permissão necessária;
- preservação do administrador legado;
- impossibilidade de inativar o último administrador ativo;
- ausência de senha nas respostas.

### Frontend

Adicionar testes para:

- usuário sem permissão não visualizar menu administrativo;
- rota administrativa redirecionar ou bloquear acesso sem permissão;
- listagem e filtros;
- criação e edição;
- tratamento de erro da API;
- inativação com confirmação;
- atualização das permissões após login, refresh e logout.

## Restrições de implementação

- Inspecionar primeiro as implementações existentes e preservar os contratos ativos.
- Não alterar o fluxo do IBGE V1 ou V2 sem necessidade para esta funcionalidade.
- Não iniciar a aplicação do backend durante a implementação.
- Não executar migrations nem alterar dados do banco durante os testes locais.
- No backend, validar sintaxe e executar somente testes focados com o interpretador/ambiente do projeto.
- No frontend, executar lint/prettier e `npm run build`.
- Não criar commits nem fazer push.
- Relatar arquivos alterados, migrations criadas, testes executados e qualquer ponto que dependa de decisão sobre dados legados.
