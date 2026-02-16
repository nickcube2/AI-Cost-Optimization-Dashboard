const formatMoney = (value) => {
  if (value === null || value === undefined) return "--";
  return `$${Number(value).toFixed(2)}`;
};

let trendChart = null;
let serviceChart = null;
let sseSource = null;
let liveEnabled = true;

const updateDashboard = (data) => {
  document.getElementById("mode-pill").textContent = `Mode: ${data.meta.mode}`;
  document.getElementById("date-pill").textContent = `Period: ${data.meta.start_date} → ${data.meta.end_date}`;
  document.getElementById("updated-pill").textContent = `Last update: ${new Date().toLocaleTimeString()}`;
  document.getElementById("total-spend").textContent = formatMoney(data.totals.total_spend);
  document.getElementById("accounts-count").textContent = `${data.totals.accounts} accounts analyzed`;

  if (data.forecast && !data.forecast.error) {
    document.getElementById("forecast-total").textContent = formatMoney(data.forecast.projected_total);
    document.getElementById("forecast-confidence").textContent = `Confidence: ${data.forecast.confidence}`;
  } else {
    document.getElementById("forecast-total").textContent = "--";
    document.getElementById("forecast-confidence").textContent = "Forecast unavailable";
  }

  if (data.budget && data.budget.alert) {
    document.getElementById("budget-status").textContent = "Alert";
    document.getElementById("budget-detail").textContent = `Over by ${formatMoney(data.budget.overage)} (${data.budget.overage_percent}%)`;
  } else if (data.budget && data.budget.projected_spend) {
    document.getElementById("budget-status").textContent = "On Track";
    document.getElementById("budget-detail").textContent = `Buffer ${formatMoney(data.budget.buffer)} (${data.budget.buffer_percent}%)`;
  } else {
    document.getElementById("budget-status").textContent = "--";
    document.getElementById("budget-detail").textContent = "--";
  }

  document.getElementById("roi-annual").textContent = `$${data.roi.annual_projected_savings.toFixed(2)}/yr`;
  document.getElementById("roi-impl").textContent = `Implemented: ${data.roi.implementation_rate}%`;

  renderTrendChart(data.daily_costs);
  renderServiceChart(data.services);
  renderAnomalies(data.anomalies);
  renderRecommendations(data.pending_recommendations);
  renderRemediationPlan(data.remediation_plan);
};

const renderTrendChart = (dailyCosts) => {
  const ctx = document.getElementById("trendChart");
  const labels = dailyCosts.map((d) => d.date);
  const values = dailyCosts.map((d) => d.cost);

  if (trendChart) {
    trendChart.data.labels = labels;
    trendChart.data.datasets[0].data = values;
    trendChart.update();
    return;
  }

  trendChart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Daily Spend",
          data: values,
          borderColor: "#f4d35e",
          backgroundColor: "rgba(244, 211, 94, 0.15)",
          tension: 0.3,
          fill: true,
        },
      ],
    },
    options: {
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: "#b6c2c7" }, grid: { color: "rgba(255,255,255,0.05)" } },
        y: { ticks: { color: "#b6c2c7" }, grid: { color: "rgba(255,255,255,0.05)" } },
      },
    },
  });
};

const renderServiceChart = (services) => {
  const ctx = document.getElementById("serviceChart");
  const topEntries = Object.entries(services).slice(0, 6);
  const labels = topEntries.map((item) => item[0].replace("Amazon ", ""));
  const values = topEntries.map((item) => item[1]);

  if (serviceChart) {
    serviceChart.data.labels = labels;
    serviceChart.data.datasets[0].data = values;
    serviceChart.update();
    return;
  }

  serviceChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          data: values,
          backgroundColor: ["#58a6ff", "#7ee081", "#f4d35e", "#ff8b8b", "#c084fc", "#ffb86b"],
        },
      ],
    },
    options: {
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: "#b6c2c7" }, grid: { color: "rgba(255,255,255,0.05)" } },
        y: { ticks: { color: "#b6c2c7" }, grid: { color: "rgba(255,255,255,0.05)" } },
      },
    },
  });
};

const renderAnomalies = (anomalies) => {
  const list = document.getElementById("anomaly-list");
  list.innerHTML = "";

  if (!anomalies.anomalies || anomalies.anomalies.length === 0) {
    list.innerHTML = "<div class='list-item'>No anomalies detected.</div>";
    return;
  }

  anomalies.anomalies.forEach((item) => {
    const div = document.createElement("div");
    div.className = "list-item";
    const severityClass = item.severity === "high" ? "badge-high" : item.severity === "medium" ? "badge-med" : "badge-low";

    div.innerHTML = `
      <strong>${item.date} • ${formatMoney(item.cost)}</strong>
      Z-score: ${item.z_score} (${item.reason})
      <div class="badge ${severityClass}">${item.severity.toUpperCase()}</div>
    `;
    list.appendChild(div);
  });
};

const renderRecommendations = (recs) => {
  const list = document.getElementById("rec-list");
  list.innerHTML = "";

  if (!recs || recs.length === 0) {
    list.innerHTML = "<div class='list-item'>No pending recommendations.</div>";
    return;
  }

  recs.forEach((rec) => {
    const div = document.createElement("div");
    div.className = "list-item";
    div.innerHTML = `
      <strong>${rec.title}</strong>
      Est. Savings: ${formatMoney(rec.estimated_monthly_savings)}/mo
      <div class="badge badge-med">Risk: ${rec.risk_level || "medium"}</div>
      <div class="badge badge-low">Effort: ${rec.effort || "medium"}</div>
    `;
    list.appendChild(div);
  });
};

const renderRemediationPlan = (plan) => {
  const list = document.getElementById("remediation-list");
  list.innerHTML = "";

  if (!plan || plan.length === 0) {
    list.innerHTML = "<div class='list-item'>No low-risk quick wins available for auto-remediation.</div>";
    return;
  }

  plan.forEach((item) => {
    const div = document.createElement("div");
    div.className = "list-item";
    div.innerHTML = `
      <strong>${item.optimization_type}</strong>
      Recommendation ID: ${item.recommendation_id || "N/A"}
      <div class="badge badge-low">Auto-safe</div>
    `;
    list.appendChild(div);
  });
};

document.getElementById("export-btn").addEventListener("click", () => {
  window.print();
});

const token = window.DASHBOARD_TOKEN || "";

const loadDashboard = async () => {
  const response = await fetch(`/api/summary${token ? `?token=${token}` : ""}`);
  const data = await response.json();
  updateDashboard(data);
};

const startSSE = () => {
  if (!liveEnabled) return;
  const url = `/api/stream${token ? `?token=${token}` : ""}`;
  sseSource = new EventSource(url);
  sseSource.addEventListener("summary", (event) => {
    const payload = JSON.parse(event.data);
    updateDashboard(payload);
  });
  sseSource.onerror = () => {
    if (sseSource) sseSource.close();
    if (liveEnabled) setTimeout(startSSE, 5000);
  };
};

const stopSSE = () => {
  if (sseSource) sseSource.close();
  sseSource = null;
};

const toggleButton = document.getElementById("toggle-live");
toggleButton.addEventListener("click", () => {
  liveEnabled = !liveEnabled;
  if (liveEnabled) {
    toggleButton.textContent = "Pause";
    toggleButton.classList.remove("paused");
    startSSE();
  } else {
    toggleButton.textContent = "Resume";
    toggleButton.classList.add("paused");
    stopSSE();
  }
});

loadDashboard();
startSSE();
