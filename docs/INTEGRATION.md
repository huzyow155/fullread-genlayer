# FullRead Frontend & dApp Integration Guide

## 1. Network & Connection Details
- **Network Name**: GenLayer Studio Network (`studionet`)
- **Chain ID**: `61999`
- **RPC URL**: `https://studio.genlayer.com/api`
- **Explorer URL**: `https://explorer-studio.genlayer.com`
- **SDK Version**: `genlayer-js@1.1.8`
- **Chain Object**: `import { studionet } from 'genlayer-js/chains'`

### Connecting with User Wallet (MetaMask / EIP-1193)
```typescript
import { createClient } from 'genlayer-js';
import { studionet } from 'genlayer-js/chains';

const client = createClient({
  chain: studionet,
  account: userAddress,
  provider: window.ethereum,
});
```
> **Security Note**: Never embed or store private keys anywhere. The dApp signs all write transactions exclusively through the user's connected wallet (e.g. MetaMask).

---

## 2. Transaction Lifecycle & Success Detection
In GenLayer, write methods initiate a consensus transaction across validator nodes.

1. **Writes Do Not Return Values Directly**:
   Submitting a write transaction returns only the transaction hash. The dApp must wait for receipt finalization and then query the discovery view methods to read the updated on-chain state.
2. **Success Detection**:
   A transaction being included is not sufficient. The UI must verify:
   ```typescript
   const receipt = await client.waitForTransactionReceipt({ hash: txHash });
   const isSuccess = receipt.status_name === "ACCEPTED" && 
                     (receipt.result_name === "MAJORITY_AGREE" || receipt.result_name === "SUCCESS");
   ```

---

## 3. Public Methods Reference

### Write Methods

#### `register_checklist(name: str, items_json: str) -> str`
- **Type**: Write
- **Arguments**:
  - `name` (`str`): Display name of checklist (e.g., `"Terms Compliance"`).
  - `items_json` (`str`): JSON string of checklist items (max 8).
- **Example Call**:
  ```typescript
  const items = [
    { id: "refund", question: "Clear refund policy present", severity: "BLOCKER", polarity: "MUST_HAVE" },
    { id: "auto_renew", question: "Auto renewal without prior notice", severity: "BLOCKER", polarity: "MUST_NOT_HAVE" }
  ];
  const txHash = await client.writeContract({
    address: FULL_READ_ADDRESS,
    functionName: "register_checklist",
    args: ["Terms Compliance", JSON.stringify(items)]
  });
  ```
- **Potential User Errors**:
  - `invalid checklist name length`
  - `items_json is not valid JSON`
  - `items must be a non-empty list`
  - `maximum of 8 checklist items allowed`
  - `item id '{iid}' does not match [a-z0-9_]{1,24}`
  - `duplicate item id '{iid}'`
  - `question for '{iid}' must be between 1 and 200 chars`
  - `invalid severity '{sev}' for '{iid}'`
  - `invalid polarity '{pol}' for '{iid}'`
  - `checklist already registered`
- **Measured Latency**: ~3.5 seconds.

#### `review(checklist_id: str, doc_url: str, max_chunks: int = 3) -> None`
- **Type**: Write (Non-deterministic Validator Consensus)
- **Arguments**:
  - `checklist_id` (`str`): 16-character hex checklist identifier. Example: `"60932b48524e8f2a"`.
  - `doc_url` (`str`): Public document URL. Example: `"https://raw.githubusercontent.com/yeagerai/genlayer-simulator/main/README.md"`.
  - `max_chunks` (`int`): Maximum chunks to evaluate (clamped 1..4). Example: `3`.
- **Potential User Errors**:
  - `unknown checklist_id`
  - `bad doc_url: must start with http:// or https://`
  - `web fetch error: ...`
  - `fetch failed with status 404`
  - `undecodable document body`
  - `document exceeds maximum allowed size`
  - `consensus failed to produce result`
