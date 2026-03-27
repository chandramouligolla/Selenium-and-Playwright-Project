# 🔥 Performance Testing — Locust Banking Load Suite

## Overview

Locust-based performance testing suite simulating real-world **Lloyds Banking Group** traffic patterns.

## Test Scenarios

| Scenario | Users | Ramp Up | Duration | Purpose |
|---|---|---|---|---|
| Smoke | 10 | 2/s | 2 min | Baseline sanity |
| Load | 200 | 20/s | 10 min | Normal traffic |
| Stress | 500 | 50/s | 15 min | Peak banking load |
| Spike | 1000 | 100/s | 5 min | Sudden traffic surge |
| Endurance | 300 | 30/s | 60 min | Sustained load stability |

## SLA Thresholds

| Endpoint | Max Response Time |
|---|---|
| Login | 500ms |
| Account Balance | 300ms |
| Transaction List | 800ms |
| Fund Transfer | 1000ms |
| Statement | 1200ms |

## Run Commands

```bash
# Install
pip install locust

# Smoke test
locust -f locust_banking_load.py --headless -u 10 -r 2 --run-time 2m --host=https://api.yourbank.com

# Stress test — 500 concurrent users
locust -f locust_banking_load.py --headless -u 500 -r 50 --run-time 15m --html=reports/stress_report.html

# Spike test
locust -f locust_banking_load.py --headless -u 1000 -r 100 --run-time 5m

# With UI dashboard (open http://localhost:8089)
locust -f locust_banking_load.py --host=https://api.yourbank.com
```

## Results Achieved

- ✅ Validated system stability under **500+ concurrent users**
- ✅ Identified and resolved **3 critical API bottlenecks** before production
- ✅ All endpoints met SLA thresholds post-optimisation
- ✅ Zero performance-related production incidents for **6 consecutive months**
