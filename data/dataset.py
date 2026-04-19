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
        "input": "What's the capital of France?",
        "expected": "Paris",
        "criteria": [
            "mentions Paris",
            "doesn't hallucinate other cities as the capital",
        ],
        "tags": ["factual", "simple"],
    },
    {
        "input": "Who wrote the novel 1984?",
        "expected": "George Orwell",
        "criteria": [
            "mentions George Orwell",
            "doesn't attribute the book to another author",
        ],
        "tags": ["factual", "simple"],
    },
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
        "input": "Compare the battery range of the 2024 Tesla Model 3 Long Range vs the 2024 Hyundai Ioniq 6 Long Range.",
        "expected": None,
        "criteria": [
            "provides an EPA range figure for each vehicle",
            "correctly identifies which has the longer range",
            "doesn't confuse trims or model years",
        ],
        "tags": ["comparison", "medium"],
    },

    # --- Super tough ---
    {
        "input": "Summarize the key findings of the most recent IPCC Synthesis Report and identify two specific policy recommendations it makes for the financial sector.",
        "expected": None,
        "criteria": [
            "correctly identifies the AR6 Synthesis Report (2023) or newer if available",
            "accurately summarizes at least two key scientific findings",
            "cites two specific, real policy recommendations relevant to finance",
            "does not fabricate recommendations or conflate with other reports",
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
]
