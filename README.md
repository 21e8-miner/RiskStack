# RiskStack – Institutional Risk Platform

## Local development
```bash
# Start full stack
docker compose up --build

# Access UI at http://localhost:8080
# API at http://localhost:8080/api/v1/docs
```

## Running tests
```bash
# Full integration test suite
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit
```

## Key features
- AI‑powered PDF ingestion with deterministic reconciliation
- Fat‑tail risk analysis (CVaR, historical simulation)
- Reg‑BI compliant immutable audit trail
- Air‑gapped Vite frontend with strict runtime validation
