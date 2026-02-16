# Bank-Friendly Integration Architecture (1 Page)

## Goal
Provide a secure, auditable, and compliant cost‑optimization workflow suitable for regulated environments (e.g., banks).

## Recommended Architecture (Governed Pipeline)
1. **Source of Truth**
   - Enable AWS **Cost & Usage Report (CUR)** to S3
   - CUR provides immutable, detailed billing data for auditability

2. **Analytics Layer**
   - Query CUR with **Athena**
   - Store query outputs in a normalized table (S3 parquet or RDS)

3. **Processing & Enrichment**
   - **EventBridge** schedule (hourly or daily)
   - **Lambda** runs queries + enrichment (anomaly checks, forecasting, ROI)
   - Results written to `dashboard_metrics` table

4. **Dashboard Delivery**
   - Flask UI reads from `dashboard_metrics`
   - Optional SSE for near‑real‑time UX (updates after each batch refresh)

5. **Security & Governance**
   - IAM roles with least privilege
   - KMS encryption for S3 + RDS
   - Private subnets and VPC endpoints
   - Centralized logging to CloudWatch

## Why This Works for Banks
- **Auditable**: CUR + Athena is finance‑grade and traceable
- **Safe**: Batch updates reduce risk vs continuous streaming
- **Governed**: Clear change control and separation of duties
- **Scalable**: Handles multi‑account billing at enterprise scale

## Optional “Near‑Real‑Time” Variant
- Use Cost Explorer API hourly for quick updates
- Keep CUR as the authoritative record

## Mentorship Talking Points
- “We separate the data plane (CUR/Athena) from the insight plane (LLM + rules).”
- “Real‑time UX doesn’t mean real‑time data risk—refreshes are controlled and logged.”
- “Auto‑remediation stays in dry‑run with Terraform review.”
