# Prior Art and Novelty Analysis

## Investigation Summary
Before finalizing the implementation and live verification, an exhaustive search was conducted across GenLayer repositories, ecosystem documentation, and publications for the following target phrases:
- `"genlayer chunked document review"`
- `"genlayer quote grounding"`
- `"genlayer coverage"`

## Findings

### 1. "genlayer chunked document review"
- **Status**: No prior art found.
- **Analysis**: Standard GenLayer examples and community Intelligent Contracts process documents either as a single prompt string or slice a fixed head prefix (e.g., `text[:6000]`). Naive single-prompt architectures are susceptible to evasion attacks where adverse clauses buried on later pages remain completely invisible to the LLM judge. No contract implements deterministic paragraph-preserving splitting across sequential LLM evaluations with code-calculated aggregate coverage.

### 2. "genlayer quote grounding"
- **Status**: No prior art found.
- **Analysis**: While quote grounding is recognized in RAG research as an off-chain hallucination guardrail, no deployed GenLayer contract implements on-chain code-verified quote grounding. In FullRead, LLM claims of `PRESENT` are rejected and downgraded to `UNCLEAR` unless supported by a verbatim citation of at least 12 characters that deterministic code proves is a substring of the active chunk.

### 3. "genlayer coverage"
- **Status**: Disambiguated / No contract coverage mechanism found.
- **Analysis**: The term "coverage" in existing GenLayer contexts refers either to:
  1. Parametric insurance claim payout limits and liability scopes;
  2. Software test coverage in developer CI/CD pipelines; or
  3. Validator stake coverage and appeal bond thresholds.
  No existing contract defines or tracks `coverage_bp` (basis points of total document text evaluated) to mathematically disallow a `PASS` verdict whenever chunks are truncated.

## Conclusion
FullRead's combination of deterministic whole-document chunking, basis-point coverage enforcement, code-verified quote grounding, and code-derived verdict synthesis represents a completely novel design on GenLayer.
