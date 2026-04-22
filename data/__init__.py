from .dataset import dataset
from .golden_dataset import golden_dataset


def reference_output(case_idx: int) -> str | None:
    """Return the pass-labeled golden output for a dataset case, if any."""
    for item in golden_dataset:
        if item["case_idx"] == case_idx and item["gold_label"] == "pass":
            return item["output"]
    return None


__all__ = ["dataset", "golden_dataset", "reference_output"]
