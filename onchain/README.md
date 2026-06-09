# Vireo Vigía — On-chain AgentRegistry

Minimal Solidity contract for the **Arbitrum Buildathon 2026**. Logs when a Vireo
Vigía agent answers a query, on Arbitrum One.

- **Contract:** [`contracts/AgentRegistry.sol`](contracts/AgentRegistry.sol) — Solidity `^0.8.20`
- **Network:** Arbitrum One (chainId `42161`)
- **Tooling:** Hardhat + ethers v6

### What it does
| Requirement | Implementation |
|---|---|
| `agentId (bytes32) => timestamp` mapping | `mapping(bytes32 => uint256) public lastQuery` |
| `registerQuery(bytes32 agentId)` sets `block.timestamp` | permissionless, so the agent's hot wallet can call it |
| `event QueryLogged(bytes32 indexed agentId, uint256 timestamp)` | emitted on every `registerQuery` |
| Owner-only metadata string | `updateMetadata(string)` guarded by `onlyOwner` |

## Deploy to Arbitrum One

```bash
cd onchain
npm install
cp .env.example .env          # fill DEPLOYER_PRIVATE_KEY (funded wallet)

npx hardhat run scripts/sanity.js          # free local check (optional)
npm run deploy:arbitrum                     # broadcasts to mainnet — spends real ETH
```

The deploy script prints the deployed address and an Arbiscan link.

### Verify source (optional)
Set `ARBISCAN_API_KEY` in `.env`, then:
```bash
npx hardhat verify --network arbitrumOne <ADDRESS> "<METADATA STRING>"
```

> `.env` is gitignored — never commit the private key.
