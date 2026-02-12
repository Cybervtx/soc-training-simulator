# SOC Training Simulator — Parte 2: Workspace de Investigação

**Documento de Requisitos do Produto - Versão 1.0**  
**Data:** 2026-02-11  
**Pré-requisito:** Parte 1 concluída

## 1. Sumário executivo (Parte 2)

Esta segunda parte foca no core educacional do sistema: o workspace de investigação onde os analistas praticarão suas habilidades. Inclui gerador de cenários, evidências simuladas e ferramentas de enriquecimento.

## 2. Objetivos da Parte 2

- Implementar gerador de cenários baseados em dados reais AbuseIPDB
- Criar workspace de investigação interativo
- Desenvolver sistema de evidências simuladas (logs, WHOIS, geolocalização)
- Implementar ferramentas de enriquecimento de dados
- Criar interface para exploração de timeline de incidentes

## 3. Escopo da Parte 2

### Incluído
- Gerador de cenários (templates de ataques)
- Workspace de investigação SPA
- Sistema de evidências simuladas
- Ferramentas de enriquecimento (WHOIS, pDNS, geolocalização)
- Timeline interativa de eventos
- Interface de análise de artefatos

### Não incluído nesta fase
- Sistema de gamificação completo (Parte 3)
- Painel administrativo (Parte 4)
- Avaliação automática (Parte 3)

## 4. Modelo de Dados (Parte 2)

### Tabela: scenarios
```sql
CREATE TABLE scenarios (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  titulo VARCHAR(200) NOT NULL,
  descricao TEXT,
  dificuldade VARCHAR(20), -- easy, medium, hard
  tipo_incidente VARCHAR(50), -- scanning, brute-force, c2, malware, phishing
  created_by UUID REFERENCES users(id),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  is_active BOOLEAN DEFAULT TRUE
);
```

### Tabela: scenario_artifacts
```sql
CREATE TABLE scenario_artifacts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  scenario_id UUID NOT NULL REFERENCES scenarios(id),
  tipo VARCHAR(50), -- ip, domain, url, file_hash, email
  valor VARCHAR(500) NOT NULL,
  is_malicious BOOLEAN DEFAULT FALSE,
  is_critical BOOLEAN DEFAULT FALSE,
  metadata JSONB, -- dados enriquecidos simulados
  pontos INT DEFAULT 10
);

CREATE INDEX idx_scenario_artifacts_scenario ON scenario_artifacts(scenario_id);
```

### Tabela: scenario_timeline
```sql
CREATE TABLE scenario_timeline (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  scenario_id UUID NOT NULL REFERENCES scenarios(id),
  timestamp TIMESTAMP NOT NULL,
  evento VARCHAR(100) NOT NULL,
  descricao TEXT,
  artefatos_relacionados JSONB, -- array de artifact IDs
  prioridade INT DEFAULT 1 -- 1=baixa, 2=média, 3=alta
);

CREATE INDEX idx_scenario_timeline_scenario ON scenario_timeline(scenario_id);
CREATE INDEX idx_scenario_timeline_timestamp ON scenario_timeline(scenario_id, timestamp);
```

### Tabela: scenario_templates
```sql
CREATE TABLE scenario_templates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  nome VARCHAR(100) NOT NULL,
  tipo_incidente VARCHAR(50) NOT NULL,
  descricao TEXT,
  estrutura_base JSONB NOT NULL, -- template da timeline
  artefatos_base JSONB, -- artefatos típicos
  dificuldade_padrao VARCHAR(20),
  created_at TIMESTAMP DEFAULT NOW()
);
```

### Tabela: enriched_data_cache
```sql
CREATE TABLE enriched_data_cache (
  id SERIAL PRIMARY KEY,
  query_type VARCHAR(50) NOT NULL, -- whois, geolocation, pdns, etc
  query_value VARCHAR(500) NOT NULL,
  result_data JSONB NOT NULL,
  cached_at TIMESTAMP DEFAULT NOW(),
  expires_at TIMESTAMP NOT NULL,
  UNIQUE(query_type, query_value)
);

CREATE INDEX idx_enriched_data_cache_query ON enriched_data_cache(query_type, query_value);
```

## 5. Gerador de Cenários

