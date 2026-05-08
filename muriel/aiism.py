"""
muriel.aiism — anti-AI-tell prose audit for paper drafts.

Codifies the stylistic tics that flag a passage as AI-drafted to a careful
reader: em-dash addiction, "load-bearing" / "structurally" / "materially"
intensifiers, definitional clefts ("the locus of X" / "the unit at which Y"),
"What X is Y" constructions, "not X but Y" parallelism, "already-Y"
compounds, mid-paragraph bold, repeated re-italicization of technical terms,
overlong clause-stacked sentences, copula-avoidance verbs ("serves as",
"stands as"), significance-inflation phrases ("a testament to", "underscores
the importance"), prescriptive narrator framing ("It is important to
note"), padded-vocabulary clusters, and hard artifacts of LLM tooling
(oaicite tokens, knowledge-cutoff disclaimers, sandbox paths).

Sources for phrase lists:
- Wikipedia: Signs of AI writing (CC-BY-SA-4.0)
- ammil-industries/vale-signs-of-ai-writing (CC-BY-SA-4.0) —
  https://github.com/ammil-industries/vale-signs-of-ai-writing
- Local critique of paper-v4 (project-specific tics)
The phrase tables here are derivative of the Wikipedia / Vale lists and
remain CC-BY-SA-4.0 compatible. The Python rule engine is muriel-licensed.

Usage
-----

Programmatic::

    from muriel.aiism import audit_text
    findings = audit_text(open("paper.md").read())
    for f in findings:
        print(f.line, f.severity, f.rule, f.message)

CLI::

    python -m muriel.aiism paper.md
    python -m muriel.aiism paper.md --severity warn   # exit 1 on warn+
    python -m muriel.aiism paper.md --respect-pencil  # skip locked sentences

Exit status: 0 = clean, 1 = findings at or above the configured severity,
2 = usage error.

Why this exists
---------------

The project's prose accumulated AI tells under sustained collaboration: a
critique reader counted "load-bearing" seven times, em-dashes in nearly
every paragraph, and a recurring "the substrate that licenses the
partition" cleft pattern. The fixes are obvious once flagged. The tool
exists so flagging is automatic rather than left to a human reader's
patience on draft N.

Companion to ``pencil`` (sentence-level voice locking): when a
``<file>.pencil.json`` sidecar is present and ``--respect-pencil`` is
set, locked sentences are skipped because they're explicitly the human
author's voice.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

SEVERITIES = ("info", "warn", "error")
_SEV_ORDER = {s: i for i, s in enumerate(SEVERITIES)}


# ---------------------------------------------------------------------------
# Hard artifacts — leaked LLM tooling / refusal residue. Zero false-positive.
# ---------------------------------------------------------------------------

HARD_ARTIFACT_RULES: list[tuple[str, str, str]] = [
    # rule_id, regex, message
    ("artifact-oaicite", r"\boaicite\b|\boai_citation\b|:contentReference\[",
     "Leaked OpenAI tool-citation token. Strip before any external pass."),
    ("artifact-turn-token", r"\bturn\d+(?:search|fetch|view|news)\d+\b",
     "Leaked LLM tool token (turn-N). Always real; strip immediately."),
    ("artifact-sandbox-path", r"\bsandbox:/mnt/data/\S+",
     "Leaked OpenAI sandbox path. Always real."),
    ("artifact-chatgpt-url", r"\b(?:chat\.openai\.com|chatgpt\.com)/[^\s)]+",
     "Live ChatGPT URL embedded in prose. Always a paste artifact."),
    ("artifact-utm-chatgpt", r"utm_source=chatgpt\.com",
     "Citation copied from ChatGPT with tracking parameter intact."),
    ("artifact-knowledge-cutoff", r"\bas\s+of\s+my\s+(?:last\s+update|knowledge\s+cutoff|training)\b",
     "Knowledge-cutoff disclaimer is LLM throat-clearing; cut."),
    ("artifact-realtime-disclaimer", r"\bI\s+don'?t\s+have\s+access\s+to\s+real[-\s]?time\b",
     "LLM real-time-data disclaimer; cut."),
    ("artifact-refusal-preamble", r"^\s*(?:Certainly!|Sure,\s+I'?d\s+be\s+happy|I\s+cannot\s+help\s+with)",
     "Refusal/preamble residue from an LLM session. Strip."),
]


@dataclass
class Finding:
    line: int
    column: int
    severity: str
    rule: str
    message: str
    excerpt: str

    def __lt__(self, other: "Finding") -> bool:
        return (self.line, self.column, self.rule) < (other.line, other.column, other.rule)


# ---------------------------------------------------------------------------
# Rule tables
# ---------------------------------------------------------------------------

# Phrases that, on first occurrence, are themselves the tell. Case-insensitive
# unless marked. (rule_id, pattern, severity, message)
SINGLE_PHRASE_RULES: list[tuple[str, str, str, str]] = [
    ("phrase-earn-their-keep", r"\bearn(?:s|ed|ing)?\s+(?:their|its)\s+keep\b", "warn",
     "Folksy where the rest is technical. Replace with something specific."),
    ("phrase-locus-of", r"\bthe\s+locus\s+of\b", "warn",
     "Definitional cleft tic. Use 'where X happens' or just name X."),
    ("phrase-unit-at-which", r"\bthe\s+unit\s+at\s+which\b", "warn",
     "Definitional cleft tic. Most uses can become 'where X is recorded' or 'X-level'."),
    ("phrase-substrate-licenses", r"\bsubstrate\s+that\s+licenses\b", "warn",
     "Performative depth. Say 'the partition is grounded in' or just state the grounding."),
    ("phrase-doing-its-share", r"\b(?:cursor|gaze|motor\s+system)\s+is\s+doing\s+its\s+share\b", "warn",
     "Anthropomorphism reviewers will quote back at you. Drop or rephrase mechanically."),
    ("phrase-observational-register", r"\bin\s+observational\s+register\b", "warn",
     "Self-conscious framing. Trust the metaphor or unpack it plainly."),
    ("phrase-names-the-same-observation", r"\bnames\s+the\s+same\s+observation\b", "warn",
     "Title-explainer tic. Cut or rewrite as plain English."),
    ("phrase-the-hope-is-that", r"\bthe\s+hope\s+is\s+that\b", "warn",
     "Authorial-voice hedging that weakens the close. State what the work does."),
    ("phrase-looking-into-the-corners", r"\blooking\s+into\s+the\s+corners\b", "info",
     "Italicized motif. Allowed once (e.g., §5 header). Flag every additional occurrence."),
    ("phrase-leaky-cursor-aside", r"\bleaky\s+cursor.{0,40}observational\s+register\b", "warn",
     "Title aside is overwrought. Trust the title or unpack plainly."),

    # --- Significance-inflation phrases (Vale/Wikipedia-derived, CC-BY-SA-4.0) ---
    ("phrase-testament-to", r"\ba\s+(?:true\s+)?testament\s+to\b", "warn",
     "Significance-inflation cliché. Almost never appears in unedited human technical prose."),
    ("phrase-reminder-of", r"\ba\s+(?:stark|powerful|sobering|striking)\s+reminder\s+of\b", "warn",
     "Significance-inflation cliché. Cut or replace with the specific point."),
    ("phrase-plays-a-role", r"\bplays?\s+a\s+(?:vital|crucial|pivotal|central|key|critical|fundamental)\s+role\b", "warn",
     "Formula phrase. Either say what it does, or say nothing."),
    ("phrase-underscores", r"\bunderscor(?:es|ing|ed)\s+the\s+(?:significance|importance|need|value)\b", "warn",
     "LLM tic. Replace with 'shows', 'demonstrates', or just state the claim."),
    ("phrase-stands-as", r"\bstands?\s+as\s+(?:a\s+|an\s+)", "warn",
     "Copula-avoidance via weighty linking verb. Use plain 'is'."),
    ("phrase-serves-as", r"\bserves?\s+as\s+(?:a\s+|an\s+|the\s+)", "info",
     "Copula-avoidance via weighty linking verb. Often 'is' is cleaner."),
    ("phrase-rich-heritage", r"\b(?:rich|profound|deep|enduring)\s+(?:heritage|legacy|tradition)\b", "warn",
     "Encyclopedic-flavor cliché. Rare in real domain writing."),
    ("phrase-indelible-mark", r"\b(?:indelible\s+mark|lasting\s+impact|enduring\s+impact|deeply\s+rooted|steadfast\s+dedication)\b",
     "warn", "Encyclopedic-flavor cliché. Cut."),
    ("phrase-contributes-to", r"\bcontributes?\s+to\s+(?:the\s+)?(?:overall|broader|wider|larger)\s+", "warn",
     "Vacuous abstraction. State what the contribution is."),

    # --- Prescriptive-narrator framing ---
    ("phrase-it-is-important", r"\bit\s+is\s+(?:important|crucial|essential|vital|necessary)\s+to\s+(?:note|recognize|understand|remember|consider|acknowledge)\b",
     "warn", "Prescriptive-narrator frame. State the point directly."),
    ("phrase-one-must", r"\b(?:one\s+must|we\s+must)\s+(?:consider|acknowledge|recognize|understand)\b", "warn",
     "Lecturing the reader. Cut or convert to plain statement."),
    ("phrase-needless-to-say", r"\b(?:needless\s+to\s+say|it\s+goes\s+without\s+saying)\b", "warn",
     "If it's needless, cut it."),
    ("phrase-worth-mentioning", r"\bit'?s?\s+worth\s+(?:mentioning|noting|pointing\s+out)\s+that\b", "warn",
     "Throat-clearing. State the thing."),

    # --- Throat-clearing temporal openers ---
    ("phrase-recent-years", r"^\s*In\s+recent\s+years,", "warn",
     "Temporal-frame opener. Lead with the claim."),
    ("phrase-past-decade", r"^\s*Over\s+the\s+(?:past|last)\s+(?:decade|few\s+years)", "warn",
     "Temporal-frame opener. Lead with the claim."),
    ("phrase-todays-world", r"\bIn\s+today'?s\s+(?:fast-paced\s+)?(?:world|era|landscape)\b", "warn",
     "Cliché opener. Cut entirely."),
    ("phrase-modern-era", r"\bIn\s+(?:the\s+)?(?:modern\s+era|an\s+increasingly\s+\w+\s+world)\b", "warn",
     "Cliché opener. Cut."),

    # --- Anthropomorphized research verbs ---
    ("phrase-research-unveiled", r"\b(?:research|the\s+study|the\s+paper)\s+(?:unveiled|revealed|discovered|uncovered)\b",
     "warn", "Anthropomorphized research verb. Use 'found', 'observed', 'reported'."),

    # --- Sourceless-authority hedges ---
    ("phrase-vague-attribution", r"\b(?:industry\s+reports\s+suggest|observers\s+have\s+noted|experts\s+(?:argue|contend|suggest)|critics\s+contend)\b",
     "warn", "Sourceless-authority frame. Name the source or drop the claim."),

    # --- En-dash escalation tic ---
    ("phrase-not-just-but", r"\bnot\s+just\s+\S+(?:\s+\S+){0,5}?\s+[—–-]\s+\S+", "warn",
     "'This is not just X — it's Y' escalation. Tell of LLM rhetoric. Convert to plain claim."),

    # --- Loaded-vocabulary in current usage ---
    ("phrase-regime", r"\bregime[s]?\b", "warn",
     "'Regime' carries political connotations in current usage; for technical contexts prefer 'phase', 'mode', or 'state'."),
]

# Phrases that repeat. Allow up to `max_count` occurrences before flagging.
REPEATED_PHRASE_RULES: list[tuple[str, str, int, str, str]] = [
    ("repeat-load-bearing", r"\bload[-\s]bearing\b", 1, "error",
     "Meme phrase. Use one place where the metaphor pulls weight; replace others with 'central', 'primary', 'defended claim'."),
    ("repeat-structurally", r"\bstructurally\b", 2, "warn",
     "Empty intensifier. Either give the number that justifies it or drop the adverb."),
    ("repeat-materially", r"\bmaterially\b", 2, "warn",
     "Empty intensifier. Either give the number or drop the adverb."),
    ("repeat-meaningfully", r"\bmeaningfully\b", 2, "warn",
     "Empty intensifier. Either give the number or drop the adverb."),
    ("repeat-already-compound", r"\balready-\w+", 5, "info",
     "Already-Y compound used many times. Vary phrasing; 'previously', 'prior', plain past tense work too."),
    ("repeat-not-x-but-y", r"\bis\s+not\s+[^.\n]{1,80}?\s+but\s+\w", 3, "warn",
     "'Not X but Y' parallelism is a tell when stacked. Spread out or convert to 'Y, not X'."),
    ("repeat-what-x-cleft", r"^\s*What\s+\w+(?:\s+\w+){0,4}?\s+(?:makes|is|carries|needs|does|matters|changes|survives)\b",
     2, "warn",
     "'What X is Y' cleft. Composed-not-written. Convert to direct subject-verb."),
]

# Cluster rules — fire when ≥threshold tokens from a list appear within a
# bounded scope (paragraph or N-word window). High false-positive on any
# single token; deadly accurate as a cluster.
# (rule_id, token_regex, threshold, scope, severity, message)
# scope ∈ {"paragraph", "200w"}
CLUSTER_RULES: list[tuple[str, str, int, str, str, str]] = [
    ("cluster-padded-vocab",
     r"\b(?:showcasing|highlighting|emphasizing|enhance(?:s|d|ment)?|fostering|leverag(?:e|es|ed|ing)|harness(?:es|ed|ing)?|robust|seamless|cutting-edge|pivotal|vibrant|meticulous|intricate|comprehensive|holistic|nuanced|profound|paramount)\b",
     3, "200w", "warn",
     "Padded-vocabulary cluster (≥3 in 200-word span). Mid-2024+ LLM residue. Replace with plain words."),
    ("cluster-hedges",
     r"\b(?:notably|obviously|clearly|undoubtedly|of\s+course|importantly|crucially|essentially|fundamentally)\b",
     3, "paragraph", "warn",
     "Hedge/booster cluster (≥3 in one paragraph). Empty intensifiers; drop most."),
    ("cluster-firstly-thirdly",
     r"\b(?:[Ff]irstly|[Ss]econdly|[Tt]hirdly|[Ll]astly)\b",
     3, "paragraph", "warn",
     "Sequenced 'firstly/secondly/thirdly' in one paragraph. Humans usually mix transitions."),
    ("cluster-significance-verbs",
     r"\b(?:underscores?|highlights?|emphasi[sz]es?|illustrates?|exemplifies?)\s+(?:the\s+)?(?:significance|importance|need|value|crucial)\b",
     2, "paragraph", "warn",
     "Multiple significance-verb constructions in one paragraph. State the point."),
]


# Pairs / proximity rules. (rule_id, regex, severity, message, max_proximity_chars)
PROXIMITY_RULES: list[tuple[str, str, str, str, int]] = [
    ("doubled-cleft",
     r"\bWhat\s+\w+(?:\s+\w+){0,6}?\s+(?:makes|is|carries|needs|does|matters|changes|survives)\s+\w+(?:\s+\w+){0,6}?\s+is\b",
     "warn",
     "Doubled 'What X is Y' cleft (two within close range). Sharper tell than single use; convert at least one to plain subject-verb.",
     220),
]

# Pattern rules that flag every occurrence (not count-thresholded).
PATTERN_RULES: list[tuple[str, str, str, str, int]] = []


# Heuristic: long-sentence detector. Naive sentence split on . ! ? followed
# by whitespace + capital, abbreviation-aware just enough not to fire on
# "et al." or "vs.". Mirrors pencil's splitter loosely.
_ABBREVS = {"e.g.", "i.e.", "et al.", "vs.", "cf.", "etc.", "approx.",
            "Fig.", "Eq.", "Sec.", "Tab.", "Mr.", "Dr.", "Prof.",
            "St.", "Inc.", "Ltd.", "No.", "Vol.", "p.", "pp.", "Refs."}
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z\[(])")

LONG_SENTENCE_WARN = 45
LONG_SENTENCE_ERROR = 65


# ---------------------------------------------------------------------------
# Markdown awareness
# ---------------------------------------------------------------------------

def _strip_code_and_math(text: str) -> str:
    """Replace fenced code, inline code, display math, and HTML comments
    with same-length whitespace so line/column offsets are preserved."""
    out = list(text)
    in_fence = False
    in_math_block = False
    in_comment = False
    line_start = 0
    i = 0
    n = len(text)
    while i < n:
        if text[i] == "\n":
            line_start = i + 1
            i += 1
            continue
        if not (in_fence or in_math_block or in_comment):
            # Detect new line-start fence/math/comment
            if i == line_start:
                rest = text[i:i + 3]
                if rest == "```":
                    in_fence = True
                    while i < n and text[i] != "\n":
                        out[i] = " "
                        i += 1
                    continue
                if rest[:2] == "$$":
                    in_math_block = True
                    while i < n and text[i] != "\n":
                        out[i] = " "
                        i += 1
                    continue
            if text[i:i + 4] == "<!--":
                in_comment = True
            elif text[i] == "`":
                end = text.find("`", i + 1)
                if end > 0 and "\n" not in text[i:end]:
                    for j in range(i, end + 1):
                        out[j] = " "
                    i = end + 1
                    continue
            elif text[i] == "$":
                end = text.find("$", i + 1)
                if end > 0 and "\n" not in text[i:end]:
                    for j in range(i, end + 1):
                        out[j] = " "
                    i = end + 1
                    continue
        else:
            if in_fence and text[i:i + 3] == "```":
                in_fence = False
                for j in range(i, min(i + 3, n)):
                    out[j] = " "
                i += 3
                continue
            if in_math_block and text[i:i + 2] == "$$":
                in_math_block = False
                out[i] = out[i + 1] = " "
                i += 2
                continue
            if in_comment and text[i:i + 3] == "-->":
                in_comment = False
                for j in range(i, min(i + 3, n)):
                    out[j] = " "
                i += 3
                continue
            out[i] = " " if text[i] != "\n" else "\n"
        i += 1
    return "".join(out)


def _line_col(text: str, offset: int) -> tuple[int, int]:
    """Convert a 0-based byte offset to (1-based line, 1-based column)."""
    line = text.count("\n", 0, offset) + 1
    last_nl = text.rfind("\n", 0, offset)
    col = offset - last_nl
    return line, col


def _excerpt(text: str, offset: int, span: int = 80) -> str:
    start = max(0, offset - 10)
    end = min(len(text), offset + span)
    return text[start:end].replace("\n", " ").strip()


# ---------------------------------------------------------------------------
# Per-rule audit functions
# ---------------------------------------------------------------------------

def _audit_hard_artifacts(text: str, source: str) -> list[Finding]:
    """Hard artifacts run against the RAW text (not source-with-code-stripped)
    because they often appear inside what looks like a citation or URL."""
    out = []
    for rule_id, pattern, message in HARD_ARTIFACT_RULES:
        for m in re.finditer(pattern, text, flags=re.IGNORECASE | re.MULTILINE):
            line, col = _line_col(text, m.start())
            out.append(Finding(line, col, "error", rule_id, message,
                               _excerpt(text, m.start())))
    return out


def _audit_single_phrases(text: str, source: str) -> list[Finding]:
    out = []
    for rule_id, pattern, severity, message in SINGLE_PHRASE_RULES:
        for m in re.finditer(pattern, source, flags=re.IGNORECASE):
            line, col = _line_col(source, m.start())
            out.append(Finding(line, col, severity, rule_id, message,
                               _excerpt(text, m.start())))
    return out


def _audit_cluster_rules(text: str, source: str) -> list[Finding]:
    """Cluster rules: fire when ≥threshold matches appear within a paragraph
    or 200-word sliding window."""
    out = []
    paragraphs: list[tuple[int, str]] = []
    offset = 0
    for chunk in re.split(r"(\n\s*\n)", source):
        if chunk.strip():
            paragraphs.append((offset, chunk))
        offset += len(chunk)

    for rule_id, pattern, threshold, scope, severity, message in CLUSTER_RULES:
        regex = re.compile(pattern, flags=re.IGNORECASE)
        if scope == "paragraph":
            for para_offset, para in paragraphs:
                hits = list(regex.finditer(para))
                if len(hits) >= threshold:
                    line, col = _line_col(source, para_offset + hits[0].start())
                    out.append(Finding(line, col, severity, rule_id,
                                       f"{message} ({len(hits)} hits in this paragraph)",
                                       _excerpt(text, para_offset + hits[0].start())))
        elif scope == "200w":
            words = list(re.finditer(r"\S+", source))
            window = 200
            i = 0
            seen_starts: set[int] = set()
            while i + window < len(words):
                window_start = words[i].start()
                window_end = words[i + window].end()
                hits = list(regex.finditer(source, window_start, window_end))
                if len(hits) >= threshold:
                    if hits[0].start() not in seen_starts:
                        line, col = _line_col(source, hits[0].start())
                        out.append(Finding(line, col, severity, rule_id,
                                           f"{message} ({len(hits)} hits in a 200-word span)",
                                           _excerpt(text, hits[0].start())))
                        seen_starts.add(hits[0].start())
                    i += window  # advance past this window to avoid duplicates
                else:
                    i += 50  # slide forward
    return out


def _audit_repeated_phrases(text: str, source: str) -> list[Finding]:
    out = []
    for rule_id, pattern, max_count, severity, message in REPEATED_PHRASE_RULES:
        flags = re.IGNORECASE | (re.MULTILINE if rule_id.startswith("repeat-what") else 0)
        matches = list(re.finditer(pattern, source, flags=flags))
        if len(matches) <= max_count:
            continue
        for m in matches:
            line, col = _line_col(source, m.start())
            out.append(Finding(line, col, severity, rule_id,
                               f"{message} (this is occurrence {matches.index(m) + 1} of {len(matches)})",
                               _excerpt(text, m.start())))
    return out


def _audit_pattern_rules(text: str, source: str) -> list[Finding]:
    out = []
    for rule_id, pattern, severity, message, flags in PATTERN_RULES:
        for m in re.finditer(pattern, source, flags=flags):
            line, col = _line_col(source, m.start())
            out.append(Finding(line, col, severity, rule_id, message,
                               _excerpt(text, m.start())))
    return out


def _audit_long_sentences(text: str, source: str) -> list[Finding]:
    out = []
    cursor = 0
    for line_no, line in enumerate(source.split("\n"), start=1):
        if not line.strip() or line.lstrip().startswith(("#", "|", "-", "*", ">")):
            cursor += len(line) + 1
            continue
        # Split into sentences within this line
        idx = cursor
        for sent in _SENT_SPLIT.split(line):
            sent = sent.strip()
            if not sent:
                continue
            words = re.findall(r"\b\w+\b", sent)
            n = len(words)
            offset_in_text = source.find(sent[:40], idx) if len(sent) >= 40 else idx
            if offset_in_text < 0:
                offset_in_text = idx
            line_no2, col = _line_col(source, offset_in_text)
            if n >= LONG_SENTENCE_ERROR:
                out.append(Finding(line_no2, col, "warn", "sentence-too-long",
                                   f"{n}-word sentence. Break into shorter sentences; reviewers tire by clause 4.",
                                   _excerpt(text, offset_in_text)))
            elif n >= LONG_SENTENCE_WARN:
                out.append(Finding(line_no2, col, "info", "sentence-long",
                                   f"{n}-word sentence. Consider breaking up.",
                                   _excerpt(text, offset_in_text)))
            idx = offset_in_text + len(sent)
        cursor += len(line) + 1
    return out


def _audit_proximity_pairs(text: str, source: str) -> list[Finding]:
    """Flag patterns that are tells specifically when they appear close
    together (e.g., two clefts in adjacent sentences)."""
    out = []
    for rule_id, pattern, severity, message, prox in PROXIMITY_RULES:
        matches = list(re.finditer(pattern, source, flags=re.MULTILINE))
        if len(matches) < 2:
            continue
        for i, m in enumerate(matches):
            for j in range(i + 1, len(matches)):
                if matches[j].start() - m.end() <= prox:
                    line, col = _line_col(source, m.start())
                    out.append(Finding(line, col, severity, rule_id,
                                       f"{message} (paired with line {_line_col(source, matches[j].start())[0]})",
                                       _excerpt(text, m.start())))
                    break
    return out


def _audit_em_dash_density(text: str, source: str) -> list[Finding]:
    out = []
    offset = 0
    for line in source.split("\n"):
        n = line.count("—") + line.count("–")
        if n >= 3:
            line_no, col = _line_col(source, offset)
            out.append(Finding(line_no, 1, "info", "density-em-dash-line",
                               f"{n} em/en-dashes on one line. Convert most to commas, periods, or parentheses.",
                               _excerpt(text, offset)))
        offset += len(line) + 1
    return out


def _audit_bold_density(text: str, source: str) -> list[Finding]:
    """Flag mid-paragraph bold (more than one **...** span per paragraph,
    or a bold span that does not start at the beginning of its paragraph)."""
    out = []
    paragraphs = re.split(r"\n\s*\n", source)
    offset = 0
    for para in paragraphs:
        bolds = list(re.finditer(r"\*\*([^*\n]{2,})\*\*", para))
        if len(bolds) >= 3:
            m = bolds[0]
            line, col = _line_col(source, offset + m.start())
            out.append(Finding(line, col, "info", "bold-overuse",
                               f"{len(bolds)} bold spans in one paragraph. Pick one register: bold the lede only.",
                               _excerpt(text, offset + m.start())))
        offset += len(para) + 2
    return out


def audit_text(text: str, *, locked_spans: list[tuple[int, int]] | None = None) -> list[Finding]:
    """Run every rule against ``text`` and return findings sorted by location.

    If ``locked_spans`` is provided (list of (start_offset, end_offset)
    tuples), findings that fall inside any locked span are dropped — those
    are the human author's voice and not subject to anti-AI rules."""
    source = _strip_code_and_math(text)
    findings: list[Finding] = []
    findings += _audit_hard_artifacts(text, source)
    findings += _audit_single_phrases(text, source)
    findings += _audit_repeated_phrases(text, source)
    findings += _audit_pattern_rules(text, source)
    findings += _audit_long_sentences(text, source)
    findings += _audit_bold_density(text, source)
    findings += _audit_em_dash_density(text, source)
    findings += _audit_proximity_pairs(text, source)
    findings += _audit_cluster_rules(text, source)

    if locked_spans:
        offsets_by_line: dict[int, int] = {}
        running = 0
        for line_no, line in enumerate(text.split("\n"), start=1):
            offsets_by_line[line_no] = running
            running += len(line) + 1

        def in_locked(f: Finding) -> bool:
            line_offset = offsets_by_line.get(f.line, 0)
            char_offset = line_offset + f.column - 1
            for start, end in locked_spans:
                if start <= char_offset < end:
                    return True
            return False

        findings = [f for f in findings if not in_locked(f)]

    findings.sort()
    return findings


