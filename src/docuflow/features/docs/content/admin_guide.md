
# DocuFlow System Administration Guide

## 1. P2P Cluster Monitoring
Administrative nodes can monitor the health of the entire cluster via the **Health Registry**. Every node emits a heartbeat every 30 seconds to the shared network.

## 2. Identity Management
User accounts and roles are decentralized. Updates to the **Identity Registry** are broadcast across the P2P bus using HMAC signatures.

## 3. Emergency Step-Down
In case of leader failure, utilize the 'EMERGENCY STEP DOWN' command to trigger a new election.
