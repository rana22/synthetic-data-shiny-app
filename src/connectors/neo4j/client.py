"""Neo4j client used by project data-source features."""

from __future__ import annotations

from typing import Any

import pandas as pd
from neo4j import GraphDatabase


class Neo4jClient:
    """Small wrapper around the Neo4j Python driver."""

    def __init__(
        self,
        *,
        uri: str,
        username: str,
        password: str,
        database: str | None = None,
    ) -> None:
        self.database = database
        self.driver = GraphDatabase.driver(
            uri,
            auth=(username, password),
        )

    def close(self) -> None:
        self.driver.close()

    def verify_connectivity(self) -> None:
        self.driver.verify_connectivity()

    def run_query(
        self,
        query: str,
        params: dict[str, Any] | None = None,
    ) -> pd.DataFrame:
        """Execute Cypher and return the result as a DataFrame."""

        session_kwargs: dict[str, Any] = {}
        if self.database:
            session_kwargs["database"] = self.database

        with self.driver.session(**session_kwargs) as session:
            result = session.run(query, params or {})
            records = [record.data() for record in result]

        if not records:
            return pd.DataFrame()

        if (
            set(records[0].keys()) == {"row"}
            and isinstance(records[0]["row"], dict)
        ):
            return pd.DataFrame(
                [record["row"] for record in records]
            )

        return pd.DataFrame(records)
