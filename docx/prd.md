# SOC Training Simulator — Product Requirements Document (PRD)

Última atualização: 2026-02-11

## 1. Sumário executivo

O **SOC Training Simulator** é uma plataforma educacional para analistas de segurança que usa dados reais do AbuseIPDB para criar cenários de treinamento práticos. A solução simula incidentes baseados em IPs maliciosos conhecidos, fornece uma interface de investigação interativa e aplica gamificação com pontuação baseada em velocidade e precisão. O objetivo é melhorar habilidades investigativas, reduzir tempo de detecção/resposta e aumentar a confiança de equipes SOC por meio de exercícios repetíveis e mensuráveis.

## 2. Objetivos do produto

- **Principal:** Prover um ambiente seguro e realista para treinar analistas SOC usando dados reais de ameaças.
- **Secundários:** reduzir tempo médio de investigação, padronizar práticas de análise, facilitar avaliação de desempenho e oferecer material para certificação interna.

## 3. Escopo

- Incluir integração com AbuseIPDB para ingestão de eventos/insights de IPs maliciosos.
- Gerar cenários simulados (incidentes) baseados em IPs reais e metadados (timestamps, ataques observados, reputação).
- Workspace de investigação com evidências simuladas (logs, conexões, WHOIS, geolocalização, tráfego de rede simplificado).
- Sistema de gamificação: pontuação, tempos, precisão, leaderboard e badges.
- Painel administrativo para criar/editar cenários, revisar resultados e ajustar parâmetros de dificuldade.
- Mecanismos de anonimização/cache para não expor dados sensíveis.

Fora do escopo inicial: integrações com ferramentas EDR/SIEM complexas (fase posterior), suporte a ingestão massiva de logs do cliente.

## 4. Personas

- **Analista Júnior:** quer prática guiada e feedback. Foco: aprender passos básicos.
- **Analista Sênior:** busca cenários complexos e métricas de eficiência. Foco: decisões rápidas e precisão.
- **Treinador/Instrutor:** cria cenários, monitora progresso e avalia resultados.
- **Manager/Team Lead:** quer relatórios de desempenho e métricas de melhoria da equipe.

## 5. Principais casos de uso

1. Analista inicia um cenário, investiga eventos e submete um relatório de conclusão.
2. Plataforma avalia automaticamente precisão (itens identificados corretamente) e tempo até detecção/resposta.
3. Instrutor cria um novo cenário usando IPs do AbuseIPDB e define objetivo/dificuldade.
4. Manager visualiza leaderboard e relatórios agregados por equipe/usuário.

## 6. Requisitos de usuário (user stories)

- Como analista, quero um ambiente que me apresente evidências reais/realistas para praticar investigações.
- Como analista, quero feedback imediato sobre decisões críticas (falso positivo/negativo) para aprender.
- Como instrutor, quero criar cenários com IPs e variar parâmetros (ruído, tempo, pistas).
- Como manager, quero métricas agregadas para avaliar progresso da equipe.

## 7. Requisitos funcionais

F1. Ingestão de dados: integrar com AbuseIPDB API para obter lista de IPs maliciosos, categorias e metadados.
F2. Gerador de cenários: combinar IPs com templates de incidentes (ex.: scanning, brute-force, C2) e artefatos (logs, conexões) para criar exercícios.
F3. Workspace de investigação: exibir timeline, evidências (simuladas), ferramentas de enriquecimento (WHOIS, geolocalização, pDNS) e área para conclusões.
F4. Avaliação automática: comparar respostas do analista com o gabarito do cenário e calcular pontuação.
F5. Gamificação: calcular pontuação por velocidade, precisão e uso de técnicas recomendadas; manter leaderboard e badges.
F6. Painel administrativo: criar/editar/ativar/desativar cenários, ver resultados e exportar relatórios CSV/PDF.
F7. Autenticação e autorização: suporte SSO (SAML/OAuth2) e roles (analista, instrutor, admin).
F8. Logging e auditoria: registrar ações do usuário para auditoria e replay de sessões.

## 8. Requisitos não-funcionais

N1. Segurança: proteção de segredos/keys, comunicação TLS, práticas OWASP para frontend/backend.
N2. Privacidade: anonimização de dados sensíveis; políticas de retenção configuráveis.
N3. Escalabilidade: suportar concorrentemente uma turma (200+ usuários) com latência aceitável (<300ms para ações interativas).
N4. Confiabilidade: disponibilidade >= 99.5% para o modo treinamento (SLA interno).
N5. Observabilidade: métricas de uso, erros e performance expostas via Prometheus/Grafana.
N6. Testabilidade: cenários com gabarito testável e testes E2E para fluxos principais.

## 9. Integração com AbuseIPDB e dados

- Uso da AbuseIPDB API para busca de IPs com reputação, categorias e histórico.
- Modo de operação:
  - Periodic fetch: obter feed de IPs populares para criar cenários.
  - On-demand: instrutor escolhe IP e puxa dados ao criar cenário.
- Restrições: rate limits da API devem ser respeitados; implementar cache local com TTL configurável.
- Sanitização: não inserir dados que exponham informações sensíveis de terceiros; logs gerados devem ser sintéticos combinados com metadados reais (reputação, timestamp aproximado).

## 10. Fluxos e UX