# ---------------------------------------------------------------------------
# Pencil sidecar integration
# ---------------------------------------------------------------------------

def _read_file(file_path: Path) -> str:
    """Read a markdown file or extract markdown cells from a Jupyter notebook.

    For .ipynb files: returns concatenated markdown-cell sources separated
    by blank lines. Code cells, outputs, and raw cells are skipped — only
    prose is audited."""
    if file_path.suffix == ".ipynb":
        nb = json.loads(file_path.read_text())
        cells = nb.get("cells", [])
        chunks = []
        for cell in cells:
            if cell.get("cell_type") != "markdown":
                continue
            source = cell.get("source", "")
            if isinstance(source, list):
                source = "".join(source)
            if source.strip():
                chunks.append(source.rstrip() + "\n")
        return "\n".join(chunks)
    return file_path.read_text()


def _load_locked_spans(file_path: Path) -> list[tuple[int, int]]:
    sc_path = file_path.with_suffix(file_path.suffix + ".pencil.json")
    if not sc_path.exists():
        return []
    sc = json.loads(sc_path.read_text())
    text = file_path.read_text()
    spans = []
    cursor = 0
    for s in sc.get("sentences", []):
        if s.get("status") != "locked":
            continue
        sent = s.get("text", "")
        if not sent:
            continue
        idx = text.find(sent, cursor)
        if idx < 0:
            continue
        spans.append((idx, idx + len(sent)))
        cursor = idx + len(sent)
    return spans


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

