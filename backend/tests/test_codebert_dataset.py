from pathlib import Path
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ml.scripts.prepare_codebert_dataset import prepare_dataset


def test_combines_dsarp_and_friend_mined_data(tmp_path: Path) -> None:
    dsarp = tmp_path / "dsarp.csv"
    mined = tmp_path / "mined.csv"
    pd.DataFrame(
        [{"text": "Architectural smell: cyclicDep", "label": "ExtractSharedComponent"}]
    ).to_csv(dsarp, index=False)
    pd.DataFrame(
        [{
            "architecture_smell": "Large Component",
            "input_text": "Large package with excessive responsibility.",
            "repository": "ant",
            "commit": "abc123",
        }]
    ).to_csv(mined, index=False)

    dataset, report = prepare_dataset([dsarp], mined)

    assert list(dataset.columns) == ["text", "label"]
    assert set(dataset["label"]) == {"ExtractSharedComponent", "ExtractComponent"}
    assert report["rows"] == 2
    assert report["sourceCounts"]["apache-mined-weak-label"] == 1


def test_removes_empty_and_duplicate_rows(tmp_path: Path) -> None:
    source = tmp_path / "input.csv"
    pd.DataFrame(
        [
            {"text": "same", "label": "ExtractComponent"},
            {"text": "same", "label": "ExtractComponent"},
            {"text": "", "label": "ExtractComponent"},
        ]
    ).to_csv(source, index=False)

    dataset, report = prepare_dataset([source], None)

    assert len(dataset) == 1
    assert report["removedEmptyRows"] == 1
    assert report["removedDuplicateRows"] == 1
    assert report["warnings"]
