# GenLayer Studionet Runtime Notes (Milestone 0 Probe)

## 1. Environment & Header
- **GenLayer Studio Network (Studionet)**: Chain ID `61999`
- **RPC URL**: `https://studio.genlayer.com/api`
- **Explorer**: `https://genlayer-explorer.vercel.app`
- **GenVM Runner**: `v0.2.16-x86_64-linux-release`
- **Probe Contract Address**: `0x81BDF8625D1E8D35cF30a1a4B1C4DB0c1D997D0a`
- **Probe Deploy Tx**: `0xfbc4d8e5c93e43e6e3d64f14e4277c83f31f0ae6f286d6a27a5a47df834ab256`
- **Web & Consensus Probe Tx**: `0x6ba2d9f9aecffc8dafa3fe574b6ff3a3de00c2e2f043486a217a55a01ebd2995` (`Status: ACCEPTED`, `Result: MAJORITY_AGREE`)
- **Contract Header & Dependencies**:
  ```python
  # v0.2.16
  # { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

  from genlayer import *
  ```
- **Encoding Requirement**: Pure ASCII required. Non-ASCII characters (em-dashes, curly quotes, arrows) cause schema extraction failure (`Could not load contract schema`).

## 2. gl.vm Inspection & Consensus
- `run_nondet`: **PRESENT** (`callable`)
- `run_nondet_unsafe`: **PRESENT** (`callable`)
- `run_nondet_default`: **ABSENT** (`hasattr` is `False`)
- `Return`: **PRESENT** (Used to wrap leader return data, accessed via `leader_res.calldata`)
- `UserError`: **PRESENT** (Used for raising user errors)

### Verified Consensus Adapter
Custom consensus using `gl.vm.run_nondet` executed successfully with 5/5 validator votes (`MAJORITY_AGREE`):
```python
def _run_custom_consensus(leader_fn, validator_fn):
    vm = gl.vm
    fn = (
        getattr(vm, "run_nondet_default", None)
        or getattr(vm, "run_nondet", None)
        or getattr(vm, "run_nondet_unsafe", None)
    )
    if fn is not None:
        return fn(leader_fn, validator_fn)
    return gl.eq_principle.strict_eq(leader_fn)

def _leader_payload(leader_res):
    if leader_res is None:
        return None
    if hasattr(leader_res, "calldata"):
        cd = leader_res.calldata
        if isinstance(cd, dict):
            return cd
        if isinstance(cd, str):
            try:
                return json.loads(cd)
            except Exception:
                return None
    if isinstance(leader_res, dict):
        return leader_res
    if isinstance(leader_res, str):
        try:
            return json.loads(leader_res)
        except Exception:
            return None
    return None
```

## 3. Web & Network Access
- `gl.nondet.web.get(url)` is **ACTIVE and VERIFIED** on-chain.
- Return type: `<class 'genlayer.gl.nondet.web.Response'>`
- Key attributes:
  - `status`: `int` (HTTP status code, e.g. 200, 404)
  - `body`: `bytes` (Must be decoded using `body.decode("utf-8")`)
  - `headers`: `dict`
- Tag stripping should be handled deterministically in pure Python post-decoding.

## 4. Storage & Imports
- `gl.storage.copy_to_memory`: **PRESENT** (`hasattr` is `True`).
- Storage type: `TreeMap[str, str]` (keys and values must be `str`, no `TreeMap()` re-assignment in `__init__`).
- Standard library modules `hashlib` and `json` import and run inside methods without issue.
- Contract class must inherit `gl.Contract` and define an explicit `def __init__(self): pass`.
