"""All prompts used by VERIFACT-Lite.

Prompts are adapted from the VERIFACT paper (Appendix A.11) and the official
implementation at https://github.com/launchnlp/VeriFact. They are shortened and
made JSON-oriented because the judges here are 3B models rather than GPT-4o /
Llama 3.3-70B / Qwen 2.5-32B, but the task definitions, the four incompleteness
subtypes and the PDTB level-1 relation definitions follow the paper.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Answer generation (the answer under evaluation; generated exactly once)
# ---------------------------------------------------------------------------
ANSWER_SYSTEM = (
    "You are a knowledgeable assistant. Answer the user's question in a single "
    "informative paragraph. Use concrete facts, figures, conditions and "
    "cause-effect statements where relevant. Do not use lists or headings."
)

ANSWER_USER = """Question: {question}

Write one paragraph of at most {max_words} words."""


# ---------------------------------------------------------------------------
# STEP 1 - Baseline fact extraction (SAFE-style decomposition)
# Few-shot demonstrations follow the official repo's BreakDownMessage, which
# intentionally produces atomic but context-poor facts.
# ---------------------------------------------------------------------------
BREAKDOWN_INSTRUCTIONS = """Instructions:
1. You are given a sentence. Break the sentence down into a list of atomic facts.
2. An atomic fact is a sentence containing a singular piece of information.
3. Each atomic fact in the output list should check a different piece of information.
4. Output only the atomic facts as a list, each item starting with "- ". No other formatting.
5. Do this for the last sentence that is given."""

BREAKDOWN_DEMOS: list[dict] = [
    {
        "role": "user",
        "content": BREAKDOWN_INSTRUCTIONS
        + "\nPlease breakdown the following sentence into independent facts: "
        "He made his acting debut in the film The Moon is the Sun's Dream (1992), and "
        "continued to appear in small and supporting roles throughout the 1990s.",
    },
    {
        "role": "assistant",
        "content": "- He made his acting debut in the film.\n"
        "- He made his acting debut in The Moon is the Sun's Dream.\n"
        "- The Moon is the Sun's Dream is a film.\n"
        "- The Moon is the Sun's Dream was released in 1992.\n"
        "- After his acting debut, he appeared in small and supporting roles.",
    },
    {
        "role": "user",
        "content": "Please breakdown the following sentence into independent facts: "
        "He is also a successful producer and engineer, having worked with a wide variety "
        "of artists, including Willie Nelson, Tim McGraw, and Taylor Swift.",
    },
    {
        "role": "assistant",
        "content": "- He is successful.\n- He is a producer.\n- He is an engineer.\n"
        "- He has worked with a wide variety of artists.\n- Willie Nelson is an artist.\n"
        "- He has worked with Willie Nelson.\n- Tim McGraw is an artist.\n"
        "- He has worked with Tim McGraw.\n- Taylor Swift is an artist.\n"
        "- He has worked with Taylor Swift.",
    },
    {
        "role": "user",
        "content": "Please breakdown the following sentence into independent facts: "
        "In 1963, Collins became one of the third group of astronauts selected by NASA and "
        "he served as the back-up Command Module Pilot for the Gemini 7 mission.",
    },
    {
        "role": "assistant",
        "content": "- Collins became an astronaut.\n"
        "- Collins became one of the third group of astronauts selected by NASA.\n"
        "- Collins became an astronaut in 1963.\n"
        "- He served as the back-up Command Module Pilot.\n"
        "- He served as the Command Module Pilot for the Gemini 7 mission.",
    },
    {
        "role": "user",
        "content": "Please breakdown the following sentence into independent facts: "
        "She currently stars in the romantic comedy series, Love and Destiny, which premiered in 2019.",
    },
    {
        "role": "assistant",
        "content": "- She currently stars in Love and Destiny.\n"
        "- Love and Destiny is a romantic comedy series.\n"
        "- Love and Destiny premiered in 2019.",
    },
]

BREAKDOWN_USER = "Please breakdown the following sentence into independent facts: {sentence}"


# ---------------------------------------------------------------------------
# STEP 1b - SAFE-style decontextualization (resolves vague references ONLY).
# This is the stage whose limits VERIFACT exists to repair: it fixes pronouns
# but does not restore conditions, comparanda or relations.
# ---------------------------------------------------------------------------
DECONTEXTUALIZE_PROMPT = """Vague references include but are not limited to:
- Pronouns (e.g., "his", "they", "her")
- Unknown entities (e.g., "this event", "the research", "the invention")
- Non-full names (e.g., "Bezos" when referring to Jeff Bezos)

Instructions:
1. The STATEMENT below was extracted from the broader context of the RESPONSE.
2. Modify the STATEMENT by replacing vague references with the proper entities from the RESPONSE.
3. You MUST NOT change any factual claim made by the original STATEMENT.
4. You MUST NOT add any additional factual claim to the original STATEMENT.
5. Output only the revised statement inside a markdown code block.

STATEMENT:
{statement}

