"""Eval dataset: questions of varying difficulty with judge criteria.

Each case has:
  - input: the prompt sent to the agent
  - expected: optional substring for cheap rule-based checks
  - criteria: numbered list passed to the LLM judge
  - tags: free-form labels (difficulty, domain, ...)
"""

dataset = [
    # --- Simple ---
    {
        "input": "What is the chemical symbol for gold?",
        "expected": "Au",
        "criteria": [
            "identifies the symbol as Au",
            "doesn't confuse with silver (Ag) or other elements",
        ],
        "tags": ["factual", "simple"],
    },

    # --- Medium ---
    {
        "input": "Which company acquired GitHub and in what year?",
        "expected": "Microsoft",
        "criteria": [
            "identifies Microsoft as the acquirer",
            "states the year as 2018",
            "optionally mentions the ~$7.5B deal value accurately",
        ],
        "tags": ["factual", "medium"],
    },
    {
        "input": "What is the current population of Tokyo, and how has it changed over the last decade?",
        "expected": None,
        "criteria": [
            "cites a recent population figure for Tokyo (city or metro, stated clearly)",
            "describes the trend observed in population",
            "cites or references a credible source",
        ],
        "tags": ["research", "medium"],
    },
    {
        "input": "Compare the battery range of the 2024 Tesla Model 3 Long Range vs the 2024 Hyundai Ioniq 6 Long Range. Make sure to check RWD and AWD.",
        "expected": None,
        "criteria": [
            "provides an EPA range figure for each vehicle",
            "correctly identifies which has the longer range",
            "notes any impact in the comparison from trim differences",
        ],
        "tags": ["comparison", "medium"],
    },

    {
        "input": "What was the S&P 500's approximate total return in 2023, and how did it compare to 2022?",
        "expected": None,
        "criteria": [
            "cites an approximately correct 2023 total return (~26%)",
            "cites an approximately correct 2022 total return (~-18%)",
            "correctly identifies 2023 as a recovery year relative to 2022",
        ],
        "tags": ["financial", "medium"],
    },

    # --- Super tough ---
    {
        "input": "Summarize the key findings of the most recent IPCC Synthesis Report and identify two specific policy recommendations it makes for the financial sector.",
        "expected": None,
        "criteria": [
            "correctly identifies the AR6 Synthesis Report (2023) or newer if available",
            "accurately summarizes at least two key scientific findings",
            "cites two specific, real policy recommendations relevant to finance",
        ],
        "tags": ["research", "hard"],
    },
    {
        "input": (
            "A mid-size US insurer wants to deploy an agentic AI system for claims triage. "
            "What are the top 3 regulatory considerations they should address in 2026, "
            "citing specific state or federal guidance?"
        ),
        "expected": None,
        "criteria": [
            "cites regulatory sources",
            "top considerations are substantive (bias testing, explainability, governance, consumer disclosure)",
            "answer is scoped to US insurance, not generic AI regulation",
        ],
        "tags": ["domain", "regulatory", "hard"],
    },
    {
        "input": (
            "Identify three publicly traded companies whose most recent 10-K explicitly discloses "
            "material risk from generative AI to their core business model, and quote the relevant risk factor language."
        ),
        "expected": None,
        "criteria": [
            "names three publicly traded companies",
            "each citation references a 10-K filing (year identified)",
            "risk described is genuinely about generative AI threatening the business, not generic tech risk",
        ],
        "tags": ["research", "financial", "hard"],
    },
    {
        "input": (
            "Which US states have enacted laws specifically regulating the use of AI in "
            "health insurance utilization management or prior authorization decisions as of 2026? "
            "Cite the statute or bill number for each."
        ),
        "expected": None,
        "criteria": [
            "names at least two US states with such laws",
            "cites specific statute, bill, or regulation identifiers (not generic references)",
            "scoped to health insurance UM/prior auth, not general AI or insurance laws",
        ],
        "tags": ["domain", "regulatory", "hard"],
    },
    {
        "input": (
            "Compare the agentic AI platform strategies of UiPath, Salesforce, and ServiceNow "
            "as articulated in their most recent earnings calls or investor events. "
            "Identify one material strategic difference between them."
        ),
        "expected": None,
        "criteria": [
            "references each of the three vendors' stated agentic AI strategy",
            "cites a specific earnings call, investor day, or public announcement",
            "identifies a genuine strategic difference (not generic feature comparison)",
        ],
        "tags": ["research", "competitive", "hard"],
    },
]