- **Measured Latency**: ~18.98 seconds (at max_chunks=1).

#### `recheck(review_id: str) -> None`
- **Type**: Write (Non-deterministic Validator Consensus)
- **Arguments**:
  - `review_id` (`str`): Previous review identifier. Example: `"60932b48_31dc8fbc_r1"`.
- **Behavior**: Re-evaluates document at same URL; sets `"drifted": true` if document hash changed since previous review.
- **Potential User Errors**:
  - `unknown review_id`
  - `associated checklist missing`
- **Measured Latency**: ~19-25 seconds.

---

### View Methods & Discovery APIs
> **Frontend Discovery Rule**: The frontend must NEVER re-implement content-addressed hashing. Use `latest_review_id` or `list_reviews` to discover IDs.

#### `get_checklist(checklist_id: str) -> str`
- **Type**: View
- **Arguments**: `checklist_id: "60932b48524e8f2a"`
- **Exact Read-Back JSON Shape**:
  ```json
  {
    "creator": "0xeB7e6284cDC2bB808226C57a89d9656Bc6b8C119",
    "id": "60932b48524e8f2a",
    "items": [
      {
        "id": "refund",
        "polarity": "MUST_HAVE",
        "question": "Clear refund policy present",
        "severity": "BLOCKER"
      },
      {
        "id": "auto_renew",
        "polarity": "MUST_NOT_HAVE",
        "question": "Auto renewal without prior notice",
        "severity": "BLOCKER"
      }
    ],
    "name": "Terms Compliance",
    "schema_version": "1.0.0"
  }
  ```

#### `latest_review_id(checklist_id: str, doc_url: str) -> str`
- **Type**: View
- **Arguments**:
  - `checklist_id: "60932b48524e8f2a"`
  - `doc_url: "https://raw.githubusercontent.com/yeagerai/genlayer-simulator/main/README.md"`
- **Returns**: `"60932b48_31dc8fbc_r1"`

#### `list_reviews(checklist_id: str, doc_url: str) -> str`
- **Type**: View
- **Returns**: JSON array of string review IDs (bounded to max 50):
  ```json
  ["60932b48_31dc8fbc_r1"]
  ```

#### `get_review(review_id: str) -> str`
- **Type**: View
- **Arguments**: `review_id: "60932b48_31dc8fbc_r1"`
- **Exact Read-Back JSON Shape**:
  ```json
  {
    "checklist_id": "60932b48524e8f2a",
    "chunk_hashes": [
      "608195a507da81cfd2be86a27861ac46d7080cfe51e33c63a38c2fca283fb8ff"
    ],
    "coverage_bp": 10000,
    "doc_sha256": "608195a507da81cfd2be86a27861ac46d7080cfe51e33c63a38c2fca283fb8ff",
    "doc_url": "https://raw.githubusercontent.com/yeagerai/genlayer-simulator/main/README.md",
    "drifted": false,
    "max_chunks": 1,
    "outcome": "FAIL",
    "previous_review_id": "",
    "quotes": {
      "auto_renew": "",
      "refund": ""
    },
    "review_id": "60932b48_31dc8fbc_r1",
    "revision": 1,
    "schema_version": "1.0.0",
    "status_by_item": {
      "auto_renew": "CLEAR",
      "refund": "MISSING"
    },
    "ungrounded_count": 0
  }
  ```

---

## 4. Known-Good Transaction Hashes for UI Demo
- **Contract Deploy Tx**: `0x9352fcce7dc65da4f6b9e4a76d64c17e153596742bc885a271844fba6bfe0668`
- **Checklist Registration Tx**: `0x17f2e8e28f136737ca5b30cc57b00af23b18230de55030b5ecad80e3c8c089f0`
- **Negative Finding (FAIL) Tx**: `0xfc4c75b5e0df91168d3906494f7eda3edf83695896304017943bb8e45848baa6` (Result: `MAJORITY_AGREE`, Status: `ACCEPTED`)
