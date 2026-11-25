import pathlib

import duckdb
import pytest

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "mini.sql"


@pytest.fixture
def mini_con():
    con = duckdb.connect()
    con.execute(FIXTURE.read_text(encoding="utf-8"))
    yield con
    con.close()
