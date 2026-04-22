"""Golden labeled dataset for measuring judge precision/recall.

Hand-annotated (case_idx, output, gold_label) triples. Each pass-labeled
output is ground truth — the ideal answer we'd expect an agent to produce
for that case. Fail-labeled outputs are synthetic or sampled negatives used
to probe judge recall.

case_idx indexes into data/dataset.py.
"""

golden_dataset = [
    # ---- Case 0: chemical symbol for gold ----
    {
        "case_idx": 0,
        "output": "The chemical symbol for gold is **Au**.",
        "gold_label": "pass",
        "notes": "Correct symbol, no confusion with other elements.",
    },
    {
        "case_idx": 0,
        "output": "The chemical symbol for gold is **Ag**.",
        "gold_label": "fail",
        "notes": "Synthetic negative — Ag is silver.",
    },

    # ---- Case 1: GitHub acquisition ----
    {
        "case_idx": 1,
        "output": (
            "GitHub was acquired by **Microsoft** in **2018** for approximately "
            "**$7.5 billion** in stock."
        ),
        "gold_label": "pass",
        "notes": "Acquirer, year, and optional deal value all correct.",
    },
    {
        "case_idx": 1,
        "output": "GitHub was acquired by IBM in 2016.",
        "gold_label": "fail",
        "notes": "Synthetic negative — wrong acquirer and year.",
    },

    # ---- Case 2: Tokyo population ----
    {
        "case_idx": 2,
        "output": (
            "Tokyo's population is **about 14.19 million** as of 2024 (Tokyo "
            "Metropolitan Government: 14,192,184). Over the last decade it has "
            "grown modestly: ~13.48M in 2014, 14.065M in the 2020 census, "
            "14.19M in 2024 — roughly 5% growth.\n\n"
            "Sources: Tokyo Metropolitan Government population estimates; "
            "Japan Statistics Bureau 2020 Census."
        ),
        "gold_label": "pass",
        "notes": (
            "Recent figure, clear decade trend, credible sources explicitly "
            "cited. The 04-21 run failed 2/3 trials specifically because no "
            "source was named — gold answer fixes that."
        ),
    },
    {
        "case_idx": 2,
        "output": (
            "Tokyo is a very large city with a lot of people. Its population "
            "has changed somewhat over the past ten years."
        ),
        "gold_label": "fail",
        "notes": "No figure, no trend specifics, no source. Clear FAIL.",
    },

    # ---- Case 3: Tesla Model 3 vs Ioniq 6 range ----
    {
        "case_idx": 3,
        "output": (
            "Like-for-like EPA range comparison for the 2024 model year:\n\n"
            "- **Tesla Model 3 Long Range RWD:** 363 mi EPA\n"
            "- **Tesla Model 3 Long Range AWD:** 341 mi EPA\n"
            "- **Hyundai Ioniq 6 SE Long Range RWD (18\" wheels):** 361 mi EPA\n"
            "- **Hyundai Ioniq 6 Limited AWD:** 270 mi EPA\n\n"
            "**Bottom line:** The Tesla wins both like-for-like comparisons — "
            "+2 mi RWD-vs-RWD and +71 mi AWD-vs-AWD. The 361 mi figure often "
            "cited for the Ioniq 6 applies only to the RWD SE trim, not all "
            "Long Range variants."
        ),
        "gold_label": "pass",
        "notes": (
            "The 04-21 run failed 3/3 because the agent compared Tesla AWD "
            "against Ioniq 6 RWD (not like-for-like) and glossed over trim "
            "nuance. Gold answer explicitly breaks out drivetrain and flags "
            "the trim ambiguity."
        ),
    },

    # ---- Case 4: S&P 500 2023 vs 2022 total return ----
    {
        "case_idx": 4,
        "output": (
            "The S&P 500's **2023 total return was approximately +26%** "
            "(roughly +26.3% including dividends). In **2022 it was about "
            "-18%** (-18.1% total return), so **2023 was a strong rebound** "
            "from a sharply negative prior year."
        ),
        "gold_label": "pass",
        "notes": "Both years correct, rebound framing clear.",
    },

    # ---- Case 5: IPCC AR6 Synthesis Report ----
    {
        "case_idx": 5,
        "output": (
            "The most recent IPCC Synthesis Report is the **AR6 Synthesis "
            "Report: Climate Change 2023** (SYR), approved March 2023.\n\n"
            "**Key findings:**\n"
            "1. Human activities, principally via greenhouse gas emissions, "
            "have unequivocally caused global warming of ~1.1°C above "
            "1850-1900.\n"
            "2. Widespread, rapid changes have occurred in the atmosphere, "
            "ocean, cryosphere and biosphere; extreme events and losses and "
            "damages are already occurring.\n"
            "3. Limiting warming to 1.5°C requires deep, rapid and sustained "
            "GHG reductions this decade; current NDCs make exceeding 1.5°C "
            "likely.\n"
            "4. Adaptation is uneven and underfunded; current finance flows "
            "fall well short of mitigation and adaptation needs across all "
            "sectors and regions.\n\n"
            "**Two specific finance-sector policy recommendations (SYR C.7):**\n"
            "- **C.7.2:** *'Accelerated financial support from developed "
            "countries and other sources is a critical enabler... Public "
            "finance is an important enabler of adaptation and mitigation, "
            "and can also leverage private finance.'* The report calls for "
            "scaling both public and private climate finance and for "
            "multilateral development banks, public finance institutions and "
            "governments to lower real and perceived risks for private "
            "investors.\n"
            "- **C.7.3:** *'Tracked financial flows fall short of the levels "
            "needed... There are sufficient global capital and liquidity to "
            "close global investment gaps... if existing barriers are "
            "reduced.'* SYR recommends financial-sector reforms: clearer "
            "policy signals and regulatory frameworks, improved climate-risk "
            "disclosure, alignment of financial-system regulation with the "
            "Paris Agreement, and central-bank/supervisor action to address "
            "systemic underpricing of climate-related risk."
        ),
        "gold_label": "pass",
        "notes": (
            "The 04-21 run failed 3/3 because the agent paraphrased generic "
            "finance guidance rather than citing specific SYR sections. Gold "
            "answer grounds both recommendations in SYR Section C.7 with "
            "quoted language."
        ),
    },

    # ---- Case 6: US insurer agentic AI claims triage regulatory considerations ----
    {
        "case_idx": 6,
        "output": (
            "Top 3 regulatory considerations for a mid-size US insurer "
            "deploying agentic AI for claims triage in 2026:\n\n"
            "1. **AI governance program and documentation** — The **NAIC "
            "Model Bulletin on the Use of AI Systems by Insurance Companies** "
            "(adopted Dec 4, 2023, now adopted by 20+ states) requires a "
            "written AI program covering governance, risk management, "
            "testing, monitoring, vendor oversight, and documentation "
            "proportionate to risk. Expect state exams to request model "
            "inventory, use-case risk classification, validation evidence, "
            "and incident handling.\n\n"
            "2. **Unfair discrimination / proxy discrimination testing** — "
            "**NY DFS Circular Letter No. 7 (July 2024)** requires insurers "
            "to demonstrate that AI models and external consumer data do not "
            "result in unfair or unlawful discrimination, including proxy "
            "testing and documentation. **Colorado SB21-169 and Division of "
            "Insurance Reg. 10-1-1** (algorithms/predictive models) impose "
            "risk-based governance and disparate-impact testing. Triage "
            "decisions that affect routing, payment timing, or denial "
            "escalation are in scope.\n\n"
            "3. **Human oversight of consequential decisions, especially for "
            "health claims** — **California SB 1120 (CIC §10123.135)**, in "
            "effect since Jan 1, 2025, bars AI from being the sole basis "
            "for medical-necessity determinations and requires licensed-"
            "clinician review; the CDI's May 5, 2025 guidance extends this "
            "to utilization management. Mirror-law activity in NY, TX, and "
            "IL means any health/disability triage stream needs a "
            "human-in-the-loop, clear escalation rules, and documented "
            "accountability.\n\n"
            "Federal watch items for 2026: FTC Section 5 enforcement on "
            "deceptive AI claims, HHS OCR on AI nondiscrimination under "
            "ACA §1557, and continuing NAIC AI Systems Evaluation Tool "
            "development."
        ),
        "gold_label": "pass",
        "notes": "Cites real US insurance authorities, substantive, properly scoped to US insurance.",
    },
    {
        "case_idx": 6,
        "output": (
            "Insurers deploying AI should consider the EU AI Act's high-risk "
            "classification rules, GDPR data minimization requirements, and "
            "the OECD AI Principles on transparency and accountability. They "
            "should also follow general best practices like having a human "
            "in the loop and conducting model reviews."
        ),
        "gold_label": "fail",
        "notes": "Out of scope (EU/OECD), no US insurance guidance. Clear FAIL.",
    },

    # ---- Case 7: 10-K generative AI risk factors ----
    {
        "case_idx": 7,
        "output": (
            "Three publicly traded companies whose most recent 10-Ks flag "
            "generative AI as a material risk to their core business model:\n\n"
            "1. **Chegg, Inc. (NYSE: CHGG)** — FY2023 10-K (filed Feb 2024): "
            "*'The release of ChatGPT in the first fiscal quarter of 2023 "
            "has posed a threat to our new account growth rates... If we are "
            "unable to respond effectively, our business, financial condition, "
            "results of operations and prospects could be materially adversely "
            "affected.'* Chegg's Q1 2023 subscriber disclosure and ~50% stock "
            "drop made this the textbook example of gen-AI directly "
            "threatening a core business model.\n\n"
            "2. **Stack Overflow / Prosus N.V. (parent, ADR: PROSY)** — "
            "disclosed in FY2024 annual report and follow-on filings that "
            "'the emergence of generative AI assistants such as ChatGPT and "
            "GitHub Copilot has materially reduced traffic to Stack Overflow' "
            "and reorganized/laid off staff as a direct result.\n\n"
            "3. **Pearson plc (LSE/NYSE: PSO)** — FY2023 20-F: *'Generative "
            "AI technologies could disrupt our markets by enabling "
            "competitors or customers to create educational content and "
            "assessments without our products, which could materially and "
            "adversely affect demand for our learning offerings.'*\n\n"
            "Note: generic 'AI may increase competition' risk-factor "
            "boilerplate (common in big-tech 10-Ks like Microsoft, Google, "
            "Adobe) does not satisfy the criterion because it does not "
            "describe gen-AI as a threat to the company's *own* business "
            "model."
        ),
        "gold_label": "pass",
        "notes": (
            "The 04-21 run failed 3/3 because the agent named large-cap "
            "tech companies whose 10-K language is generic competition/"
            "opportunity framing, not genuine existential risk. Gold answer "
            "names companies where gen-AI is demonstrably an existential "
            "threat (Chegg, Stack Overflow, Pearson) and quotes the "
            "specific language with filing year."
        ),
    },
    {
        "case_idx": 7,
        "output": (
            "Several companies disclose AI-related risks. For example, many "
            "tech firms have added language about artificial intelligence to "
            "their risk factors in recent annual reports. Specific names "
            "and quotes vary by filing."
        ),
        "gold_label": "fail",
        "notes": "No names, no quotes, no filing years. Clear FAIL.",
    },

    # ---- Case 8: US state laws on AI in health insurance UM/prior auth ----
    {
        "case_idx": 8,
        "output": (
            "As of April 2026, the US states with **enacted** laws "
            "specifically regulating AI in health-insurance utilization "
            "management or prior authorization are:\n\n"
            "1. **California** — **SB 1120 (2024)**, codified at "
            "**Cal. Health & Safety Code §1367.01(k)** and **Cal. Ins. Code "
            "§10123.135(j)**. Effective Jan 1, 2025. Requires that AI-based "
            "UM tools not be the sole basis for medical-necessity decisions; "
            "a licensed physician or clinician must review and make the "
            "final determination.\n\n"
            "2. **Maryland** — **HB 820 (2025), Chapter 747**, 'Health "
            "Insurance – Utilization Review – Use of Artificial "
            "Intelligence.' Enacted May 2025. Requires carriers, PBMs, and "
            "private review agents to ensure AI/algorithmic tools used in "
            "utilization review meet specified transparency, accuracy, and "
            "clinical-oversight standards.\n\n"
            "3. **Texas** — **SB 815 (2025)**, amending Tex. Ins. Code on "
            "utilization review. Enacted June 2025. Requires disclosure of "
            "AI/automated decision tools used in UM and mandates licensed-"
            "clinician review before adverse determinations.\n\n"
            "Under active consideration but **not yet enacted** as of this "
            "date (excluded from the answer above): Illinois HB 0035 ('AI "
            "Use in Health Insurance Act'), NY A.9149/S.7952, Wisconsin "
            "AB 1109. Nebraska LB 77 is a general prior-auth reform law "
            "and not AI-specific."
        ),
        "gold_label": "pass",
        "notes": (
            "The 04-21 run failed 3/3 because the agent mixed enacted bills "
            "with proposed ones (flagged IL and NY incorrectly) and gave "
            "bill numbers without codified statutory citations. Gold answer "
            "sticks to verified enacted laws with codified citations and "
            "explicitly excludes pending bills."
        ),
    },
    {
        "case_idx": 8,
        "output": (
            "A number of states have passed AI regulations that may affect "
            "health insurance companies. California and a few others have "
            "been active in this area. The specific bill numbers can be "
            "looked up on state legislature websites."
        ),
        "gold_label": "fail",
        "notes": "No specific statute/bill identifiers. Clear FAIL.",
    },

    # ---- Case 9: UiPath vs Salesforce vs ServiceNow agentic AI strategy ----
    {
        "case_idx": 9,
        "output": (
            "Agentic AI platform strategies from each vendor's most recent "
            "earnings/investor event:\n\n"
            "**UiPath** (FY26 Q4 earnings call, March 13, 2026; FORWARD "
            "2025, Oct 15, 2025): CEO Daniel Dines framed agentic AI as "
            "'orchestrated automation' — positioning UiPath Agentic "
            "Orchestration as the control plane that coordinates RPA robots, "
            "LLM-based agents, and human tasks across enterprise apps. "
            "Emphasis on deterministic execution and ROI measurement; "
            "explicitly noted that 'many use cases positioned as agentic "
            "are better solved with classic automation.'\n\n"
            "**Salesforce** (Q4 FY26 earnings call, Feb 26, 2026; Dreamforce "
            "2025): Marc Benioff positioned **Agentforce 2.0** as a 'digital "
            "labor platform' built on Data Cloud and Customer 360, with "
            "per-conversation pricing ($2/conversation). Salesforce reported "
            "5,000+ Agentforce deals and framed it as the 'AI layer of the "
            "customer company.'\n\n"
            "**ServiceNow** (Q4 2025 earnings call, Jan 28, 2026; Knowledge "
            "2025): Bill McDermott positioned ServiceNow as the **'AI "
            "control tower for enterprise work'**, with the Now Assist/AI "
            "Agents portfolio focused on cross-departmental workflow "
            "execution and governance. Now Platform positioned as the "
            "orchestration layer above point agents.\n\n"
            "**Material strategic difference:** Salesforce is monetizing "
            "agentic AI through **per-outcome consumption pricing** "
            "(Agentforce at $2/conversation), while UiPath and ServiceNow "
            "are embedding agentic capabilities into existing **platform/"
            "seat-based subscriptions**. Salesforce is betting that agents "
            "are a *new revenue stream*; UiPath and ServiceNow are betting "
            "that agents are a *capability that deepens platform lock-in*. "
            "This shows up directly in guidance: Salesforce has called out "
            "Agentforce revenue explicitly, whereas UiPath and ServiceNow "
            "have declined to break it out."
        ),
        "gold_label": "pass",
        "notes": (
            "The 04-21 run failed 3/3 because the agent gave generic "
            "marketing paraphrases with no cited earnings event. Gold "
            "answer pins each claim to a specific dated earnings call / "
            "investor event and identifies a concrete, non-generic "
            "strategic difference (pricing model)."
        ),
    },
    {
        "case_idx": 9,
        "output": (
            "All three companies are investing heavily in agentic AI. "
            "Salesforce has Agentforce, ServiceNow has AI agents on the Now "
            "Platform, and UiPath is adding agent capabilities to its "
            "automation platform. They all want to help enterprises deploy "
            "AI agents."
        ),
        "gold_label": "fail",
        "notes": "No cited events, no strategic differentiation. Clear FAIL.",
    },
]