### Templates de Incidentes Suportados

1. **Port Scanning**
   - IPs de origem maliciosos
   - Múltiplas portas abertas
   - Padrão de scan reconocible

2. **Brute Force SSH**
   - Múltiplas tentativas de login
   - IP malicioso conhecido
   - Credenciais fracas utilizadas

3. **C2 Communication**
   - Conexões periódicas
   - Domínios/CDNs suspeitos
   - Padrão de beacon identificável

4. **Malware Distribution**
   - Downloads de URLs maliciosas
   - Hashes de arquivos
   - Conexões de rede suspeitas

5. **Phishing Campaign**
   - Emails de phishing
   - URLs falsas
   - Links para payloads

### Algoritmo de Geração

```python
def generate_scenario(template, abuseipdb_data, difficulty):
    # 1. Selecionar IP(s) maliciosos do AbuseIPDB
    # 2. Injetar na timeline base do template
    # 3. Ajustar ruído baseado em dificuldade
    # 4. Gerar artefatos relacionados
    # 5. Calcular gabarito implícito
    return Scenario(...)
```

### Parâmetros de Dificuldade

| Parâmetro | Easy | Medium | Hard |
|-----------|------|--------|------|
| Ruído nos logs | Mínimo | Moderado | Alto |
| Tempo limite | Ilimitado | 30 min | 15 min |
| Pistas explícitas | Sim | Parciais | Não |
| Quantidade de artefatos | 3-5 | 5-10 | 10-20 |

## 6. Workspace de Investigação

### Layout da Interface

```
┌─────────────────────────────────────────────────────────┐
│  Header: Scenario Title | Timer | User Info            │
├──────────┬──────────────────────────────────────────────┤
│          │  Panel: Incident Brief                       │
│  Menu    ├──────────────────────────────────────────────┤
│  - IPs   │  Panel: Timeline                            │
│  - Logs  │  [timestamp] Event 1                         │
│  - WHOIS │  [timestamp] Event 2                         │
│  - pDNS  │  ...                                        │
│          ├──────────────────────────────────────────────┤
│          │  Panel: Evidence Workspace                  │
│          │  [artifact] [tag: confirmed/fp/investigate] │
│          │  [artifact] ...                              │
├──────────┴──────────────────────────────────────────────┤
│  Footer: Actions | Submit | Notes                      │
└─────────────────────────────────────────────────────────┘
```

### Funcionalidades do Workspace

1. **Visualização de Timeline**
   - Scroll chronological
   - Filtros por tipo de evento
   - Highlight de eventos críticos
   - Zoom temporal

2. **Análise de Artefatos**
   - IP investigation
   - Domain lookup
   - URL analysis
   - File hash search

3. **Marcação de Evidências**
   - Status: confirmed, false_positive, investigating
   - Notas por artefato
   - Tags personalizáveis

4. **Ferramentas de Enriquecimento**

### WHOIS Simulado
```json
{
  "domain": "malicious-domain.com",
  "registrar": "NameCheap, Inc.",
  "created_date": "2024-01-15",
  "expires_date": "2025-01-15",
  "nameservers": ["ns1.cloudprovider.com", "ns2.cloudprovider.com"],
  "whois_server": "whois.namecheap.com"
}
```

### Geolocalização Simulada
```json
{
  "ip": "185.220.101.42",
  "country_code": "DE",
  "country_name": "Germany",
  "city": "Frankfurt",
  "latitude": 50.1109,
  "longitude": 8.6821,
  "isp": "Hetzner Online GmbH",
  "as_number": "AS24940"
}
```

### pDNS Simulado
```json
{
  "domain": "malicious-domain.com",
  "records": [
    {
      "type": "A",
      "value": "185.220.101.42",
      "first_seen": "2024-01-15",
      "last_seen": "2025-02-01"
    },
    {
      "type": "MX",
      "value": "mail.malicious-domain.com",
      "first_seen": "2024-01-20"
    }
  ]
}
```

### Logs Simulados

#### Firewall Log
```
2025-02-11T10:23:45Z DENY TCP 185.220.101.42:12345 -> 10.0.0.5:22
2025-02-11T10:23:46Z DENY TCP 185.220.101.42:12346 -> 10.0.0.5:22
2025-02-11T10:23:47Z DENY TCP 185.220.101.42:12347 -> 10.0.0.5:22
```

