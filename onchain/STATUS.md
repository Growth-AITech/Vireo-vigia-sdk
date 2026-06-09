# AgentRegistry — Estado y Continuación

> Contrato on-chain para la **Arbitrum Buildathon 2026**. Registra cuándo un agente
> Vireo Vigía responde una consulta, en Arbitrum One.
> Última actualización: 2026-06-08.

## Estado actual

| Pieza | Estado |
|---|---|
| Contrato `AgentRegistry.sol` (Solidity ^0.8.20) | ✅ Escrito |
| Compilación (solc 0.8.28, optimizer 200) | ✅ Compila limpio |
| Checks locales (timestamp / evento / owner-gating) | ✅ Pasan (`scripts/sanity.js`) |
| Proyecto Hardhat (config Arbitrum One, deploy + verify) | ✅ Listo |
| **Deploy a Arbitrum One mainnet** | ⏳ **PENDIENTE** — requiere wallet financiada |
| Dirección del contrato | ⏳ Existe sólo tras el deploy |
| Verificación de código en Arbiscan | ⏳ Tras el deploy (opcional) |
| Wiring en el agente (`registerQuery` desde `chat()`) | ⏳ No iniciado (opcional) |

## Qué hace el contrato

- `mapping(bytes32 => uint256) public lastQuery` — agentId → timestamp.
- `registerQuery(bytes32 agentId)` — guarda `block.timestamp`, **permissionless**
  (la hot wallet del agente puede llamarlo sin ser owner). Emite `QueryLogged`.
- `event QueryLogged(bytes32 indexed agentId, uint256 timestamp)`.
- `updateMetadata(string)` — sólo owner. Metadata libre (nombre/versión del protocolo).
- `transferOwnership(address)` — sólo owner (extra).

## Por dónde continuar (próximos pasos)

### 1. Desplegar a mainnet (paso bloqueante para la submission)
```bash
cd onchain
npm install                   # si aún no se instaló
cp .env.example .env          # rellenar DEPLOYER_PRIVATE_KEY (wallet con ETH en Arbitrum One)
npx hardhat run scripts/sanity.js     # check local gratis (opcional)
npm run deploy:arbitrum               # broadcast real — gasta ~$0.10–0.50 de ETH
```
- La wallet necesita ETH **en Arbitrum One** (bridgeado desde L1, no en L1).
- El script imprime la dirección + link de Arbiscan. El deploy falla rápido si el balance es 0.
- **Anotar la dirección aquí** una vez desplegado:
  ```
  AgentRegistry (Arbitrum One): 0x________________________________________
  Tx de deploy:                 0x________________________________________
  ```

### 2. (Opcional) Verificar el código en Arbiscan
```bash
# Poner ARBISCAN_API_KEY en onchain/.env, luego:
npx hardhat verify --network arbitrumOne <ADDRESS> "<METADATA STRING>"
```

### 3. (Opcional) Conectar el agente al contrato
Hacer que cada `Agent.chat()` llame a `registerQuery` para dejar rastro on-chain.
- Punto de integración: `src/vireo_vigia/agent/base.py`.
- Necesita: RPC de Arbitrum, hot wallet con algo de ETH, ABI de `AgentRegistry`
  (en `onchain/artifacts/contracts/AgentRegistry.sol/AgentRegistry.json` tras compilar).
- agentId sugerido: `keccak256("vireo-vigia-<protocolo>")`.

## Notas / gotchas

- `onchain/.env` está **gitignored** — nunca commitear la private key.
- El deploy lo corre el usuario en su máquina (la key no pasa por la sesión).
- Tooling: Hardhat 2 + ethers v6 sobre Node 24. Foundry no está instalado.
- `hardhat-verify` usa la API unificada de Etherscan v2; una key de Etherscan/Arbiscan sirve.
