# SOC Training Simulator - Parte 1: Fundação (MVP Core)

## Visão Geral

SOC Training Simulator é uma plataforma de treinamento para analistas de Security Operations Center (SOC). Esta é a **Parte 1: Fundação (MVP Core)**, que estabelece a arquitetura técnica básica necessária para as fases subsequentes.

## Objetivos da Parte 1

- ✅ Estabelecer arquitetura técnica com Flask + Supabase + Tailwind
- ✅ Implementar integração básica com AbuseIPDB (fetch + cache)
- ✅ Criar modelo de dados essencial
- ✅ Configurar autenticação básica de usuários
- ✅ Preparar estrutura do projeto para desenvolvimento iterativo

## Stack Tecnológica

### Backend
- **Linguagem:** Python 3.11+
- **Framework:** Flask
- **Banco de dados:** PostgreSQL via Supabase
- **ORM:** SQLAlchemy
- **Autenticação:** JWT + bcrypt

### Frontend
- **Framework:** Vanilla JS
- **Estilização:** Tailwind CSS via CDN
- **Ícones:** FontAwesome via CDN

## Estrutura do Projeto

```
soc-training-simulator/
├── backend/
│   ├── app.py                    # Flask app principal
│   ├── config.py                 # Configurações
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py               # Modelo de usuário
│   │   ├── abuseipdb_cache.py   # Cache de IPs
│   │   └── abuseipdb_log.py      # Log de API
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py               # Rotas de autenticação
│   │   ├── abuseipdb.py          # Rotas do AbuseIPDB
│   │   └── health.py             # Health checks
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py      # Serviço de autenticação
│   │   ├── abuseipdb_service.py # Serviço do AbuseIPDB
│   │   └── cache_service.py      # Serviço de cache
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── js/
│   │   └── app.js
│   └── pages/
│       ├── login.html
│       └── dashboard.html
├── supabase/
│   └── schema.sql                # Schema do banco de dados
├── .env.example
├── docker-compose.yml
├── Dockerfile
└── README.md
```

## Pré-requisitos

- Python 3.11+
- PostgreSQL (local ou Supabase)
- pip ou conda
- (Opcional) Docker e Docker Compose

## Instalação Rápida

### 1. Clonar o Repositório

```bash
git clone <repository-url>
cd soc-training-simulator
```

### 2. Configurar Ambiente Virtual

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
.\venv\Scripts\activate  # Windows
```

### 3. Instalar Dependências

```bash
pip install -r backend/requirements.txt
```

### 4. Configurar Variáveis de Ambiente

```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

### 5. Configurar Banco de Dados

#### Opção A: Usando Supabase (Recomendado para produção)

1. Crie um projeto no [Supabase](https://supabase.com)
2. Execute o script SQL em `supabase/schema.sql` no SQL Editor
3. Configure as variáveis de ambiente no `.env`

#### Opção B: Usando PostgreSQL Local

```bash
psql -U postgres -c "CREATE DATABASE soc_training;"
psql -U postgres -d soc_training -f supabase/schema.sql
```

### 6. Obter API Key do AbuseIPDB

1. Registre-se em [AbuseIPDB](https://www.abuseipdb.com)
2. Gere uma API key
3. Adicione ao arquivo `.env`:

```env
ABUSEIPDB_API_KEY=sua-api-key-aqui
```

### 7. Executar a Aplicação

```bash
# Development
python backend/app.py

# Ou com ambiente de desenvolvimento
FLASK_ENV=development python backend/app.py
```

A aplicação estará disponível em `http://localhost:5000`

## Usando Docker Compose

```bash
docker-compose up -d
```

## Endpoints da API

### Autenticação

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/auth/register` | Registrar novo usuário |
| POST | `/api/auth/login` | Login |
| POST | `/api/auth/logout` | Logout |
| GET | `/api/auth/me` | Perfil atual |
| POST | `/api/auth/refresh` | Renovar token |

### AbuseIPDB

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/abuseipdb/check?ip=x.x.x.x` | Verificar IP |
| GET | `/api/abuseipdb/reports` | Listar reports |
| GET | `/api/abuseipdb/stats` | Estatísticas |
| GET | `/api/abuseipdb/popular` | IPs populares |
| POST | `/api/abuseipdb/refresh` | Forçar refresh |

### Sistema

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/health` | Health check |
| GET | `/api/config` | Configurações públicas |

## Testes

```bash
# Instalar dependências de teste
pip install pytest pytest-flask pytest-cov

# Executar testes
pytest tests/ -v

# Executar com cobertura
pytest tests/ --cov=backend
```

## Próximos Passos

Após conclusão da Parte 1, avançar para:

- **Parte 2:** Workspace de Investigação
  - Gerador de cenários
  - Evidências simuladas
  - Ferramentas de análise

- **Parte 3:** Gamificação e Avaliação
  - Sistema de pontos
  - Rankings
  - Certificados

- **Parte 4:** Painel Administrativo
  - Gerenciamento de usuários
  - Relatórios avançados
  - Configurações do sistema

## Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## Licença

Este projeto está sob a licença MIT.

## Contato

Equipe de Segurança e Treinamento
