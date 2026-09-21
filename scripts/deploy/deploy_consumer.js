const { createClient, chains, createAccount } = require('genlayer-js');
const fs = require('fs');

async function main() {
  const account = createAccount();
  const client = createClient({
    chain: chains.studionet,
    account: account,
  });

  const dep = JSON.parse(fs.readFileSync('scripts/deploy/deployments.json', 'utf8'));
  const fullReadAddress = dep.contractAddress;
  console.log("FullRead Address:", fullReadAddress);

  const code = fs.readFileSync('examples/consumer/consumer.py', 'utf8');

  console.log("Deploying DocumentPolicyConsumer...");
  const txHash = await client.deployContract({
    code: code,
    args: [fullReadAddress],
  });
  console.log("Consumer Deploy Tx Hash:", txHash);

  const receipt = await client.waitForTransactionReceipt({ hash: txHash });
  console.log("Consumer Status:", receipt.status_name);
  console.log("Consumer Result:", receipt.result_name);
  console.log("Consumer Contract Address:", receipt.recipient);

  dep.consumerContractAddress = receipt.recipient;
  dep.consumerDeployTx = txHash;
  fs.writeFileSync('scripts/deploy/deployments.json', JSON.stringify(dep, null, 2));
}

main().catch(console.error);
