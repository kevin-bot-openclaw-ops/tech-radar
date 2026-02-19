# skills-demand.md — Job Market Demand Tracking

**Source of truth for demand counts in radar.json.**
All numbers must come from actual job scan results. No fabrication.

**Updated:** 2026-02-19
**Scanner:** job-search-tracker (Brave Search, euremotejobs.com + remoteok.com) + targeted search (TASK-013)
**Scan window:** Feb 2026 (TASK-002 run + TASK-013 verification scan)

---

## Methodology

- Demand = number of distinct job postings mentioning the skill
- Only remote-eligible roles counted (REMOTE_REJECT_PHRASES filter active)
- Minimum score threshold: 5 (below this, jobs filtered before reaching demand tracking)
- Skills not appearing in scan = demand 0 (not fabricated as "likely relevant")

---

## Confirmed Demand Counts (Feb 2026 scan)

| Skill | Demand | Notes |
|-------|--------|-------|
| RAG Pipeline | 7 | Highest signal — appears across ML Platform, AI Engineer, Senior ML roles |
| Azure | 5 | Dominant cloud in EU AI/ML market |
| Agentic AI Systems | 3 | "LLM agents", "agentic workflows" in JDs |
| AI Model Evaluation / RLHF | 3 | "model evaluation", "RLHF", "benchmark design" |
| LLM APIs | 3 | "OpenAI API", "Anthropic", "LLM integration" |
| LLM Inference Infrastructure | 3 | "vLLM", "TGI", "model serving infrastructure" |
| Python | 3 | Required across all ML roles |
| MLOps | 2 | "MLOps engineer", "model deployment pipeline" |
| MLflow | 2 | "experiment tracking", "MLflow", "model registry" |
| Vector Databases | 2 | "vector store", "embedding database", "Pinecone/Chroma" |
| LLM Prompt Engineering | 2 | "prompt engineering", "context design" |
| AI-Assisted Development | 2 | "AI-assisted development", "Copilot" |
| Make.com / n8n | 2 | "workflow automation", "n8n", "Make.com" |
| AWS | 2 | Cloud infra — less prevalent than Azure in EU |
| Kubernetes | 2 | Container orchestration in ML contexts |
| MCP (Model Context Protocol) | 1 | Strategic override — 1 scan appearance, early-mover signal |
| NLP Embeddings | 1 | "sentence transformers", "text embeddings" |
| LLM Integration Patterns | 1 | "LLM integration", "enterprise LLM" |
| LLM Fine-tuning / LoRA | 1 | "fine-tuning", "LoRA" |
| Ollama | 1 | Local LLM deployment |
| Pinecone | 1 | Managed vector DB |
| BigQuery | 1 | GCP data platform |
| OpenTelemetry | 1 | Observability |
| Grafana | 1 | Monitoring dashboards |
| TypeScript | 1 | (Low relevance — AI agent tooling context) |
| Kafka / Event Streaming | 1 | Streaming ML pipelines |
| Spark | 1 | (Low relevance — data engineering, not ML eng) |
| LangChain4j | 1 | Java LLM framework — bridge skill; demand verified TASK-013 (niche, EU remote: 1 mention) |
| Spring AI | 1 | Java AI framework — bridge skill; demand verified TASK-013 (Indeed: ~8 global, EU remote: 1) |
| C++ | 1 | Elastic role (hard gap) |
| Go (Golang) | 1 | Xebia role (hard gap) |
| React / Node.js | 1 | Full-stack (avoid) |
| PyTorch | 2 | Research roles (not target) |
| Kubeflow | 1 | ML orchestration (not target over MLflow) |
| Banking Domain | 1 | Finance AI context mentions |
| Chatbot Integration | 1 | "enterprise chatbot", "conversational AI" |
| Solution Architecture | 1 | Senior/Staff level roles |
| FastAPI | 2 | Python web/API for ML serving |
| CI/CD | 2 | DevOps component in MLOps JDs |
| DevOps Practices | 1 | MLOps-adjacent |
| TensorFlow | 1 | Research-adjacent (not target) |
| HubSpot API | 0 | CRM — not strategic |
| EHR Systems | 0 | Healthcare — not target |
| TCP/IP Networking | 0 | Low-level infra — not relevant |
| Cognigy / Kore.ai | 0 | Vendor-specific — not strategic |
| Java | 0 | Not appearing in AI/ML job scans (backend context only) |
| REST API Design | 0 | Table stakes — not listed as required skill in JDs |
| SQL | 0 | Foundational — not listed as differentiator in target JDs |
| Spring Boot | 0 | Legacy framing — not in AI/ML JDs |
| Docker | 0 | Table stakes — not counted as differentiator |
| Microservices | 0 | Architecture pattern — not in AI JDs |
| Terraform | 0 | IaC — not differentiating for AI/ML |
| JavaScript | 0 | Not relevant for target roles |

---

## TASK-013 — Verification Complete (2026-02-19)

Spring AI and LangChain4j demand=1 verified via targeted Brave Search scan:
- Spring AI: Indeed shows ~8 global jobs; EU remote senior: 1 explicit mention (bridge category confirmed)
- LangChain4j: Very niche in EU remote market; 1 mention (not to be confused with Python LangChain — 245 jobs)
- Both remain at demand=1; both confirmed as bridge category (Java + AI intersection)
- No ring changes required; radar.json is accurate
