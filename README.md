# 🤖 AI Cost Optimization Dashboard

> **AI-powered AWS cost analysis that identified $15,400/month in optimization opportunities across EC2, RDS, and S3 — fully automated, Slack-delivered, production-ready.**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![AWS](https://img.shields.io/badge/AWS-Cost%20Explorer-orange.svg)](https://aws.amazon.com/aws-cost-management/aws-cost-explorer/)
[![Claude AI](https://img.shields.io/badge/Claude-Anthropic-blueviolet.svg)](https://www.anthropic.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-Compatible-black.svg)](https://openai.com/)
[![Terraform](https://img.shields.io/badge/IaC-Terraform-623CE4.svg)](https://www.terraform.io/)
[![Docker](https://img.shields.io/badge/Container-Docker-2496ED.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 💡 Why This Exists

Cloud teams waste thousands on idle resources every month — not because they don't care, but because manual cost review doesn't scale. This tool automates the entire FinOps loop: **fetch → analyze → recommend → alert → track**.

Built by a DevOps engineer who's operated 24/7 broadcast infrastructure where every dollar of cloud spend is visible and accountable.

---

## 📊 Real-World Impact

| Metric | Result |
|--------|--------|
| 💰 Monthly savings identified | **$15,400/month** |
| ☁️ Services analyzed | EC2, RDS, S3, Lambda, NAT Gateway, KMS |
| ⚡ Time to first recommendation | < 2 minutes |
| 📬 Delivery | Automated Slack weekly reports |
| 🏗️ Deployment | Docker + Terraform on AWS |

---

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────────────┐     ┌──────────────────┐
│   AWS Account   │────▶│   Python Engine      │────▶│   LLM Provider   │
│  Cost Explorer  │     │  - Cost fetching     │     │  Claude / OpenAI │
│  (CUR / API)    │     │  - Anomaly detection │     └──────────────────┘
└─────────────────┘     │  - Forecasting       │              │
                        │  - ROI ranking       │              ▼
                        └──────────┬───────────┘     ┌──────────────────┐
                                   │                  │  Recommendations │
                          ┌────────┴────────┐         │  + Action Items  │
                          │                 │         └──────────────────┘
                    ┌─────▼──────┐  ┌───────▼──────┐
                    │ Flask Web  │  │ Slack Webhook│
                    │ Dashboard  │  │  (Weekly)    │
                    │ Chart.js   │  └──────────────┘
                    └────────────┘
```

**For regulated environments (banking / fintech):**
```
CUR → S3 → Athena (auditable SQL) → EventBridge → Lambda → Dashboard
```
Fully governed, deterministic, KMS-encrypted, IAM-scoped.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔍 **Cost Analysis** | 7/30/90-day spend breakdown by service, account, tag |
| 🤖 **AI Recommendations** | Claude or OpenAI ranks opportunities by ROI |
| 🚨 **Anomaly Detection** | Z-score + IQR detects spend spikes before they escalate |
| 📈 **Forecasting** | 30-day cost projections with confidence intervals |
| 💾 **Savings Tracker** | Tracks implemented optimizations and ROI over time |
| 🔧 **Auto-Remediation** | Generates Terraform stubs for approved changes |
| 📊 **Web Dashboard** | Flask + Chart.js with SSE real-time updates |
| 📄 **PDF Export** | Print-ready reports from the dashboard |
| 📬 **Slack Integration** | Weekly automated delivery with action items |
| 🐳 **Docker + Compose** | One-command local or cloud deployment |
| ☁️ **Terraform** | Production AWS deployment via IaC |
| 🔒 **Security** | Token auth, DRY_RUN mode, IAM least-privilege |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or 3.12 (not 3.14)
- AWS account with Cost Explorer enabled
- OpenAI or Claude API key
- Slack webhook (optional)

### 1. Clone & Install
```bash
git clone https://github.com/nickcube2/AI-Cost-Optimization-Dashboard.git
cd AI-Cost-Optimization-Dashboard
pip install -r requirements.txt
```

### 2. Configure
```bash
cp .env.example .env
```

```bash
# .env
AWS_REGION=us-east-1
LLM_PROVIDER=anthropic          # anthropic | openai | mock
CLAUDE_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
MONTHLY_BUDGET=5000
DAYS_TO_ANALYZE=30
DRY_RUN=false
```

### 3. Run

**CLI (quickest)**
```bash
python cost_optimizer.py
```

**Web Dashboard (local)**
```bash
python app.py
# Open http://localhost:5000
```

**Demo mode (no AWS creds needed)**
```bash
python advanced_optimizer.py --demo
```

**Docker**
```bash
docker compose up --build
# Open http://localhost:5000
```

---

## 🐳 Docker Deployment

```bash
# Dashboard
docker run --rm -p 5000:5000 --env-file .env \
  -e DASHBOARD_HOST=0.0.0.0 \
  ai-cost-optimization-dashboard

# CLI workflow
docker run --rm --env-file .env \
  ai-cost-optimization-dashboard python advanced_optimizer.py --demo
```

---

## ☁️ Terraform Deployment (AWS)

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
terraform init && terraform plan && terraform apply
```

```bash
# Makefile shortcuts
make tf-plan
make tf-apply
make tf-destroy
```

---

## 🔧 Advanced Usage

```bash
# With AI-powered 30-day forecast
python advanced_optimizer.py --report --ai-forecast

# Auto-remediation plan + Terraform stubs (dry-run safe)
python advanced_optimizer.py --auto-remediate --generate-terraform

# Full report output
python advanced_optimizer.py --report
```

---

## 📋 Sample Output

```
══════════════════════════════════════════════════════════════════════
🚀 AI COST OPTIMIZATION DASHBOARD
══════════════════════════════════════════════════════════════════════

📊 Fetching AWS cost data for last 30 days...
   📅 Date range: 2026-01-17 to 2026-02-16
   📈 Trend: up 8.4% vs previous 30 days
   ✅ Total: $12,858.00 | Services: 12

💰 Cost Distribution:
──────────────────────────────────────────────────────────────────────
EC2                  ████████████████████  $  4,892.00
RDS                  ██████████████        $  3,241.00
S3                   ████████              $  2,180.00
Lambda               ████                  $    890.00
NAT Gateway          ██                    $    520.00
──────────────────────────────────────────────────────────────────────

🤖 AI RECOMMENDATIONS

## 📊 SPENDING OVERVIEW
Total: $12,858 | Trend: +8.4% | Budget: On Track

## 💰 TOP OPPORTUNITIES
1. EC2 Right-sizing (prod cluster)       → Save $4,200/mo  [Quick Win]
2. RDS Reserved Instance conversion      → Save $1,800/mo  [Medium]
3. S3 Intelligent-Tiering (archive)      → Save $950/mo    [Quick Win]
4. NAT Gateway consolidation             → Save $380/mo    [Medium]

ROI Total: $7,330/month → $87,960/year
```

---

## 🔒 AWS IAM Policy (Least Privilege)

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": [
      "ce:GetCostAndUsage",
      "ce:GetCostForecast",
      "ce:GetDimensionValues",
      "ce:GetReservationUtilization"
    ],
    "Resource": "*"
  }]
}
```

---

## 🔐 Security Features

- `DASHBOARD_API_TOKEN` — token-based auth for all `/api/*` endpoints
- `DRY_RUN=true` — full execution without any API charges
- `DASHBOARD_CACHE_TTL` — prevents repeated AWS API calls
- IAM scoped to read-only Cost Explorer permissions
- VPC endpoint support for regulated environments

---

## 📁 Project Structure

```
ai-cost-optimization-dashboard/
├── app.py                    # Flask web dashboard (SSE + Chart.js)
├── cost_optimizer.py         # Core optimizer (CLI entry point)
├── advanced_optimizer.py     # Multi-feature demo runner
├── anomaly_detector.py       # Z-score + IQR anomaly detection
├── cost_forecaster.py        # 30-day cost forecasting
├── auto_remediator.py        # Terraform auto-remediation stubs
├── savings_tracker.py        # ROI tracking over time
├── llm_client.py             # Cloud-agnostic LLM client (Claude/OpenAI)
├── dashboard_data.py         # Dashboard JSON payload builder
├── Dockerfile                # Container definition
├── docker-compose.yml        # Local orchestration
├── Makefile                  # Convenience commands
├── terraform/                # AWS infrastructure as code
├── static/                   # Frontend assets
├── templates/                # Flask HTML templates
├── screenshots/              # Dashboard preview images
└── reports/                  # Generated cost reports
```

---

## 🗺️ Roadmap

- [x] Core cost analysis + AI recommendations (Week 1)
- [x] Slack integration + cron scheduling (Week 1)
- [x] Anomaly detection + trend analysis (Week 1)
- [x] ROI-based ranking + risk assessment (Week 1)
- [x] Multi-account support + savings tracker (Week 2)
- [x] Web dashboard — Flask + Chart.js + SSE (Week 3)
- [x] Terraform auto-remediation stubs (Week 4)
- [x] Docker + Terraform production deployment (Week 4)
- [ ] Multi-cloud support (Azure Cost Management, GCP Billing)
- [ ] Slack slash command (`/aws-costs`) for on-demand reports
- [ ] Grafana dashboard integration
- [ ] GitHub Actions scheduled workflow

---

## 👤 Author

**Nicholas Awuni** — Senior DevOps / Cloud Engineer  
AWS Certified Solutions Architect | HashiCorp Terraform Associate | FinOps Practitioner

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Nicholas%20Awuni-0077B5?style=flat&logo=linkedin)](https://www.linkedin.com/in/nicholas-awuni-6018041b1/)
[![GitHub](https://img.shields.io/badge/GitHub-nickcube2-181717?style=flat&logo=github)](https://github.com/nickcube2)

> *"I've seen teams waste thousands on idle resources — not from negligence, but because manual cost review doesn't scale. This project makes FinOps automatic and actionable."*

---

## 📄 License

MIT — see [LICENSE](LICENSE)