RESPONSE:
{response}"""


# ---------------------------------------------------------------------------
# STEP 2A - Incomplete fact detection (paper Appendix A.11.1)
# ---------------------------------------------------------------------------
INCOMPLETE_TYPES = [
    "ambiguous_concept_or_pronoun",
    "missing_comparison",
    "omitted_condition_or_source",
    "other",
]

COMPLETENESS_PROMPT = """# Task
Given a context and a claim extracted from the context, decide whether the claim is INDEPENDENT or DEPENDENT.
* INDEPENDENT: the claim by itself precisely reflects its original meaning in the context.
* DEPENDENT: the claim needs additional context or detail to precisely reflect its original meaning.

A DEPENDENT claim belongs to exactly one type:
* ambiguous_concept_or_pronoun
  The claim contains vague terms ("this method", "they") or pronouns with no clear referent.
  Context: "Decarbonizing aviation requires SAFs."
  Claim: "They reduce emissions." -> DEPENDENT (ambiguous pronoun "they").
* missing_comparison
  The claim implies a comparison ("more", "better", "faster", "longer") but omits the comparison target stated in the context.
  Context: "SAFs reduce emissions by 80% compared to jet fuels."
  Claim: "SAFs reduce emissions by 80%." -> DEPENDENT (missing "compared to jet fuels").
* omitted_condition_or_source
  The claim omits a critical condition, hypothetical scenario, time qualifier or source stated in the context.
  Context: "If the demand for gold as jewelry disappeared, the price of gold could drop by 20-50%."
  Claim: "The price of gold could drop by 20-50%." -> DEPENDENT (omits the "if" condition).
  Context: "As of 2023, the U.S. top 1% net worth is about $10M (Smith et al., 2023)."
  Claim: "The U.S. top 1% net worth is about $10M." -> DEPENDENT (omits time and source).
* other
  Any other case where the claim cannot be understood on its own.

# Output format
Return ONLY this JSON object, with no extra text:
{{"is_incomplete": true or false, "type": "one of ambiguous_concept_or_pronoun | missing_comparison | omitted_condition_or_source | other | none", "reason": "one short sentence"}}

# Example
Context: "This approach achieves better performance on the new task with less data and training time compared to training a model from scratch."
Claim: "Training a model from scratch requires more data."
Output: {{"is_incomplete": true, "type": "missing_comparison", "reason": "The claim says 'more data' without the comparison target from the context."}}

# Example
Context: "Acorns is a financial technology company founded in 2012 that provides micro-investing services."
Claim: "Acorns was founded in 2012."
Output: {{"is_incomplete": false, "type": "none", "reason": "The claim stands alone and keeps its original meaning."}}

# Your Task
Question: {question}

Context:
"{context}"

Claim:
"{claim}"

Output:"""


# ---------------------------------------------------------------------------
# STEP 2C - Missing relation detection (paper Appendix A.11.2)
# PDTB level-1 definitions, condensed from the official repo's PTDB_definition.
# ---------------------------------------------------------------------------
PDTB_DEFINITION = """The PDTB annotation manual (Section 4.2: Sense Classification) defines four level-1 discourse relations:
1. Temporal - situations related in time.
   * Synchronous: events overlap in time. (E.g., The company operates under Chapter 11, giving it court protection while restructuring.)
   * Asynchronous: one event precedes the other. (E.g., After the merger closed, the stock rose.)
   Signals: before, after, later, previously, subsequently, during, while, simultaneously, then, until.
