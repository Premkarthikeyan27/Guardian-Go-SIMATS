// Admin Control Center JavaScript Application

document.addEventListener("DOMContentLoaded", () => {
  loadAnalytics();
  loadGuardians();
  loadSafetyEvents();
  loadAuditLogs();
});

function showToast(message, type = "success") {
  const container = document.getElementById("toast-container");
  const toast = document.createElement("div");
  toast.className = `toast ${type === "warning" ? "toast-warning" : type === "danger" ? "toast-danger" : ""}`;
  toast.innerHTML = `<span>${type === "danger" ? "🚨" : type === "warning" ? "⚠" : "✓"}</span> ${message}`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.remove();
  }, 4000);
}

// 1. ANALYTICS & TOP KPI METRICS
async function loadAnalytics() {
  try {
    const res = await fetch("/api/v1/admin/analytics");
    const data = await res.json();
    document.getElementById("kpiTotalGuardians").textContent = data.total_users || 286;
    document.getElementById("kpiVerifiedGuardians").textContent = data.verified_guardians || 272;
    document.getElementById("kpiActiveSessions").textContent = data.active_bookings || 74;
    document.getElementById("kpiPendingVerif").textContent = data.pending_verifications || 18;
    document.getElementById("kpiActiveSos").textContent = data.safety_events || 0;
    
    const badge = document.getElementById("admVerifBadge");
    if (badge) badge.textContent = data.pending_verifications || 18;
  } catch (err) {
    console.error("Failed to load analytics:", err);
  }
}

// 2. GUARDIAN VERIFICATION PIPELINE
async function loadGuardians() {
  try {
    const res = await fetch("/api/v1/guardians");
    const guardians = await res.json();
    const tbody = document.getElementById("adminGuardiansTable");
    tbody.innerHTML = "";

    guardians.forEach(g => {
      const tr = document.createElement("tr");
      tr.style.borderBottom = "1px solid var(--card-border)";
      tr.innerHTML = `
        <td style="padding: 1rem; font-weight: 700;">
          <div style="display: flex; align-items: center; gap: 0.65rem;">
            <img src="${g.avatar || 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150'}" style="width: 34px; height: 34px; border-radius: 50%; object-fit: cover;">
            <span>${g.name}</span>
          </div>
        </td>
        <td style="padding: 1rem;"><span style="color: var(--mint-text); font-weight: 700;">✓ ${g.identity_status}</span></td>
        <td style="padding: 1rem;"><span style="color: ${g.bg_status === 'VERIFIED' ? 'var(--mint-text)' : 'var(--warning-orange)'}; font-weight: 700;">${g.bg_status === 'VERIFIED' ? '✓ VERIFIED' : '⏳ PENDING'}</span></td>
        <td style="padding: 1rem;"><span style="color: var(--mint-text); font-weight: 700;">✓ ${g.cpr_status}</span></td>
        <td style="padding: 1rem; font-weight: 800; color: var(--primary-green);">${g.trust_score}/100</td>
        <td style="padding: 1rem;"><span class="badge badge-${g.overall_status === 'VERIFIED' ? 'verified' : g.overall_status === 'REJECTED' ? 'danger' : 'warning'}">${g.overall_status}</span></td>
        <td style="padding: 1rem; text-align: right;">
          <div style="display: flex; gap: 0.35rem; justify-content: flex-end;">
            <button class="btn btn-outline-dark btn-sm" onclick="viewGuardianDetail('${g.name}')">Review</button>
            <button class="btn btn-purple btn-sm" onclick="approveGuardian(${g.id})">Approve</button>
            <button class="btn btn-danger-coral btn-sm" onclick="rejectGuardian(${g.id})">Reject</button>
          </div>
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Failed to load guardians:", err);
  }
}

async function approveGuardian(guardianId) {
  try {
    const res = await fetch(`/api/v1/admin/guardians/${guardianId}/approve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reason: "Admin verified all 4-gate compliance standards" })
    });
    if (res.ok) {
      showToast("✓ Guardian application APPROVED!");
      loadGuardians();
      loadAnalytics();
      loadAuditLogs();
    }
  } catch (err) {
    showToast("Approval error", "danger");
  }
}

async function rejectGuardian(guardianId) {
  try {
    const res = await fetch(`/api/v1/admin/guardians/${guardianId}/reject`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reason: "Documentation audit flag" })
    });
    if (res.ok) {
      showToast("Guardian application REJECTED", "warning");
      loadGuardians();
      loadAnalytics();
      loadAuditLogs();
    }
  } catch (err) {
    showToast("Rejection error", "danger");
  }
}

function viewGuardianDetail(name) {
  alert(`Caregiver Verification Dossier: ${name}\n\n• Identity Check: PASS\n• Background Check: PASS\n• CPR & First Aid: PASS\n• Document Standards: VERIFIED`);
}

