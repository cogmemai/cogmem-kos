Below is a handoff-ready, detailed build spec for a new repo named cogmem-kos. It’s written so Windsurf can plan + scaffold + implement a working vertical slice on your existing OVH/Rancher/RKE cluster (Postgres + OpenSearch + Qdrant + Neo4j + SurrealDB already running).

You can paste this whole thing into Windsurf as the “project brief”.

⸻

cogmem-kos — Build Spec (Framework-Agnostic Knowledge OS Kernel)

0) Goal and non-goals

Goal

Build cogmem-kos as a framework-agnostic Knowledge Operating System kernel that provides:
	1.	Retrieval spine (search-first):

	•	Text search with highlight snippets + faceting (OpenSearch)
	•	Graph expansion + entity pages (Neo4j)
	•	Vector search (Qdrant)
	•	Optional “solo mode” using SurrealDB for all capabilities

	2.	Agent subsystem (write-path):

	•	Job/event model for ingestion + enrichment + indexing
	•	Agents are workers/daemons (not chat-first)
	•	Framework integrations are examples, not core dependencies

	3.	Public APIs:

	•	HTTP API (FastAPI) for CogMem UI + developer clients
	•	MCP server (optional milestone, but scaffold early)

Non-goals (v1)
	•	Building the CogMem frontend UI
	•	Implementing many connectors (Gmail/Notion/etc.) — start with file/chat ingestion stub
	•	Fine-grained ACL enforcement across all stores (basic tenant/user scoping only in v1)

⸻

1) Product shape / architecture

Modes

Enterprise mode (default): uses the existing cluster “best of breed”
	•	Postgres = admin/run logs/outbox
	•	OpenSearch = text search + highlighting + facets
	•	Neo4j = entity graph + provenance graph
	•	Qdrant = embeddings + semantic recall

Solo mode (optional): SurrealDB-only
	•	SurrealDB provides text-ish search + graph + vectors (capability-limited compared to OpenSearch)

Key principle (must enforce)

Core contracts must not import:
	•	langchain / semantic_kernel / crewai / autogen
	•	opensearch / neo4j / qdrant / surrealdb client packages
	•	fastapi

Frameworks + DB clients live behind providers/adapters.

⸻

2) Repository structure (must match)

Create this structure exactly (or extremely close):

cogmem-kos/
  README.md
  pyproject.toml
  .env.example
  docs/
    architecture/overview.md
    architecture/contracts.md
    architecture/retrieval-plans.md
    architecture/agents.md
    architecture/providers.md

  examples/
    enterprise/
      demo_search_first.py
      demo_entity_page.py
    integrations/
      langchain/demo_agent_calls_kos.py
      langgraph/demo_node_calls_kos.py
      crewai/demo_tool_calls_kos.py
      autogen/demo_context_injection.py

  src/
    kos/
      core/
        models/
          item.py
          passage.py
          entity.py
          artifact.py
          agent_action.py
          ids.py
        contracts/
          llm.py
          embeddings.py
          reranker.py
          stores/
            admin_store.py
            object_store.py
            outbox_store.py
            retrieval/
              text_search.py
              vector_search.py
              graph_search.py
              graph_vector_search.py
        events/
          event_types.py
          envelope.py
        jobs/
          job_types.py
          envelope.py
        planning/
          search_first.py
          wikipedia_page.py
          semantic_first.py
          provenance_explain.py
        util/
          config.py
          retry.py
          hashing.py

      kernel/
        config/settings.py
        registry/providers.py
        registry/agents.py
        runtime/outbox.py
        runtime/scheduler.py
        runtime/worker.py
        security/tenancy.py
        api/http/main.py
        api/http/routes/search.py
        api/http/routes/entities.py
        api/http/routes/items.py
        api/http/schemas/
        api/mcp/server.py
        api/mcp/tools/

      providers/
        postgres/
        opensearch/
        neo4j/
        qdrant/
        surrealdb/

      adapters/
        litellm/gateway.py
        langchain/ (optional later)
        semantic_kernel/ (optional later)

      agents/
        ingest/
        extract/
        enrich/
        index/
        curate/

      cli/
        main.py
        commands/
          init.py
          run_worker.py
          dev_server.py

  tests/
    unit/
    integration/


⸻

3) Core domain objects (canonical KOS objects)

Implement these as Pydantic v2 models (in kos/core/models/).

IDs
	•	kos_id: stable global id (string, UUID ok)
	•	tenant_id: string
	•	user_id: string
	•	source: enum/string (“files”, “chat”, “gmail”, “notion”, …)

Objects (minimum v1)

