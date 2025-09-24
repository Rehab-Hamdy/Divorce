// ==========================
// Global Config
// ==========================
const API_BASE = "http://127.0.0.1:8000"; // FastAPI backend URL
let doctorId = localStorage.getItem("doctorId");

// ==========================
// Register Doctor
// ==========================
document.getElementById("registerForm")?.addEventListener("submit", async (e) => {
  e.preventDefault();
  const data = {
    name: document.getElementById("regName").value,
    email: document.getElementById("regEmail").value,
  };

  const res = await fetch(`${API_BASE}/doctors`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    const err = await res.json();
    alert("Doctor registration failed: " + JSON.stringify(err));
    return;
  }

  const doctor = await res.json();
  doctorId = doctor.doctor_id || doctor.id;
  localStorage.setItem("doctorId", doctorId);

  alert(`Doctor registered! ID: ${doctorId}`);
  window.location.href = "dashboard.html";
});

// ==========================
// Login Doctor
// ==========================
document.getElementById("loginForm")?.addEventListener("submit", async (e) => {
  e.preventDefault();
  const email = document.getElementById("loginEmail").value;

  // Call your API to check doctor by email
  const res = await fetch(`${API_BASE}/doctors/by_email?email=${encodeURIComponent(email)}`);
  
  if (!res.ok) {
    alert("Doctor not found. Please register first.");
    return;
  }

  const doctor = await res.json();
  doctorId = doctor.doctor_id || doctor.id;
  localStorage.setItem("doctorId", doctorId);

  alert(`Welcome back, Dr. ${doctor.name}!`);
  window.location.href = "dashboard.html";
});

// ==========================
// Load dashboard
// ==========================
async function loadDashboard() {
  if (!doctorId) {
    alert("Please login first");
    window.location.href = "index.html";
    return;
  }

  const res = await fetch(`${API_BASE}/doctors/${doctorId}/dashboard`);
  if (!res.ok) {
    alert("Failed to load dashboard");
    return;
  }

  const data = await res.json();
  const tbody = document.querySelector("#couplesTable tbody");
  tbody.innerHTML = ""; // clear old rows

  // Calculate statistics
  let total = data.couples.length;
  let divorced = 0;
  let married = 0;
  let noPrediction = 0;

  data.couples.forEach(couple => {
    if (couple.last_class === 1) {
      divorced++;
    } else if (couple.last_class === 0) {
      married++;
    } else {
      noPrediction++;
    }
  });

  // Update statistics in the UI
  document.getElementById('totalCouples').textContent = total;
  document.getElementById('divorcedCouples').textContent = divorced;
  document.getElementById('marriedCouples').textContent = married;
  document.getElementById('noPrediction').textContent = noPrediction;

  data.couples.forEach((c) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${c.partner_a_name} & ${c.partner_b_name}</td>
      <td>${c.last_proba ? (c.last_proba * 100).toFixed(1) + "%" : "-"}</td>
      <td>${c.last_class === null ? "-" : c.last_class === 1 ? "Divorced" : "Married"}</td>
      <td>
        <a href="timeline.html?couple_id=${c.couple_id}" class="history-btn">View History</a>
      </td>
      <td>
        <button onclick="goToAssessment(${c.couple_id})">Create Assessment</button>
      </td>
    `;
    tbody.appendChild(row);
  });
}

// ==========================
// Go to assessment page
// ==========================
function goToAssessment(coupleId) {
  localStorage.setItem("currentCoupleId", coupleId);
  window.location.href = "assessment.html";
}

// ==========================
// Add couple
// ==========================
document.getElementById("coupleForm")?.addEventListener("submit", async (e) => {
  e.preventDefault();

  if (!doctorId) {
    alert("Please register/login as a doctor first!");
    return;
  }

  const data = {
    doctor_id: Number(doctorId),
    partner_a_name: document.getElementById("partnerA").value,
    partner_b_name: document.getElementById("partnerB").value,
  };

  const res = await fetch(`${API_BASE}/couples`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    const err = await res.json();
    alert("Error adding couple: " + JSON.stringify(err));
    return;
  }

  alert("Couple added successfully!");
  window.location.href = "dashboard.html";
});

// ==========================
// Create assessment
// ==========================
document.getElementById("assessmentForm")?.addEventListener("submit", async (e) => {
  e.preventDefault();
  const doctorId = localStorage.getItem("doctorId");  
  if (!doctorId) {
    alert("No doctor logged in");
    window.location.href = "index.html";
    return;
  }

  const data = {
    doctor_id: Number(doctorId),
    couple_id: Number(document.getElementById("coupleId").value),
    title: document.getElementById("title").value,
  };

  const res = await fetch(`${API_BASE}/assessments`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    const err = await res.json();
    alert("Error creating assessment: " + JSON.stringify(err));
    return;
  }

  const assessment = await res.json();
  alert("Assessment created with ID " + assessment.id);
  localStorage.setItem("assessmentId", assessment.id); 
  window.location.href = "assessment.html?id=" + assessment.id;
});

function goToAssessment(coupleId) {
  if (!doctorId) {
    alert("Please login first");
    window.location.href = "index.html";
    return;
  }
  localStorage.setItem("currentCoupleId", coupleId);
  window.location.href = "assessment.html";
}

// ==========================
// Add question + answer
// ==========================
document.getElementById("answerForm")?.addEventListener("submit", async (e) => {
  e.preventDefault();

  const assessmentId = Number(document.getElementById("assessmentId").value);
  const doctorId = Number(localStorage.getItem("doctorId"));

  // 1️⃣ Create question with doctor_id
  const questionRes = await fetch(`${API_BASE}/questions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      assessment_id: assessmentId,
      doctor_id: doctorId,
      text: document.getElementById("featureName").value
    }),
  });

  if (!questionRes.ok) {
    const err = await questionRes.json();
    alert("Error creating question: " + JSON.stringify(err));
    return;
  }

  const question = await questionRes.json();

  // 2️⃣ Add answer linked to that question
  const answerData = {
    items: [
      {
        question_id: question.id || question.question_id,
        text: document.getElementById("featureName").value,  // ✅ required by backend
        value: Number(document.getElementById("featureValue").value),
        partner: document.getElementById("partner").value
      }
    ]
  };

  const res = await fetch(`${API_BASE}/assessments/${assessmentId}/answers/bulk`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(answerData),
  });

  if (!res.ok) {
    const err = await res.json();
    alert("Error adding answer: " + JSON.stringify(err));
    return;
  }

  alert("Question + Answer added successfully!");
});

// ==========================
// Predict
// ==========================
document.getElementById("predictForm")?.addEventListener("submit", async (e) => {
  e.preventDefault();
  const id = Number(document.getElementById("predictId").value);

  const res = await fetch(`${API_BASE}/assessments/${id}/predict`, { method: "POST" });

  if (!res.ok) {
    const err = await res.json();
    alert("Prediction failed: " + JSON.stringify(err));
    return;
  }

  const result = await res.json();
  document.getElementById("predictResult").textContent = JSON.stringify(result, null, 2);
});
