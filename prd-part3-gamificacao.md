# SOC Training Simulator — Parte 3: Gamificação e Avaliação

**Documento de Requisitos do Produto - Versão 1.0**  
**Data:** 2026-02-11  
**Pré-requisito:** Partes 1 e 2 concluídas

## 1. Sumário executivo (Parte 3)

Esta terceira parte implementa o sistema de gamificação e avaliação automática, transformando o workspace de investigação em uma experiência gamificada com pontuação, feedback imediato e acompanhamento de progresso.

## 2. Objetivos da Parte 3

- Implementar sistema de avaliação automática de submissões
- Criar mecânicas de gamificação (pontuação, badges, levels)
- Desenvolver leaderboards e rankings
- Fornecer feedback detalhado ao analista
- Implementar tracking de progresso por usuário

## 3. Escopo da Parte 3

### Incluído
- Sistema de avaliação automática
- Cálculo de pontuação (precisão, velocidade, critical decisions)
- Badges e achievements
- Leaderboards (global, por time, por cenário)
- Feedback detalhado pós-submissão
- Tracking de progresso individual
- Histórico de performances

### Não incluído nesta fase
- Painel administrativo completo (Parte 4)
- SSO avançado (Parte 4)
- Relatórios exportáveis (Parte 4)

## 4. Modelo de Dados (Parte 3)

### Tabela: submissions
```sql
CREATE TABLE submissions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  scenario_id UUID NOT NULL REFERENCES scenarios(id),
  started_at TIMESTAMP NOT NULL,
  submitted_at TIMESTAMP NOT NULL,
  time_spent_seconds INT NOT NULL,
  artifacts_marked JSONB NOT NULL, -- {artifact_id: status}
  conclusions JSONB, -- {pergunta: resposta}
  score_precision DECIMAL(5,2),
  score_speed DECIMAL(5,2),
  score_critical DECIMAL(5,2),
  total_score DECIMAL(5,2) CHECK (total_score >= 0 AND total_score <= 100),
  feedback JSONB, -- feedback detalhado gerado
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_submissions_user ON submissions(user_id);
CREATE INDEX idx_submissions_scenario ON submissions(scenario_id);
CREATE INDEX idx_submissions_date ON submissions(submitted_at);
```

### Tabela: scenario_answer_keys
```sql
CREATE TABLE scenario_answer_keys (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  scenario_id UUID NOT NULL REFERENCES scenarios(id),
  artifact_id UUID NOT NULL REFERENCES scenario_artifacts(id),
  expected_status VARCHAR(20) NOT NULL, -- confirmed, false_positive, investigating
  pontos INT DEFAULT 10,
  is_critical BOOLEAN DEFAULT FALSE,
  feedback_if_wrong TEXT,
  UNIQUE(scenario_id, artifact_id)
);

CREATE INDEX idx_answer_keys_scenario ON scenario_answer_keys(scenario_id);
```

### Tabela: user_progress
```sql
CREATE TABLE user_progress (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  total_scenarios_completed INT DEFAULT 0,
  total_points DECIMAL(10,2) DEFAULT 0,
  average_score DECIMAL(5,2) DEFAULT 0,
  average_time_seconds INT DEFAULT 0,
  current_level VARCHAR(20) DEFAULT 'novice',
  current_xp DECIMAL(10,2) DEFAULT 0,
  last_activity TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_user_progress_user ON user_progress(user_id);
```

### Tabela: badges
```sql
CREATE TABLE badges (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  nome VARCHAR(100) NOT NULL,
  descricao TEXT NOT NULL,
  icone VARCHAR(100), -- path ou nome do ícone
  criterio_type VARCHAR(50) NOT NULL, -- scenarios_completed, score, time, etc
  criterio_value JSONB NOT NULL, -- {threshold: 10, type: 'gte'}
  pontos_bonus INT DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Badges padrão do sistema
INSERT INTO badges (nome, descricao, icone, criterio_type, criterio_value, pontos_bonus) VALUES
('Rapid Responder', 'Completou cenário em menos de 5 minutos', 'clock', 'time_under', '{"seconds": 300, "scenario_count": 1}', 15),
('Forensic Pro', 'Atingiu 100% de precisão em 5 cenários', 'microscope', 'precision', '{"percentage": 100, "count": 5}', 50),
('Zero False Positives', 'Não marcou falsos positivos em 10 cenários', 'check-circle', 'false_positives', '{"max_fp": 0, "count": 10}', 30),
('Centurion', 'Completou 100 cenários', 'trophy', 'scenarios_completed', '{"count": 100}', 100),
('Night Owl', 'Completou cenário às 3AM', 'moon', 'time_of_day', '{"hour_min": 2, "hour_max": 5}', 10);
```

