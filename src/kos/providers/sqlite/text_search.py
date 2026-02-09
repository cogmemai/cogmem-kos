"""SQLite FTS5 implementation of TextSearchProvider."""

import json
import time
from datetime import datetime
from typing import Any

from kos.core.contracts.stores.retrieval.text_search import (
    TextSearchProvider,
    TextSearchResults,
    TextSearchHit,
    Facet,
    FacetBucket,
)
from kos.providers.sqlite.connection import SQLiteConnection


class SQLiteTextSearchProvider(TextSearchProvider):
    """SQLite FTS5 implementation of TextSearchProvider."""

    def __init__(self, connection: SQLiteConnection):
        self._conn = connection

    async def search(
        self,
        query: str,
        tenant_id: str,
        user_id: str | None = None,
        filters: dict[str, Any] | None = None,
        facets: list[str] | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> TextSearchResults:
        start_time = time.time()

        async with self._conn.connection() as conn:
            where_clauses = ["m.tenant_id = ?"]
            params: list[Any] = [tenant_id]

            if user_id:
                where_clauses.append("m.user_id = ?")
                params.append(user_id)

            if filters:
                for field, value in filters.items():
                    if isinstance(value, list):
                        placeholders = ",".join("?" * len(value))
                        where_clauses.append(f"m.{field} IN ({placeholders})")
                        params.extend(value)
                    else:
                        where_clauses.append(f"m.{field} = ?")
                        params.append(value)

            where_sql = " AND ".join(where_clauses)

            if query:
                fts_query = self._build_fts_query(query)
                search_sql = f"""
                    SELECT 
                        m.kos_id,
                        m.tenant_id,
                        m.user_id,
                        m.item_id,
                        m.title,
                        m.source,
                        m.content_type,
                        m.tags,
                        m.metadata,
                        f.text,
                        bm25(passages_fts) as score,
                        snippet(passages_fts, 1, '<em>', '</em>', '...', 32) as snippet
                    FROM passages_fts f
                    JOIN passages_meta m ON f.kos_id = m.kos_id
                    WHERE passages_fts MATCH ? AND {where_sql}
                    ORDER BY score
                    LIMIT ? OFFSET ?
                """
                params = [fts_query] + params + [limit, offset]
            else:
                search_sql = f"""
                    SELECT 
                        m.kos_id,
                        m.tenant_id,
                        m.user_id,
                        m.item_id,
                        m.title,
                        m.source,
                        m.content_type,
                        m.tags,
                        m.metadata,
                        '' as text,
                        0 as score,
                        '' as snippet
                    FROM passages_meta m
                    WHERE {where_sql}
                    LIMIT ? OFFSET ?
                """
                params = params + [limit, offset]

            cursor = await conn.execute(search_sql, params)
            rows = await cursor.fetchall()

            hits = []
            for row in rows:
                text = row["text"] or ""
                snippet_text = row["snippet"] if row["snippet"] else (text[:200] + "..." if len(text) > 200 else text)

                highlights = []
                if row["snippet"]:
                    highlights = [row["snippet"]]

                hits.append(
                    TextSearchHit(
                        kos_id=row["kos_id"],
                        score=abs(row["score"]) if row["score"] else 0.0,
                        highlights=highlights,
                        snippet=snippet_text,
                        title=row["title"],
                        source=row["source"],
                        content_type=row["content_type"],
                        item_id=row["item_id"],
                        metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                    )
                )

            total = len(hits)
            if query:
                count_sql = f"""
                    SELECT COUNT(*) as cnt
                    FROM passages_fts f
                    JOIN passages_meta m ON f.kos_id = m.kos_id
                    WHERE passages_fts MATCH ? AND {where_sql}
                """
                count_params = [fts_query, tenant_id]
                if user_id:
                    count_params.append(user_id)
                if filters:
                    for field, value in filters.items():
                        if isinstance(value, list):
                            count_params.extend(value)
                        else:
                            count_params.append(value)
                cursor = await conn.execute(count_sql, count_params)
                count_row = await cursor.fetchone()
                total = count_row["cnt"] if count_row else 0

            result_facets = []
            if facets:
                for facet_field in facets:
                    if facet_field in ("source", "content_type"):
                        facet_sql = f"""
                            SELECT {facet_field} as value, COUNT(*) as count
                            FROM passages_meta m
                            WHERE tenant_id = ?
                            GROUP BY {facet_field}
                            ORDER BY count DESC
                            LIMIT 20
                        """
                        cursor = await conn.execute(facet_sql, (tenant_id,))
                        facet_rows = await cursor.fetchall()
                        buckets = [
                            FacetBucket(value=str(r["value"]) if r["value"] else "unknown", count=r["count"])
                            for r in facet_rows
                            if r["value"]
                        ]
                        result_facets.append(Facet(field=facet_field, buckets=buckets))

            took_ms = int((time.time() - start_time) * 1000)

            return TextSearchResults(
                hits=hits,
                facets=result_facets,
                total=total,
                took_ms=took_ms,
            )

    def _build_fts_query(self, query: str) -> str:
        """Build FTS5 query from user input."""
        terms = query.strip().split()
        if not terms:
            return '""'
        escaped = [term.replace('"', '""') for term in terms]
        return " OR ".join(f'"{term}"' for term in escaped)

    async def index_passage(
        self,
        kos_id: str,
        tenant_id: str,
        user_id: str,
        item_id: str,
        text: str,
        title: str | None = None,
        source: str | None = None,
        content_type: str | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        async with self._conn.connection() as conn:
            await conn.execute(
                """
                INSERT OR REPLACE INTO passages_meta 
                (kos_id, tenant_id, user_id, item_id, title, source, content_type, tags, created_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    kos_id,
                    tenant_id,
                    user_id,
                    item_id,
                    title,
                    source,
                    content_type,
                    json.dumps(tags or []),
                    datetime.utcnow().isoformat(),
                    json.dumps(metadata or {}),
                ),
            )

            await conn.execute(
                "DELETE FROM passages_fts WHERE kos_id = ?",
                (kos_id,),
            )

            await conn.execute(
                """
                INSERT INTO passages_fts (kos_id, text, title)
                VALUES (?, ?, ?)
                """,
                (kos_id, text, title or ""),
            )

            await conn.commit()
        return True

    async def delete_passage(self, kos_id: str) -> bool:
        async with self._conn.connection() as conn:
            await conn.execute(
                "DELETE FROM passages_fts WHERE kos_id = ?",
                (kos_id,),
            )
            cursor = await conn.execute(
                "DELETE FROM passages_meta WHERE kos_id = ?",
                (kos_id,),
            )
            await conn.commit()
            return cursor.rowcount > 0

    async def delete_passages_for_item(self, item_id: str) -> int:
        async with self._conn.connection() as conn:
            cursor = await conn.execute(
                "SELECT kos_id FROM passages_meta WHERE item_id = ?",
                (item_id,),
            )
            rows = await cursor.fetchall()
            kos_ids = [row["kos_id"] for row in rows]

            if kos_ids:
                placeholders = ",".join("?" * len(kos_ids))
                await conn.execute(
                    f"DELETE FROM passages_fts WHERE kos_id IN ({placeholders})",
                    kos_ids,
                )

            cursor = await conn.execute(
                "DELETE FROM passages_meta WHERE item_id = ?",
                (item_id,),
            )
            await conn.commit()
            return cursor.rowcount
