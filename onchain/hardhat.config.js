require("@nomicfoundation/hardhat-ethers");
require("@nomicfoundation/hardhat-verify");
require("dotenv").config();

// Read from env. Never commit real secrets — see .env.example.
const DEPLOYER_PRIVATE_KEY = process.env.DEPLOYER_PRIVATE_KEY || "";
const ARBITRUM_RPC_URL =
  process.env.ARBITRUM_RPC_URL || "https://arb1.arbitrum.io/rpc";
const ARBISCAN_API_KEY = process.env.ARBISCAN_API_KEY || "";

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: {
    version: "0.8.28",
    settings: {
      optimizer: { enabled: true, runs: 200 },
    },
  },
  networks: {
    arbitrumOne: {
      url: ARBITRUM_RPC_URL,
      chainId: 42161,
      accounts: DEPLOYER_PRIVATE_KEY ? [DEPLOYER_PRIVATE_KEY] : [],
    },
  },
  etherscan: {
    // hardhat-verify uses the unified Etherscan v2 API; an Etherscan/Arbiscan key works.
    apiKey: { arbitrumOne: ARBISCAN_API_KEY },
  },
};
