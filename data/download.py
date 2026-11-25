"""Download the VCT dataset from Kaggle into data/raw/ (skips if CSVs are already there).

Needs KAGGLE_USERNAME and KAGGLE_KEY in the environment (never commit them).
Usage: python -m data.download <owner/dataset-slug>
"""
import glob
import os
import sys


def download(dest: str = "data/raw", slug: str | None = None) -> list[str]:
    existing = sorted(glob.glob(os.path.join(dest, "**", "*.csv"), recursive=True))
    if existing:
        return existing
    slug = slug or os.environ.get("VCT_DATASET_SLUG")
    if not slug:
        raise SystemExit("Give the Kaggle dataset slug, e.g. python -m data.download owner/dataset")
    from kaggle.api.kaggle_api_extended import KaggleApi

    api = KaggleApi()
    api.authenticate()
    os.makedirs(dest, exist_ok=True)
    api.dataset_download_files(slug, path=dest, unzip=True, quiet=False)
    return sorted(glob.glob(os.path.join(dest, "**", "*.csv"), recursive=True))


if __name__ == "__main__":
    for p in download(slug=sys.argv[1] if len(sys.argv) > 1 else None):
        print(p)
