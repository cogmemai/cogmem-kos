"""Demo: Search-first retrieval plan.

This example demonstrates:
1. Inserting sample items
2. Running agents to chunk and index
3. Calling /search endpoint
4. Displaying results with highlights and facets

Usage:
    python demo_search_first.py

Requires:
    - Postgres running with cogmem_kos database
    - OpenSearch running
    - Environment variables configured (see .env.example)
"""

import asyncio
import uuid
from datetime import datetime

import httpx


API_BASE = "http://localhost:8000"
TENANT_ID = "demo_tenant"
USER_ID = "demo_user"


SAMPLE_ITEMS = [
    {
        "title": "Introduction to Machine Learning",
        "content_text": """
Machine learning is a subset of artificial intelligence that enables systems to learn 
and improve from experience without being explicitly programmed. It focuses on developing 
computer programs that can access data and use it to learn for themselves.

The process begins with observations or data, such as examples, direct experience, or 
instruction, to look for patterns in data and make better decisions in the future. 
The primary aim is to allow computers to learn automatically without human intervention.

Key concepts include supervised learning, unsupervised learning, and reinforcement learning.
Dr. Andrew Ng from Stanford University has been instrumental in popularizing machine learning
through his online courses. Companies like Google, Microsoft, and OpenAI are leading
research in this field.
        """,
        "content_type": "article",
        "source": "files",
    },
    {
        "title": "Natural Language Processing Overview",
        "content_text": """
Natural Language Processing (NLP) is a branch of artificial intelligence that helps 
computers understand, interpret, and manipulate human language. NLP draws from many 
disciplines, including computer science and computational linguistics.

Applications of NLP include machine translation, sentiment analysis, chatbots, and 
text summarization. Major breakthroughs have come from transformer architectures,
particularly the BERT model from Google and GPT models from OpenAI.

Dr. Christopher Manning at Stanford University has made significant contributions to
NLP research. The field continues to evolve rapidly with new models and techniques
being developed by research teams at universities and companies worldwide.
        """,
        "content_type": "article",
        "source": "files",
    },
    {
        "title": "Project Status Update - Q4 2025",
        "content_text": """
The CogMem project has made significant progress this quarter. Our team, led by 
John Smith and Sarah Johnson, has completed the core retrieval infrastructure.

Key achievements:
- Implemented search-first retrieval plan
- Deployed to production on AWS infrastructure
- Integrated with OpenSearch for text search
- Added Neo4j for entity graph storage

Next quarter, we plan to focus on:
- Improving entity extraction accuracy
- Adding support for more data sources
- Performance optimization for large-scale deployments

The project is on track for the January 2026 release. Budget utilization is at 85%
of the allocated $500,000 for this phase.
        """,
        "content_type": "report",
        "source": "files",
    },
]


async def create_item(client: httpx.AsyncClient, item: dict) -> dict:
    """Create an item via the API."""
    response = await client.post(
        f"{API_BASE}/items",
        json={
            "tenant_id": TENANT_ID,
            "user_id": USER_ID,
            **item,
        },
    )
    response.raise_for_status()
    return response.json()


async def search(client: httpx.AsyncClient, query: str) -> dict:
    """Execute a search query."""
    response = await client.post(
        f"{API_BASE}/search",
        json={
            "tenant_id": TENANT_ID,
            "user_id": USER_ID,
            "query": query,
            "facets_requested": ["source", "content_type"],
            "limit": 10,
        },
    )
    response.raise_for_status()
    return response.json()


async def main():
    """Run the demo."""
    print("=" * 60)
    print("cogmem-kos Search-First Demo")
    print("=" * 60)
    print()

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Check health
        print("Checking API health...")
        try:
            health = await client.get(f"{API_BASE}/admin/health")
            print(f"Health: {health.json()}")
        except Exception as e:
            print(f"Error: API not reachable at {API_BASE}")
            print("Make sure to run: kos dev-server")
            return

        print()

        # Create sample items
        print("Creating sample items...")
        for item in SAMPLE_ITEMS:
            try:
                result = await create_item(client, item)
                print(f"  Created: {result['title'][:40]}... (id: {result['kos_id'][:8]})")
            except Exception as e:
                print(f"  Error creating item: {e}")

        print()
        print("Note: Items need to be processed by workers before they appear in search.")
        print("Run 'kos run-worker' in another terminal to process events.")
        print()

        # Wait a moment for indexing
        await asyncio.sleep(2)

        # Run some searches
        queries = [
            "machine learning",
            "natural language processing",
            "project status",
            "Stanford University",
        ]

        for query in queries:
            print(f"Searching for: '{query}'")
            print("-" * 40)

            try:
                results = await search(client, query)
                print(f"  Total hits: {results['total']}")
                print(f"  Took: {results.get('took_ms', 'N/A')}ms")

                if results["hits"]:
                    for hit in results["hits"][:3]:
                        print(f"  - {hit['title'] or 'Untitled'} (score: {hit['score']:.2f})")
                        if hit["highlights"]:
                            print(f"    Highlight: {hit['highlights'][0][:80]}...")
                else:
                    print("  No results found")

                if results["facets"]:
                    print("  Facets:")
                    for facet in results["facets"]:
                        buckets = ", ".join(
                            f"{b['value']}({b['count']})" for b in facet["buckets"][:3]
                        )
                        print(f"    {facet['field']}: {buckets}")

            except Exception as e:
                print(f"  Error: {e}")

            print()

    print("=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
