const { createClient, chains } = require('genlayer-js');
const fs = require('fs');

async function main() {
  const filePath = process.argv[2] || 'contracts/probe.py';
  const client = createClient({ chain: chains.studionet });
  const code = fs.readFileSync(filePath, 'utf8');

  try {
    const schema = await client.getContractSchemaForCode(code);
    console.log(`Studionet Schema retrieved for ${filePath}:`);
    console.log(JSON.stringify(schema, null, 2));
  } catch (err) {
    console.error("Schema error:", err);
    process.exit(1);
  }
}

main();
