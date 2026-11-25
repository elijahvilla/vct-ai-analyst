import pandas as pd

from data.download import download
from etl.profile import profile_csv


def test_download_skips_when_csvs_exist(tmp_path):
    (tmp_path / "players.csv").write_text("a,b\n1,2\n")
    paths = download(dest=str(tmp_path), slug="owner/never-called")
    assert [p.replace("\\", "/").split("/")[-1] for p in paths] == ["players.csv"]


def test_profile_reports_rows_columns_and_distincts(tmp_path):
    f = tmp_path / "overview.csv"
    pd.DataFrame(
        {"Agent": ["jett", "sova", "jett"], "Map": ["Ascent", "Bind", "Ascent"], "Kills": [20, 15, 18]}
    ).to_csv(f, index=False)
    report = profile_csv(str(f))
    assert report["rows"] == 3
    assert [c for c, _ in report["columns"]] == ["Agent", "Map", "Kills"]
    assert report["distinct"] == {"Agent": 2, "Map": 2}
