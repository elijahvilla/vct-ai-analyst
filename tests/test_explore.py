import duckdb

from etl.explore import run


def test_run_prints_query_result(tmp_path, capsys):
    db = tmp_path / "t.duckdb"
    con = duckdb.connect(str(db)); con.execute("CREATE TABLE t AS SELECT 'jett' AS agent, 3 AS n"); con.close()
    run("SELECT * FROM t", db_path=str(db))
    out = capsys.readouterr().out
    assert "jett" in out and "3" in out