_SEV_GLYPH = {"info": "·", "warn": "!", "error": "X"}
_SEV_ANSI = {"info": "\033[90m", "warn": "\033[33m", "error": "\033[31m"}
_RESET = "\033[0m"


def format_findings(findings: list[Finding], *, color: bool = True) -> str:
    if not findings:
        return "clean — no AI-tell patterns detected."
    by_severity: dict[str, int] = {"info": 0, "warn": 0, "error": 0}
    by_rule: dict[str, int] = {}
    lines = []
    for f in findings:
        by_severity[f.severity] += 1
        by_rule[f.rule] = by_rule.get(f.rule, 0) + 1
        glyph = _SEV_GLYPH[f.severity]
        if color:
            sev = f"{_SEV_ANSI[f.severity]}{glyph} {f.severity}{_RESET}"
        else:
            sev = f"{glyph} {f.severity}"
        lines.append(f"  {f.line:>4}:{f.column:<3} {sev:<14} {f.rule:<28} {f.message}")
        lines.append(f"        > {f.excerpt[:110]}")
    summary = (f"\n{by_severity['error']} error · "
               f"{by_severity['warn']} warn · "
               f"{by_severity['info']} info "
               f"({len(findings)} total, {len(by_rule)} rules)")
    by_rule_lines = "\n".join(
        f"  {n:>3}  {rule}" for rule, n in sorted(by_rule.items(), key=lambda kv: -kv[1])
    )
    return "\n".join(lines) + summary + "\n\nrule counts:\n" + by_rule_lines


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="muriel.aiism", description=__doc__.split("\n\n")[0])
    p.add_argument("file", help="markdown file to audit")
    p.add_argument("--severity", choices=SEVERITIES, default="warn",
                   help="exit nonzero if any finding is at or above this severity (default: warn)")
    p.add_argument("--respect-pencil", action="store_true",
                   help="skip findings inside pencil-locked sentences (reads <file>.pencil.json)")
    p.add_argument("--no-color", action="store_true", help="disable ANSI color")
    p.add_argument("--rule", action="append", help="filter to specific rule id (repeatable)")
    p.add_argument("--json", action="store_true", help="emit findings as JSON for tool integration")
    args = p.parse_args(argv)

    fp = Path(args.file)
    if not fp.exists():
        print(f"file not found: {fp}", file=sys.stderr)
        return 2

    text = _read_file(fp)
    locked_spans = _load_locked_spans(fp) if args.respect_pencil else []
    findings = audit_text(text, locked_spans=locked_spans)
    if args.rule:
        findings = [f for f in findings if f.rule in set(args.rule)]

    if args.json:
        payload = {
            "file": str(fp),
            "findings": [
                {"line": f.line, "column": f.column, "severity": f.severity,
                 "rule": f.rule, "message": f.message, "excerpt": f.excerpt}
                for f in findings
            ],
            "summary": {
                "total": len(findings),
                "error": sum(1 for f in findings if f.severity == "error"),
                "warn": sum(1 for f in findings if f.severity == "warn"),
                "info": sum(1 for f in findings if f.severity == "info"),
            },
        }
        print(json.dumps(payload, indent=2))
    else:
        print(format_findings(findings, color=not args.no_color))

    if not findings:
        return 0
    threshold = _SEV_ORDER[args.severity]
    worst = max(_SEV_ORDER[f.severity] for f in findings)
    return 1 if worst >= threshold else 0


if __name__ == "__main__":
    sys.exit(main())
