const { createClient, chains, createAccount } = require('genlayer-js');
const fs = require('fs');

async function main() {
  const account = createAccount();
  console.log("Using deployer address:", account.address);
  const client = createClient({
    chain: chains.studionet,
    account: account,
  });

  const code = fs.readFileSync('contracts/full_read.py', 'utf8');

  console.log("Deploying FullRead contract to Studionet...");
  const deployTxHash = await client.deployContract({
    code: code,
    args: [],
  });
  console.log("Deploy Transaction Hash:", deployTxHash);

  const receipt = await client.waitForTransactionReceipt({ hash: deployTxHash });
  console.log("Deploy Receipt Status:", receipt.status_name);
  console.log("Deploy Receipt Result:", receipt.result_name);
  const contractAddress = receipt.recipient;
  console.log("Deployed Contract Address:", contractAddress);

  if (!contractAddress) {
    throw new Error("Deployment did not return contract address");
  }

  // 1. Register checklist
  console.log("\n--- Registering Checklist ---");
  const items = [
    {
      id: "refund",
      question: "Clear refund policy present",
      severity: "BLOCKER",
      polarity: "MUST_HAVE"
    },
    {
      id: "auto_renew",
      question: "Auto renewal without prior notice",
      severity: "BLOCKER",
      polarity: "MUST_NOT_HAVE"
    }
  ];

  const regTx = await client.writeContract({
    address: contractAddress,
    functionName: 'register_checklist',
    args: ["Terms Compliance", JSON.stringify(items)],
  });
  console.log("Register Checklist Tx:", regTx);
  const regReceipt = await client.waitForTransactionReceipt({ hash: regTx });
  console.log("Register Status:", regReceipt.status_name);
  console.log("Register Result:", regReceipt.result_name);

  // Compute CID locally
  const crypto = require('crypto');
  const canonicalItems = JSON.stringify(items);
  // Matches Python: json.dumps(clean_items, sort_keys=True, separators=(",", ":"))
  const sortedItems = items.map(it => ({
    id: it.id,
    polarity: it.polarity,
    question: it.question,
    severity: it.severity
  }));
  const canonicalJson = JSON.stringify(sortedItems);
  const expectedCid = crypto.createHash('sha256').update(canonicalJson).digest('hex').slice(0, 16);
  console.log("Computed Checklist ID:", expectedCid);

  const checklistData = await client.readContract({
    address: contractAddress,
    functionName: 'get_checklist',
    args: [expectedCid],
  });
  console.log("Checklist Readback:", checklistData);

  // 2. Run Review on a tiny test doc
  console.log("\n--- Running Milestone 1 Test Review ---");
  // A tiny stable raw document URL
  const testUrl = "https://raw.githubusercontent.com/genlayerlabs/genlayer-simulator/main/README.md";
  const startReviewTime = Date.now();
  const reviewTx = await client.writeContract({
    address: contractAddress,
    functionName: 'review',
    args: [expectedCid, testUrl, 1],
  });
  console.log("Review Tx Hash:", reviewTx);
  const reviewReceipt = await client.waitForTransactionReceipt({ hash: reviewTx });
  const reviewDurationSec = ((Date.now() - startReviewTime) / 1000).toFixed(2);
  console.log(`Review Completed in ${reviewDurationSec}s`);
  console.log("Review Status:", reviewReceipt.status_name);
  console.log("Review Result:", reviewReceipt.result_name);

  const latestId = await client.readContract({
    address: contractAddress,
    functionName: 'latest_review_id',
    args: [expectedCid, testUrl],
  });
  console.log("Latest Review ID:", latestId);

  const reviewRecord = await client.readContract({
    address: contractAddress,
    functionName: 'get_review',
    args: [latestId],
  });
  console.log("Review Record Readback:\n", reviewRecord);

  // Save deployment info
  const deploymentInfo = {
    network: "studionet",
    chainId: chains.studionet.id,
    rpcUrl: chains.studionet.rpcUrls.default.http[0],
    explorer: chains.studionet.blockExplorers.default.url,
    contractAddress: contractAddress,
    deployTx: deployTxHash,
    checklistId: expectedCid,
    registerTx: regTx,
    m1TestReviewTx: reviewTx,
    m1ReviewLatencySec: reviewDurationSec,
  };
  fs.writeFileSync('scripts/deploy/deployments.json', JSON.stringify(deploymentInfo, null, 2));
  console.log("Saved deployment info to scripts/deploy/deployments.json");
}

main().catch(err => {
  console.error("Execution failed:", err);
  process.exit(1);
});
