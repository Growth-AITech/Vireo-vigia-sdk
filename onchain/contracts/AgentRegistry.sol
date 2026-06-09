// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title AgentRegistry
/// @notice Minimal on-chain registry that logs when a Vireo Vigía agent answers
///         a query. Each agentId records the timestamp of its most recent query,
///         and every call emits an event so off-chain indexers can build a full
///         audit trail. Deployed for the Arbitrum Buildathon 2026.
contract AgentRegistry {
    /// @notice Account allowed to update protocol metadata.
    address public owner;

    /// @notice Free-form metadata (e.g. "Vireo Vigía v0.1.1 — Aave/Hyperliquid").
    string public metadata;

    /// @notice agentId => unix timestamp of its most recent registered query.
    mapping(bytes32 => uint256) public lastQuery;

    /// @notice Emitted on every registerQuery call.
    event QueryLogged(bytes32 indexed agentId, uint256 timestamp);

    /// @notice Emitted whenever the owner updates the metadata string.
    event MetadataUpdated(string metadata);

    /// @notice Emitted when ownership is transferred.
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    error NotOwner();
    error ZeroAddress();

    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner();
        _;
    }

    constructor(string memory initialMetadata) {
        owner = msg.sender;
        metadata = initialMetadata;
        emit OwnershipTransferred(address(0), msg.sender);
    }

    /// @notice Record that `agentId` just handled a query. Permissionless so the
    ///         agent's own hot wallet can call it without being the owner.
    /// @param agentId Opaque 32-byte identifier for the agent (e.g. keccak256 of its name).
    function registerQuery(bytes32 agentId) external {
        lastQuery[agentId] = block.timestamp;
        emit QueryLogged(agentId, block.timestamp);
    }

    /// @notice Update the protocol metadata string. Owner only.
    function updateMetadata(string calldata newMetadata) external onlyOwner {
        metadata = newMetadata;
        emit MetadataUpdated(newMetadata);
    }

    /// @notice Transfer ownership to a new account. Owner only.
    function transferOwnership(address newOwner) external onlyOwner {
        if (newOwner == address(0)) revert ZeroAddress();
        emit OwnershipTransferred(owner, newOwner);
        owner = newOwner;
    }
}
