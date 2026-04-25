# Judge Precision/Recall -- correctness

- **Examples:** 55 (per-criterion)
- **TP/FP/TN/FN:** 33/1/19/2
- **Precision:** 97.06%
- **Recall:** 94.29%
- **F1:** 95.65%
- **Accuracy:** 94.55%
- **Auto-labeled rows:** 55/55 (cheap migration -- F1 not directly comparable to Phase 1)
- **Total time:** 55.10s

| fixed_output_id | criterion_id | case_id | gold | predicted | outcome | labeler |
|---|---|---|---|---|---|---|
| 1 | 60 | 1 | pass | pass | TP | auto-from-case-level |
| 1 | 61 | 1 | pass | pass | TP | auto-from-case-level |
| 2 | 60 | 1 | fail | fail | TN | auto-from-case-level |
| 2 | 61 | 1 | fail | fail | TN | auto-from-case-level |
| 3 | 62 | 2 | pass | pass | TP | auto-from-case-level |
| 3 | 63 | 2 | pass | pass | TP | auto-from-case-level |
| 3 | 64 | 2 | pass | pass | TP | auto-from-case-level |
| 4 | 62 | 2 | fail | fail | TN | auto-from-case-level |
| 4 | 63 | 2 | fail | fail | TN | auto-from-case-level |
| 4 | 64 | 2 | fail | fail | TN | auto-from-case-level |
| 5 | 65 | 3 | pass | pass | TP | auto-from-case-level |
| 5 | 66 | 3 | pass | pass | TP | auto-from-case-level |
| 5 | 67 | 3 | pass | pass | TP | auto-from-case-level |
| 6 | 65 | 3 | pass | pass | TP | auto-from-case-level |
| 6 | 66 | 3 | pass | pass | TP | auto-from-case-level |
| 6 | 67 | 3 | pass | pass | TP | auto-from-case-level |
| 7 | 65 | 3 | fail | fail | TN | auto-from-case-level |
| 7 | 66 | 3 | fail | fail | TN | auto-from-case-level |
| 7 | 67 | 3 | fail | fail | TN | auto-from-case-level |
| 8 | 68 | 4 | pass | pass | TP | auto-from-case-level |
| 8 | 69 | 4 | pass | pass | TP | auto-from-case-level |
| 8 | 70 | 4 | pass | pass | TP | auto-from-case-level |
| 9 | 71 | 5 | pass | pass | TP | auto-from-case-level |
| 9 | 72 | 5 | pass | pass | TP | auto-from-case-level |
| 9 | 73 | 5 | pass | pass | TP | auto-from-case-level |
| 10 | 74 | 6 | pass | pass | TP | auto-from-case-level |
| 10 | 75 | 6 | pass | pass | TP | auto-from-case-level |
| 10 | 76 | 6 | pass | pass | TP | auto-from-case-level |
| 11 | 77 | 7 | pass | pass | TP | auto-from-case-level |
| 11 | 78 | 7 | pass | pass | TP | auto-from-case-level |
| 11 | 79 | 7 | pass | pass | TP | auto-from-case-level |
| 12 | 77 | 7 | pass | pass | TP | auto-from-case-level |
| 12 | 78 | 7 | pass | pass | TP | auto-from-case-level |
| 12 | 79 | 7 | pass | pass | TP | auto-from-case-level |
| 13 | 77 | 7 | fail | fail | TN | auto-from-case-level |
| 13 | 78 | 7 | fail | fail | TN | auto-from-case-level |
| 13 | 79 | 7 | fail | fail | TN | auto-from-case-level |
| 14 | 80 | 8 | pass | pass | TP | auto-from-case-level |
| 14 | 81 | 8 | pass | fail | FN | auto-from-case-level |
| 14 | 82 | 8 | pass | fail | FN | auto-from-case-level |
| 15 | 80 | 8 | fail | fail | TN | auto-from-case-level |
| 15 | 81 | 8 | fail | fail | TN | auto-from-case-level |
| 15 | 82 | 8 | fail | fail | TN | auto-from-case-level |
| 16 | 83 | 9 | pass | pass | TP | auto-from-case-level |
| 16 | 84 | 9 | pass | pass | TP | auto-from-case-level |
| 16 | 85 | 9 | pass | pass | TP | auto-from-case-level |
| 17 | 83 | 9 | fail | pass | FP | auto-from-case-level |
| 17 | 84 | 9 | fail | fail | TN | auto-from-case-level |
| 17 | 85 | 9 | fail | fail | TN | auto-from-case-level |
| 18 | 86 | 10 | pass | pass | TP | auto-from-case-level |
| 18 | 87 | 10 | pass | pass | TP | auto-from-case-level |
| 18 | 88 | 10 | pass | pass | TP | auto-from-case-level |
| 19 | 86 | 10 | fail | fail | TN | auto-from-case-level |
| 19 | 87 | 10 | fail | fail | TN | auto-from-case-level |
| 19 | 88 | 10 | fail | fail | TN | auto-from-case-level |
