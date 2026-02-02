# Retrieval Plans

Retrieval plans orchestrate multi-store queries to produce unified results.

## Plan A: Search First (MVP)

The primary retrieval strategy for cogmem-kos.

### Input

- `query`: Search query string
- `tenant_id`: Tenant identifier
- `user_id`: User identifier
- `filters`: Optional filter criteria
- `facets_requested`: Facet fields to aggregate
- `limit`, `offset`: Pagination

### Steps

1. **OpenSearch lexical search** → top hits with highlights + facets
2. **Hydrate objects** (Item/Passage) from ObjectStore by kos_id
3. **Graph expansion** for top N hits (extract entity IDs, call Neo4j)
4. **Assemble response** with unified payload

### Output

```json
{
  "hits": [
    {
      "kos_id": "...",
      "title": "...",
      "snippet": "...",
      "highlights": ["..."],
      "score": 0.95,
      "source": "files",
      "content_type": "pdf"
    }
  ],
  "facets": {
    "source": [{"value": "files", "count": 10}],
    "content_type": [{"value": "pdf", "count": 5}]
  },
  "related_entities": [
    {"kos_id": "...", "name": "...", "type": "person"}
  ],
  "total": 42
}
```

## Plan B: Wikipedia Page (Entity View)

Builds a comprehensive entity page.

### Input

- `entity_id`: Entity kos_id

### Steps

1. **Neo4j**: Entity neighborhood, linked items, top passages
2. **OpenSearch**: Top passages mentioning entity with highlights
3. **Qdrant** (optional): Similar entities by embedding
4. **Assemble EntityPagePayload**

### Output

```json
{
  "entity": {
    "kos_id": "...",
    "name": "...",
    "type": "person",
    "aliases": []
  },
  "summary": "...",
  "facts": [
    {"predicate": "works_at", "object": "Acme Corp"}
  ],
  "evidence_snippets": [
    {"passage_id": "...", "text": "...", "source_item_id": "..."}
  ],
  "related_entities": [],
  "timeline": []
}
```

## Plan C: Semantic First (Optional)

Vector-first retrieval with optional reranking.

### Steps

1. **Qdrant vector search** → top candidates
2. **Rerank** with cross-encoder (optional)
3. **Hydrate** from ObjectStore
4. **Return** ranked results