- Fluxo do Analista:
  1. Seleciona um cenário (ou modo aleatório).
  2. Visualiza brief do incidente e objetivos (ex.: identificar IPs comprometidos, recomendar mitigação).
  3. Explora timeline e evidências; usa ferramentas de enriquecimento.
  4. Marca artefatos como “confirmado”, “falso positivo” ou “investigar mais”.
  5. Submete relatório final; recebe pontuação e feedback detalhado.
- Fluxo do Instrutor/Admin:
  1. Cria cenário: escolhe IP(s) (do AbuseIPDB ou custom), template de ataque, nível de ruído e tempo limite.
  2. Publica cenário para turmas.
  3. Revê submissões e ajusta gabarito/weights se necessário.

## 11. Gamificação e regras de pontuação

- Componentes de pontuação:
  - Precisão (P): % de artefatos corretamente classificados.
  - Velocidade (T): tempo até submissão comparado com um baseline.
  - Acurácia de decisão crítica (C): identificação correta de IPs críticos (maior peso).
- Fórmula exemplo: Score = 0.6 _ P + 0.3 _ (1 - min(T/T_baseline,1)) + 0.1 \* C
- Sistema de badges: "Rapid Responder", "Forensic Pro", "Zero False Positives".
- Leaderboard: por usuário, por time, por cenário; histórico de performances.

## 12. Métricas e KPIs

- Tempo médio de investigação (MTTI) por cenário.
- Taxa de precisão média por turma e por cenário.
- Número de cenários concluídos por usuário/mês.
- Evolução de desempenho (tendência) por usuário.

## 13. Arquitetura técnica (alto nível)

- Componentes:
  - Frontend SPA (React/Vue) com workspace de investigação.
  - Backend (API REST/GraphQL) gerenciando cenários, avaliações e integração AbuseIPDB.
  - Banco de dados relacional para usuários/cenários/resultado (Postgres).
  - Cache e filas (Redis, RabbitMQ) para ingestão e geração de cenários.
  - Armazenamento de logs e evidências (objet storage S3-compatible).
  - Observability (Prometheus, Grafana, ELK).

  ### Stack tecnológica (escolha preferida)
  - **Linguagem / Backend:** Python
  - **Framework web:** Flask
  - **Templates / Server-side rendering:** Jinja
  - **Frontend / Estilos:** Tailwind CSS via CDN
  - **Banco / BaaS:** Supabase (Postgres gerenciado, autenticação e storage)

  Motivação: essa stack permite desenvolvimento rápido de protótipos e produção com custo operacional reduzido; Supabase oferece compatibilidade com Postgres e autenticação pronta, enquanto Flask + Jinja mantêm a aplicação simples e testável. Tailwind via CDN acelera o desenvolvimento de UI sem adicionar complexidade de build no MVP.

## 14. Modelo de dados (essencial)

- `users` (id, nome, email, role)
- `scenarios` (id, título, descrição, dificuldade, gabarito, parâmetros)
- `artifacts` (id, scenario_id, tipo, conteúdo_simulado, evidência_meta)
- `submissions` (id, user_id, scenario_id, decisions, tempo, score)
- `abuseipdb_cache` (ip, reputacao, categorias, last_checked)

## 15. Segurança, privacidade e conformidade

- Não armazenar dados PII desnecessários; criptografar dados sensíveis em repouso.
- Chaves de API da AbuseIPDB guardadas em secret manager; rotacionáveis.
- Consentimento: se usar dados de clientes em cenários, obter consentimento explícito.
- Revisões regulares de segurança e testes de penetração em lançamentos críticos.

## 16. Testes e QA

- Testes unitários e integração para backend e frontend.
- Testes E2E cobrem criação de cenário, execução do analista e avaliação automática.
- Testes de performance para simular 200+ usuários simultâneos.

## 17. Roadmap e milestones (sugestão)

MVP (0-3 meses):

- Integração básica com AbuseIPDB (cache + fetching).
- Gerador simples de cenários com gabarito.
- Workspace de investigação minimal e avaliação automática.
- Sistema básico de pontuação e leaderboard.

Fase 2 (3-6 meses):

- Painel administrativo avançado.
- Templates de treino e currículos (módulos).
- Integrações SSO e relatórios exportáveis.

Fase 3 (6-12 meses):

- Integrações com SIEM/EDR (opcional), cenários colaborativos, suporte a turmas grandes e certificação interna.

## 18. Riscos e mitigações

- Dependência de AbuseIPDB (rate limits/indisponibilidade): implementar cache robusto e fallback para IPs históricos.
- Risco de exposição de dados sensíveis: aplicar sanitização e geração de evidências sintéticas.
- Usuários confundidos por realismo excessivo: oferecer modos "guiado" e "livre".

## 19. Critérios de sucesso

- Adoção: X equipes/testers no primeiro trimestre após lançamento.
- Melhoria de skills: redução do MTTI médio em 20% após 3 meses de uso.
- Engajamento: >70% dos usuários completam pelo menos 3 cenários por mês.

## 20. Apêndice

- Glossário: SOC, MTTI, EDR, SIEM, AbuseIPDB.
- Referências: AbuseIPDB API docs, OWASP Top 10, frameworks pedagógicos (spaced repetition aplicável a treino técnico).

---

Contato do produto: equipe de segurança e treinamento (definir e-mail interno)
