# FullRead Verification & On-Chain Performance

## 1. Network & Contract Deployments
- **Network**: GenLayer Studio Network (`studionet`)
- **Chain ID**: `61999`
- **RPC URL**: `https://studio.genlayer.com/api`
- **Explorer Base**: `https://genlayer-explorer.vercel.app`
- **GenVM Runner Version**: `v0.2.16-x86_64-linux-release`

| Contract | Address | Deploy Tx Hash | Deploy Status | Result |
| :--- | :--- | :--- | :--- | :--- |
| **RuntimeProbe** | `0x81BDF8625D1E8D35cF30a1a4B1C4DB0c1D997D0a` | `0xfbc4d8e5c93e43e6e3d64f14e4277c83f31f0ae6f286d6a27a5a47df834ab256` | `ACCEPTED` | `MAJORITY_AGREE` |
| **FullRead** | `0x86579015A531C3CB76879213244BcE355Ad4EA8C` | `0x9352fcce7dc65da4f6b9e4a76d64c17e153596742bc885a271844fba6bfe0668` | `ACCEPTED` | `MAJORITY_AGREE` |
| **DocumentPolicyConsumer** | `0x3C0f216B8df54c48d6a95F898c35482E7BA5370d` | `0xb1e5ef320972e55aaf531713ee786b19de9fd81443c1c6fce4636241ebeb37e9` | `ACCEPTED` | `MAJORITY_AGREE` |

---

## 2. On-Chain Transaction Log

| Operation | Target / Review ID | Tx Hash | Latency | Status | Result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **M0 Probe Web & Consensus** | `RuntimeProbe` | `0x6ba2d9f9aecffc8dafa3fe574b6ff3a3de00c2e2f043486a217a55a01ebd2995` | ~14.2s | `ACCEPTED` | `MAJORITY_AGREE` |
| **Register Checklist** | CID: `60932b48524e8f2a` | `0x17f2e8e28f136737ca5b30cc57b00af23b18230de55030b5ecad80e3c8c089f0` | ~3.5s | `ACCEPTED` | `MAJORITY_AGREE` |
| **M1 Test Review** | `60932b48_31dc8fbc_r1` | `0xfc4c75b5e0df91168d3906494f7eda3edf83695896304017943bb8e45848baa6` | **18.98s** | `ACCEPTED` | `MAJORITY_AGREE` |

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
