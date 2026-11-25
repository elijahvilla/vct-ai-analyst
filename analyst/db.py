"""Open the VCT database and describe its tables."""
import duckdb


def connect(path: str = "data/vct.duckdb", read_only: bool = True) -> duckdb.DuckDBPyConnection:
    return duckdb.connect(path, read_only=read_only)


def schema_summary(con: duckdb.DuckDBPyConnection) -> dict[str, list[str]]:
    """Table name -> column names, for the main schema only (raw_* views excluded)."""
    rows = con.execute(
        """SELECT c.table_name, c.column_name
           FROM information_schema.columns c
           JOIN information_schema.tables t USING (table_schema, table_name)
           WHERE c.table_schema = 'main' AND t.table_type = 'BASE TABLE'
           ORDER BY c.table_name, c.ordinal_position"""
    ).fetchall()
    summary: dict[str, list[str]] = {}
    for table, column in rows:
        summary.setdefault(table, []).append(column)
    return summary
