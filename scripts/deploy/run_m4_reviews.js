const { createClient, chains, createAccount } = require('genlayer-js');
const fs = require('fs');

const COMMIT_SHA = "d395a4f9efef8086ec35cdf5ce7fa0793b735f7f";
const BASE_URL = `https://raw.githubusercontent.com/huzyow155/fullread-genlayer/${COMMIT_SHA}/tests/fixtures/`;

const CONTRACT_ADDRESS = "0x86579015A531C3CB76879213244BcE355Ad4EA8C";
const CONSUMER_ADDRESS = "0x3C0f216B8df54c48d6a95F898c35482E7BA5370d";
const CHECKLIST_ID = "60932b48524e8f2a";

async function executeReview(client, title, fixtureName, expectedOutcome) {
  const docUrl = BASE_URL + fixtureName;
  console.log(`\n======================================================`);
  console.log(`Starting Review: ${title}`);
  console.log(`Document URL: ${docUrl}`);
  console.log(`Max Chunks: 3 (Expected Outcome: ${expectedOutcome})`);
  console.log(`======================================================`);

  const startTime = Date.now();
  const txHash = await client.writeContract({
    address: CONTRACT_ADDRESS,
    functionName: 'review',
    args: [CHECKLIST_ID, docUrl, 3],
  });
  console.log(`Transaction submitted. Hash: ${txHash}`);

  console.log(`Awaiting consensus confirmation from studionet validators (up to 300s)...`);
  const receipt = await client.waitForTransactionReceipt({ hash: txHash, retries: 100, interval: 3000 });
  const elapsedSec = ((Date.now() - startTime) / 1000).toFixed(2);

  console.log(`Execution completed in: ${elapsedSec}s`);
  console.log(`Transaction Status: ${receipt.status_name}`);
  console.log(`Consensus Result: ${receipt.result_name}`);

  // Inspect execution result from transaction details
  const txDetails = await client.getTransaction({ hash: txHash });
  const executionResult = txDetails.statusName || receipt.status_name;
  console.log(`Execution Result Status: ${executionResult}`);

  // Read back latest review ID
  const latestId = await client.readContract({
    address: CONTRACT_ADDRESS,
    functionName: 'latest_review_id',
    args: [CHECKLIST_ID, docUrl],
  });
  console.log(`Latest Review ID: ${latestId}`);

  // Read back review record
  const reviewJson = await client.readContract({
    address: CONTRACT_ADDRESS,
    functionName: 'get_review',
    args: [latestId],
  });
  console.log(`Stored Review Record:\n${reviewJson}`);

  const parsed = JSON.parse(reviewJson);
  console.log(`Recorded Outcome: ${parsed.outcome}`);
  console.log(`Coverage BP: ${parsed.coverage_bp}`);
  console.log(`Status by Item:`, JSON.stringify(parsed.status_by_item));
  console.log(`Quotes:`, JSON.stringify(parsed.quotes));

  if (parsed.outcome !== expectedOutcome) {
    console.error(`WARNING: Outcome mismatch! Expected ${expectedOutcome}, got ${parsed.outcome}`);
  } else {
    console.log(`MATCH: Outcome matches expected ${expectedOutcome}!`);
  }

  return {
    title,
    fixtureName,
    docUrl,
    txHash,
    latencySec: elapsedSec,
    status: receipt.status_name,
    result: receipt.result_name,
    executionResult: executionResult,
    reviewId: latestId,
    record: parsed,
  };
}

async function main() {
  const account = createAccount();
  const client = createClient({
    chain: chains.studionet,
    account: account,
  });

  console.log("Using account:", account.address);
  console.log("Target FullRead Contract:", CONTRACT_ADDRESS);
  console.log("Target Consumer Contract:", CONSUMER_ADDRESS);

  const results = [];

  // Run 1: Compliant document
  const r1 = await executeReview(
    client,
    "Run 1 - Compliant Document",
    "compliant.md",
    "PASS"
  );
  results.push(r1);

  // Run 2: Violation in first chunk
  const r2 = await executeReview(
    client,
    "Run 2 - Violation in First Chunk",
    "violation_in_first_chunk.md",
    "FAIL"
  );
  results.push(r2);

  // Run 3: Buried violation in last chunk
  const r3 = await executeReview(
    client,
    "Run 3 - Buried Violation in Last Chunk (Chunk 3)",
    "violation_in_last_chunk.md",
    "FAIL"
  );
  results.push(r3);

  // Cross-contract verification with DocumentPolicyConsumer
  console.log(`\n======================================================`);
  console.log(`Testing Cross-Contract View Call with DocumentPolicyConsumer`);
  console.log(`======================================================`);

  console.log(`Attempting approval of Compliant Review (ID: ${r1.reviewId})...`);
  const approveTx = await client.writeContract({
    address: CONSUMER_ADDRESS,
    functionName: 'approve_if_passed',
    args: [r1.reviewId],
  });
  console.log(`Approve Tx Hash: ${approveTx}`);
  const approveReceipt = await client.waitForTransactionReceipt({ hash: approveTx, retries: 100, interval: 3000 });
  console.log(`Approve Status: ${approveReceipt.status_name}, Result: ${approveReceipt.result_name}`);

  const isApproved = await client.readContract({
    address: CONSUMER_ADDRESS,
    functionName: 'is_document_approved',
    args: [r1.docUrl],
  });
  console.log(`is_document_approved(${r1.docUrl}): ${isApproved}`);

  const approvalRevId = await client.readContract({
    address: CONSUMER_ADDRESS,
    functionName: 'get_approval_review_id',
    args: [r1.docUrl],
  });
  console.log(`get_approval_review_id: ${approvalRevId}`);

  // Save all results to deployments.json and docs/VERIFICATION.md
  const deployments = JSON.parse(fs.readFileSync('scripts/deploy/deployments.json', 'utf8'));
  deployments.m4Runs = results;
  deployments.crossContractVerification = {
    consumerAddress: CONSUMER_ADDRESS,
    approveTx: approveTx,
    status: approveReceipt.status_name,
    result: approveReceipt.result_name,
    isApproved: isApproved,
    approvalRevId: approvalRevId
  };
  fs.writeFileSync('scripts/deploy/deployments.json', JSON.stringify(deployments, null, 2));
  console.log(`\nUpdated scripts/deploy/deployments.json with complete M4 evidence.`);
}

main().catch(err => {
  console.error("M4 Execution failed:", err);
  process.exit(1);
});
