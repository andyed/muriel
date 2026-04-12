"""
render_assets.stats — APA-style statistical reporting helpers.

Point estimates, confidence intervals, effect sizes, and phrasing
helpers for research prose, figure captions, and notebook narratives.

Enforces the rules from `channels/science.md` in the Render skill:

  - Every point estimate paired with a 95% CI
  - Every null framed as a detection limit ("not detected at this
    granularity"), never as "no effect"
  - Effect sizes reported with sample size
  - Exploratory findings labeled explicitly

All formatters return plain ``str`` with proper typography:
U+2212 minus signs (not ASCII hyphen), APA-style leading-zero stripping
for probabilities and correlations, non-italic Greek letters inline.

Dependencies
------------
Standard library only. No numpy, scipy, or pandas required. The Cohen's
d, Fisher z, and CI formulas use normal approximations (z = 1.96 for
95% CI) that are accurate for n ≥ 30 and adequate for most reporting.
If your audience needs exact t-distribution CIs, compute those upstream
and pass the endpoints into ``format_comparison`` / ``format_correlation``
directly.

Usage
-----
::

    from render_assets.stats import (
        format_comparison, format_null, format_correlation,
        format_auc, format_chi2, format_exploratory,
        cohens_d, cohens_d_paired, fisher_ci,
        apa_number, format_p, format_ci,
    )

    d = cohens_d(
        mean1=1.42, sd1=0.12, n1=127,
        mean2=0.98, sd2=0.11, n2=127,
    )
    print(format_comparison(
        "baseline", "treatment",
        mean_a=1.42, sd_a=0.12, n_a=127,
        mean_b=0.98, sd_b=0.11, n_b=127,
    ))

    print(format_null(delta=0.03, ci_lo=-0.12, ci_hi=0.18, n=84))
    print(format_correlation(r=0.34, n=62, p=0.007))
    print(format_chi2(chi2=0.09, df=1, n=168, p=0.77, cramers_v=0.02))
"""

from __future__ import annotations

import math
from typing import Optional

__all__ = [
    "apa_number",
    "format_p",
    "format_ci",
    "cohens_d",
    "cohens_d_paired",
    "ci_from_se",
    "ci_from_sd",
    "fisher_ci",
    "format_comparison",
    "format_null",
    "format_correlation",
    "format_auc",
    "format_chi2",
    "format_exploratory",
]


# Critical values for common two-sided CI levels. Normal approximation.
_Z_CRITICAL = {0.10: 1.645, 0.05: 1.960, 0.01: 2.576, 0.001: 3.291}


# ─── Number formatting ───────────────────────────────────────────────────

def apa_number(x: float, decimals: int = 2, strip_zero: bool = False) -> str:
    """
    Format a number in APA style.

    Parameters
    ----------
    x : float
        The number to format.
    decimals : int
        Number of decimal places. Default 2.
    strip_zero : bool
        If True, strip the leading zero (``0.34`` → ``.34``). Use for
        quantities bounded in [0, 1] such as correlations, p-values,
        and probabilities.

    Returns
    -------
    str
        The formatted number. Minus signs are rendered as U+2212 MINUS
        SIGN, not ASCII hyphen, so the string renders correctly in
        typographic contexts.
    """
    if not math.isfinite(x):
        if math.isnan(x):
            return "NaN"
        return "∞" if x > 0 else "−∞"
    s = f"{x:.{decimals}f}"
    if strip_zero:
        s = s.replace("0.", ".").replace("-.", "−.")
    s = s.replace("-", "−")
    return s


def format_p(p: float) -> str:
    """
    APA-style p-value formatter.

    - ``p < .001`` for values below 0.001 (never prints "p = 0.000")
    - ``p > .999`` for values above 0.999
    - Three-decimal form with stripped leading zero otherwise
    """
    if not math.isfinite(p) or p < 0 or p > 1:
        return f"p = {p}"
    if p < 0.001:
        return "p < .001"
    if p >= 0.999:
        return "p > .999"
    s = f"{p:.3f}".replace("0.", ".")
    return f"p = {s}"


