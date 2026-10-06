document.addEventListener("DOMContentLoaded", () => {

// Global application state
const state = {
currentData: null,
summary: null,
items: [],
selectedModel: "llama3",
chatHistory: [],
charts: {
stockDemand: null,
riskDoughnut: null,
itemHistory: null
}
};
// DOM references
const dom = {
navTabs: document.querySelectorAll(".nav-tab"),
tabContents: document.querySelectorAll(".tab-content"),
dropZone: document.getElementById("drop-zone"),
fileInput: document.getElementById("file-input"),
btnLoadSample: document.getElementById("btn-load-sample"),
googleSheetUrl: document.getElementById("google-sheet-url"),
btnFetchSheet: document.getElementById("btn-fetch-sheet"),
forecastMethod: document.getElementById("forecast-method"),
weightingType: document.getElementById("weighting-type"),
weightingTypeWrapper: document.getElementById("weighting-type-wrapper"),
serviceLevel: document.getElementById("service-level"),
forecastHorizon: document.getElementById("forecast-horizon"),
btnRecalculate: document.getElementById("btn-recalculate"),
ollamaStatusBadge: document.getElementById("ollama-status-badge"),
ollamaStatusText: document.getElementById("ollama-status-text"),
ollamaModelSelect: document.getElementById("ollama-model-select"),
kpiTotalItems: document.getElementById("kpi-total-items"),
kpiCriticalRisk: document.getElementById("kpi-critical-risk"),
kpiReorderCount: document.getElementById("kpi-reorder-count"),
kpiReorderInvestment: document.getElementById("kpi-reorder-investment"),
kpiTotalStockVal: document.getElementById("kpi-total-stock-val"),
kpiOverstockCount: document.getElementById("kpi-overstock-count"),
kpiMethodSub: document.getElementById("kpi-method-sub"),
tableBody: document.getElementById("table-body"),
tableSearch: document.getElementById("table-search"),
filterStatus: document.getElementById("filter-status"),
btnExportCsv: document.getElementById("btn-export-csv"),
btnGenerateReport: document.getElementById("btn-generate-report"),
btnCopyReport: document.getElementById("btn-copy-report"),
btnPrintReport: document.getElementById("btn-print-report"),
reportContent: document.getElementById("report-content"),
reportLoading: document.getElementById("report-loading"),
reportSourceBadge: document.getElementById("report-source-badge"),
chatMessages: document.getElementById("chat-messages"),
chatInput: document.getElementById("chat-input"),
btnSendChat: document.getElementById("btn-send-chat"),
chatContextStatus: document.getElementById("chat-context-status"),
chips: document.querySelectorAll(".suggestion-chips .chip"),
itemModal: document.getElementById("item-modal"),
btnCloseModal: document.getElementById("btn-close-modal"),
modalStock: document.getElementById("modal-stock"),
modalDemand: document.getElementById("modal-demand"),
modalSafetyStock: document.getElementById("modal-safety-stock"),
modalRop: document.getElementById("modal-rop"),
modalOrderQty: document.getElementById("modal-order-qty"),
modalOrderCost: document.getElementById("modal-order-cost"),
modalExplanation: document.getElementById("modal-explanation"),
toast: document.getElementById("toast")
};
init();
function init() {
setupEventListeners();
checkOllamaStatus();
loadSampleData();
}
// Event listeners
function setupEventListeners() {
dom.navTabs.forEach(tab => {
tab.addEventListener("click", () => {
switchTab(tab.getAttribute("data-tab"));
});
});
if (dom.forecastMethod) {
dom.forecastMethod.addEventListener("change", e => {
const showWeighting =
e.target.value === "weighted_mean" ||
e.target.value === "ensemble";
if (dom.weightingTypeWrapper) {
dom.weightingTypeWrapper.style.display = showWeighting ? "block" : "none";
}
});
}
if (dom.dropZone && dom.fileInput) {
dom.dropZone.addEventListener("click", () => dom.fileInput.click());
dom.fileInput.addEventListener("change", handleFileUpload);
dom.dropZone.addEventListener("dragover", e => {
e.preventDefault();
dom.dropZone.classList.add("dragover");
});
dom.dropZone.addEventListener("dragleave", () => {
dom.dropZone.classList.remove("dragover");
});
dom.dropZone.addEventListener("drop", e => {
e.preventDefault();
dom.dropZone.classList.remove("dragover");
const file = e.dataTransfer.files[0];
if (file) uploadFile(file);
});
}
if (dom.btnLoadSample) {
dom.btnLoadSample.addEventListener("click", loadSampleData);
}
if (dom.btnFetchSheet) {
dom.btnFetchSheet.addEventListener("click", handleGoogleSheetImport);
}
if (dom.btnRecalculate) {
dom.btnRecalculate.addEventListener("click", () => {
if (state.items.length === 0) {
showToast("Please load or upload inventory data first.", "warning");
return;
}
recalculatePredictions();
});
}
if (dom.ollamaModelSelect) {
dom.ollamaModelSelect.addEventListener("change", e => {
state.selectedModel = e.target.value;
showToast(`Active AI Model: ${state.selectedModel}`);
});
}
if (dom.tableSearch) {
dom.tableSearch.addEventListener("input", filterTable);
}
if (dom.filterStatus) {
dom.filterStatus.addEventListener("change", filterTable);
}
if (dom.btnExportCsv) {
dom.btnExportCsv.addEventListener("click", exportTableToCSV);
}
if (dom.btnGenerateReport) {
dom.btnGenerateReport.addEventListener("click", generateAIReport);
}
if (dom.btnCopyReport) {
dom.btnCopyReport.addEventListener("click", copyReportMarkdown);
}
if (dom.btnPrintReport) {
dom.btnPrintReport.addEventListener("click", () => window.print());
}
if (dom.btnSendChat) {
dom.btnSendChat.addEventListener("click", sendChatMessage);
}
if (dom.chatInput) {
dom.chatInput.addEventListener("keydown", e => {
if (e.key === "Enter" && !e.shiftKey) {
e.preventDefault();
sendChatMessage();
}
});
}
dom.chips.forEach(chip => {
chip.addEventListener("click", () => {
const query = chip.getAttribute("data-query") || "";
if (dom.chatInput) {
dom.chatInput.value = query;
sendChatMessage();
}
});
});
if (dom.btnCloseModal) {
dom.btnCloseModal.addEventListener("click", closeModal);
}
if (dom.itemModal) {
dom.itemModal.addEventListener("click", e => {
if (e.target === dom.itemModal) closeModal();
});
}
}
// Tabs
function switchTab(tabId) {
dom.navTabs.forEach(tab => {
tab.classList.toggle("active", tab.getAttribute("data-tab") === tabId);
});
dom.tabContents.forEach(content => {
content.classList.toggle("active", content.id === tabId);
});
}
// Toast
function showToast(message, type = "info") {
if (!dom.toast) return;
dom.toast.textContent = message;
dom.toast.style.display = "block";
if (type === "error") {
dom.toast.style.borderColor = "var(--color-danger)";
} else if (type === "warning") {
dom.toast.style.borderColor = "var(--color-warning)";
} else {
dom.toast.style.borderColor = "var(--brand-primary)";
}
clearTimeout(showToast.timer);
showToast.timer = setTimeout(() => {
dom.toast.style.display = "none";
}, 3500);
}
// Ollama
async function checkOllamaStatus() {
if (!dom.ollamaStatusBadge || !dom.ollamaStatusText) return;
try {
const res = await fetch("/api/ollama/status");
if (!res.ok) {
throw new Error("Ollama status request failed");
}
const data = await res.json();
const models = Array.isArray(data.models) ? data.models : [];
if (data.online !== false) {
dom.ollamaStatusBadge.className = "ollama-badge online";
dom.ollamaStatusText.textContent =
`Ollama: Online (${models.length} models)`;
if (dom.ollamaModelSelect && models.length > 0) {
dom.ollamaModelSelect.innerHTML = "";
models.forEach(model => {
const option = document.createElement("option");
option.value = model;
option.textContent = model;
dom.ollamaModelSelect.appendChild(option);
});
state.selectedModel = models[0];
dom.ollamaModelSelect.value = state.selectedModel;
}
} else {
dom.ollamaStatusBadge.className = "ollama-badge offline";
dom.ollamaStatusText.textContent =
"Ollama: Offline (Rule Engine Active)";
}
} catch (error) {
dom.ollamaStatusBadge.className = "ollama-badge offline";
dom.ollamaStatusText.textContent = "Ollama: Offline";
}
}
// File upload
function handleFileUpload(event) {
const file = event.target.files?.[0];
if (file) uploadFile(file);
}
async function uploadFile(file) {
const formData = new FormData();
formData.append("file", file);
formData.append("method", dom.forecastMethod?.value || "weighted_mean");
formData.append("weighting_type", dom.weightingType?.value || "recent_heavy");
formData.append("service_level", dom.serviceLevel?.value || "0.95");
formData.append("horizon", dom.forecastHorizon?.value || "1");
showToast(`Uploading and analyzing ${file.name}...`);
try {
const res = await fetch("/api/upload", {
method: "POST",
body: formData
});
const data = await parseJsonResponse(res, "Upload failed");
applyPredictionData(data);
showToast(
`Successfully analyzed ${data.items?.length || 0} items from ${file.name}!`,
"success"
);
} catch (error) {
showToast(error.message, "error");
}
}
// Google Sheets
async function handleGoogleSheetImport() {
const url = dom.googleSheetUrl?.value?.trim();
if (!url) {
showToast("Please enter a Google Sheet URL.", "warning");
return;
}
try {
showToast("Importing Google Sheet...");
const res = await fetch("/api/google-sheet", {
method: "POST",
headers: { "Content-Type": "application/json" },
body: JSON.stringify({
url,
method: dom.forecastMethod?.value || "weighted_mean",
weighting_type: dom.weightingType?.value || "recent_heavy",
service_level: parseFloat(dom.serviceLevel?.value || "0.95"),
horizon: parseInt(dom.forecastHorizon?.value || "1", 10)
})
});
const data = await parseJsonResponse(
res,
"Failed to load Google Sheet"
);
applyPredictionData(data);
showToast(
`Successfully imported ${data.items?.length || 0} items from Google Sheet!`,
"success"
);
} catch (error) {
showToast(error.message, "error");
}
}
// Sample data
async function loadSampleData() {
try {
const method = dom.forecastMethod?.value || "weighted_mean";
const weighting = dom.weightingType?.value || "recent_heavy";
const service = dom.serviceLevel?.value || "0.95";
const horizon = dom.forecastHorizon?.value || "1";
const params = new URLSearchParams({
method,
weighting_type: weighting,
service_level: service,
horizon
});
const res = await fetch(`/api/sample-data?${params.toString()}`);
const data = await parseJsonResponse(res, "Error loading sample data");
applyPredictionData(data);
showToast("Sample retail dataset loaded and forecasted!", "success");
} catch (error) {
showToast(error.message, "error");
}
}
// Recalculate predictions
async function recalculatePredictions() {
showToast("Recalculating forecasts...");
try {
const res = await fetch("/api/predict", {
method: "POST",
headers: { "Content-Type": "application/json" },
body: JSON.stringify({
items: state.items,
method: dom.forecastMethod?.value || "weighted_mean",
weighting_type: dom.weightingType?.value || "recent_heavy",
service_level: parseFloat(dom.serviceLevel?.value || "0.95"),
horizon: parseInt(dom.forecastHorizon?.value || "1", 10)
})
});
const data = await parseJsonResponse(
res,
"Failed to recalculate predictions"
);
applyPredictionData(data);
showToast("Forecasts updated with new parameters!", "success");
} catch (error) {
showToast(error.message, "error");
}
}
async function parseJsonResponse(response, fallbackMessage) {
let data = null;
try {
data = await response.json();
} catch {
throw new Error(fallbackMessage);
}
if (!response.ok) {
throw new Error(data?.detail || data?.message || fallbackMessage);
}
return data;
}
// Apply prediction results
function applyPredictionData(data) {
if (!data || typeof data !== "object") {
showToast("Invalid prediction data received from the server.", "error");
return;
}
state.currentData = data;
state.summary = data.summary || {};
state.items = Array.isArray(data.items) ? data.items : [];
const summary = state.summary;
setText(dom.kpiTotalItems, summary.total_items ?? state.items.length);
setText(dom.kpiCriticalRisk, summary.critical_risk_count ?? 0);
setText(dom.kpiReorderCount, summary.reorder_needed_count ?? 0);
setText(
dom.kpiReorderInvestment,
formatCurrency(summary.total_reorder_investment)
);
setText(
dom.kpiTotalStockVal,
formatCurrency(summary.total_stock_value)
);
setText(dom.kpiOverstockCount, summary.overstock_count ?? 0);
setText(
dom.kpiMethodSub,
`${summary.method_used || "N/A"} (SL: ${summary.service_level_pct ?? "N/A"}%)`
);
setText(
dom.chatContextStatus,
`Monitoring ${state.items.length} items (${summary.reorder_needed_count ?? 0} need reorder). Using ${dom.ollamaModelSelect?.value || state.selectedModel}.`
);
renderStockDemandChart();
renderRiskDoughnutChart();
renderTable(state.items);
}
function setText(element, value) {
if (element) element.textContent = value;
}
function formatCurrency(value) {
const number = Number(value);
if (!Number.isFinite(number)) return "$0.00";
return `$${number.toLocaleString("en-US", {
minimumFractionDigits: 2,
maximumFractionDigits: 2
})}`;
}
// Charts
function renderStockDemandChart() {
const canvas = document.getElementById("stockDemandChart");
if (!canvas || typeof Chart === "undefined") return;
const ctx = canvas.getContext("2d");
if (state.charts.stockDemand) {
state.charts.stockDemand.destroy();
}
const topItems = state.items.slice(0, 10);
const labels = topItems.map(item => item.sku ?? "");
const currentStock = topItems.map(item => Number(item.current_stock) || 0);
const predictedDemand = topItems.map(
item => Number(item.next_period_forecast) || 0
);
const reorderPoints = topItems.map(
item => Number(item.reorder_point) || 0
);
state.charts.stockDemand = new Chart(ctx, {
type: "bar",
data: {
labels,
datasets: [
{
label: "Current Stock",
data: currentStock,
backgroundColor: "rgba(56, 189, 248, 0.75)",
borderColor: "#38bdf8",
borderWidth: 1,
borderRadius: 4
},
{
label: "Predicted Demand",
data: predictedDemand,
backgroundColor: "rgba(168, 85, 247, 0.75)",
borderColor: "#a855f7",
borderWidth: 1,
borderRadius: 4
},
{
label: "Reorder Point (ROP)",
data: reorderPoints,
backgroundColor: "rgba(239, 68, 68, 0.75)",
borderColor: "#ef4444",
borderWidth: 1,
borderRadius: 4
}
]
},
options: {
responsive: true,
maintainAspectRatio: false,
onClick: (event, elements) => {
if (elements.length > 0) {
const index = elements[0].index;
if (topItems[index]) openItemModal(topItems[index]);
}
},
plugins: {
legend: {
labels: {
color: "#94a3b8",
font: {
family: "'Plus Jakarta Sans', sans-serif"
}
}
},
tooltip: {
backgroundColor: "#1e2638",
titleColor: "#f0f4fc",
bodyColor: "#94a3b8",
borderColor: "#384766",
borderWidth: 1
}
},
scales: {
x: {
grid: { color: "rgba(255, 255, 255, 0.05)" },
ticks: { color: "#94a3b8" }
},
y: {
grid: { color: "rgba(255, 255, 255, 0.05)" },
ticks: { color: "#94a3b8" }
}
}
}
});
}
function renderRiskDoughnutChart() {
const canvas = document.getElementById("riskDoughnutChart");
if (!canvas || typeof Chart === "undefined") return;
const ctx = canvas.getContext("2d");
if (state.charts.riskDoughnut) {
state.charts.riskDoughnut.destroy();
}
const counts = {
critical: 0,
high: 0,
medium: 0,
overstock: 0,
healthy: 0
};
state.items.forEach(item => {
switch (String(item.risk_level || "").toUpperCase()) {
case "CRITICAL":
counts.critical++;
break;
case "HIGH":
counts.high++;
break;
case "MEDIUM":
counts.medium++;
break;
case "OVERSTOCK":
counts.overstock++;
break;
default:
counts.healthy++;
}
});
state.charts.riskDoughnut = new Chart(ctx, {
type: "doughnut",
data: {
labels: [
"Stockout / Critical",
"Low Stock (Safety)",
"Below ROP",
"Overstocked (>90d)",
"Healthy"
],
datasets: [
{
data: [
counts.critical,
counts.high,
counts.medium,
counts.overstock,
counts.healthy
],
backgroundColor: [
"#ef4444",
"#f97316",
"#f59e0b",
"#06b6d4",
"#10b981"
],
borderWidth: 0
}
]
},
options: {
responsive: true,
maintainAspectRatio: false,
plugins: {
legend: {
labels: { color: "#94a3b8" }
}
}
}
});
}
// -----------------------------
// Inventory table
// -----------------------------
function renderTable(itemsToRender) {
if (!dom.tableBody) return;
if (!itemsToRender || itemsToRender.length === 0) {
dom.tableBody.innerHTML =
'<tr><td colspan="12" class="empty-state">No matching items found.</td></tr>';
return;
}
dom.tableBody.innerHTML = "";
itemsToRender.forEach(item => {
const tr = document.createElement("tr");
const badgeClass = `badge-${item.status_badge || "healthy"}`;
tr.innerHTML = `
<td><strong>${escapeHtml(item.sku)}</strong></td>
<td>${escapeHtml(item.name)}</td>
<td><span class="helper-tag">${escapeHtml(item.category)}</span></td>
<td><strong>${item.current_stock ?? 0}</strong></td>
<td>${item.lead_time_days ?? 0}d</td>
<td>${item.next_period_forecast ?? 0}</td>
<td>${item.safety_stock ?? 0}</td>
<td><strong>${item.reorder_point ?? 0}</strong></td>
<td>
<strong style="color: ${
Number(item.recommended_order_qty) > 0 ? "#fbbf24" : "#94a3b8"
}">
${item.recommended_order_qty ?? 0}
</strong>
</td>
<td>${formatCurrency(item.reorder_investment)}</td>
<td><span class="badge ${badgeClass}">${escapeHtml(item.status)}</span></td>
<td>
<button
class="btn btn-secondary btn-inspect"
style="padding: 4px 8px; font-size: 11px;"
type="button"
>
n Inspect
</button>
</td>
`;
tr.querySelector(".btn-inspect")?.addEventListener("click", () => {
openItemModal(item);
});
dom.tableBody.appendChild(tr);
});
}
function filterTable() {
const query = (dom.tableSearch?.value || "").toLowerCase().trim();
const statusFilter = dom.filterStatus?.value || "ALL";
const filtered = state.items.filter(item => {
const sku = String(item.sku || "").toLowerCase();
const name = String(item.name || "").toLowerCase();
const category = String(item.category || "").toLowerCase();
const matchesQuery =
!query ||
sku.includes(query) ||
name.includes(query) ||
category.includes(query);
const matchesStatus =
statusFilter === "ALL" || item.risk_level === statusFilter;
return matchesQuery && matchesStatus;
});
renderTable(filtered);
}
// CSV export
function exportTableToCSV() {
if (!state.items.length) {
showToast("No inventory data available to export.", "warning");
return;
}
const headers = [
"SKU",
"Name",
"Category",
"Current Stock",
"Lead Time Days",
"Next Period Forecast",
"Safety Stock",
"Reorder Point",
"Recommended Order Qty",
"Reorder Investment",
"Status",
"Risk Level",
"Days of Inventory"
];
const rows = state.items.map(item => [
csvCell(item.sku),
csvCell(item.name),
csvCell(item.category),
item.current_stock ?? 0,
item.lead_time_days ?? 0,
item.next_period_forecast ?? 0,
item.safety_stock ?? 0,
item.reorder_point ?? 0,
item.recommended_order_qty ?? 0,
item.reorder_investment ?? 0,
csvCell(item.status),
csvCell(item.risk_level),
item.days_of_inventory ?? 0
]);
const csvContent = [
headers.map(csvCell).join(","),
...rows.map(row => row.join(","))
].join("\n");
const blob = new Blob([csvContent], {
type: "text/csv;charset=utf-8;"
});
const url = URL.createObjectURL(blob);
const link = document.createElement("a");
link.href = url;
link.download =
`inventory_predictions_${new Date().toISOString().slice(0, 10)}.csv`;
document.body.appendChild(link);
link.click();
link.remove();
URL.revokeObjectURL(url);
showToast("Prediction CSV exported successfully!", "success");
}
function csvCell(value) {
return `"${String(value ?? "").replace(/"/g, '""')}"`;
}
// -----------------------------
// Item modal
// -----------------------------
function openItemModal(item) {
if (!item) return;
setText(dom.modalStock, `${item.current_stock ?? 0} units`);
setText(dom.modalDemand, `${item.next_period_forecast ?? 0} units/mo`);
setText(dom.modalSafetyStock, `${item.safety_stock ?? 0} units`);
setText(dom.modalRop, `${item.reorder_point ?? 0} units`);
setText(
dom.modalOrderQty,
`${item.recommended_order_qty ?? 0} units`
);
setText(
dom.modalOrderCost,
formatCurrency(item.reorder_investment)
);
if (dom.modalExplanation) {
dom.modalExplanation.innerHTML = `
<strong>Method:</strong> ${escapeHtml(item.forecast_method || "N/A")}
(${escapeHtml(item.forecast_formula || "")})<br>
<strong>Analysis:</strong>
Daily demand is <code>${item.daily_demand ?? 0} units/day</code>
with a <code>${item.lead_time_days ?? 0}-day</code> lead time.
Lead time demand is <code>${item.lead_time_demand ?? 0} units</code>.
With a safety stock buffer of
<code>${item.safety_stock ?? 0} units</code>, the Reorder Point is
<strong>${item.reorder_point ?? 0} units</strong>.
${
item.needs_reorder
? `<span style="color:#fbbf24;">
nn Current stock (${item.current_stock ?? 0}) is at or below ROP.
Place PO for ${item.recommended_order_qty ?? 0} units.
</span>`
: `<span style="color:#34d399;">
n Current stock covers demand and buffer safely.
</span>`
}
`;
}
renderItemHistoryChart(item);
if (dom.itemModal) {
dom.itemModal.style.display = "flex";
dom.itemModal.classList.add("active");
}
}
function closeModal() {
if (!dom.itemModal) return;
dom.itemModal.style.display = "none";
dom.itemModal.classList.remove("active");
}
function renderItemHistoryChart(item) {
const canvas =
document.getElementById("itemHistoryChart") ||
document.getElementById("itemHistory");
if (!canvas || typeof Chart === "undefined") return;
const ctx = canvas.getContext("2d");
if (state.charts.itemHistory) {
state.charts.itemHistory.destroy();
}
const history = Array.isArray(item.demand_history)
? item.demand_history
: [];
const labels = history.map(
(_, index) => `Month -${history.length - index}`
);
labels.push("Forecast Next Mo");
const dataPoints = [
...history.map(value => Number(value) || 0),
Number(item.next_period_forecast) || 0
];
state.charts.itemHistory = new Chart(ctx, {
type: "line",
data: {
labels,
datasets: [
{
label: `${item.sku || "Item"} Sales Velocity`,
data: dataPoints,
borderColor: "#38bdf8",
backgroundColor: "rgba(56, 189, 248, 0.1)",
fill: true,
tension: 0.3,
pointBackgroundColor: labels.map((_, index) =>
index === labels.length - 1 ? "#a855f7" : "#38bdf8"
),
pointRadius: labels.map((_, index) =>
index === labels.length - 1 ? 7 : 4
)
}
]
},
options: {
responsive: true,
maintainAspectRatio: false,
plugins: {
legend: {
labels: { color: "#94a3b8" }
}
},
scales: {
x: {
ticks: { color: "#94a3b8" }
},
y: {
ticks: { color: "#94a3b8" }
}
}
}
});
}
// AI report
async function generateAIReport() {
if (!state.items.length) {
showToast("Please load data before generating an AI report.", "warning");
return;
}
switchTab("report-tab");
if (dom.reportLoading) dom.reportLoading.style.display = "block";
if (dom.reportContent) dom.reportContent.innerHTML = "";
try {
const res = await fetch("/api/ai/report", {
method: "POST",
headers: { "Content-Type": "application/json" },
body: JSON.stringify({
summary: state.summary,
items: state.items,
model: dom.ollamaModelSelect?.value || state.selectedModel
})
});
const data = await parseJsonResponse(
res,
"Error generating AI report"
);
if (dom.reportLoading) dom.reportLoading.style.display = "none";
if (data.success) {
setText(
dom.reportSourceBadge,
`Synthesized by: ${data.source || "Ollama"}`
);
if (dom.reportContent) {
if (typeof marked !== "undefined") {
dom.reportContent.innerHTML = marked.parse(
data.report_markdown || ""
);
} else {
dom.reportContent.textContent = data.report_markdown || "";
}
}
showToast(
"Executive report generated successfully!",
"success"
);
} else {
if (dom.reportContent) {
dom.reportContent.innerHTML =
'<p style="color:var(--color-danger)">Report generation failed.</p>';
}
showToast("Report generation failed.", "error");
}
} catch (error) {
if (dom.reportLoading) dom.reportLoading.style.display = "none";
showToast(error.message, "error");
}
}
function copyReportMarkdown() {
const text = dom.reportContent?.innerText?.trim() || "";
if (!text || text.includes("No Report Generated Yet")) {
showToast("No report content to copy.", "warning");
return;
}
navigator.clipboard
.writeText(text)
.then(() => showToast("Report copied to clipboard!", "success"))
.catch(() => showToast("Could not copy report.", "error"));
}
// AI chat
async function sendChatMessage() {
const text = dom.chatInput?.value?.trim();
if (!text) return;
if (dom.chatInput) dom.chatInput.value = "";
appendChatMessage("user", text);
const typingIndicator = appendChatMessage(
"assistant",
"Thinking..."
);
try {
const res = await fetch("/api/ai/chat", {
method: "POST",
headers: { "Content-Type": "application/json" },
body: JSON.stringify({
message: text,
history: state.chatHistory,
summary: state.summary,
items: state.items || [],
model: dom.ollamaModelSelect?.value || state.selectedModel
})
});
const data = await parseJsonResponse(
res,
"AI chat request failed"
);
typingIndicator.remove();
appendChatMessage(
"assistant",
data.reply || "No response received.",
true
);
state.chatHistory.push({
role: "user",
content: text
});
state.chatHistory.push({
role: "assistant",
content: data.reply || ""
});
} catch (error) {
typingIndicator.remove();
appendChatMessage(
"assistant",
`Sorry, an error occurred: ${error.message}`
);
}
}
function appendChatMessage(role, content, isMarkdown = false) {
if (!dom.chatMessages) {
return document.createElement("div");
}
const msgDiv = document.createElement("div");
msgDiv.className = `message ${role}`;
const avatar = role === "user" ? "n" : "n";
let bodyContent;
if (isMarkdown && typeof marked !== "undefined") {
bodyContent = marked.parse(String(content ?? ""));
} else {
const p = document.createElement("p");
p.textContent = String(content ?? "");
bodyContent = p.outerHTML;
}
msgDiv.innerHTML = `
<div class="message-avatar">${avatar}</div>
<div class="message-content">${bodyContent}</div>
`;
dom.chatMessages.appendChild(msgDiv);
dom.chatMessages.scrollTop = dom.chatMessages.scrollHeight;
return msgDiv;
}
// Security/helper functions
function escapeHtml(value) {
return String(value ?? "")
.replace(/&/g, "&amp;")
.replace(/</g, "&lt;")
.replace(/>/g, "&gt;")
.replace(/"/g, "&quot;")
.replace(/'/g, "&#039;");
}
});