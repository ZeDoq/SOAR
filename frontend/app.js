/**
 * ===== SOAR 控制室前端应用 =====
 *
 * 纯前端 JavaScript 应用，通过 REST API 与后端通信。
 * 提供告警查看、剧本执行触发和运行结果展示功能。
 *
 * 交互流程：
 *   1. 页面加载 → 获取告警列表和运行记录
 *   2. 用户点击某条告警的 "Run Playbook" 按钮
 *      → POST /runs 触发剧本执行（立即返回 queued 状态）
 *   3. 用户点击运行记录 → GET /runs/{id} 查看详细步骤日志
 *   4. "Refresh" 按钮 → 刷新所有数据
 *
 * API 基地址可通过页面顶部的文本框配置，默认为 http://127.0.0.1:8000
 */

// DOM 元素引用
const alertsList = document.getElementById("alertsList");      // 告警列表容器
const runsList = document.getElementById("runsList");          // 运行记录列表容器
const runDetail = document.getElementById("runDetail");        // 运行详情展示区
const apiBaseInput = document.getElementById("apiBase");       // API 基地址输入框
const refreshBtn = document.getElementById("refreshBtn");      // 刷新按钮
const importBtn = document.getElementById("importBtn");        // 导入样本数据按钮


/**
 * 获取当前配置的 API 基地址，并去除末尾斜杠
 */
function apiBase() {
  return apiBaseInput.value.replace(/\/$/, "");
}


/**
 * 根据运行状态生成对应的 HTML 标签徽章
 * @param {string} status - 运行状态（completed/failed/running 等）
 * @returns {string} 带样式类名的 span 标签 HTML
 */
function statusBadge(status) {
  if (!status) return "";
  return `<span class="status ${status}">${status}</span>`;
}


/**
 * 渲染告警列表。
 * 每条告警显示 IP 地址、描述、时间，以及 "Run Playbook" 按钮。
 *
 * @param {Array} alerts - 告警对象数组
 */
function renderAlerts(alerts) {
  alertsList.innerHTML = "";
  alerts.forEach((alert) => {
    const item = document.createElement("li");
    item.className = "card";
    item.innerHTML = `
      <div class="card-title">${alert.ip}</div>
      <div class="card-meta">${alert.description || "No description"}</div>
      <div class="card-meta">${alert.observed_at}</div>
      <button data-alert="${alert.id}">Run Playbook</button>
    `;
    // "Run Playbook" 按钮点击 → 触发剧本执行
    item.querySelector("button").addEventListener("click", (event) => {
      event.stopPropagation();
      startRun(alert.id);
    });
    // 点击告警卡片 → 查看告警详情
    item.addEventListener("click", () => renderRunDetail(null, alert));
    alertsList.appendChild(item);
  });
}


/**
 * 渲染运行记录列表。
 * 每条记录显示运行编号、关联告警 ID、状态和时间。
 *
 * @param {Array} runs - 运行记录对象数组
 */
function renderRuns(runs) {
  runsList.innerHTML = "";
  runs.forEach((run) => {
    const item = document.createElement("li");
    item.className = "card";
    item.innerHTML = `
      <div class="card-title">Run #${run.id}</div>
      <div class="card-meta">Alert ${run.alert_id} - ${run.started_at || "queued"}</div>
      ${statusBadge(run.status)}
    `;
    // 点击运行记录 → 获取并显示详细步骤日志
    item.addEventListener("click", () => fetchRunDetail(run.id));
    runsList.appendChild(item);
  });
}


/**
 * 渲染运行详情。
 * 显示运行状态、风险评分、最终决策，以及每一步的执行日志。
 *
 * @param {Object|null} run - 运行对象（含 run 和 steps 字段）
 * @param {Object|null} alert - 告警对象（当只查看告警时）
 */
function renderRunDetail(run, alert) {
  if (!run && !alert) {
    runDetail.textContent = "Select an alert or run to view details.";
    return;
  }
  // 只查看告警详情
  if (alert && !run) {
    runDetail.textContent = `Alert ${alert.id}\nIP: ${alert.ip}\nSource: ${alert.source}\nTags: ${alert.tags}`;
    return;
  }
  // 查看运行详情（包含步骤日志）
  const steps = run.steps || [];
  const lines = [
    `Run ${run.run.id}`,
    `Status: ${run.run.status}`,
    `Risk Score: ${run.run.risk_score ?? "-"}`,
    `Decision: ${
      typeof run.run.decision === "string"
        ? run.run.decision
        : JSON.stringify(run.run.decision, null, 2)
    }`,
    "",
    "Steps:",
  ];
  // 列出每个步骤的名称、状态和详细输出
  steps.forEach((step) => {
    lines.push(`- ${step.name}: ${step.status}`);
    if (step.detail) {
      const detailText =
        typeof step.detail === "string"
          ? step.detail
          : JSON.stringify(step.detail, null, 2);
      lines.push(`  detail: ${detailText}`);
    }
  });
  runDetail.textContent = lines.join("\n");
}


/**
 * 从 API 获取告警列表并渲染
 */
async function fetchAlerts() {
  const response = await fetch(`${apiBase()}/alerts`);
  const data = await response.json();
  renderAlerts(data.alerts || []);
}


/**
 * 从 API 获取运行记录列表并渲染
 */
async function fetchRuns() {
  const response = await fetch(`${apiBase()}/runs`);
  const data = await response.json();
  renderRuns(data.runs || []);
}


/**
 * 从 API 获取单次运行的详细步骤日志并渲染
 * @param {number} runId - 运行记录 ID
 */
async function fetchRunDetail(runId) {
  const response = await fetch(`${apiBase()}/runs/${runId}`);
  const data = await response.json();
  renderRunDetail({ run: data.run, steps: data.steps });
}


/**
 * 触发指定告警的剧本执行。
 * POST /runs 返回后立即刷新列表，后台异步执行剧本。
 *
 * @param {number} alertId - 告警 ID
 */
async function startRun(alertId) {
  await fetch(`${apiBase()}/runs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ alert_id: alertId }),
  });
  await refreshAll();
}


/**
 * 导入样本告警数据。
 * 提示用户在终端执行导入命令。
 */
async function importSampleAlerts() {
  alert(
    "Run: python backend/import_alerts.py data/alerts.json in a terminal to load sample alerts."
  );
}


/**
 * 刷新所有数据（告警列表 + 运行记录）
 */
async function refreshAll() {
  await Promise.all([fetchAlerts(), fetchRuns()]);
}


// ---- 事件绑定 ----
refreshBtn.addEventListener("click", refreshAll);
importBtn.addEventListener("click", importSampleAlerts);

// ---- 页面加载时自动刷新数据 ----
refreshAll();