#### SSH Log
```
2025-02-11T10:25:01Z FAILED Password for root from 185.220.101.42
2025-02-11T10:25:03Z FAILED Password for admin from 185.220.101.42
2025-02-11T10:25:05Z FAILED Password for ubuntu from 185.220.101.42
```

#### DNS Query Log
```
2025-02-11T10:30:15Z QUERY A malware-c2.badssl.com -> 185.220.101.42
2025-02-11T10:30:45Z QUERY A malware-c2.badssl.com -> 185.220.101.42
2025-02-11T10:31:15Z QUERY A malware-c2.badssl.com -> 185.220.101.42
```

## 7. Fluxo do Usuário (Parte 2)

```
┌──────────────────────────────────────────────────────────────┐
│ 1. Analista seleciona cenário disponível                     │
│    ↓                                                          │
│ 2. Visualiza brief do incidente                              │
│    - Tipo de ataque                                          │
│    - IPs envolvidos                                          │
│    - Objetivos da investigação                               │
│    ↓                                                          │
│ 3. Explora timeline e evidências                             │
│    - Navega por eventos                                      │
│    - Usa ferramentas de enriquecimento                       │
│    - Marca artefatos como confirmados/FP                    │
│    ↓                                                          │
│ 4. Prepara relatório final                                   │
│    - Conclusões por artefato                                 │
│    - Recomendação de mitigação                               │
│    ↓                                                          │
│ 5. Salva progresso (opcional)                                │
│    ↓                                                          │
│ 6. Submete para avaliação (Parte 3)                          │
└──────────────────────────────────────────────────────────────┘
```

## 8. API Endpoints (Parte 2)

### Cenários
- `GET /api/scenarios` - Listar cenários disponíveis
- `GET /api/scenarios/{id}` - Detalhes de cenário
- `POST /api/scenarios` - Criar novo cenário (instructor+)
- `POST /api/scenarios/generate` - Gerar cenário automaticamente

### Artefatos
- `GET /api/scenarios/{id}/artifacts` - Listar artefatos
- `GET /api/artifacts/{id}/enrich` - Enriquecer artefato
- `PATCH /api/artifacts/{id}/status` - Atualizar status

### Timeline
- `GET /api/scenarios/{id}/timeline` - Listar timeline
- `GET /api/timeline/{id}` - Detalhes de evento

### Ferramentas de Investigação
- `GET /api/tools/whois?query={domain}` - WHOIS lookup
- `GET /api/tools/geoip?query={ip}` - Geolocalização
- `GET /api/tools/pdns?query={domain}` - DNS passivo
- `GET /api/tools/shodan?query={ip}` - Dados Shodan (simulado)

## 9. Frontend Components

### Vue.js Components Recomendados
```
components/
├── Layout/
│   ├── MainLayout.vue
│   ├── Header.vue
│   └── Sidebar.vue
├── Scenario/
│   ├── ScenarioList.vue
│   ├── ScenarioDetail.vue
│   └── ScenarioBrief.vue
├── Workspace/
│   ├── TimelineView.vue
│   ├── EvidencePanel.vue
│   ├── ArtifactCard.vue
│   └── ArtifactActions.vue
├── Investigation/
│   ├── IpAnalysis.vue
│   ├── DomainAnalysis.vue
│   ├── WhoisLookup.vue
│   └── GeolocationMap.vue
└── Common/
    ├── StatusBadge.vue
    └── LoadingSpinner.vue
```

## 10. Critérios de Conclusão (Parte 2)

- [x] Gerador de cenários funcional
- [x] Workspace de investigação com timeline interativa
- [x] Sistema de evidências simuladas operacional
- [x] Ferramentas de enriquecimento implementadas
- [x] Interface de análise de artefatos
- [x] Backend API completo para Parte 2
- [x] Testes de integração workspace

## 11. Próximos Passos

Após conclusão da Parte 2, avançar para:
- **Parte 3:** Gamificação e Avaliação Automática
- **Parte 4:** Painel Administrativo

---

**Contato:** equipe de segurança e treinamento