Item
	•	kos_id
	•	tenant_id, user_id
	•	source
	•	external_id (optional)
	•	title, content_text (raw extracted text)
	•	content_type (email/pdf/html/chat/etc.)
	•	created_at, updated_at
	•	metadata (dict)

Passage
	•	kos_id
	•	item_id
	•	tenant_id, user_id
	•	text
	•	span (start/end offsets optional)
	•	metadata

Entity
	•	kos_id
	•	tenant_id, user_id
	•	name
	•	type (person/org/project/concept/etc.)
	•	aliases (list)
	•	metadata

Artifact
	•	kos_id
	•	tenant_id, user_id
	•	artifact_type (summary/tags/entity_page/embedding_ref)
	•	source_ids (list of kos_ids: item/passage/entity)
	•	text (for summaries/pages)
	•	metadata

AgentAction
	•	kos_id
	•	tenant_id, user_id
	•	agent_id
	•	action_type (extract_entities/index_opensearch/etc.)
	•	inputs (refs)
	•	outputs (refs)
	•	model_used, tokens, latency_ms
	•	created_at

⸻

4) Contracts (interfaces) — must be DB/framework-agnostic

Implement as Protocol or ABC in kos/core/contracts/.

Retrieval providers

TextSearchProvider
	•	search(query, tenant_id, user_id, filters, facets, limit, offset) -> TextSearchResults
	•	results must include:
	•	hits[] with kos_id, score, highlights[], snippet, metadata
	•	facets buckets
	•	total

VectorSearchProvider
	•	search(query_text OR embedding, filters, limit) -> VectorResults

GraphSearchProvider
	•	expand(seed_ids, hops, edge_types, filters, limit) -> Subgraph
	•	entity_page(entity_id) -> EntityPagePayload (optional convenience)

GraphVectorSearchProvider (optional v1)
	•	search_similar_entities(query_text, entity_types, filters, limit)

Stores

AdminStore (Postgres in enterprise mode)
	•	tenants/users/connector configs
	•	run logs
	•	job queue/outbox records

ObjectStore
	•	store/retrieve Items, Passages, Entities, Artifacts (can be Postgres for v1)

OutboxStore
	•	enqueue_event(event)
	•	dequeue_events(limit)

LLM/Embedding/Rerank

LLMGateway
	•	generate(messages, model, temperature, json_schema=None, tools=None) -> LLMResponse

EmbedderBase
	•	embed(texts: list[str]) -> list[list[float]]

RerankerBase
	•	rerank(query, candidates) -> reranked_candidates

⸻

5) Provider implementations (enterprise mode)

Postgres provider
	•	Use SQLAlchemy or asyncpg; choose one and be consistent.
	•	Tables (minimum):
	•	items, passages, entities, artifacts, agent_actions
	•	outbox_events
	•	job_runs (status, retries, timestamps, error)

OpenSearch provider

Create indices + mappings:

Index: kos_passages
Fields:
	•	kos_id (keyword)
	•	tenant_id, user_id (keyword)
	•	item_id (keyword)
	•	source (keyword)
	•	content_type (keyword)
	•	text (text)
	•	title (text or keyword)
	•	created_at (date)
	•	tags (keyword) optional

Must support:
	•	highlighting on text
	•	facets on source, content_type, date histogram, tags

Neo4j provider

Minimal graph schema:

Nodes:
	•	:Entity {kos_id, tenant_id, user_id, name, type}
	•	:Item {kos_id, tenant_id, user_id, title, source}
	•	:Passage {kos_id, tenant_id, user_id} (optional node)

Rels:
	•	(Item)-[:HAS_PASSAGE]->(Passage)
	•	(Passage)-[:MENTIONS]->(Entity)
	•	(Entity)-[:RELATED_TO {type}]->(Entity) (optional v1)
	•	provenance edges (optional v1 but scaffold now)

Qdrant provider
	•	collection: kos_passages_vectors
	•	payload fields: kos_id, tenant_id, user_id, item_id, source

⸻

6) Retrieval Plans (your IP)

Implement in kos/core/planning/.

Plan A: Search First (MVP)

Input: query + tenant_id + user_id + filters
Steps:
	1.	OpenSearch lexical search → top hits with highlights + facets
	2.	Hydrate objects (Item/Passage) from ObjectStore by kos_id
	3.	Extract entity ids (if present) and call Graph expansion for the top N hits
	4.	Return a UI-ready payload:

	•	hits (snippet + highlights)
	•	facets
	•	“related entities” (graph neighborhood)
	•	provenance pointers

Return as structured JSON (not chat text).

Plan B: Wikipedia Page (Entity view)

