const { createClient, chains, createAccount } = require('genlayer-js');
const fs = require('fs');

async function main() {
  const account = createAccount();
  console.log("Generated account address:", account.address);
  const client = createClient({
    chain: chains.studionet,
    account: account,
  });

  const code = fs.readFileSync('contracts/probe.py', 'utf8');

  try {
    console.log("Attempting deployment...");
    const txHash = await client.deployContract({
      code: code,
      args: [],
    });
    console.log("Deploy tx hash:", txHash);
  } catch (err) {
    console.error("Deploy attempt error:", err.message);
  }
}

main();
