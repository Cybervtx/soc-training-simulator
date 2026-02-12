# SOC Training Simulator — Parte 1: Fundação (MVP Core)

**Documento de Requisitos do Produto - Versão 1.0**  
**Data:** 2026-02-11  
**Status:** ✅ Concluída (Parte 1)

## 1. Sumário executivo (Parte 1)

Esta é a primeira parte do projeto SOC Training Simulator, focada em estabelecer a fundação técnica necessária para as fases subsequentes. O objetivo é criar uma estrutura funcional com integração AbuseIPDB, modelo de dados e arquitetura base.

## 2. Objetivos da Parte 1

- Estabelecer arquitetura técnica com Flask + Supabase + Tailwind
- Implementar integração básica com AbuseIPDB (fetch + cache)
- Criar modelo de dados essencial
- Configurar autenticação básica de usuários
- Preparar estrutura do projeto para desenvolvimento iterativo

## 3. Escopo da Parte 1

### Incluído
- Setup do projeto (backend Flask, frontend SPA básico)
- Configuração do banco de dados PostgreSQL via Supabase
- Integração com AbuseIPDB API (periodic fetch + cache)
- Sistema de autenticação básico (email/password ou Supabase Auth)
- Modelos de dados: users, abuseipdb_cache
- Estrutura de API REST básica
- Ambiente de desenvolvimento configurado

### Não incluído nesta fase
- Workspace de investigação completo (Parte 2)
- Sistema de gamificação (Parte 3)
- Painel administrativo completo (Parte 4)

## 4. Stack Tecnológica

### Backend
- **Linguagem:** Python 3.11+
- **Framework:** Flask
- **Templates:** Jinja2 (para páginas estáticas simples)
- **Banco de dados:** PostgreSQL via Supabase
- **ORM:** SQLAlchemy ou raw SQL com psycopg2
- **Cache:** Redis (TTL configurável para AbuseIPDB)

### Frontend
- **Framework:** Vanilla JS ou Vue.js 3 (CDN)
- **Estilização:** Tailwind CSS via CDN
- **Ícones:** FontAwesome via CDN

### Infraestrutura
- **Banco gerenciado:** Supabase (Postgres, Auth, Storage)
- **Secrets:** Variáveis de ambiente ou Supabase Secrets
- **Versionamento:** Git

## 5. Modelo de Dados (Parte 1)

### Tabela: users
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  nome VARCHAR(100) NOT NULL,
  role VARCHAR(20) DEFAULT 'analyst', -- analyst, instructor, admin
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

### Tabela: abuseipdb_cache
```sql
CREATE TABLE abuseipdb_cache (
  id SERIAL PRIMARY KEY,
  ip VARCHAR(45) UNIQUE NOT NULL,
  reputation_score INT,
  categories TEXT[], -- ARRAY de categorias
  country_code VARCHAR(2),
  country_name VARCHAR(100),
  domain VARCHAR(255),
  last_checked TIMESTAMP NOT NULL,
  cached_at TIMESTAMP DEFAULT NOW(),
  expires_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_abuseipdb_cache_ip ON abuseipdb_cache(ip);
CREATE INDEX idx_abuseipdb_cache_expires ON abuseipdb_cache(expires_at);
```

### Tabela: abuseipdb_api_log
```sql
CREATE TABLE abuseipdb_api_log (
  id SERIAL PRIMARY KEY,
  endpoint VARCHAR(100) NOT NULL,
  request_params JSONB,
  response_status INT,
  rate_limit_remaining INT,
  created_at TIMESTAMP DEFAULT NOW()
);
```

## 6. Integração com AbuseIPDB (Parte 1)

### Endpoints da API a utilizar
- `GET /api/v2/check-block` - Verificar IP específico
- `GET /api/v2/reports` - Listar reports de IP
- `GET /api/v2/stats` - Estatísticas gerais

### Funcionalidades a implementar
1. **Periodic Fetch**
   - Job que executa a cada X horas
   - Busca IPs populares/mais reportados
   - Armazena no cache local

2. **On-demand Fetch**
   - API endpoint para buscar dados de IP sob demanda
   - Verifica cache primeiro
   - Se expirado ou não existente, faz chamada à API

3. **Rate Limiting**
   - Respeitar limites da AbuseIPDB (1.000 requests/dia gratuito)
   - Log de todas as requisições
   - Alertas quando demócrati limite

### CacheStrategy
- TTL padrão: 24 horas
- TTL configurável por tipo de dado
- Invalidação manual disponível
- Cleanup job para dados expirados

## 7. Arquitetura de API (Parte 1)

### Endpoints HTTP

#### Autenticação
- `POST /api/auth/register` - Registrar novo usuário
- `POST /api/auth/login` - Login
- `POST /api/auth/logout` - Logout
- `GET /api/auth/me` - Perfil atual

#### AbuseIPDB
- `GET /api/abuseipdb/check?ip=x.x.x.x` - Verificar IP
- `GET /api/abuseipdb/stats` - Estatísticas da API
- `GET /api/abuseipdb/popular` - IPs mais populares do cache
- `POST /api/abuseipdb/refresh` - Forçar refresh de IP

#### Sistema
- `GET /api/health` - Health check
- `GET /api/config` - Configurações públicas

## 8. Estrutura do Projeto

```
soc-training-simulator/
├── backend/
│   ├── app.py                    # Flask app principal
│   ├── config.py                 # Configurações
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── abuseipdb_cache.py
│   │   └── abuseipdb_log.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── abuseipdb.py
│   │   └── health.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── abuseipdb_service.py
│   │   └── cache_service.py
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── css/
│   │   └── styles.css (Tailwind via CDN)
│   ├── js/
│   │   └── app.js
│   └── pages/
│       ├── login.html
│       └── dashboard.html
├── supabase/
│   ├── schema.sql
│   └── migrations/
├── tests/
│   ├── test_api/
│   └── test_models/
├── .env.example
├── README.md
└── docker-compose.yml (opcional)
```

## 9. Requisitos Não-Funcionais (Parte 1)

### Segurança
- HTTPS em produção
- Senhas hasheadas (bcrypt)
- JWT para autenticação
- Variáveis de ambiente para segredos
- Validação de inputs

### Performance
- Tempo de resposta API < 300ms
- Cache de queries frequentes
- Conexões de banco otimizadas

### Confiabilidade
- Health checks implementados
- Logs estruturados
- Error handling adequado

## 10. Critérios de Conclusão (Parte 1)

- [x] Backend Flask rodando e respondendo
- [x] Banco de dados Supabase configurado com tabelas
- [x] Sistema de autenticação funcionando
- [x] Integração AbuseIPDB operacional (fetch + cache)
- [x] Frontend básico com login e dashboard
- [x] Testes unitários para funcionalidades core
- [x] Documentação de setup para desenvolvedores

---

**Status:** ✅ Parte 1 - TOTALMENTE CONCLUÍDA (7/7 critérios)

## 11. Próximos Passos

Após conclusão da Parte 1, avançar para:
- **Parte 2:** Workspace de Investigação (gerador de cenários, evidências simuladas)
- **Parte 3:** Gamificação e Avaliação
- **Parte 4:** Painel Administrativo

---

**Contato:** equipe de segurança e treinamento
