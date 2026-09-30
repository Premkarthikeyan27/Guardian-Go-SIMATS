// Guardian Dashboard JavaScript Application

document.addEventListener("DOMContentLoaded", () => {
  loadAssignedBookings();
  loadBeaconStatus();
  setInterval(loadBeaconStatus, 5000);
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

// 1. ASSIGNED BOOKINGS & ACTIONS
async function loadAssignedBookings() {
  try {
    const res = await fetch("/api/v1/bookings?role=guardian&user_id=1");
    const bookings = await res.json();
    const list = document.getElementById("assignedBookingsGrid");
    list.innerHTML = "";

    const pending = bookings.filter(b => b.status === "REQUESTED");
    const badge = document.getElementById("gPendingBadge");
    if (badge) badge.textContent = pending.length;
    const countBadge = document.getElementById("pendingCountBadge");
    if (countBadge) countBadge.textContent = `${pending.length} Pending`;

    if (bookings.length === 0) {
      list.innerHTML = "<div style='color: var(--text-muted); text-align: center; padding: 1rem;'>No active booking requests assigned.</div>";
      return;
    }

    bookings.forEach(b => {
      const card = document.createElement("div");
      card.style.cssText = "background: var(--main-bg); border: 1px solid var(--card-border); padding: 1.1rem; border-radius: 12px;";
      card.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem;">
          <div>
            <div style="font-weight: 800; font-size: 1rem;">${b.parent_name}</div>
            <div style="font-size: 0.82rem; color: var(--primary-green); font-weight: 700;">${b.care_type}</div>
          </div>
          <span class="badge badge-${b.status}">${b.status}</span>
        </div>
        <div style="font-size: 0.82rem; color: var(--text-muted); margin-bottom: 0.85rem;">
          📅 ${b.date} • ⏱️ ${b.time}<br>
          📝 Notes: ${b.notes || 'No special instructions.'}
        </div>
        ${b.status === 'REQUESTED' ? `
          <div style="display: flex; gap: 0.5rem;">
            <button class="btn btn-purple btn-sm" style="flex: 1;" onclick="acceptBooking(${b.id})">Accept Booking</button>
            <button class="btn btn-outline-dark btn-sm" style="flex: 1; color: var(--coral-danger);" onclick="declineBooking(${b.id})">Decline</button>
          </div>
        ` : `
          <div style="font-size: 0.8rem; color: var(--mint-text); font-weight: 700;">✓ Booking Confirmed</div>
        `}
      `;
      list.appendChild(card);
    });
  } catch (err) {
    console.error("Failed to load assigned bookings:", err);
  }
}

async function acceptBooking(bookingId) {
  try {
    const res = await fetch(`/api/v1/bookings/${bookingId}/accept`, { method: "POST" });
    if (res.ok) {
      showToast("✓ Booking request accepted!");
      loadAssignedBookings();
    } else {
      showToast("Failed to accept booking", "danger");
    }
  } catch (err) {
    showToast("Error accepting booking", "danger");
  }
}

async function declineBooking(bookingId) {
  try {
    const res = await fetch(`/api/v1/bookings/${bookingId}/decline`, { method: "POST" });
    if (res.ok) {
      showToast("Booking request declined", "warning");
      loadAssignedBookings();
    } else {
      showToast("Failed to decline booking", "danger");
    }
  } catch (err) {
    showToast("Error declining booking", "danger");
  }
}

// 2. CHECK IN / CHECK OUT
async function handleCheckIn() {
  try {
    const res = await fetch("/api/v1/care-sessions/check-in", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ booking_id: 1, guardian_id: 1 })
    });
    if (res.ok) {
      showToast("✓ Checked in! Active session timer started.");
    }
  } catch (err) {
    showToast("Error checking in", "danger");
  }
}

async function handleCheckOut() {
  try {
    const res = await fetch("/api/v1/care-sessions/check-out", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ booking_id: 1, guardian_id: 1 })
    });
    if (res.ok) {
      showToast("✓ Check-out recorded. Session complete!");
    }
  } catch (err) {
    showToast("Error checking out", "danger");
  }
}

// 3. ROUTINE LOG SUBMISSION
async function submitRoutineForm(event) {
  event.preventDefault();
  const category = document.getElementById("routineCategory").value;
  const title = document.getElementById("routineTitle").value;
  const details = document.getElementById("routineDetails").value;

  try {
    const res = await fetch("/api/v1/care/routine", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: 1,
        guardian_id: 1,
        category: category,
        title: title,
        details: details
      })
    });

    if (res.ok) {
      showToast("✓ Care routine log submitted!");
      document.getElementById("routineTitle").value = "";
      document.getElementById("routineDetails").value = "";
    } else {
      showToast("Failed to submit routine log", "danger");
    }
  } catch (err) {
    showToast("Error submitting routine", "danger");
  }
}

// 4. BLE BEACON STATUS & SIMULATION
async function loadBeaconStatus() {
  try {
    const res = await fetch("/api/v1/beacon/status");
    const b = await res.json();
    const gDesc = document.getElementById("gBeaconDesc");
    if (gDesc) {
      if (b.in_safe_zone) {
        gDesc.textContent = `CONNECTED • ${b.distance_m} m`;
        gDesc.style.color = "white";
      } else {
        gDesc.textContent = `⚠ BREACH • ${b.distance_m} m`;
        gDesc.style.color = "#f87171";
      }
    }
  } catch (err) {
    console.error("Beacon status error:", err);
  }
}

async function simulateWarning() {
  try {
    const res = await fetch("/api/v1/beacon/simulate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "warning" })
    });
    if (res.ok) {
      showToast("⚠ Simulated child beacon zone breach warning!", "warning");
      loadBeaconStatus();
    }
  } catch (err) {
    showToast("Simulation error", "danger");
  }
}

// 5. SOS & AI DRAWER
function openSosModal() {
  document.getElementById("sosModal").classList.add("active");
}

function closeSosModal() {
  document.getElementById("sosModal").classList.remove("active");
}

async function confirmSosAlert() {
  try {
    const res = await fetch("/api/v1/safety/sos", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: 2,
        guardian_id: 1,
        notes: "Guardian triggered Emergency SOS button"
      })
    });

    if (res.ok) {
      closeSosModal();
      showToast("🚨 EMERGENCY SOS BROADCAST ACTIVATED!", "danger");
    }
  } catch (err) {
    showToast("Failed to trigger SOS", "danger");
  }
}

function openGuardianAiDrawer() {
  document.getElementById("gAiDrawerModal").classList.add("active");
}

function closeGuardianAiDrawer() {
  document.getElementById("gAiDrawerModal").classList.remove("active");
}

async function handleGAiSubmit(event) {
  event.preventDefault();
  const input = document.getElementById("gAiInput");
  const prompt = input.value.trim();
  if (!prompt) return;

  const chatWin = document.getElementById("gAiChatWindow");
  
  const userMsg = document.createElement("div");
  userMsg.style.cssText = "margin-bottom: 0.75rem; text-align: right;";
  userMsg.innerHTML = `<span style="background: var(--primary-green); color: white; padding: 0.5rem 0.85rem; border-radius: 12px 12px 0 12px; display: inline-block; font-size: 0.85rem; text-align: left;">${prompt}</span>`;
  chatWin.appendChild(userMsg);

  input.value = "";
  chatWin.scrollTop = chatWin.scrollHeight;

  const btn = document.getElementById("gAiSubmitBtn");
  btn.disabled = true;
  btn.textContent = "Thinking...";

  try {
    const res = await fetch("/api/v1/ai/assistant/guardian", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: prompt, user_id: 2 })
    });

    const data = await res.json();
    
    const aiMsg = document.createElement("div");
    aiMsg.style.cssText = "margin-bottom: 0.75rem; text-align: left;";
    aiMsg.innerHTML = `
      <div style="background: white; border: 1px solid var(--card-border); padding: 0.75rem 1rem; border-radius: 0 12px 12px 12px; display: inline-block; max-width: 90%; font-size: 0.85rem; box-shadow: var(--card-shadow);">
        <strong style="color: var(--primary-green); display: block; margin-bottom: 0.25rem;">🤖 Guardian Protocol AI:</strong>
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