Input: entity_id
Steps:
	1.	Neo4j: entity neighborhood, linked items, top passages
	2.	OpenSearch: top passages mentioning entity with highlights
	3.	Optional: Qdrant “similar entities”
	4.	Assemble EntityPagePayload:

	•	summary (if exists)
	•	facts/relationships
	•	evidence snippets
	•	timeline hooks (optional later)

⸻

7) Agent subsystem (write-path)

Agents are workers that:
	•	consume outbox events or jobs
	•	create/update objects
	•	write to providers
	•	emit new events

Jobs/events (minimum list)

Events:
	•	ITEM_UPSERTED
	•	PASSAGES_CREATED
	•	ENTITIES_EXTRACTED
	•	VECTORS_CREATED
	•	TEXT_INDEXED
	•	GRAPH_INDEXED
	•	ENTITY_PAGE_DIRTY

Jobs:
	•	EXTRACT_ITEM
	•	CHUNK_ITEM
	•	EXTRACT_ENTITIES
	•	EMBED_PASSAGES
	•	INDEX_TEXT
	•	INDEX_GRAPH
	•	BUILD_ENTITY_PAGE

Minimum v1 agents
	•	ChunkAgent: Item → Passages
	•	EmbedAgent: Passages → Qdrant upsert
	•	IndexTextAgent: Passages → OpenSearch index
	•	EntityExtractAgent: Passages → Entities + graph MENTIONS edges
	•	WikipediaPageAgent: Entity → entity_page Artifact

Important: agents must import ONLY kos.core.* and contract interfaces; providers are injected.

⸻

8) API (FastAPI) — endpoints required for CogMem UI integration

/search (POST)

Request:
	•	tenant_id, user_id
	•	query
	•	filters
	•	facets_requested
	•	limit, offset

Response:
	•	hits[] with kos_id, title, snippet, highlights, score, source, content_type, timestamps
	•	facets
	•	related_entities[] (optional)

/entities/{entity_id} (GET)

Returns EntityPagePayload.

/items/{item_id} (GET)

Return item + passages + entities.

/admin/health (GET)

Check connectivity to providers.

⸻

9) Configuration and deployment

Config model

KOS_MODE=enterprise|solo
Provider URLs:
	•	POSTGRES_DSN
	•	OPENSEARCH_URL
	•	NEO4J_URI + auth
	•	QDRANT_URL
	•	SURREALDB_URL (solo mode)

Deployment model

Provide:
	•	Dockerfile for API
	•	Dockerfile for worker
	•	k8s manifests (deployment + service + configmap + secret refs)

Workers should run as:
	•	1 deployment per worker type, or
	•	one worker deployment that runs multiple agent registries (simple v1)

⸻

10) Milestones / build order (Windsurf must implement in this order)

Milestone 1 — Vertical slice (search-first)
	1.	Core models + contracts
	2.	Postgres ObjectStore + Outbox tables
	3.	OpenSearch TextSearchProvider (index + search + highlights + facets)
	4.	FastAPI /search endpoint calling SearchFirst plan
	5.	cli init to create indices/tables
✅ Goal: CogMem UI can call /search and show snippets/facets.

Milestone 2 — Entity graph
	6.	Neo4j GraphSearchProvider:

	•	create nodes/relationships
	•	expand neighborhood

	7.	Entity extraction agent (simple LLM-based or regex-based for v1)
	8.	/entities/{id} endpoint (Wikipedia page payload scaffold)
✅ Goal: search results show “related entities” and entity page loads.

Milestone 3 — Vector + hybrid
	9.	Embed agent + Qdrant provider
	10.	Semantic-first plan (/semantic_search optional)
✅ Goal: semantic recall works, but search-first remains primary.

⸻

11) Coding standards and guardrails
	•	Core contracts must not import provider client libs.
	•	Providers must not import FastAPI.
	•	Agents must not import provider clients directly (only interfaces).
	•	Optional extras pattern:
	•	pip install cogmem-kos[langchain] should add LC adapters
	•	use try/except ImportError inside adapters only

⸻

12) Acceptance criteria (what “done” means for v1)
	•	kos-api container runs and connects to OpenSearch + Postgres at minimum
	•	/search returns:
	•	highlighted snippets
	•	facets
	•	stable IDs
	•	kos-worker can:
	•	take a demo Item, chunk it, index to OpenSearch
	•	basic entity graph path works:
	•	entity extraction creates nodes + MENTIONS edges
	•	/entities/{id} returns neighborhood + evidence snippets

⸻

13) Output expected from Windsurf
	1.	Repo scaffold exactly as specified
	2.	Working local dev run (docker-compose optional, but must run against cluster too)
	3.	docs/architecture/*.md filled with the implemented contracts
	4.	examples/enterprise/demo_search_first.py that:
	•	inserts sample items
	•	runs agents
	•	demonstrates /search and /entities/{id}

⸻

