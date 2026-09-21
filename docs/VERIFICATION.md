# FullRead Verification & On-Chain Performance

## 1. Network & Contract Deployments
- **Network**: GenLayer Studio Network (`studionet`)
- **Chain ID**: `61999`
- **RPC URL**: `https://studio.genlayer.com/api`
- **Explorer Base**: `https://explorer-studio.genlayer.com`
- **GenVM Runner Version**: `v0.2.16-x86_64-linux-release`

| Contract | Address | Deploy Tx Hash | Deploy Status | Result |
| :--- | :--- | :--- | :--- | :--- |
| **RuntimeProbe** | `0x81BDF8625D1E8D35cF30a1a4B1C4DB0c1D997D0a` | `0xfbc4d8e5c93e43e6e3d64f14e4277c83f31f0ae6f286d6a27a5a47df834ab256` | `ACCEPTED` | `MAJORITY_AGREE` |
| **FullRead** | `0xfC2d4d29b46f44A6f4d09496451ff662dA8b4d33` | `0x78d9b6be8e9bf32bc6cec8ecb9252268ee420f4bb2bba545cfaa7f45db2801d8` | `ACCEPTED` | `MAJORITY_AGREE` |
| **DocumentPolicyConsumer** | `0xE8424C568FCB418fBAD5D272470f9A9fD6452860` | `0x89ce9521ba7108bcaddd8ebfc47c153a87be211b57e06ec553328bac53008e82` | `ACCEPTED` | `MAJORITY_AGREE` |

---

## 2. On-Chain Transaction Log (Studionet Measured Evidence)

| Operation | Target / Review ID | Tx Hash | Measured Latency | Tx Status | Consensus Result | Outcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **M0 Probe Web & Consensus** | `RuntimeProbe` | `0x6ba2d9f9aecffc8dafa3fe574b6ff3a3de00c2e2f043486a217a55a01ebd2995` | ~14.2s | `ACCEPTED` | `MAJORITY_AGREE` | - |
| **Register Checklist** | CID: `60932b48524e8f2a` | `0xca3034fa752650a8035d13e85f919009ecc47b464b11eb4a5fe0fcc483ff1b1f` | ~12.1s | `ACCEPTED` | `MAJORITY_AGREE` | - |
| **M4 Review 1 (Compliant)** | `60932b48_34af5201_r1` | `0x07111f986baa69c2df180f454e0c3fa95d7c239f8ff325aff7b59cd336c9a2cc` | **106.44s** | `ACCEPTED` | `MAJORITY_AGREE` | `PASS` (10000 bp) |
| **M4 Review 2 (First Chunk)** | `60932b48_d101aeae_r1` | `0xe811755132eee419fd92abd835b6e77fd14847869840a1cac974e208fd82d70b` | **52.30s** | `ACCEPTED` | `MAJORITY_AGREE` | `FAIL` (10000 bp) |
| **M4 Review 3 (Buried Clause)** | `60932b48_abac5b2d_r1` | `0xb39d24b377990cb335e46019eccb46f38faff55cb617755a142150c92308e212` | **29.12s** | `ACCEPTED` | `MAJORITY_AGREE` | `FAIL` (10000 bp) |
| **Consumer Cross-Contract Approval** | Document Policy Approval | `0x3a3955069980a2cb56da8a874ae6ec1d5c2788a2b61429a2b6d87a5008fffb4a` | ~11.8s | `ACCEPTED` | `MAJORITY_AGREE` | Approved: `true` |

### Cross-Contract Verification Details
- `DocumentPolicyConsumer.approve_if_passed(review_id)` made an on-chain cross-contract view call to `FullRead.get_review(review_id)`.
- Verified that `outcome == "PASS"` and `coverage_bp == 10000`.
- Calling `consumer.is_document_approved(doc_url)` returned `true`.
- Calling `consumer.get_approval_review_id(doc_url)` returned `"60932b48_34af5201_r1"`.

---

## 3. Automated Test Verification

### Layer 1: Pure Logic & Normalization (`tests/direct/test_pure_helpers.py`)
- **Results**: 11 passed in 0.004s.
- Verifies paragraph preservation, whitespace/CRLF canonicalization, HTML stripping, case-insensitive quote grounding (min 12 chars), JSON parse resilience, reduce logic across severity/polarity matrices, and validator equality comparison (`_same_decision`).

### Layer 2 & 3: Pipeline, Injection Guard & Consensus Simulation (`tests/direct/test_pipeline_and_validator.py`)
- **Results**: 8 passed in 0.008s.
- Verifies:
  - Star test: Buried clause in last chunk produces `FAIL` while single-chunk window produces `UNRESOLVED` / `REVIEW`.
  - Hallucinated / ungrounded quotes stripped and downgraded.
  - Documents exceeding `max_chunks` capped at `REVIEW` (never `PASS`).
  - Malformed LLM output handled safely without crash.
  - Prompt injection attacks contained via `<UNTRUSTED_DOCUMENT>` boundaries.
  - Non-200 / 404 responses handled cleanly.
  - Validator independent verification with tolerance for quote wording variations.

### Fixtures Execution (`tests/direct/test_fixtures.py`)
- **Results**: 3 passed in 0.039s.
- Verifies the 3 actual full-length markdown fixtures (`compliant.md`, `violation_in_first_chunk.md`, `violation_in_last_chunk.md`) produce exact expected outcomes (`PASS`, `FAIL`, `FAIL`).
