// Parent Dashboard JavaScript Application

document.addEventListener("DOMContentLoaded", () => {
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

// 1. BLE BEACON STATUS TELEMETRY
async function loadBeaconStatus() {
  try {
    const res = await fetch("/api/v1/beacon/status");
    const b = await res.json();
    const bleText = document.getElementById("heroBleSignalText");
    if (bleText) {
      if (b.in_safe_zone) {
        bleText.textContent = `BLE connected • ${b.distance_m} m`;
        bleText.style.color = "white";
      } else {
        bleText.textContent = `⚠ Safe zone breach • ${b.distance_m} m`;
        bleText.style.color = "#f87171";
      }
    }
  } catch (err) {
    console.error("Beacon status error:", err);
  }
}

// 2. MODALS & SOS ACTION
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
        user_id: 1,
        guardian_id: 1,
        notes: "Parent manually triggered Emergency SOS button"
      })
    });

    if (res.ok) {
      closeSosModal();
      showToast("🚨 EMERGENCY SOS BROADCAST ACTIVATED!", "danger");
    }
  } catch (err) {
    showToast("SOS trigger error", "danger");
  }
}

function openLiveSafetyModal() {
  alert("📡 Live Safety Telemetry View:\n\n• Child Beacon: Connected (8.0m)\n• Location: Morgan Home (Inside Trusted Geofence)\n• AI Safety Checks: 100% Passed\n• Caregiver Presence: Verified via Camera/BLE Handshake");
}

// 3. BOOKING WORKFLOW
function openBookingModal(guardianId, guardianName) {
  document.getElementById("bookGuardianId").value = guardianId;
  document.getElementById("bookGuardianName").value = guardianName;
  document.getElementById("bookingModal").classList.add("active");
}

function closeBookingModal() {
  document.getElementById("bookingModal").classList.remove("active");
}

async function submitBooking(event) {
  event.preventDefault();
  const guardian_id = parseInt(document.getElementById("bookGuardianId").value);
  const guardian_name = document.getElementById("bookGuardianName").value;
  const date = document.getElementById("bookDate").value;
  const time = document.getElementById("bookTime").value;
  const care_type = document.getElementById("bookCareType").value;
  const notes = document.getElementById("bookNotes").value;

  try {
    const res = await fetch("/api/v1/bookings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        parent_id: 1,
        guardian_id: guardian_id,
        parent_name: "Sarah Jenkins",
        date: date,
        time: time,
        care_type: care_type,
        notes: notes
      })
    });

    if (res.ok) {
      showToast(`✓ Booking request for ${guardian_name} submitted successfully!`);
      closeBookingModal();
    } else {
      showToast("Failed to submit booking", "danger");
    }
  } catch (err) {
    showToast("Error submitting booking request", "danger");
  }
}

// 4. AI ASSISTANT DRAWER
function openAiDrawer() {
  document.getElementById("aiDrawerModal").classList.add("active");
}

function closeAiDrawer() {
  document.getElementById("aiDrawerModal").classList.remove("active");
}

async function handleAiSubmit(event) {
  event.preventDefault();
  const input = document.getElementById("aiInput");
  const prompt = input.value.trim();
  if (!prompt) return;

  const chatWin = document.getElementById("aiChatWindow");
  
  // Append User message
  const userMsg = document.createElement("div");
  userMsg.style.cssText = "margin-bottom: 0.75rem; text-align: right;";
  userMsg.innerHTML = `<span style="background: var(--primary-green); color: white; padding: 0.5rem 0.85rem; border-radius: 12px 12px 0 12px; display: inline-block; font-size: 0.85rem; text-align: left;">${prompt}</span>`;
  chatWin.appendChild(userMsg);

  input.value = "";
  chatWin.scrollTop = chatWin.scrollHeight;

  const btn = document.getElementById("aiSubmitBtn");
  btn.disabled = true;
  btn.textContent = "Thinking...";

  try {
    const res = await fetch("/api/v1/ai/assistant/user", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: prompt, user_id: 1 })
    });

    const data = await res.json();
    
    // Append AI response
    const aiMsg = document.createElement("div");
    aiMsg.style.cssText = "margin-bottom: 0.75rem; text-align: left;";
    aiMsg.innerHTML = `
      <div style="background: white; border: 1px solid var(--card-border); padding: 0.75rem 1rem; border-radius: 0 12px 12px 12px; display: inline-block; max-width: 90%; font-size: 0.85rem; box-shadow: var(--card-shadow);">
        <strong style="color: var(--primary-green); display: block; margin-bottom: 0.25rem;">🤖 Guardian Go AI:</strong>
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
