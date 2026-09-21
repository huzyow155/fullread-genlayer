const { createClient, chains, createAccount } = require('genlayer-js');

async function main() {
  const account = createAccount();
  const client = createClient({
    chain: chains.studionet,
    account: account,
  });

  const contractAddress = '0x81BDF8625D1E8D35cF30a1a4B1C4DB0c1D997D0a';
  const testUrl = 'https://raw.githubusercontent.com/genlayerlabs/genlayer-simulator/main/README.md';

  console.log("Calling probe_web_and_consensus...");
  const txHash = await client.writeContract({
    address: contractAddress,
    functionName: 'probe_web_and_consensus',
    args: [testUrl],
  });
  console.log("Write tx hash:", txHash);

  console.log("Waiting for receipt...");
  const receipt = await client.waitForTransactionReceipt({ hash: txHash });
  console.log("Status:", receipt.status_name);
  console.log("Result:", receipt.result_name);

  const consensusUsed = await client.readContract({
    address: contractAddress,
    functionName: 'get_probe_data',
    args: ['consensus_used'],
  });
  console.log("consensus_used:", consensusUsed);

  const webResult = await client.readContract({
    address: contractAddress,
    functionName: 'get_probe_data',
    args: ['web_result'],
  });
  console.log("web_result:", webResult);
}

main().catch(console.error);