### Tabela: user_badges
```sql
CREATE TABLE user_badges (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  badge_id UUID NOT NULL REFERENCES badges(id),
  earned_at TIMESTAMP DEFAULT NOW(),
  scenario_id UUID REFERENCES scenarios(id), -- cenário que gerou o badge
  UNIQUE(user_id, badge_id)
);

CREATE INDEX idx_user_badges_user ON user_badges(user_id);
```

### Tabela: leaderboard_entries
```sql
CREATE TABLE leaderboard_entries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  period_type VARCHAR(20) NOT NULL, -- daily, weekly, monthly, all_time
  period_start DATE,
  period_end DATE,
  total_score DECIMAL(10,2) NOT NULL,
  scenarios_completed INT DEFAULT 0,
  rank_position INT,
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(user_id, period_type, period_start, period_end)
);

CREATE INDEX idx_leaderboard_period ON leaderboard_entries(period_type, period_start, period_end);
CREATE INDEX idx_leaderboard_rank ON leaderboard_entries(period_type, period_start, period_end, rank_position);
```

## 5. Sistema de Avaliação Automática

### Algoritmo de Avaliação

```python
def evaluate_submission(submission, answer_key):
    results = {
        'correct': 0,
        'incorrect': 0,
        'missed': 0,
        'false_positives': 0,
        'artifact_details': []
    }
    
    for artifact in answer_key:
        user_status = submission.artifacts_marked.get(str(artifact.artifact_id))
        expected = artifact.expected_status
        
        if user_status == expected:
            results['correct'] += 1
            results['artifact_details'].append({
                'artifact_id': artifact.artifact_id,
                'status': 'correct',
                'points': artifact.pontos
            })
        elif user_status is None:
            results['missed'] += 1
            results['artifact_details'].append({
                'artifact_id': artifact.artifact_id,
                'status': 'missed',
                'points': 0,
                'expected': expected
            })
        else:
            results['incorrect'] += 1
            results['false_positives'] += 1 if user_status == 'false_positive' and expected == 'confirmed' else 0
            results['artifact_details'].append({
                'artifact_id': artifact.artifact_id,
                'status': 'incorrect',
                'points': -artifact.pontos if user_status == 'confirmed' and expected == 'false_positive' else 0,
                'expected': expected,
                'user_gave': user_status
            })
    
    return results
```

### Componentes de Pontuação

#### Precisão (P)
```
P = (Artefatos Corretamente Classificados) / (Total de Artefatos) × 100

Artefatos incluem:
- IPs confirmados como maliciosos
- IPs marcados como falsos positivos
- Artefatos marcados para investigar
```

#### Velocidade (T)
```
T_baseline = tempo médio do cenário para todos os analistas
T_ratio = T_baseline / T_analista

Score_Velocidade = min(1.3, T_ratio) × 100  -- bônus até 30% mais rápido
```

#### Decisões Críticas (C)
```
C = Σ(Pontos Artefatos Críticos Corretos) / Σ(Pontos Totais Artefatos Críticos) × 100

Artefatos críticos: IPs C2, domínios de phishing, payloads maliciosos
```

#### Pontuação Total
```
Score = (0.50 × P) + (0.30 × T) + (0.20 × C)

Escala: 0-100
Classificação:
- 90-100: Excelente
- 75-89: Bom
- 60-74: Regular
- 40-59: Precisa Melhoria
- 0-39: Insuficiente
```

## 6. Sistema de Gamificação

### Níveis e XP

