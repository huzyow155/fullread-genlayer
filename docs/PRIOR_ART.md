# Prior Art and Novelty Analysis

## Investigation Summary
Before finalizing the implementation and verification on studionet, a search was conducted across GenLayer repositories, ecosystem documentation, and community examples for the following target phrases:
- `"genlayer chunked document review"`
- `"genlayer quote grounding"`
- `"genlayer coverage"`

## Findings

### 1. "genlayer chunked document review"
- **Status**: We found no contract that performs chunked full document review.
- **Analysis**: Available GenLayer examples and community Intelligent Contracts typically process documents either within a single prompt string or slice a fixed head prefix (e.g., `text[:6000]`). Naive single-prompt approaches are susceptible to evasion attacks where adverse clauses buried on later pages remain unexamined by the LLM. We found no contract that implements deterministic paragraph-preserving splitting across sequential LLM evaluations with code-calculated aggregate coverage.

### 2. "genlayer quote grounding"
- **Status**: We found no contract that implements on-chain code-verified quote grounding.
- **Analysis**: While quote grounding is recognized in RAG research as an off-chain hallucination guardrail, we found no contract on GenLayer that validates quote grounding directly in contract code. In FullRead, LLM claims of `PRESENT` are rejected and downgraded to `UNCLEAR` unless supported by a verbatim citation of at least 12 characters that deterministic code proves is a substring of the active chunk.

### 3. "genlayer coverage"
- **Status**: Disambiguated / We found no contract that tracks document coverage.
- **Analysis**: The term "coverage" in existing GenLayer contexts refers either to:
  1. Parametric insurance claim payout limits and liability scopes;
  2. Software test coverage in developer CI/CD pipelines; or
  3. Validator stake coverage and appeal bond thresholds.
  We found no contract that defines or tracks `coverage_bp` (basis points of total document text evaluated) to disallow a `PASS` verdict whenever chunks are truncated.

## Conclusion
Based on our review of available repositories and documentation, we found no contract that combines deterministic whole-document chunking, basis-point coverage enforcement, code-verified quote grounding, and code-derived verdict synthesis on GenLayer studionet.
