const { createClient, chains } = require('genlayer-js');
const fs = require('fs');

async function main() {
  const client = createClient({ chain: chains.studionet });
  const contracts = [
    'contracts/full_read.py',
    'contracts/probe.py',
    'examples/consumer/consumer.py'
  ];

  for (const cPath of contracts) {
    console.log(`Checking Studionet schema for ${cPath}...`);
    const code = fs.readFileSync(cPath, 'utf8');
    const schema = await client.getContractSchemaForCode(code);
    console.log(`PASS: ${cPath} (${Object.keys(schema.methods).length} methods)`);
  }
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
