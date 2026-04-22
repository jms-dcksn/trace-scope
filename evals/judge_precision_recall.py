"""Judge precision/recall against the hand-labeled golden dataset.

Treats `pass` as the positive class:
  - TP: judge says pass, gold says pass
  - FP: judge says pass, gold says fail (judge is too lenient)
  - FN: judge says fail, gold says pass (judge is too harsh)
  - TN: judge says fail, gold says fail
"""
import time

from data import dataset, golden_dataset, reference_output
from judge import CorrectnessJudge
from report import write_report


def run_judge_precision_recall(model: str = "gpt-5.4") -> None:
    judge = CorrectnessJudge(model)
    tp = fp = tn = fn = 0
    rows = []
    start = time.perf_counter()

    for i, item in enumerate(golden_dataset, 1):
        case = dataset[item["case_idx"]]
        ref = reference_output(item["case_idx"])
        result = judge.evaluate(case["input"], item["output"], case["criteria"], ref)
        predicted = result.label
        confidence = result.confidence
        reasoning = result.reasoning
        gold = item["gold_label"]
        if predicted == "pass" and gold == "pass":
            tp += 1; outcome = "TP"
        elif predicted == "pass" and gold == "fail":
            fp += 1; outcome = "FP"
        elif predicted == "fail" and gold == "fail":
            tn += 1; outcome = "TN"
        else:
            fn += 1; outcome = "FN"
        print(f"[{i:2d}] case {item['case_idx'] + 1} gold={gold} pred={predicted} → {outcome}")
        rows.append((i, item["case_idx"] + 1, gold, predicted, confidence, outcome, reasoning))

    elapsed = time.perf_counter() - start
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    accuracy = (tp + tn) / len(golden_dataset)

    print(f"\nTP={tp} FP={fp} TN={tn} FN={fn}")
    print(f"Precision={precision:.2%}  Recall={recall:.2%}  F1={f1:.2%}  "
          f"Accuracy={accuracy:.2%}  ({elapsed:.1f}s)")

    lines = [
        "# Judge Precision/Recall",
        "",
        f"- **Examples:** {len(golden_dataset)}  ",
        f"- **TP/FP/TN/FN:** {tp}/{fp}/{tn}/{fn}  ",
        f"- **Precision:** {precision:.2%}  ",
        f"- **Recall:** {recall:.2%}  ",
        f"- **F1:** {f1:.2%}  ",
        f"- **Accuracy:** {accuracy:.2%}  ",
        f"- **Total time:** {elapsed:.2f}s",
        "",
        "| # | Case | Gold | Predicted | Confidence | Outcome | Judge reasoning |",
        "|---|------|------|-----------|------------|---------|-----------------|",
        *[f"| {n} | {c} | {g} | {p} | {conf} | {o} | {r.replace('|', '\\|')} |"
          for n, c, g, p, conf, o, r in rows],
    ]
    path = write_report("judge-pr", "\n".join(lines))
    print(f"\nReport saved to {path.name}")