```python
LEVELS = {
    'novice': {'xp_required': 0, 'title': 'Novato'},
    'junior': {'xp_required': 100, 'title': 'Analista Júnior'},
    'intermediate': {'xp_required': 300, 'title': 'Analista Intermediário'},
    'senior': {'xp_required': 600, 'title': 'Analista Sênior'},
    'expert': {'xp_required': 1000, 'title': 'Especialista'},
    'master': {'xp_required': 2000, 'title': 'Mestre SOC'},
    'legend': {'xp_required': 5000, 'title': 'Lenda da Segurança'}
}

def calculate_xp_earned(scenario, submission):
    base_xp = 50
    bonus_xp = 0
    
    # Bônus por pontuação
    if submission.total_score >= 90:
        bonus_xp += 30
    elif submission.total_score >= 75:
        bonus_xp += 20
    elif submission.total_score >= 60:
        bonus_xp += 10
    
    # Bônus por velocidade
    if submission.time_spent_seconds < scenario.time_limit_seconds * 0.5:
        bonus_xp += 15
    
    # Bônus por precisão
    if submission.score_precision >= 95:
        bonus_xp += 20
    
    return base_xp + bonus_xp
```

### Badges por Categoria

#### Desempenho
| Badge | Requisito | XP Bonus |
|-------|-----------|----------|
| Estrela do Mês | Top 1 mensal | 100 |
| Dez em Dez | 10 cenários com 100% | 75 |
| Consistent | 5 cenários com nota >80 | 40 |

#### Velocidade
| Badge | Requisito | XP Bonus |
|-------|-----------|----------|
| Relâmpago | <5min em cenário medium | 20 |
| Veloz | <10min em cenário hard | 25 |
| Sem Pause | 3 cenários em 1 hora | 30 |

#### Precisão
| Badge | Requisito | XP Bonus |
|-------|-----------|----------|
| Olho de Águia | 100% em 3 cenários hard | 50 |
| Mira Perfeita | Zero FP em 10 cenários | 35 |
| Detalhista | Identificou todos os IPs críticos | 30 |

#### Engajamento
| Badge | Requisito | XP Bonus |
|-------|-----------|----------|
| Primeiros Passos | Primeiro cenário | 10 |
| Dedicação | 7 dias consecutivos | 50 |
| Veterano | 30 dias ativos | 100 |

### Leaderboards

#### Tipos de Leaderboard
1. **Global Geral** - Todos os tempos
2. **Mensal** - Período atual
3. **Semanal** - Período atual
4. **Diário** - Hoje
5. **Por Equipe** - Agrupado por team_id (futuro)
6. **Por Cenário** - Rankings específicos

#### Critérios de Ranking
```
Ranking = (Total Pontos × 0.4) + (Cenários Completados × 20) + (XP Total × 0.2) + (Badges × 10)
```

## 7. Feedback ao Analista

### Feedback Imediato (Pós-Submissão)

```json
{
  "status": "success",
  "score": {
    "total": 82.5,
    "precision": 85.0,
    "speed": 75.0,
    "critical": 90.0
  },
  "classification": "Bom",
  "time_spent": "12:34",
  "xp_earned": 75,
  "level_up": {
    "current": "junior",
    "next": "intermediate",
    "xp_needed": 125
  },
  "badges_earned": ["Rapid Responder"],
  "feedback_details": {
    "correct_artifacts": 17,
    "incorrect_artifacts": 3,
    "missed_artifacts": 2,
    "false_positives": 1
  }
}
```

### Relatório Detalhado

