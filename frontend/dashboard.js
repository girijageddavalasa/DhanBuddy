const metricNames = [
  ["total_calls", "Total calls"], ["successful_calls", "Successful"],
  ["failed_calls", "Failed"], ["success_rate", "Success rate", "%"],
  ["average_duration_seconds", "Average duration", " sec"],
  ["average_latency_ms", "Average latency", " ms"], ["escalation_count", "Escalations"],
];

function renderBars(target, values) {
  const root = document.querySelector(target); root.replaceChildren();
  const maximum = Math.max(...Object.values(values), 1);
  for (const [label, value] of Object.entries(values)) {
    const row = document.createElement("div"); row.className = "bar-row";
    const name = document.createElement("span"); name.textContent = `${label} (${value})`;
    const bar = document.createElement("i"); bar.style.width = `${value * 100 / maximum}%`;
    row.append(name, bar); root.append(row);
  }
}

async function refresh() {
  const query = new URLSearchParams();
  for (const [id, key] of [["from","date_from"],["to","date_to"],["language","language"],["channel","channel"],["outcome","outcome"]]) {
    const value = document.querySelector(`#${id}`).value; if (value) query.set(key, value);
  }
  const response = await fetch(`/api/analytics?${query}`); const data = await response.json();
  const metrics = document.querySelector("#metrics"); metrics.replaceChildren();
  for (const [key, label, suffix = ""] of metricNames) {
    const card = document.createElement("article"); card.className = "metric";
    const value = data[key] == null ? "Unknown" : `${data[key]}${suffix}`;
    card.innerHTML = `<span>${label}</span><strong>${value}</strong>`; metrics.append(card);
  }
  renderBars("#outcome-bars", data.outcomes); renderBars("#language-bars", data.languages);
  renderBars("#failure-bars", data.failure_types); renderBars("#channel-bars", data.channels);
  renderBars("#time-bars", data.calls_over_time);
  const history = document.querySelector("#history"); history.replaceChildren();
  for (const call of data.recent_calls) {
    const row = document.createElement("tr");
    for (const key of ["started_at","duration_seconds","channel","language","outcome","failure_type"]) {
      const cell = document.createElement("td"); cell.textContent = call[key] ?? "Unknown"; row.append(cell);
    } history.append(row);
  }
}
document.querySelector("#apply").addEventListener("click", refresh);
refresh().catch(console.error); setInterval(() => refresh().catch(console.error), 10000);
