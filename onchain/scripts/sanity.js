// Local sanity check on Hardhat's in-memory network (no real funds, no network).
// Run: npx hardhat run scripts/sanity.js
const hre = require("hardhat");

async function main() {
  const [owner, other] = await hre.ethers.getSigners();
  const registry = await (
    await hre.ethers.getContractFactory("AgentRegistry")
  ).deploy("Vireo Vigia test");
  await registry.waitForDeployment();

  const agentId = hre.ethers.id("vireo-vigia-agent-1"); // keccak256 -> bytes32

  // 1) registerQuery sets timestamp + emits QueryLogged
  const tx = await registry.registerQuery(agentId);
  const receipt = await tx.wait();
  const block = await hre.ethers.provider.getBlock(receipt.blockNumber);
  const stored = await registry.lastQuery(agentId);
  assert(stored === BigInt(block.timestamp), "lastQuery == block.timestamp");
  const ev = receipt.logs.map((l) => registry.interface.parseLog(l)).find(Boolean);
  assert(ev && ev.name === "QueryLogged", "QueryLogged emitted");
  assert(ev.args.agentId === agentId, "event agentId matches");

  // 2) owner can update metadata
  await (await registry.updateMetadata("Vireo Vigia v0.1.1")).wait();
  assert((await registry.metadata()) === "Vireo Vigia v0.1.1", "metadata updated");

  // 3) non-owner cannot
  let reverted = false;
  try {
    await registry.connect(other).updateMetadata("hacked");
  } catch {
    reverted = true;
  }
  assert(reverted, "non-owner updateMetadata reverts");

  console.log("All sanity checks passed ✔");
}

function assert(cond, msg) {
  if (!cond) throw new Error("FAILED: " + msg);
  console.log("  ✔ " + msg);
}

main().catch((e) => {
  console.error(e);
  process.exitCode = 1;
});
