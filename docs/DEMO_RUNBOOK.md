# Demo Runbook — AI Cost Optimization Dashboard

Coffee with CoBank IT Director: Thursday, February 19, 2026 at 1:00 PM

## Goal (5–7 minutes)
Show an end-to-end FinOps workflow:
1. Spend visibility + anomalies
2. Forecast + budget risk
3. ROI tracking
4. Auto-remediation readiness

## Pre-Demo Checklist (10 minutes before)
1. `python app.py` (demo mode)
2. Open `http://localhost:5000`
3. Click `Export PDF` once to confirm print flow
4. Optional: open terminal in separate window for CLI backup

## Primary Demo Flow (Web UI)
1. **Hero + KPIs**
   - “This is a unified cloud spend view with forecast, anomalies, and ROI.”
   - Point to Total Spend, Forecast, Budget, ROI.

2. **Trend + Top Services**
   - “Here’s the daily trend and the top cost drivers.”
   - Call out a top service and why it matters.

3. **Anomalies**
   - “We detect spend spikes using statistical thresholds.”
   - Mention severity and impact.

4. **Recommendations + ROI**
   - “Recommendations are tracked with estimated vs. actual savings.”
   - “Implementation rate makes ROI real, not hypothetical.”

5. **Auto-Remediation Preview**
   - “Low-risk quick wins can be auto-remediated.”
   - “We generate Terraform stubs, but keep it in dry-run for safety.”

6. **Export PDF**
   - Click `Export PDF` → Save as PDF.
   - “This is ready for weekly executive reporting.”

## Backup CLI Demo (if browser fails)
```bash
python advanced_optimizer.py --demo
```

## One-Liners to Remember
- “The system is cloud-aware but LLM-agnostic—OpenAI by default, Anthropic optional.”
- “We don’t just find savings; we track implementation and ROI.”
- “Auto-remediation stays safe with dry-run + Terraform review.”

## If Asked About Real Data
- “Live mode runs with AWS Cost Explorer; demo mode is deterministic for consistent storytelling.”

## Close
“I’d love your feedback on making this production-ready for a real FinOps workflow.”
