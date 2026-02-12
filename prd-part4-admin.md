# SOC Training Simulator — Parte 4: Painel Administrativo e Funcionalidades Avançadas

**Documento de Requisitos do Produto - Versão 1.0**  
**Data:** 2026-02-11  
**Pré-requisito:** Partes 1, 2 e 3 concluídas

## 1. Sumário executivo (Parte 4)

Esta quarta e última parte foca no painel administrativo completo, SSO, relatórios exportáveis, logging de auditoria e funcionalidades avançadas para gestão de turmas e avaliações organizacionais.

## 2. Objetivos da Parte 4

- Implementar painel administrativo completo
- Adicionar suporte SSO (SAML/OAuth2)
- Criar sistema de turmas e grupos
- Implementar relatórios exportáveis (CSV, PDF)
- Adicionar logging e auditoria de sessões
- Criar sistema de módulos e currículos
- Implementar métricas avançadas e KPIs

## 3. Escopo da Parte 4

### Incluído
- Painel administrativo com todas as funcionalidades
- SSO (Google Workspace, Azure AD, Okta)
- Sistema de turmas e grupos de usuários
- Relatórios exportáveis (CSV, PDF)
- Logging e replay de sessões
- Módulos e currículos de treinamento
- Métricas avançadas e dashboards
- Configurações avançadas do sistema

### Não incluído
- Integração com SIEM/EDR externos (roadmap futuro)
- Cenários colaborativos em tempo real (roadmap futuro)

## 4. Modelo de Dados (Parte 4)

### Tabela: teams
```sql
CREATE TABLE teams (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  nome VARCHAR(100) NOT NULL,
  descricao TEXT,
  manager_id UUID REFERENCES users(id),
  created_at TIMESTAMP DEFAULT NOW(),
  is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_teams_manager ON teams(manager_id);
```

### Tabela: team_members
```sql
CREATE TABLE team_members (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  team_id UUID NOT NULL REFERENCES teams(id),
  user_id UUID NOT NULL REFERENCES users(id),
  role VARCHAR(20) DEFAULT 'member', -- member, lead
  joined_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(team_id, user_id)
);
```

### Tabela: modules
```sql
CREATE TABLE modules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  titulo VARCHAR(200) NOT NULL,
  descricao TEXT,
  ordem INT DEFAULT 0,
  duracao_estimada_min INT,
  created_by UUID REFERENCES users(id),
  created_at TIMESTAMP DEFAULT NOW(),
  is_published BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_modules_order ON modules(ordem);
```

### Tabela: module_scenarios
```sql
CREATE TABLE module_scenarios (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  module_id UUID NOT NULL REFERENCES modules(id),
  scenario_id UUID NOT NULL REFERENCES scenarios(id),
  ordem INT DEFAULT 0,
  obrigatorio BOOLEAN DEFAULT TRUE,
  UNIQUE(module_id, scenario_id)
);

CREATE INDEX idx_module_scenarios_module ON module_scenarios(module_id);
```

### Tabela: curricula
```sql
CREATE TABLE curricula (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  nome VARCHAR(200) NOT NULL,
  descricao TEXT,
  modulo_ids UUID[], -- array de module IDs
  duracao_total_min INT,
  created_by UUID REFERENCES users(id),
  created_at TIMESTAMP DEFAULT NOW(),
  is_published BOOLEAN DEFAULT FALSE
);
```

### Tabela: user_enrollments
```sql
CREATE TABLE user_enrollments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  curriculum_id UUID NOT NULL REFERENCES curricula(id),
  modulo_id UUID REFERENCES modules(id),
  status VARCHAR(20) DEFAULT 'enrolled', -- enrolled, in_progress, completed
  progress_percentage DECIMAL(5,2) DEFAULT 0,
  enrolled_at TIMESTAMP DEFAULT NOW(),
  completed_at TIMESTAMP,
  UNIQUE(user_id, curriculum_id)
);

CREATE INDEX idx_enrollments_user ON user_enrollments(user_id);
CREATE INDEX idx_enrollments_curriculum ON user_enrollments(curriculum_id);
```

