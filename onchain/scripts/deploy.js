const hre = require("hardhat");

// Metadata baked in at deploy time; owner can change it later via updateMetadata.
const INITIAL_METADATA =
  process.env.AGENT_METADATA || "Vireo Vigia v0.1.1 — Aave V3 / Hyperliquid (Arbitrum)";

async function main() {
  const net = await hre.ethers.provider.getNetwork();
  const [deployer] = await hre.ethers.getSigners();

  if (!deployer) {
    throw new Error(
      "No deployer account. Set DEPLOYER_PRIVATE_KEY in onchain/.env before deploying."
    );
  }

  const balance = await hre.ethers.provider.getBalance(deployer.address);
  console.log(`Network:  ${net.name} (chainId ${net.chainId})`);
  console.log(`Deployer: ${deployer.address}`);
  console.log(`Balance:  ${hre.ethers.formatEther(balance)} ETH`);
  console.log(`Metadata: ${INITIAL_METADATA}`);

  if (balance === 0n) {
    throw new Error("Deployer balance is 0 ETH — fund the wallet on Arbitrum One first.");
  }

  const factory = await hre.ethers.getContractFactory("AgentRegistry");
  const registry = await factory.deploy(INITIAL_METADATA);
  console.log(`\nDeploy tx sent: ${registry.deploymentTransaction().hash}`);
  console.log("Waiting for confirmation...");

  await registry.waitForDeployment();
  const address = await registry.getAddress();

  console.log("\n==================================================");
  console.log(`AgentRegistry deployed to: ${address}`);
  console.log(`Arbiscan: https://arbiscan.io/address/${address}`);
  console.log("==================================================");
  console.log("\nVerify with:");
  console.log(
    `  npx hardhat verify --network arbitrumOne ${address} "${INITIAL_METADATA}"`
  );
}

main().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});
