const { createClient, chains, createAccount } = require('genlayer-js');
const fs = require('fs');

const COMMIT_SHA = "2300c1f7c24c9eb3c3b09513b2550ec38aa5e730";
const BASE_URL = `https://raw.githubusercontent.com/huzyow155/fullread-genlayer/${COMMIT_SHA}/tests/fixtures/`;

async function main() {
  const account = createAccount();
  const client = createClient({
    chain: chains.studionet,
    account: account,
  });

  console.log("Deployer account:", account.address);

  // 1. Deploy FullRead Contract
  console.log("\n--- 1. Deploying FullRead to Studionet ---");
  const fullReadCode = fs.readFileSync('contracts/full_read.py', 'utf8');
  const fullReadDeployTx = await client.deployContract({
    code: fullReadCode,
    args: [],
  });
  console.log("FullRead Deploy Tx:", fullReadDeployTx);
  const fullReadReceipt = await client.waitForTransactionReceipt({
    hash: fullReadDeployTx,
    retries: 100,
    interval: 3000
  });
  const fullReadAddress = fullReadReceipt.recipient;
  console.log("FullRead Status:", fullReadReceipt.status_name, "Result:", fullReadReceipt.result_name);
  console.log("FullRead Address:", fullReadAddress);

  // 2. Register Checklist
  console.log("\n--- 2. Registering Checklist ---");
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
    address: fullReadAddress,
    functionName: 'register_checklist',
    args: ["Terms Compliance", JSON.stringify(items)],
  });
  console.log("Register Checklist Tx:", regTx);
  const regReceipt = await client.waitForTransactionReceipt({
    hash: regTx,
    retries: 100,
    interval: 3000
  });
  console.log("Register Status:", regReceipt.status_name, "Result:", regReceipt.result_name);

  // Compute checklist ID
  const crypto = require('crypto');
  const sortedItems = items.map(it => ({
    id: it.id,
    polarity: it.polarity,
    question: it.question,
    severity: it.severity
  }));
  const canonicalJson = JSON.stringify(sortedItems);
  const checklistId = crypto.createHash('sha256').update(canonicalJson).digest('hex').slice(0, 16);
  console.log("Checklist ID:", checklistId);

  // 3. Deploy Consumer Contract
  console.log("\n--- 3. Deploying DocumentPolicyConsumer ---");
  const consumerCode = fs.readFileSync('examples/consumer/consumer.py', 'utf8');
  const consumerDeployTx = await client.deployContract({
    code: consumerCode,
    args: [fullReadAddress],
  });
  console.log("Consumer Deploy Tx:", consumerDeployTx);
  const consumerReceipt = await client.waitForTransactionReceipt({
    hash: consumerDeployTx,
    retries: 100,
    interval: 3000
  });
  const consumerAddress = consumerReceipt.recipient;
  console.log("Consumer Status:", consumerReceipt.status_name, "Result:", consumerReceipt.result_name);
  console.log("Consumer Address:", consumerAddress);

  // 4. Execute 3 Reviews
  const reviewsConfig = [
    {
      title: "Run 1 - Compliant Document",
      fixture: "compliant.md",
      expected: "PASS"
    },
    {
      title: "Run 2 - Violation in First Chunk",
      fixture: "violation_in_first_chunk.md",
      expected: "FAIL"
    },
    {
      title: "Run 3 - Buried Violation in Last Chunk",
      fixture: "violation_in_last_chunk.md",
      expected: "FAIL"
    }
  ];

  const reviewResults = [];

  for (const rc of reviewsConfig) {
    const docUrl = BASE_URL + rc.fixture;
    console.log(`\n======================================================`);
    console.log(`Starting: ${rc.title}`);
    console.log(`URL: ${docUrl}`);
    console.log(`Max Chunks: 3`);
    console.log(`======================================================`);

    const startTime = Date.now();
    const txHash = await client.writeContract({
      address: fullReadAddress,
      functionName: 'review',
      args: [checklistId, docUrl, 3],
    });
    console.log(`Tx submitted: ${txHash}`);
    console.log(`Awaiting consensus confirmation...`);

    const receipt = await client.waitForTransactionReceipt({
      hash: txHash,
      retries: 120,
      interval: 3000
    });
    const durationSec = ((Date.now() - startTime) / 1000).toFixed(2);
    console.log(`Confirmed in ${durationSec}s!`);
    console.log(`Status: ${receipt.status_name}, Result: ${receipt.result_name}`);

    const txDetails = await client.getTransaction({ hash: txHash });
    const executionResult = txDetails.statusName || receipt.status_name;
    console.log(`Execution Result Status: ${executionResult}`);

    const latestId = await client.readContract({
      address: fullReadAddress,
      functionName: 'latest_review_id',
      args: [checklistId, docUrl],
    });
    console.log(`Latest Review ID: ${latestId}`);

    const recordJson = await client.readContract({
      address: fullReadAddress,
      functionName: 'get_review',
      args: [latestId],
    });
    console.log(`Stored Record:\n`, recordJson);
    const parsed = JSON.parse(recordJson);

    reviewResults.push({
      title: rc.title,
      fixture: rc.fixture,
      docUrl: docUrl,
      txHash: txHash,
      latencySec: durationSec,
      status: receipt.status_name,
      result: receipt.result_name,
      executionResult: executionResult,
      reviewId: latestId,
      record: parsed,
    });
  }

  // 5. Cross-Contract View Verification
  console.log(`\n======================================================`);
  console.log(`Testing Cross-Contract Approval via DocumentPolicyConsumer`);
  console.log(`======================================================`);

  const compliantResult = reviewResults[0];
  console.log(`Approving Review ID: ${compliantResult.reviewId}...`);
  const approveTx = await client.writeContract({
    address: consumerAddress,
    functionName: 'approve_if_passed',
    args: [compliantResult.reviewId],
  });
  console.log(`Approve Tx: ${approveTx}`);
  const approveReceipt = await client.waitForTransactionReceipt({
    hash: approveTx,
    retries: 100,
    interval: 3000
  });
  console.log(`Approve Status: ${approveReceipt.status_name}, Result: ${approveReceipt.result_name}`);

  const isApproved = await client.readContract({
    address: consumerAddress,
    functionName: 'is_document_approved',
    args: [compliantResult.docUrl],
  });
  console.log(`is_document_approved: ${isApproved}`);

  const approvalReviewId = await client.readContract({
    address: consumerAddress,
    functionName: 'get_approval_review_id',
    args: [compliantResult.docUrl],
  });
  console.log(`get_approval_review_id: ${approvalReviewId}`);

  // 6. Save comprehensive deployments.json
  const deploymentsData = {
    network: "studionet",
    chainId: chains.studionet.id,
    rpcUrl: chains.studionet.rpcUrls.default.http[0],
    explorer: "https://explorer-studio.genlayer.com",
    contractAddress: fullReadAddress,
    deployTx: fullReadDeployTx,
    commitSha: COMMIT_SHA,
    githubRepo: "https://github.com/huzyow155/fullread-genlayer",
    checklistId: checklistId,
    registerTx: regTx,
    consumerContractAddress: consumerAddress,
    consumerDeployTx: consumerDeployTx,
    crossContractApprovalTx: approveTx,
    crossContractApproved: isApproved,
    reviews: reviewResults
  };

  fs.writeFileSync('scripts/deploy/deployments.json', JSON.stringify(deploymentsData, null, 2));
  console.log(`\nAll results saved to scripts/deploy/deployments.json!`);
}

main().catch(err => {
  console.error("Execution failed:", err);
  process.exit(1);
});
