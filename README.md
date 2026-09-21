# FullRead: Whole-Document Legal & Compliance Intelligent Contract

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

FullRead is a standalone GenLayer Intelligent Contract that reviews entire public documents against structured checklists and proves full coverage.

Deployed to **GenLayer studionet**:
- **Contract Address**: `0xfC2d4d29b46f44A6f4d09496451ff662dA8b4d33`
- **Explorer Link**: [View on GenLayer Explorer](https://explorer-studio.genlayer.com/address/0xfC2d4d29b46f44A6f4d09496451ff662dA8b4d33)
- **Chain ID**: `61999`
- **GenVM Runner**: `v0.2.16-x86_64-linux-release`

---

## The Problem
Most AI-enabled smart contracts read external documents by slicing the beginning of a document (e.g. `page[:6000]`). An adverse party can easily bury an exclusionary clause, auto-renewal trap, or liability disclaimer on page 40. The AI judge evaluates only the opening pages and issues a positive verdict, failing to detect the violation.

## Why GenLayer
GenLayer enables decentralized Intelligent Contracts written in Python that access the web and run LLM evaluations inside a multi-validator consensus protocol. FullRead leverages this to enforce whole-document auditing:
1. Documents are fetched and deterministically partitioned into numbered chunks.
2. The LLM evaluates every chunk under prompt-injection isolation.
3. Every finding requires a verbatim quote verified by deterministic code to be present in that chunk.
4. The final verdict is computed by deterministic Python logic, not free-form LLM text.
5. Validators independently re-fetch the document, re-chunk it, re-verify the leader's quotes, and reach consensus.

---

## Consensus Matrix

| Component | In Non-Deterministic Block? | What Validators Compare | Why |
| :--- | :--- | :--- | :--- |
| **Web Fetch** (`gl.nondet.web.get`) | Yes | `doc_sha256` | Ensures leader and validator analyzed the identical public text. |
| **Document Chunking** | Yes (inside pipeline) | `chunk_hashes` & `coverage_bp` | Guarantees the document was partitioned deterministically and coverage basis points match. |
| **LLM Evaluation** (`gl.nondet.exec_prompt`) | Yes | Derived `status_by_item` & final `outcome` | Different LLMs may phrase answers differently, but the logical classification (`SATISFIED`, `VIOLATED`, etc.) must agree. |
| **Quote Grounding** (`_grounded`) | Yes (inside pipeline) | Leader quotes grounded in validator's own chunks | Prevents fabricated or hallucinated quotes from being accepted into consensus. |
| **Quote Wording** | Yes | **Not compared strictly** | Eliminates spurious validator disagreement when two models select slightly different verbatim bounds of the same sentence. |
| **Verdict Synthesis** (`_reduce`) | Deterministic pure code | `outcome` (`PASS`, `FAIL`, `REVIEW`) | Ensures business logic cannot be subverted by prompt injection. |

---

## Contract API

### Write Methods
- `register_checklist(name: str, items_json: str) -> str`: Registers up to 8 criteria with fields `{id, question, severity, polarity}`. Content-addressed 16-hex sha256 ID.
- `review(checklist_id: str, doc_url: str, max_chunks: int = 3) -> None`: Runs validator consensus review across document chunks. Clamped to 1..4 chunks.
- `recheck(review_id: str) -> None`: Re-executes the review against current document content; sets `"drifted": true` if document hash changed.

### View Methods
- `get_checklist(checklist_id: str) -> str`: Returns canonical JSON checklist.
- `get_review(review_id: str) -> str`: Returns canonical JSON review record.
- `latest_review_id(checklist_id: str, doc_url: str) -> str`: Returns the latest review ID for a given checklist and document URL.
- `list_reviews(checklist_id: str, doc_url: str) -> str`: Returns JSON array of all review IDs for that document (up to 50).

---

## Integration Example

Downstream contracts can inspect review results synchronously using cross-contract views:

```python
from genlayer import *
import json

class DocumentPolicyConsumer(gl.Contract):
    full_read_address: Address
    approved: TreeMap[str, str]

    def __init__(self, full_read_addr: str):
        self.full_read_address = Address(full_read_addr)

    @gl.public.write
    def approve_if_passed(self, review_id: str) -> None:
        full_read = gl.get_contract_at(self.full_read_address)
        review_data = json.loads(full_read.view().get_review(review_id))

        if review_data.get("outcome") != "PASS" or review_data.get("coverage_bp") != 10000:
            raise gl.vm.UserError("Approval requires outcome PASS with 10000 bp coverage")

        self.approved[review_data["doc_url"]] = review_id
```

---

## Deploy Steps for Studionet

1. Clone or open this repository.
2. Install dependencies:
   ```bash
   npm install genlayer-js
   ```
3. Run test suite:
   ```bash
   python -m unittest discover -s tests/direct -p "test_*.py"
   ```
4. Verify pure ASCII:
   ```bash
   python scripts/ascii_check.py contracts/full_read.py
   ```
5. Deploy to studionet:
   ```bash
   node scripts/deploy/deploy_full_read.js
   ```

---

## Prior Art & Novelty
We searched ecosystem contracts and documentation for prior implementations of chunked document reviews and quote grounding on GenLayer. We found no contract that combines deterministic whole-document chunking, basis-point coverage enforcement, code-verified quote grounding, and code-derived verdict synthesis on GenLayer studionet.

---

## Known Limitations
1. **Document Length**: Documents exceeding 40,000 characters or 4 chunks cannot achieve `PASS` (capped at `REVIEW` with partial coverage basis points).
2. **Dynamic Rendering**: Dynamic client-rendered JavaScript pages are out of scope (requires plain text, markdown, or static HTML).
3. **External Translation**: Non-English documents must be evaluated with checklist questions in the source language.
4. **Latency**: Each chunk requires an LLM call across validators; 1-chunk reviews complete in ~19 seconds, 3-chunk reviews take ~45-60 seconds on studionet.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