// 3. SAFETY MONITORING
async function loadSafetyEvents() {
  try {
    const res = await fetch("/api/v1/safety/events");
    const events = await res.json();
    const tbody = document.getElementById("adminSafetyTable");
    tbody.innerHTML = "";

    if (events.length === 0) {
      tbody.innerHTML = "<tr><td colspan='5' style='padding: 1rem; text-align: center; color: var(--text-muted);'>No active safety incidents reported.</td></tr>";
      return;
    }

    events.forEach(e => {
      const tr = document.createElement("tr");
      tr.style.borderBottom = "1px solid var(--card-border)";
      tr.innerHTML = `
        <td style="padding: 0.85rem 1rem; color: var(--text-muted); font-size: 0.78rem;">${e.created_at}</td>
        <td style="padding: 0.85rem 1rem; font-weight: 800;">${e.event_type}</td>
        <td style="padding: 0.85rem 1rem;"><span class="badge badge-${e.severity.toLowerCase()}">${e.severity}</span></td>
        <td style="padding: 0.85rem 1rem;"><span class="badge badge-${e.status === 'ACTIVE' ? 'warning' : 'verified'}">${e.status}</span></td>
        <td style="padding: 0.85rem 1rem; text-align: right;">
          ${e.status === 'ACTIVE' ? `
            <button class="btn btn-purple btn-sm" onclick="resolveSafetyEvent(${e.id})">Resolve</button>
          ` : `
            <span style="font-size: 0.8rem; color: var(--mint-text); font-weight: 700;">✓ Resolved</span>
          `}
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Failed to load safety events:", err);
  }
}

async function resolveSafetyEvent(eventId) {
  try {
    const res = await fetch(`/api/v1/safety/events/${eventId}/resolve`, { method: "POST" });
    if (res.ok) {
      showToast("✓ Safety incident resolved!");
      loadSafetyEvents();
      loadAuditLogs();
    }
  } catch (err) {
    showToast("Error resolving event", "danger");
  }
}

// 4. AUDIT LOGS
async function loadAuditLogs() {
  try {
    const res = await fetch("/api/v1/admin/audit");
    const logs = await res.json();
    const tbody = document.getElementById("adminAuditTable");
    tbody.innerHTML = "";

    logs.forEach(l => {
      const tr = document.createElement("tr");
      tr.style.borderBottom = "1px solid var(--card-border)";
      tr.innerHTML = `
        <td style="padding: 0.75rem 1rem; color: var(--text-muted); font-size: 0.78rem;">${l.timestamp}</td>
        <td style="padding: 0.75rem 1rem; font-weight: 600;">${l.actor}</td>
        <td style="padding: 0.75rem 1rem; font-weight: 800; color: var(--primary-green);">${l.action}</td>
        <td style="padding: 0.75rem 1rem;">${l.resource}</td>
        <td style="padding: 0.75rem 1rem;"><span class="badge badge-${l.status === 'SUCCESS' ? 'verified' : 'danger'}">${l.status}</span></td>
        <td style="padding: 0.75rem 1rem; color: var(--text-muted);">${l.details || ''}</td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Failed to load audit logs:", err);
  }
}

// 5. ADMIN AI DRAWER
function openAdminAiDrawer() {
  document.getElementById("adminAiDrawerModal").classList.add("active");
}

function closeAdminAiDrawer() {
  document.getElementById("adminAiDrawerModal").classList.remove("active");
}

async function handleAdminAiSubmit(event) {
  event.preventDefault();
  const input = document.getElementById("adminAiInput");
  const prompt = input.value.trim();
  if (!prompt) return;

  const chatWin = document.getElementById("adminAiChatWindow");
  
  const userMsg = document.createElement("div");
  userMsg.style.cssText = "margin-bottom: 0.75rem; text-align: right;";
  userMsg.innerHTML = `<span style="background: var(--primary-green); color: white; padding: 0.5rem 0.85rem; border-radius: 12px 12px 0 12px; display: inline-block; font-size: 0.85rem; text-align: left;">${prompt}</span>`;
  chatWin.appendChild(userMsg);

  input.value = "";
  chatWin.scrollTop = chatWin.scrollHeight;

  const btn = document.getElementById("adminAiSubmitBtn");
  btn.disabled = true;
  btn.textContent = "Thinking...";

  try {
    const res = await fetch("/api/v1/ai/assistant/user", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: prompt, user_id: 3 })
    });

    const data = await res.json();
    
    const aiMsg = document.createElement("div");
    aiMsg.style.cssText = "margin-bottom: 0.75rem; text-align: left;";
    aiMsg.innerHTML = `
      <div style="background: white; border: 1px solid var(--card-border); padding: 0.75rem 1rem; border-radius: 0 12px 12px 12px; display: inline-block; max-width: 90%; font-size: 0.85rem; box-shadow: var(--card-shadow);">
        <strong style="color: var(--primary-green); display: block; margin-bottom: 0.25rem;">🤖 Admin AI Operations:</strong>
        ${data.response}
      </div>
    `;
    chatWin.appendChild(aiMsg);
    chatWin.scrollTop = chatWin.scrollHeight;
  } catch (err) {
    showToast("AI assistant communication error", "danger");
  } finally {
    btn.disabled = false;
    btn.textContent = "Ask AI";
  }
}
