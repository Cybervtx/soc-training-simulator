# SOC Training Simulator — Divisão do PRD

Este documento foi dividido em 4 partes para implementação gradativa.

## Estrutura dos Documentos

| Parte | Foco | Status | Arquivo |
|-------|------|--------|---------|
| 1 | Fundação (MVP Core) | A desenvolver | `prd-part1-fundacao.md` |
| 2 | Workspace de Investigação | Futuro | `prd-part2-workspace.md` |
| 3 | Gamificação e Avaliação | Futuro | `prd-part3-gamificacao.md` |
| 4 | Painel Admin e Avançado | Futuro | `prd-part4-admin.md` |

## Resumo por Parte

### Parte 1: Fundação (MVP Core)
- Arquitetura Flask + Supabase + Tailwind
- Integração AbuseIPDB (fetch + cache)
- Modelo de dados essencial
- Autenticação básica

### Parte 2: Workspace de Investigação
- Gerador de cenários
- Workspace de investigação SPA
- Sistema de evidências simuladas
- Ferramentas de enriquecimento (WHOIS, geolocalização, pDNS)

### Parte 3: Gamificação e Avaliação
- Sistema de avaliação automática
- Pontuação (precisão, velocidade, decisões críticas)
- Badges e achievements
- Leaderboards
- Feedback ao analista

### Parte 4: Painel Admin e Avançado
- Painel administrativo completo
- SSO (Google, Azure, Okta, SAML)
- Sistema de turmas e grupos
- Relatórios exportáveis (CSV, PDF)
- Logging e auditoria
- Módulos e currículos

## Próximos Passos

1. Revisar e aprovar **Parte 1: Fundação**
2. Iniciar implementação da Parte 1
3. Concluir Parte 1 antes de avançar para Parte 2

---

**Documento original:** `prd.md`
