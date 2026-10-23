def build_disease_terms_query(
    *,
    node_label: str,
    property_name: str,
) -> str:
    """Build a query returning available disease vocabulary terms."""

    if not node_label.replace("_", "").isalnum():
        raise ValueError("Invalid Neo4j node label.")

    if not property_name.replace("_", "").isalnum():
        raise ValueError("Invalid Neo4j property name.")

    return f"""
        MATCH (n:`{node_label}`)
        WHERE n.`{property_name}` IS NOT NULL
          AND trim(toString(n.`{property_name}`)) <> ''

        RETURN
            n.`{property_name}` AS disease,
            count(*) AS count

        ORDER BY disease
    """