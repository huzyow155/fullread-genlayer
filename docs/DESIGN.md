# FullRead Intelligent Contract Design & Architecture

## Overview
FullRead is a standalone GenLayer Intelligent Contract designed to overcome the critical vulnerability of naive context-window slicing in smart contract legal/policy audits (where contracts read only `page[:6000]` and miss decisive clauses).

FullRead guarantees:
1. **Deterministic Whole-Document Coverage**: Splits documents deterministically into numbered chunks, tracking exact coverage basis points (`coverage_bp`). Partial document reads can never produce a `PASS`.
2. **Code-Verified Quote Grounding**: LLMs cannot declare findings without providing verbatim quotes of at least 12 characters. The contract verifies in deterministic code that the quote actually exists in the processed chunk.
3. **Independent Validator Consensus**: Validators re-fetch the public document, re-normalize, re-chunk, and re-analyze independently. Validators compare decisions (`outcome`, `coverage_bp`, `doc_sha256`, `chunk_hashes`, `status_by_item`) and independently verify leader quotes against their own chunks.
4. **Deterministic Synthesis**: Final verdicts (`PASS`, `FAIL`, `REVIEW`) are computed purely in deterministic code, never by free LLM prose.

---

## Storage Schema

Storage uses strictly deploy-friendly `TreeMap[str, str]` mappings:
```python
checklists: TreeMap[str, str]   # checklist_id -> canonical JSON
reviews:    TreeMap[str, str]   # review_id    -> canonical JSON
revcount:   TreeMap[str, str]   # "cid|urlhash" -> revision count as decimal string
review_ids: TreeMap[str, str]   # "cid|urlhash" -> comma-joined review ids (max 50)
```

All storage keys and values are strings. `TreeMap()` is not reassigned in `__init__`.

### 1. Checklist Record Schema (`schema_version: "1.0.0"`)
Key: `checklist_id` (16-char hex sha256 of sorted canonical items)
```json
{
  "schema_version": "1.0.0",
  "id": "16_char_hex_hash",
  "name": "Checklist Display Name",
  "items": [
    {
      "id": "item_identifier",
      "question": "Evaluation question text (<= 200 chars)",
      "severity": "BLOCKER" | "MAJOR" | "MINOR",
      "polarity": "MUST_HAVE" | "MUST_NOT_HAVE"
    }
  ],
  "creator": "0xSenderAddressHex"
}
```

### 2. Review Record Schema (`schema_version: "1.0.0"`)
Key: `review_id` (e.g. `{checklist_id[:8]}_{url_hash[:8]}_r{rev_num}`)
```json
{
  "schema_version": "1.0.0",
  "review_id": "c1a2b3c4_d5e6f7a8_r1",
  "checklist_id": "c1a2b3c4d5e6f7a8",
  "doc_url": "https://...",
  "revision": 1,
  "max_chunks": 3,
  "doc_sha256": "64_char_hex_sha256_of_normalized_text",
  "chunk_hashes": ["hash1", "hash2", "hash3"],
  "coverage_bp": 10000,
  "outcome": "PASS" | "FAIL" | "REVIEW",
  "status_by_item": {
    "item_1": "SATISFIED" | "VIOLATED" | "MISSING" | "CLEAR" | "UNRESOLVED"
  },
  "quotes": {
    "item_1": "verbatim text from document"
  },
  "ungrounded_count": 0,
  "drifted": false,
  "previous_review_id": ""
}
```

---

## Consensus Architecture

Consensus operates through GenLayer's non-deterministic execution framework (`gl.vm.run_nondet` / `gl.vm.run_nondet_unsafe`):

```
+-------------------------------------------------------------+
| Leader Node                                                 |
| 1. Web fetch & clean HTML tags                              |
| 2. Deterministic normalization & chunking                   |
| 3. gl.nondet.exec_prompt for each chunk with injection guard|
| 4. Deterministic code verifies quote grounding in chunks    |
| 5. Deterministic code synthesizes verdict (_reduce)         |
| 6. Returns canonical analysis dictionary                    |
+-------------------------------------------------------------+
                              |
                     Leader Result Payload
                              v
+-------------------------------------------------------------+
| Validator Node                                              |
| 1. Unpack leader payload (gl.vm.Return.calldata)            |
| 2. Re-fetch document independently (blind execution)        |
| 3. Re-normalize, re-chunk, and re-analyze chunks            |
| 4. Check _same_decision(leader, mine):                      |
|    - outcome must match exactly                             |
|    - coverage_bp must match exactly                         |
|    - doc_sha256 must match exactly                          |
|    - chunk_hashes must match exactly                        |
|    - status_by_item must match exactly                      |
| 5. Verify every leader quote is _grounded in validator chunk|
| 6. Returns True if all match, False otherwise               |
+-------------------------------------------------------------+
```

### Why Quote Wording is Decoupled
LLMs can select slightly different verbatim snippets for the same clause (e.g. "mandatory 30-day money back guarantee" vs "30-day money back guarantee for all users"). FullRead validators require:
1. The derived status and final outcome MUST match identically.
2. The leader's quote MUST be grounded in the validator's own document chunk.
3. The document hashes MUST match identically.
Quote wording differences that are both grounded and lead to the same verdict pass validation.

---

## Verdict Decision Matrix (`_reduce`)

For each item:
- If verbatim quote is found and grounded:
  - `MUST_HAVE` &rarr; `SATISFIED`
  - `MUST_NOT_HAVE` &rarr; `VIOLATED`
- If no grounded quote, but LLM reported `UNCLEAR` or document was truncated (`full=False`):
  - &rarr; `UNRESOLVED`
- If no quote and cleanly `ABSENT`:
  - `MUST_HAVE` &rarr; `MISSING`
  - `MUST_NOT_HAVE` &rarr; `CLEAR`

Aggregate Outcome:
- `FAIL`: Any `BLOCKER` is `MISSING` or `VIOLATED`.
- `PASS`: Document was fully read (`full=True`) and ALL `BLOCKER` and `MAJOR` items are `SATISFIED` or `CLEAR`.
- `REVIEW`: Any other condition (e.g., partial document coverage, unresolved items, or ungrounded quotes).
