"""Demo: Entity page (Wikipedia-style view).

This example demonstrates:
1. Querying an entity by ID
2. Displaying entity relationships
3. Showing evidence snippets

Usage:
    python demo_entity_page.py <entity_id>

Requires:
    - All services running (Postgres, OpenSearch, Neo4j)
    - Some data already indexed with entities extracted
"""

import asyncio
import sys

import httpx


API_BASE = "http://localhost:8000"
TENANT_ID = "demo_tenant"


async def get_entity_page(client: httpx.AsyncClient, entity_id: str) -> dict:
    """Fetch an entity page."""
    response = await client.get(
        f"{API_BASE}/entities/{entity_id}",
        params={"tenant_id": TENANT_ID},
    )
    response.raise_for_status()
    return response.json()


async def search_for_entities(client: httpx.AsyncClient, query: str) -> list:
    """Search and return related entities."""
    response = await client.post(
        f"{API_BASE}/search",
        json={
            "tenant_id": TENANT_ID,
            "query": query,
            "limit": 5,
        },
    )
    response.raise_for_status()
    return response.json().get("related_entities", [])


async def main():
    """Run the demo."""
    print("=" * 60)
    print("cogmem-kos Entity Page Demo")
    print("=" * 60)
    print()

    entity_id = sys.argv[1] if len(sys.argv) > 1 else None

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Check health
        try:
            health = await client.get(f"{API_BASE}/admin/health")
            print(f"API Health: {health.json()['status']}")
        except Exception as e:
            print(f"Error: API not reachable at {API_BASE}")
            print("Make sure to run: kos dev-server")
            return

        print()

        # If no entity ID provided, search for some entities
        if not entity_id:
            print("No entity ID provided. Searching for entities...")
            print()

            queries = ["Stanford", "Google", "machine learning"]
            for query in queries:
                print(f"Searching '{query}' for entities...")
                entities = await search_for_entities(client, query)
                if entities:
                    for e in entities[:3]:
                        print(f"  - {e['name']} ({e['type']}) - ID: {e['kos_id']}")
                else:
                    print("  No entities found")
                print()

            print("Run with an entity ID to see the full entity page:")
            print("  python demo_entity_page.py <entity_id>")
            return

        # Fetch entity page
        print(f"Fetching entity page for: {entity_id}")
        print("-" * 40)

        try:
            page = await get_entity_page(client, entity_id)

            # Display entity info
            entity = page["entity"]
            print(f"\n# {entity.get('name', 'Unknown')}")
            print(f"Type: {entity.get('type', 'unknown')}")
            print(f"ID: {entity['kos_id']}")

            # Display summary
            if page.get("summary"):
                print(f"\n## Summary")
                print(page["summary"][:500])
                if len(page.get("summary", "")) > 500:
                    print("...")

            # Display facts/relationships
            if page.get("facts"):
                print(f"\n## Relationships ({len(page['facts'])})")
                for fact in page["facts"][:10]:
                    print(f"  - {fact['predicate']}: {fact['object_name']}")

            # Display evidence snippets
            if page.get("evidence_snippets"):
                print(f"\n## Evidence ({len(page['evidence_snippets'])} snippets)")
                for snippet in page["evidence_snippets"][:5]:
                    text = snippet["text"][:150] + "..." if len(snippet["text"]) > 150 else snippet["text"]
                    print(f"  - {text}")
                    if snippet.get("source_title"):
                        print(f"    Source: {snippet['source_title']}")

            # Display related entities
            if page.get("related_entities"):
                print(f"\n## Related Entities ({len(page['related_entities'])})")
                for related in page["related_entities"][:5]:
                    print(f"  - {related.get('name', 'Unknown')} ({related.get('type', 'unknown')})")

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                print(f"Entity not found: {entity_id}")
            elif e.response.status_code == 503:
                print("Entity graph not available. Neo4j may not be configured.")
            else:
                print(f"Error: {e}")
        except Exception as e:
            print(f"Error: {e}")

    print()
    print("=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