2. Contingency - cause-effect relationships.
   * Cause.Result: Arg1 gives a reason, Arg2 its effect. (E.g., The debt is declared equity, so it isn't deductible.)
   * Cause.NegResult: Arg1 prevents the effect in Arg2. (E.g., Investors acted too late to avoid losses.)
   * Purpose: an agent acts to achieve a goal. (E.g., A company sells radio stations to focus on programming.)
   * Condition: one situation depends on another being realized. (E.g., If Congress agrees, the government will relinquish its stake.)
   * Negative Condition: the effect occurs unless a condition is met. (E.g., Profits may remain low unless the Fed eases rates.)
   Signals: because, therefore, so, due to, if, unless, leading to, resulting in, making, causing, in order to, thus.
3. Comparison - highlights differences or similarities (contrast, concession, similarity).
   Signals: although, however, whereas, on the other hand, even though, similarly.
4. Expansion - extends the discourse (conjunction, instantiation, level-of-detail, manner, substitution).
   Signals: and, for example, in other words, instead of, by, specifically."""

RELATION_DETECT_PROMPT = """{pdtb}

# Answer
{response}

# Span
"{span}"

-> In the answer above, does the span "{span}" indicate a discourse relation between two events or statements?
Only level-1 relations are needed: Temporal, Contingency, Comparison, Expansion.
VERIFACT only cares about Temporal and Contingency relations.

Return ONLY this JSON object:
{{"is_missing_relation": true or false, "relation_type": "temporal | contingency | comparison | expansion | none", "reason": "one short sentence"}}

Set is_missing_relation to true only when the relation type is temporal or contingency.

Output:"""

RELATION_COVERAGE_PROMPT = """I have a list of extracted facts.

{fact_list}

Does any single fact above already capture the relation expressed by the span "{span}"?
For a temporal relation, a fact that explicitly says "before", "after", "during", "simultaneously" counts as YES.
For a contingency relation, a fact that explicitly says "if", "unless", "because", "so that", "resulting in" counts as YES.
A fact that merely mentions one of the two events, without the relation, counts as NO.
If the relation is only obtained by combining two or more facts, answer NO.

Return ONLY this JSON object:
{{"already_covered": true or false, "supporting_fact": "the fact id such as F3, or null"}}

Output:"""


# ---------------------------------------------------------------------------
# STEP 3 - Refinement of incomplete facts (paper Appendix A.11.6)
# ---------------------------------------------------------------------------
REFINE_INCOMPLETE_PROMPT = """# Task
I will give you a question, an answer, and a claim extracted from the answer. The claim is problematic:
it cannot be correctly understood without context from the answer. I also give you the error type and the reason.

Revise the claim so that it is self-contained. Rules:
1. Preserve the original meaning of the claim.
2. Add only the context that is necessary.
3. Prefer the exact wording used in the answer.
4. Use no information from outside the answer. Do not add new knowledge.
5. Resolve missing references, include omitted conditions, include omitted comparison targets.
6. Do not merge unrelated claims. Keep the claim concise, one sentence.
Use the MINIMAL number of extra words, taken FROM the answer.

# Example
Question: What is the best way to go from Oakland to Boston?
Answer: One option is to fly from Oakland to Boston in about 5 hours. Another option is to take a train or bus, but this would be a longer journey, taking around 72 hours.
Problematic Claim: Taking the train or the bus would be a longer journey.
Error Type and Reason: missing_comparison: The claim mentions "a longer journey" but omits the comparison target.
Refined Claim:
```
Taking the train or the bus would be a longer journey compared to flying.
```

# Your Turn
Question: {question}

Answer: {response}

Problematic Claim: {claim}

Error Type and Reason: {error_type}: {reason}

Output only the refined claim inside a markdown code block.
Refined Claim:"""


# ---------------------------------------------------------------------------
# STEP 3B - Adding a missing relational fact (paper Appendix A.11.6)
# ---------------------------------------------------------------------------
ADD_RELATION_FACT_PROMPT = """I will give you a question, an answer, and a span of text from the answer that
expresses a relationship between two events or statements. The relationship is either temporal
(the order or overlap of events) or contingency (a cause-effect, condition or purpose relation).

Write ONE sentence that states that relationship explicitly, using the minimal number of words.
Rules:
* Use only information from the answer. Do not add outside knowledge.
* Name both related events or statements.
* State the relation explicitly (e.g. "if", "because", "resulting in", "after", "while").
* One sentence only. Do not repeat a fact that is already in the list below.

# Question
{question}

# Answer
{response}

# Span
"{span}"

# Relationship Type
{relation_type}

# Facts already extracted
{fact_list}

Output only the new fact inside a markdown code block.
New Fact:"""


# ---------------------------------------------------------------------------
# STEP 4 - Query generation for evidence retrieval
# ---------------------------------------------------------------------------
QUERY_GEN_PROMPT = """You are preparing to fact-check a claim with an encyclopedia search engine.

Claim: {claim}

Write {n} DIFFERENT short search queries that would retrieve evidence about this claim.
Make them genuinely diverse:
1. a keyword query naming the main entities,
2. an entity or topic query naming the subject area,
3. a query about the relationship, condition or comparison in the claim.
Do not repeat the claim verbatim. No question marks. 3 to 8 words each.

Return ONLY this JSON object:
{{"queries": ["...", "...", "..."]}}

Output:"""


# ---------------------------------------------------------------------------
# STEP 4 - Fact verification
# ---------------------------------------------------------------------------
VERIFY_PROMPT = """You are a careful fact-checker. Decide whether the evidence supports the claim.

Labels:
* SUPPORTED: the evidence directly supports the claim.
* CONTRADICTED: the evidence conflicts with the claim.
* UNDECIDED: the evidence does not contain enough information to decide.

Rules:
* Absence of evidence is NOT support. If the evidence does not address the claim, answer UNDECIDED.
* Judge only against the evidence below, not your own knowledge.
* If the claim states a condition, comparison or cause-effect relation, that part must also be supported.
* Cite the evidence ids you relied on.

# Claim
{claim}

# Evidence
{evidence}

Return ONLY this JSON object:
{{"label": "SUPPORTED | CONTRADICTED | UNDECIDED", "confidence": 0.0 to 1.0, "evidence_ids": ["E1"], "reason": "one short sentence"}}

Output:"""


# ---------------------------------------------------------------------------
# Recall - entailment of a reference fact by the model response
# (paper Appendix A.11.5)
# ---------------------------------------------------------------------------
RECALL_ENTAILMENT_PROMPT = """I will give you a claim and a paragraph. Decide whether the claim is supported by the paragraph.
The paragraph supports the claim only if the paragraph states the claim or clearly implies it.
Paraphrases count as support. Related-but-different information does not.

Claim: {claim}

Paragraph: {paragraph}

Return ONLY this JSON object:
{{"covered": true or false, "supporting_text": "the shortest quote from the paragraph, or null"}}

Output:"""
