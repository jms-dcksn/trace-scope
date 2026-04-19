"""Golden labeled dataset for measuring judge precision/recall.

Hand-annotated (case_idx, output, gold_label) triples. Outputs are sampled
from real runs (see results-archive.txt). gold_label is the human verdict on
whether the output meets the criteria — it does NOT always agree with the
judge's historical verdict; the disagreements are the point.
"""

golden_dataset = [
    # ---- Case 1: simple factual ----
    {
        "case_idx": 0,
        "output": "The capital of France is **Paris**.",
        "gold_label": "pass",
        "notes": "Trivially correct.",
    },
    {
        "case_idx": 0,
        "output": "The capital of France is Lyon.",
        "gold_label": "fail",
        "notes": "Synthetic negative — wrong city, judge must catch this.",
    },

    # ---- Case 2: 1984 author ----
    {
        "case_idx": 1,
        "output": "*1984* was written by **George Orwell**.",
        "gold_label": "pass",
        "notes": "Correct author.",
    },
    {
        "case_idx": 1,
        "output": "*1984* was written by Aldous Huxley, best known for Brave New World.",
        "gold_label": "fail",
        "notes": "Synthetic negative — wrong author.",
    },

    # ---- Case 3: chemical symbol for gold ----
    {
        "case_idx": 2,
        "output": "The chemical symbol for gold is **Au**.",
        "gold_label": "pass",
        "notes": "Correct symbol.",
    },

    # ---- Case 4: GitHub acquisition ----
    {
        "case_idx": 3,
        "output": (
            "GitHub was acquired by **Microsoft** in **2018** for approximately "
            "$7.5 billion in stock."
        ),
        "gold_label": "pass",
        "notes": "All three optional details correct.",
    },

    # ---- Case 5: Tokyo population ----
    {
        "case_idx": 4,
        "output": (
            "Tokyo's population is **about 14.19 million** as of 2024 (Tokyo "
            "Metropolitan Government: 14,192,184). Over the last decade it has "
            "grown modestly: ~13.48M in 2014, 14.065M in the 2020 census, "
            "14.19M in 2024 — roughly 5% growth. Sources: Tokyo Metropolitan "
            "Government and Japan Statistics Bureau."
        ),
        "gold_label": "pass",
        "notes": "Recent figure, clear trend, credible sources cited.",
    },
    {
        "case_idx": 4,
        "output": (
            "Tokyo's current population is about 14.19 million (Tokyo "
            "Metropolitan Government, 2024). Over the last decade Tokyo's "
            "population has been remarkably stable, with only modest growth "
            "rather than dramatic increase or decline."
        ),
        "gold_label": "pass",
        "notes": (
            "Judge marked this FAIL in archive (claimed trend should be flat/"
            "decline). Disagree — criteria only require *describing* the trend "
            "and citing a source, both done. The kind of false negative the "
            "precision/recall measurement should expose."
        ),
    },

    # ---- Case 6: Tesla Model 3 vs Ioniq 6 range ----
    {
        "case_idx": 5,
        "output": (
            "**2024 Tesla Model 3 Long Range:** EPA 363 mi (RWD) / 346 mi "
            "(AWD).\n**2024 Hyundai Ioniq 6 SE Long Range:** EPA 361 mi "
            "(RWD) / 316 mi (AWD).\n\nLike-for-like, the Tesla wins both: "
            "+2 mi RWD vs RWD, +30 mi AWD vs AWD."
        ),
        "gold_label": "pass",
        "notes": (
            "Judge marked similar outputs FAIL in archive for 'mixing trims', "
            "but the answer explicitly distinguishes RWD/AWD and does a "
            "like-for-like comparison. Another likely judge false negative."
        ),
    },

    # ---- Case 7: IPCC Synthesis Report ----
    {
        "case_idx": 6,
        "output": (
            "The most recent IPCC Synthesis Report is the **AR6 Synthesis "
            "Report: Climate Change 2023**.\n\nKey findings: (1) human "
            "influence on climate is unequivocal; warming, sea-level rise and "
            "extreme events are already affecting people and ecosystems; "
            "(2) impacts and risks rise with every increment of warming and "
            "some losses are already unavoidable; (3) strong, rapid, sustained "
            "emissions cuts this decade are essential to keep 1.5°C in reach; "
            "(4) adaptation is uneven and underfunded, and current financial "
            "flows fall short of mitigation/adaptation needs.\n\nTwo "
            "finance-sector policy recommendations: (a) align public finances "
            "and government signals to lower regulatory, cost and market "
            "barriers, redirecting capital toward climate action; "
            "(b) financial actors — investors, intermediaries, central banks, "
            "and regulators — should address the systemic underpricing of "
            "climate-related risks and close the gap between available capital "
            "and climate investment needs."
        ),
        "gold_label": "pass",
        "notes": "Correctly identifies AR6 (2023), real findings, real finance recs.",
    },

    # ---- Case 8: US insurer regulatory considerations ----
    {
        "case_idx": 7,
        "output": (
            "Top 3 regulatory considerations for a mid-size US insurer "
            "deploying agentic AI for claims triage in 2026:\n\n"
            "1. **Unfair discrimination / bias in claims decisions.** NY DFS "
            "Circular Letter No. 7 (2024) requires insurers to manage AI/"
            "predictive models in compliance with anti-discrimination law and "
            "forbids relying solely on a vendor's non-discrimination claim. "
            "Colorado SB24-205 imposes 'reasonable care' duties on high-risk "
            "AI systems.\n"
            "2. **Claims-handling and unfair claims settlement practices.** "
            "Triage that affects routing, prioritization or payment timing is "
            "subject to state unfair claims practices laws and the NAIC AI "
            "Model Bulletin (Dec 2023), which requires a written AI governance "
            "program proportionate to risk.\n"
            "3. **Governance, documentation and exam readiness.** The NAIC "
            "Model Bulletin and NAIC's developing AI Systems Evaluation Tool "
            "expect insurers to demonstrate testing, monitoring, vendor "
            "oversight and human override; NYDFS may audit AI use directly."
        ),
        "gold_label": "pass",
        "notes": "Cites real US insurance authorities, substantive, properly scoped.",
    },
    {
        "case_idx": 7,
        "output": (
            "Insurers deploying AI should consider the EU AI Act's high-risk "
            "classification rules, GDPR data minimization requirements, and "
            "the OECD AI Principles on transparency and accountability. They "
            "should also follow general best practices like having a human in "
            "the loop and conducting model reviews."
        ),
        "gold_label": "fail",
        "notes": (
            "Out of scope (EU/GDPR/OECD instead of US insurance), no US state "
            "or federal insurance guidance cited. Should be a clear FAIL."
        ),
    },

    # ---- Case 9: 10-K generative AI risk factors ----
    {
        "case_idx": 8,
        "output": (
            "Three publicly traded companies whose most recent 10-Ks disclose "
            "material generative-AI risk to their core business:\n\n"
            "1. **Manhattan Associates (NASDAQ: MANH)** — 10-K for FY2024: "
            "'Generative AI features embedded in our software products may "
            "create incomplete or inaccurate outputs and this could result in "
            "customer dissatisfaction or potential claims related to product "
            "performance.'\n"
            "2. **Gen Digital (NASDAQ: GEN)** — 10-K for FY2025: 'there is a "
            "risk of employees inadvertently inputting trade secret information "
            "into Gen AI technologies, thereby enabling third parties, "
            "including our competitors, to access such information.'\n"
            "3. **Veritone (NASDAQ: VERI)** — 10-K for FY2024: 'Issues in the "
            "use of AI (including machine learning) in our platforms may result "
            "in reputational harm or liability.'"
        ),
        "gold_label": "fail",
        "notes": (
            "Real companies with plausible quotes, but Gen Digital's quote is "
            "employee-leak risk (generic infosec, not a gen-AI threat to the "
            "business model) and Veritone's is generic AI reliability. Two of "
            "three fail the 'genuinely about generative AI threatening the "
            "business' criterion. Agree with archive: FAIL."
        ),
    },
    {
        "case_idx": 8,
        "output": (
            "Several companies disclose AI-related risks. For example, many "
            "tech firms have added language about artificial intelligence to "
            "their risk factors in recent annual reports, noting that AI could "
            "disrupt their business or expose them to new competitive threats. "
            "Specific names and quotes vary by filing."
        ),
        "gold_label": "fail",
        "notes": "No company names, no quotes, no filing years. Clear FAIL.",
    },
]
