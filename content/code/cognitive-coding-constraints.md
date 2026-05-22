---
title: "Cognitive Coding Constraints: When Code Structure Affects LLM Cost"
date: 2026-03-04
comments: true
---

**Cognitive-Derived Coding Constraints (CDCC)**: A reproducible Python research pipeline that measures how naming conventions and function complexity affect LLM tokenization, output quality, and API cost — with results that turned out to be more significant than expected.

## The Question

LLMs process code as tokens. Tokens are not characters, not words, not logical units — they're subword sequences determined by a trained vocabulary. The same identifier written differently produces a different number of tokens. Does that difference matter?

The hypothesis worth testing: if cognitive science tells us that human programmers prefer certain naming conventions for readability, do LLMs share those preferences at the tokenization level? And if they do, does writing code that reads well for humans also cost less to process by machines?

The answer is yes, and the dollar amounts are not trivial.

## Three Experiments

### Experiment 1: Tokenization by Naming Convention

A corpus of 200 identifiers was created across four naming styles: `camelCase`, `snake_case`, `dot.notation`, and `PascalCase`. Each identifier was tokenized by five different LLM tokenizers (GPT-4o, GPT-4, Claude, Llama, Gemini).

**Key finding**: dot notation produces 1.12–1.20× more tokens than camelCase across all tested tokenizers. Wilcoxon signed-rank test, p < 0.001.

```python
import tiktoken

encoders = {
    'gpt-4o':  tiktoken.get_encoding('o200k_base'),
    'gpt-4':   tiktoken.get_encoding('cl100k_base'),
}

identifiers = {
    'camelCase':    'getUserProfileAvatar',
    'snake_case':   'get_user_profile_avatar',
    'dot_notation': 'user.profile.avatar',
}

for style, ident in identifiers.items():
    for model, enc in encoders.items():
        tokens = enc.encode(ident)
        print(f"{model} | {style}: {len(tokens)} tokens — {tokens}")
```

The camelCase advantage is consistent across all five tokenizers with Spearman ρ = 1.000. This is not a GPT artifact — it's a property of how subword tokenization works on concatenated words versus separated words.

### Experiment 2: The Production Function

CDCC defines thresholds derived from cognitive science: functions should be under ~10 lines, cyclomatic complexity below 4, nesting depth below 3. These match human working-memory constraints.

The experiment measured LLM output quality (output tokens per input token) for 100 real Python functions from open-source repositories, split by whether they satisfy CDCC thresholds or violate them.

**Key finding**: CDCC-compliant functions achieve 0.141 output/input ratio versus 0.043 for violating functions — a 3.3× gap, Mann-Whitney U, p < 0.001.

The production function elasticity β = 0.102: each 1% increase in function complexity yields only 0.10% more useful output. Complexity yields diminishing returns, measurably.

### Experiment 3: Cost Projection

At 1 million API calls per day, the camelCase vs. dot-notation token difference projects to an annual cost delta of **$54,499** (95% CI: $46,902–$62,301) at GPT-4o pricing.

```python
def annual_cost_delta(
    daily_calls: int,
    dot_tokens: float,
    camel_tokens: float,
    cost_per_token: float = 5e-6
) -> float:
    daily_diff = (dot_tokens - camel_tokens) * daily_calls
    return daily_diff * cost_per_token * 365
```

This is not a recommendation to use camelCase everywhere. It's a measurement of the economic scale of a decision that most teams treat as a style preference.

## Reproducibility

The pipeline is fully reproducible. All LLM responses are cached with SHA-256 keyed JSON — re-runs don't re-invoke the model, so results are stable and free to reproduce:

```bash
git clone https://github.com/lucianofedericopereira/cognitive-coding-constraints
cd cognitive-coding-constraints
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

make corpus   # Build identifier corpus
make exp1     # Tokenization analysis
make exp3     # Cross-model correlations
make exp2     # Production function (requires Ollama)
make plots    # Generate figures
```

Experiment 2 uses Ollama for local inference — no API key, no cost, full control over the model.

## The Companion Papers

This repository is the empirical component of a larger research effort:

- *Confirmation Bias in Post-LLM Software Architecture* — on how teams optimize for LLM readability at the expense of human maintainability
- *Cognitive-Derived Constraints for AI-Assisted Software Engineering* — the theoretical framework that CDCC is grounded in

The empirical study exists to validate the framework with data, not just argument.

## What to Do With This

The actionable takeaway is not "switch all your APIs to camelCase." It's more nuanced:

1. **Name for humans first.** CDCC-compliant code reads better and processes better.
2. **Measure before optimizing.** Token counts are auditable. Run your codebase through a tokenizer before assuming you have a cost problem.
3. **Complexity has a price.** Functions that violate cognitive thresholds don't just frustrate human reviewers — they produce lower-quality LLM output.

## Links

- **GitHub**: [lucianofedericopereira/cognitive-coding-constraints](https://github.com/lucianofedericopereira/cognitive-coding-constraints)
- **Paper (Zenodo)**: [10.5281/zenodo.18735784](https://doi.org/10.5281/zenodo.18735784)

## License

LGPL-2.1
