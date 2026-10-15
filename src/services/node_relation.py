from __future__ import annotations

import os, copy
from pathlib import Path
from typing import Any

import requests
import yaml
import pandas as pd
from typing import Any

def _normalize_mul(mul: str | None, default: str) -> str:
    if mul:
        return mul.lower()
    return default.lower()

def _resolve_direction(src: str, dst: str, mul: str) -> tuple[str, str, str]:
    """
    Convert model relationship into:
    parent → child with normalized type
    """

    if mul == "many_to_one":
        # many (src) → one (dst)
        return dst, src, "one_to_many"

    if mul == "one_to_many":
        return src, dst, "one_to_many"

    if mul == "one_to_one":
        return dst, src, "one_to_one"

    if mul == "many_to_many":
        return src, dst, "many_to_many"

    return dst, src, mul

def extract_relationships(node_model: dict[str, Any]) -> list[dict[str, Any]]:
    rels = node_model.get("Relationships", {})
    output: list[dict[str, Any]] = []

    for rel_name, rel_spec in rels.items():
        default_mul = rel_spec.get("Mul", "many_to_one")

        for end in rel_spec.get("Ends", []):
            src = end.get("Src")
            dst = end.get("Dst")

            if not src or not dst:
                continue

            mul = _normalize_mul(end.get("Mul"), default_mul)

            # Normalize to parent-child
            parent, child, rel_type = _resolve_direction(src, dst, mul)

            output.append({
                "relation": rel_name,
                "parent": parent,
                "child": child,
                "type": rel_type,
                "properties": []  # will be filled later
            })

    return output

def infer_property_links(
    parent: str,
    child: str,
    parent_schema: dict[str, Any],
    child_schema: dict[str, Any],
) -> list[tuple[str, str]]:
    """
    VERY SIMPLE heuristic (expand later)
    """

    parent_props = parent_schema.get("properties", {})
    child_props = child_schema.get("properties", {})

    matches = []

    for p_key in parent_props:
        for c_key in child_props:
            # simple heuristic: substring or exact match
            if p_key == c_key:
                matches.append((f"{parent}.{p_key}", f"{child}.{c_key}"))
            elif p_key in c_key or c_key in p_key:
                matches.append((f"{parent}.{p_key}", f"{child}.{c_key}"))

    return matches

def enrich_relationships_with_properties(
    relationships: list[dict[str, Any]],
    node_schemas: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:

    for rel in relationships:
        parent = rel["parent"]
        child = rel["child"]

        parent_schema = node_schemas.get(parent)
        child_schema = node_schemas.get(child)

        if not parent_schema or not child_schema:
            continue

        props = infer_property_links(parent, child, parent_schema, child_schema)
        rel["properties"] = props

    return relationships

def relationships_to_dataframe(
    relationships: list[dict[str, Any]]
) -> pd.DataFrame:

    rows = []

    for rel in relationships:
        relation_name = rel["relation"]
        parent = rel["parent"]
        child = rel["child"]
        rel_type = rel["type"]
        props = rel.get("properties", [])

        # If no properties found, still keep the relationship
        if not props:
            rows.append({
                "relation": relation_name,
                "parent": parent,
                "child": child,
                "type": rel_type,
                "parent_prop": None,
                "child_prop": None,
            })
        else:
            for p_prop, c_prop in props:
                rows.append({
                    "relation": relation_name,
                    "parent": parent,
                    "child": child,
                    "type": rel_type,
                    "parent_prop": p_prop,
                    "child_prop": c_prop,
                })

    df = pd.DataFrame(rows)

    # Optional: enforce ordering for readability
    df = df.sort_values(by=["parent", "child"]).reset_index(drop=True)

    return df


def filter_clusters_by_nodes(clusters, node_list):
    node_set = set(node_list)

    filtered = []

    for cluster in clusters:
        if all(node in node_set for node in cluster):
            filtered.append(cluster)

    return filtered