### Tabela: audit_logs
```sql
CREATE TABLE audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  action VARCHAR(100) NOT NULL,
  entity_type VARCHAR(50),
  entity_id UUID,
  details JSONB,
  ip_address INET,
  user_agent TEXT,
  timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
```

### Tabela: session_replays
```sql
CREATE TABLE session_replays (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  submission_id UUID REFERENCES submissions(id),
  events JSONB NOT NULL, -- array de eventos da sessão
  duration_seconds INT,
  started_at TIMESTAMP NOT NULL,
  ended_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_session_replays_user ON session_replays(user_id);
CREATE INDEX idx_session_replays_submission ON session_replays(submission_id);
```

### Tabela: sso_configurations
```sql
CREATE TABLE sso_configurations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  provider VARCHAR(50) NOT NULL, -- google, azure, okta, saml
  name VARCHAR(100) NOT NULL,
  config JSONB NOT NULL, -- configurações do provider
  is_active BOOLEAN DEFAULT FALSE,
  created_by UUID REFERENCES users(id),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

### Tabela: system_config
```sql
CREATE TABLE system_config (
  id SERIAL PRIMARY KEY,
  chave VARCHAR(100) UNIQUE NOT NULL,
  valor TEXT NOT NULL,
  descricao TEXT,
  updated_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO system_config (chave, valor, descricao) VALUES
('abuseipdb_cache_ttl_hours', '24', 'TTL do cache de IPs AbuseIPDB'),
('max_scenarios_per_day', '10', 'Máximo cenários por dia por usuário'),
('enable_sso', 'false', 'Habilitar autenticação SSO'),
('default_difficulty', 'medium', 'Dificuldade padrão para cenários'),
('session_timeout_minutes', '60', 'Timeout de sessão em minutos');
```

## 5. Painel Administrativo

### Seções do Admin Panel

```
┌─────────────────────────────────────────────────────────────┐
│  SOC Training Admin                                          │
├─────────────────────────────────────────────────────────────┤
│  [Dashboard] [Usuários] [Cenários] [Turmas] [Relatórios]   │
│  [Módulos] [Configurações] [Auditoria]                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Dashboard                                                  │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │Usuários │ │Cenários │ │Turmas  │ │Média   │           │
│  │ Ativos  │ │ Ativos  │ │Ativas  │ │Score   │           │
│  │   45    │ │   23    │ │    5   │ │ 78.5   │           │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘           │
│                                                              │
│  Atividade Recente                                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ João completou "Brute Force SSH" (score: 92)     │   │
│  │ Maria iniciou "C2 Communication"                 │   │
│  │ Novo usuário registrado: pedro@empresa.com       │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  Métricas da Semana                                         │
│  [Gráfico de cenários completados por dia]                 │
│  [Gráfico de score médio por turma]                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Funcionalidades por Seção

#### Usuários
- Listar todos os usuários
- Editar perfil e role
- Ativar/desativar usuário
- Resetar senha
- Ver histórico de performance
- Atribuir a turmas
- Exportar lista (CSV)

#### Cenários
- Criar/editar/excluir cenários
- Ativar/desativar cenários
- Clonar cenários existentes
- Visualizar estatísticas de uso
- Ajustar gabarito
- Definir dificuldade

#### Turmas
- Criar/editar turmas
- Adicionar/remover membros
- Atribuir currículos
- Visualizar progresso da turma
- Comparar performance entre turmas
- Gerenciar coaches/instrutores

#### Relatórios
- Relatório de performance individual
- Relatório de performance por turma
- Relatório de uso da plataforma
- Relatório de progresso de currículos
- Exportar PDF e CSV
- Agendar relatórios automáticos

#### Módulos/Currículos
- Criar módulos de treinamento
- Organizar em currículos
- Definir pré-requisitos
- Aprovar/rejeitar conclusões
- Visualizar engajamento

#### Configurações
- Configurações gerais
- Integrações SSO
- Configurações de cache
- Limites e quotas
- Notificações

#### Auditoria
- Log de todas as ações
- Filtros por usuário, ação, data
- Replay de sessões
- Exportação de logs

## 6. SSO e Autenticação

### Providers Suportados

#### Google Workspace
```python
# config.json para Google SSO
{
  "provider": "google",
  "client_id": "xxx.apps.googleusercontent.com",
  "client_secret": "xxx",
  "redirect_uri": "https://soc-training.com/auth/callback/google",
  "scopes": ["openid", "email", "profile"]
}
```

#### Microsoft Azure AD
```python
# config.json para Azure AD
{
  "provider": "azure",
  "client_id": "xxx",
  "client_secret": "xxx",
  "tenant_id": "xxx",
  "redirect_uri": "https://soc-training.com/auth/callback/azure",
  "scopes": ["openid", "email", "profile", "User.Read"]
}
```

#### Okta
```python
# config.json para Okta
{
  "provider": "okta",
  "client_id": "xxx",
  "client_secret": "xxx",
  "issuer": "https://dev-xxx.okta.com",
  "redirect_uri": "https://soc-training.com/auth/callback/okta"
}
```

#### SAML Genérico
```python
# config.json para SAML
{
  "provider": "saml",
  "entity_id": "soc-training-simulator",
  "sso_url": "https://idp.example.com/sso",
  "certificate": "-----BEGIN CERTIFICATE-----...",
  "attribute_mapping": {
    "email": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress",
    "name": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name",
    "groups": "http://schemas.microsoft.com/ws/2008/06/identity/claims/groups"
  }
}
```

### Fluxo de Autenticação SSO

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Usuário acessa /login                                    │
│    ↓                                                         │
│ 2. Escolhe "Login com [Provider]"                           │
│    ↓                                                         │
│ 3. Redireciona para provider SSO                            │
│    ↓                                                         │
│ 4. Usuário faz login no provider                            │
│    ↓                                                         │
│ 5. Provider redireciona com code/callback                   │
│    ↓                                                         │
│ 6. Backend troca code por tokens e obtém info usuário       │
│    ↓                                                         │
│ 7. Cria/faz login usuário no sistema                        │
│    ↓                                                         │
│ 8. Redireciona para dashboard                               │
└─────────────────────────────────────────────────────────────┘
```

### Mapeamento de Roles via SSO
```python
ROLE_MAPPINGS = {
    'google': {
        'admin@empresa.com': 'admin',
        'coach@empresa.com': 'instructor'
    },
    'azure': {
        'AAD Group: SOC-Admins': 'admin',
        'AAD Group: SOC-Trainers': 'instructor'
    }
}
```

## 7. Relatórios Exportáveis

### Tipos de Relatório

#### Relatório Individual (PDF)
```
═══════════════════════════════════════════════════════════
              SOC TRAINING - CERTIFICADO DE CONCLUSÃO
═══════════════════════════════════════════════════════════

Nome: João Silva
Período: 01/01/2025 - 28/02/2025
Currículo: SOC Analyst Fundamentals

RESUMO DE PROGRESSO
───────────────────────────────────────────────────────────
Cenários Completados:              15
Média de Score:                    82.5%
Média de Tempo:                    18:32
Nível Atual:                       Senior
Badges Obtidos:                    7

MÓDULOS CONCLUÍDOS
───────────────────────────────────────────────────────────
✓ Fundamentos de SIEM           (12/02/2025)   Score: 85%
✓ Análise de Logs               (15/02/2025)   Score: 78%
✓ Investigação de IPs           (20/02/2025)   Score: 90%

───────────────────────────────────────────────────────────
                   Emitido em: 01/03/2025
              SOC Training Simulator
═══════════════════════════════════════════════════════════
```

#### Relatório de Turmas (PDF)
```
═══════════════════════════════════════════════════════════
           RELATÓRIO DE DESEMPENHO - TURMA SOC-2025-01
═══════════════════════════════════════════════════════════

Período: 01/01/2025 - 28/02/2025
Instrutor Responsável: Maria Santos

RESUMO DA TURMA
───────────────────────────────────────────────────────────
Alunos Matriculados:              20
Alunos Ativos:                   18
Cenários Disponíveis:            12
Cenários Média por Aluno:        8.5

DESEMPENHO CONSOLIDADO
───────────────────────────────────────────────────────────
Média de Score Global:           76.8%
Média de Tempo por Cenário:      21:15
Taxa de Conclusão:               85%
Alunos no Nível Senior+:          5

RANKING DA TURMA
───────────────────────────────────────────────────────────
1. João Silva       - 845 pts  - Senior
2. Pedro Costa      - 820 pts  - Senior
3. Ana Oliveira     - 795 pts  - Intermediate
...

CENÁRIOS COM MAIOR DIFICULDADE
───────────────────────────────────────────────────────────
1. Advanced C2 Detection  - Média: 62%  - 40% não completou
2. Malware Hunt          - Média: 68%  - 25% não completou
═══════════════════════════════════════════════════════════
```

#### Exportação CSV
```csv
# usuarios_2025-03-01.csv
id,nome,email,team,level,xp,scenarios_completed,avg_score,avg_time,last_active
uuid-1,João Silva,joao@empresa.com,SOC-01,senior,845,15,82.5,18:32,2025-02-28
uuid-2,Pedro Costa,pedro@empresa.com,SOC-01,senior,820,14,80.2,20:15,2025-02-28
```

## 8. Logging e Auditoria

### Tipos de Eventos Auditados

| Categoria | Eventos |
|-----------|---------|
| Autenticação | login, logout, login_failed, password_reset, sso_login |
| Cenários | scenario_view, scenario_start, scenario_submit |
| Avaliação | submission_created, evaluation_completed |
| Admin | user_created, user_updated, user_deleted, role_changed |
| Sistema | config_updated, cache_cleared, sso_config_changed |
| Dados | artifact_exported, report_generated |

### Formato de Log
```json
{
  "id": "uuid-audit-log",
  "timestamp": "2025-02-11T14:32:45Z",
  "user_id": "uuid-user",
  "user_email": "joao@empresa.com",
  "action": "scenario_submit",
  "entity_type": "submission",
  "entity_id": "uuid-submission",
  "details": {
    "scenario_id": "uuid-scenario",
    "scenario_title": "Brute Force SSH",
    "score": 85.5,
    "time_spent_seconds": 743
  },
  "ip_address": "10.0.0.42",
  "user_agent": "Mozilla/5.0...",
  "session_id": "uuid-session"
}
```

### Session Replay
```json
{
  "submission_id": "uuid-submission",
  "events": [
    {"timestamp": 0, "type": "page_view", "page": "/workspace/xyz"},
    {"timestamp": 15000, "type": "artifact_click", "artifact_id": "ip-123"},
    {"timestamp": 18000, "type": "tool_use", "tool": "whois"},
    {"timestamp": 45000, "type": "artifact_mark", "artifact_id": "ip-123", "status": "confirmed"},
    {"timestamp": 60000, "type": "artifact_click", "artifact_id": "domain-456"},
    {"timestamp": 120000, "type": "submit"}
  ]
}
```

## 9. API Endpoints (Parte 4)

### Admin - Usuários
- `GET /api/admin/users` - Listar usuários (paginado)
- `POST /api/admin/users` - Criar usuário
- `GET /api/admin/users/{id}` - Detalhes
- `PATCH /api/admin/users/{id}` - Editar
- `DELETE /api/admin/users/{id}` - Excluir
- `POST /api/admin/users/{id}/reset-password` - Resetar senha
- `GET /api/admin/users/{id}/performance` - Performance
- `POST /api/admin/users/{id}/teams` - Atribuir a turmas

### Admin - Cenários
- `GET /api/admin/scenarios` - Listar cenários
- `POST /api/admin/scenarios` - Criar cenário
- `GET /api/admin/scenarios/{id}` - Detalhes
- `PATCH /api/admin/scenarios/{id}` - Editar
- `DELETE /api/admin/scenarios/{id}` - Excluir
- `POST /api/admin/scenarios/{id}/clone` - Clonar
- `POST /api/admin/scenarios/{id}/activate` - Ativar
- `POST /api/admin/scenarios/{id}/deactivate` - Desativar

### Admin - Turmas
- `GET /api/admin/teams` - Listar turmas
- `POST /api/admin/teams` - Criar turma
- `PATCH /api/admin/teams/{id}` - Editar
- `DELETE /api/admin/teams/{id}` - Excluir
- `POST /api/admin/teams/{id}/members` - Adicionar membro
- `DELETE /api/admin/teams/{id}/members/{user_id}` - Remover membro
- `GET /api/admin/teams/{id}/progress` - Progresso da turma

### Admin - Currículos
- `GET /api/admin/curricula` - Listar currículos
- `POST /api/admin/curricula` - Criar
- `PATCH /api/admin/curricula/{id}` - Editar
- `POST /api/admin/curricula/{id}/publish` - Publicar
- `POST /api/admin/curricula/{id}/assign` - Atribuir a usuários

### Relatórios
- `GET /api/reports/performance?user_id=xxx` - Performance
- `GET /api/reports/team?team_id=xxx` - Relatório de turma
- `GET /api/reports/usage` - Relatório de uso
- `GET /api/reports/export/csv?type=users` - Exportar CSV
- `GET /api/reports/export/pdf?type=team&team_id=xxx` - Exportar PDF

### SSO
- `GET /api/admin/sso` - Listar configs SSO
- `POST /api/admin/sso` - Criar config
- `PATCH /api/admin/sso/{id}` - Editar
- `DELETE /api/admin/sso/{id}` - Remover
- `POST /api/admin/sso/{id}/test` - Testar configuração

### Auditoria
- `GET /api/admin/audit/logs` - Listar logs (paginado)
- `GET /api/admin/audit/logs/{id}` - Detalhes
- `GET /api/admin/audit/replay/{session_id}` - Replay de sessão
- `GET /api/admin/audit/export` - Exportar logs

## 10. Frontend Components (Parte 4)

```
components/
├── Admin/
│   ├── Dashboard/
│   │   ├── StatsCards.vue
│   │   ├── ActivityFeed.vue
│   │   └── MetricsChart.vue
│   ├── Users/
│   │   ├── UserList.vue
│   │   ├── UserForm.vue
│   │   └── UserDetail.vue
│   ├── Scenarios/
│   │   ├── ScenarioList.vue
│   │   ├── ScenarioForm.vue
│   │   └── ScenarioStats.vue
│   ├── Teams/
│   │   ├── TeamList.vue
│   │   ├── TeamForm.vue
│   │   └── TeamProgress.vue
│   ├── Reports/
│   │   ├── ReportFilters.vue
│   │   ├── ReportPreview.vue
│   │   └── ReportExport.vue
│   ├── Settings/
│   │   ├── GeneralSettings.vue
│   │   ├── SsoConfig.vue
│   │   └── CacheConfig.vue
│   └── Audit/
│       ├── AuditLogList.vue
│       ├── AuditFilters.vue
│       └── SessionReplay.vue
├── Curriculum/
│   ├── CurriculumList.vue
│   ├── CurriculumForm.vue
│   ├── ModuleCard.vue
│   └── EnrollmentProgress.vue
└── Common/
    ├── Pagination.vue
    ├── ExportButton.vue
    └── FilterPanel.vue
```

## 11. Critérios de Conclusão (Parte 4)

- [ ] Painel administrativo completo funcional
- [ ] SSO implementado (Google, Azure AD, Okta, SAML)
- [ ] Sistema de turmas e grupos operacional
- [ ] Currículos e módulos funcionando
- [ ] Relatórios exportáveis (CSV, PDF)
- [ ] Logging e auditoria implementados
- [ ] Session replay funcional
- [ ] Métricas e KPIs avançados
- [ ] Configurações do sistema completas
- [ ] Testes E2E de todos os fluxos admin

## 12. Roadmap Futuro (Pós-Parte 4)

- Integração com SIEM/EDR
- Cenários colaborativos em tempo real
- Certificação interna automática
- API pública para integrações
- Suporte a múltiplas linguagens
- White-label para parceiros

---

**Contato:** equipe de segurança e treinamento