```
┌─────────────────────────────────────────────────────────────┐
│ RELATÓRIO DE INVESTIGAÇÃO                                   │
├─────────────────────────────────────────────────────────────┤
│ Cenário: Brute Force SSH Attack                            │
│ Data: 2025-02-11                                           │
│ Tempo: 12:34                                               │
│ Pontuação: 82.5/100 (Bom)                                   │
├─────────────────────────────────────────────────────────────┤
│ PRECISÃO                                                    │
│ ✓ IPs confirmados corretamente: 17/22                       │
│ ✗ Falsos positivos: 1                                      │
│ ✗ Artefatos não identificados: 2                          │
├─────────────────────────────────────────────────────────────┤
│ VELOCIDADE                                                  │
│ ⏱️ Tempo: 12:34 (baseline: 15:00)                          │
│ Bônus: +15% por estar acima do baseline                    │
├─────────────────────────────────────────────────────────────┤
│ DECISÕES CRÍTICAS                                          │
│ ✓ Identificou IP C2 principal                              │
│ ✓ Classificou corretamente domínio de C&C                   │
│ ✗ Não marcou segundo IP como malicioso                      │
├─────────────────────────────────────────────────────────────┤
│ FEEDBACK DETALHADO                                          │
│ 1. IP 185.220.101.42 foi corretamente identificado        │
│    como malicioso e crítico                                 │
│ 2. IP 45.33.32.156 foi marcado como falso positivo,        │
│    mas era malicioso - revisar indicadores de ameaça       │
│ 3. Domínio fast-c2.com não foi investigado                │
│    - Este domínio tem histórico de C2 documentado         │
└─────────────────────────────────────────────────────────────┘
```

### Dicas de Melhoria

Baseado em erros comuns:
- "Para cenários de brute force, sempre verifique todos os IPs
  que tentaram login, não apenas o primeiro"
- "Domínios com registro recente (<30 dias) são frequentemente
  usados em campanhas de phishing"
- "Considere a geolocalização como pista, não como prova -
  attackers usam VPNs/proxies"

## 8. API Endpoints (Parte 3)

### Submissões
- `POST /api/submissions` - Criar nova submissão
- `GET /api/submissions/{id}` - Ver detalhes
- `GET /api/submissions/user/{user_id}` - Histórico do usuário
- `GET /api/submissions/scenario/{scenario_id}` - Todas para cenário

### Avaliação
- `POST /api/evaluate` - Avaliar submissão
- `GET /api/evaluate/{submission_id}/feedback` - Feedback detalhado

### Gamificação
- `GET /api/gamification/user/{user_id}/progress` - Progresso
- `GET /api/gamification/user/{user_id}/badges` - Badges
- `GET /api/gamification/user/{user_id}/level` - Nível atual
- `POST /api/gamification/badges/claim` - Claim badge

### Leaderboards
- `GET /api/leaderboard` - Leaderboard padrão
- `GET /api/leaderboard?type=weekly` - Leaderboard semanal
- `GET /api/leaderboard?type=user&user_id=xxx` - Ranking específico

### Relatórios
- `GET /api/reports/user/{user_id}/performance` - Performance
- `GET /api/reports/user/{user_id}/trends` - Tendências
- `GET /api/reports/scenario/{scenario_id}/stats` - Stats do cenário

## 9. Frontend Components (Parte 3)

```
components/
├── Gamification/
│   ├── ScoreCard.vue
│   ├── ProgressBar.vue
│   ├── LevelBadge.vue
│   ├── XpDisplay.vue
│   └── BadgeNotification.vue
├── Leaderboard/
│   ├── LeaderboardTable.vue
│   ├── LeaderboardFilters.vue
│   └── RankCard.vue
├── Feedback/
│   ├── FeedbackSummary.vue
│   ├── DetailedReport.vue
│   ├── ImprovementTips.vue
│   └── ComparisonChart.vue
└── History/
    ├── SubmissionHistory.vue
    ├── PerformanceChart.vue
    └── TrendsAnalysis.vue
```

## 10. Critérios de Conclusão (Parte 3)

- [ ] Sistema de avaliação automática operacional
- [ ] Cálculo de pontuação implementado (precisão, velocidade, critical)
- [ ] Sistema de XP e níveis funcionando
- [ ] Badges implementados e award system operacional
- [ ] Leaderboards (global, semanal, mensal)
- [ ] Feedback detalhado ao analista
- [ ] Tracking de progresso individual
- [ ] Histórico de performances
- [ ] Testes de avaliação e gamificação

## 11. Próximos Passos

Após conclusão da Parte 3, avançar para:
- **Parte 4:** Painel Administrativo e Funcionalidades Avançadas

---

**Contato:** equipe de segurança e treinamento