def format_ci(
    lo: float, hi: float,
    decimals: int = 2,
    level: int = 95,
    strip_zero: bool = False,
) -> str:
    """Format a confidence interval: ``95% CI [−0.61, −0.27]``."""
    return (
        f"{level}% CI ["
        f"{apa_number(lo, decimals, strip_zero)}, "
        f"{apa_number(hi, decimals, strip_zero)}]"
    )


# ─── Effect-size computations ────────────────────────────────────────────

def cohens_d(
    mean1: float, sd1: float, n1: int,
    mean2: float, sd2: float, n2: int,
    alpha: float = 0.05,
) -> dict:
    """
    Cohen's d for two independent groups (pooled SD), with normal-
    approximation CI.

    Returns a dict with keys:
        d, se, ci_lo, ci_hi, pooled_sd
    """
    pooled_sd = math.sqrt(
        ((n1 - 1) * sd1 ** 2 + (n2 - 1) * sd2 ** 2) / (n1 + n2 - 2)
    )
    d = (mean1 - mean2) / pooled_sd
    # Hedges (1981) SE approximation
    se = math.sqrt((n1 + n2) / (n1 * n2) + d ** 2 / (2 * (n1 + n2)))
    z = _Z_CRITICAL.get(alpha, 1.96)
    return {
        "d": d,
        "se": se,
        "ci_lo": d - z * se,
        "ci_hi": d + z * se,
        "pooled_sd": pooled_sd,
    }


def cohens_d_paired(
    mean_diff: float, sd_diff: float, n: int,
    alpha: float = 0.05,
) -> dict:
    """
    Cohen's d_z for paired / within-subjects designs.

    Returns a dict with keys:
        dz, se, ci_lo, ci_hi
    """
    if sd_diff == 0:
        return {"dz": 0.0, "se": 0.0, "ci_lo": 0.0, "ci_hi": 0.0}
    dz = mean_diff / sd_diff
    se = math.sqrt(1 / n + dz ** 2 / (2 * n))
    z = _Z_CRITICAL.get(alpha, 1.96)
    return {
        "dz": dz,
        "se": se,
        "ci_lo": dz - z * se,
        "ci_hi": dz + z * se,
    }


def ci_from_se(
    mean: float, se: float, alpha: float = 0.05
) -> tuple[float, float]:
    """Two-sided CI for a mean from standard error (normal approximation)."""
    z = _Z_CRITICAL.get(alpha, 1.96)
    return (mean - z * se, mean + z * se)


def ci_from_sd(
    mean: float, sd: float, n: int, alpha: float = 0.05
) -> tuple[float, float]:
    """Two-sided CI for a mean from sample SD and n (normal approximation)."""
    if n < 1:
        return (mean, mean)
    return ci_from_se(mean, sd / math.sqrt(n), alpha)


def fisher_ci(
    r: float, n: int, alpha: float = 0.05
) -> tuple[float, float]:
    """
    Fisher z-transform CI for a Pearson correlation.

    Undefined when |r| ≥ 1 or n < 4; in those edge cases returns the
    point estimate as both endpoints.
    """
    if abs(r) >= 1 or n < 4:
        return (r, r)
    z = _Z_CRITICAL.get(alpha, 1.96)
    fz = 0.5 * math.log((1 + r) / (1 - r))
    se = 1 / math.sqrt(n - 3)
    lo = math.tanh(fz - z * se)
    hi = math.tanh(fz + z * se)
    return (lo, hi)


# ─── Formatted outputs ───────────────────────────────────────────────────

