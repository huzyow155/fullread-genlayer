const { createClient, chains, createAccount } = require('genlayer-js');
const fs = require('fs');

async function main() {
  const account = createAccount();
  const client = createClient({
    chain: chains.studionet,
    account: account,
  });

  const contractAddress = '0x86579015A531C3CB76879213244BcE355Ad4EA8C';
  const checklistId = '60932b48524e8f2a';
  const validUrl = 'https://raw.githubusercontent.com/yeagerai/genlayer-simulator/main/README.md';

  console.log("Calling review on valid 200 URL:", validUrl);
  const startReviewTime = Date.now();
  const reviewTx = await client.writeContract({
    address: contractAddress,
    functionName: 'review',
    args: [checklistId, validUrl, 1],
  });
  console.log("Review Tx Hash:", reviewTx);

  console.log("Waiting for receipt...");
  const receipt = await client.waitForTransactionReceipt({ hash: reviewTx });
  const latencySec = ((Date.now() - startReviewTime) / 1000).toFixed(2);
  console.log(`Receipt received in ${latencySec}s`);
  console.log("Status:", receipt.status_name);
  console.log("Result:", receipt.result_name);

  if (receipt.status_name === 'ACCEPTED') {
    const latestId = await client.readContract({
      address: contractAddress,
      functionName: 'latest_review_id',
      args: [checklistId, validUrl],
    });
    console.log("Latest Review ID:", latestId);

    const record = await client.readContract({
      address: contractAddress,
      functionName: 'get_review',
      args: [latestId],
    });
    console.log("Readback Record:\n", record);

    // Update deployments.json
    const dep = JSON.parse(fs.readFileSync('scripts/deploy/deployments.json', 'utf8'));
    dep.m1TestReviewTx = reviewTx;
    dep.m1ReviewLatencySec = latencySec;
    dep.m1Status = receipt.status_name;
    dep.m1Result = receipt.result_name;
    fs.writeFileSync('scripts/deploy/deployments.json', JSON.stringify(dep, null, 2));
    console.log("Updated scripts/deploy/deployments.json");
  }
}

main().catch(console.error);