def format_comparison(
    name_a: str, name_b: str,
    mean_a: float, sd_a: float, n_a: int,
    mean_b: float, sd_b: float, n_b: int,
    decimals: int = 2,
    include_means: bool = True,
) -> str:
    """
    Format a between-groups comparison with Δ, 95% CI, Cohen's d, and n.

    Direction: Δ = mean_b − mean_a (treatment − control convention).
    """
    d = cohens_d(mean_a, sd_a, n_a, mean_b, sd_b, n_b)
    delta = mean_b - mean_a
    se_delta = math.sqrt(sd_a ** 2 / n_a + sd_b ** 2 / n_b)
    delta_lo, delta_hi = ci_from_se(delta, se_delta)

    parts = []
    if include_means:
        parts.append(
            f"{name_a}: M = {apa_number(mean_a, decimals)} "
            f"(SD = {apa_number(sd_a, decimals)}, n = {n_a})"
        )
        parts.append(
            f"{name_b}: M = {apa_number(mean_b, decimals)} "
            f"(SD = {apa_number(sd_b, decimals)}, n = {n_b})"
        )
    parts.append(
        f"Δ = {apa_number(delta, decimals)}, "
        f"{format_ci(delta_lo, delta_hi, decimals)}, "
        f"Cohen's d = {apa_number(d['d'], decimals)}, "
        f"n = {n_a + n_b}"
    )
    return ". ".join(parts) + "."


def format_null(
    delta: float, ci_lo: float, ci_hi: float, n: int,
    metric: str = "Δ",
    decimals: int = 2,
) -> str:
    """
    Frame a null result as a detection limit.

    Enforces the ``feedback_empirical_not_truth.md`` rule: never write
    "no effect", write "not detected at this granularity" and state
    what the CI *excludes*.
    """
    wider = max(abs(ci_lo), abs(ci_hi))
    return (
        f"Not detected ({metric} = {apa_number(delta, decimals)}, "
        f"{format_ci(ci_lo, ci_hi, decimals)}, n = {n}). "
        f"The 95% CI excludes effects larger than "
        f"{apa_number(wider, decimals)}; smaller effects may exist but "
        f"cannot be resolved at this sample size."
    )


def format_correlation(
    r: float, n: int,
    decimals: int = 2,
    p: Optional[float] = None,
    alpha: float = 0.05,
) -> str:
    """
    Format a Pearson correlation with Fisher z 95% CI.

    Leading zeros stripped from r and CI bounds (APA convention for
    quantities bounded in [−1, 1]).
    """
    ci_lo, ci_hi = fisher_ci(r, n, alpha)
    out = (
        f"r = {apa_number(r, decimals, strip_zero=True)}, "
        f"{format_ci(ci_lo, ci_hi, decimals, strip_zero=True)}, "
        f"n = {n}"
    )
    if p is not None:
        out += f", {format_p(p)}"
    return out


def format_auc(
    auc: float, n: int,
    ci_lo: Optional[float] = None,
    ci_hi: Optional[float] = None,
    chance: float = 0.5,
    decimals: int = 2,
) -> str:
    """
    Format an ROC-AUC with optional CI and chance reference.
    """
    out = f"AUC = {apa_number(auc, decimals)}"
    if ci_lo is not None and ci_hi is not None:
        out += f", {format_ci(ci_lo, ci_hi, decimals)}"
    out += f", chance = {apa_number(chance, decimals)}, n = {n}"
    return out


def format_chi2(
    chi2: float, df: int, n: int, p: float,
    cramers_v: Optional[float] = None,
    decimals: int = 2,
) -> str:
    """
    Format a chi-squared result with optional Cramer's V.
    """
    out = f"χ²({df}) = {apa_number(chi2, decimals)}, {format_p(p)}"
    if cramers_v is not None:
        out += (
            f", Cramer's V = "
            f"{apa_number(cramers_v, decimals, strip_zero=True)}"
        )
    out += f", n = {n}"
    return out


def format_exploratory(finding_text: str) -> str:
    """
    Label an exploratory finding explicitly.

    Wraps a formatted finding string with the "Exploratory: ..." prefix
    and the "Not pre-registered; candidate for replication." suffix
    required by the rules in channels/science.md.
    """
    return (
        f"Exploratory: {finding_text}. "
        f"Not pre-registered; candidate for replication."
    )
