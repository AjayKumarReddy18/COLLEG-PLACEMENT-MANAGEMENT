const user = JSON.parse(sessionStorage.getItem("currentUser") || "null");
const accessToken = sessionStorage.getItem("accessToken");

const API_BASE = "http://127.0.0.1:8000/api";

if (!user || !accessToken) {
    window.location.href = "index.html";
} else {
    initializeCompanyDashboard();
}

/* =========================
   COMMON API FUNCTION
========================= */

async function apiRequest(url, options = {}) {
    const response = await fetch(`${API_BASE}${url}`, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${accessToken}`,
            ...(options.headers || {})
        }
    });

    if (response.status === 401) {
        sessionStorage.clear();
        window.location.href = "index.html";
        return null;
    }

    const text = await response.text();

    if (!text) {
        return [];
    }

    try {
        return JSON.parse(text);
    } catch {
        return [];
    }
}

/* =========================
   INITIALIZE DASHBOARD
========================= */

async function initializeCompanyDashboard() {

    const fullName =
        `${user.first_name || ""} ${user.last_name || ""}`.trim();

    const greeting = document.querySelector("#user-greeting");

    if (greeting) {
        greeting.textContent =
            `Signed in as ${fullName || user.email}. Your workspace is ready.`;
    }

    const companyName = document.querySelector("#company-name-display");

    if (companyName) {
        companyName.textContent = fullName || user.email;
    }

    const avatar = document.querySelector("#company-avatar");

    if (avatar) {
        avatar.textContent =
            (fullName || user.email || "CO")
                .substring(0, 2)
                .toUpperCase();
    }

    setupNavigation();
    setupLogout();

    await loadCompanyData();
}

/* =========================
   NAVIGATION
========================= */

function setupNavigation() {

    document.querySelectorAll("[data-company-section]").forEach(button => {

        button.addEventListener("click", () => {

            const sectionId = button.dataset.companySection;

            document.querySelectorAll(".nav-item").forEach(item => {
                item.classList.remove("is-active");
            });

            if (button.classList.contains("nav-item")) {
                button.classList.add("is-active");
            }

            if (sectionId === "overview") {
                document.querySelector("#overview")?.scrollIntoView({
                    behavior: "smooth"
                });
                return;
            }

            const section = document.getElementById(sectionId);

            if (section) {
                section.scrollIntoView({
                    behavior: "smooth"
                });
            }
        });
    });
}

/* =========================
   LOGOUT
========================= */

function setupLogout() {

    document.querySelectorAll('[data-action="logout"]').forEach(button => {

        button.addEventListener("click", () => {
            sessionStorage.clear();
            window.location.href = "index.html";
        });

    });
}

/* =========================
   LOAD COMPANY DATA
========================= */

async function loadCompanyData() {

    try {

        const jobs = await apiRequest("/company/jobs/");

        const jobList = normalizeList(jobs);

        renderJobs(jobList);

        let allApplications = [];

        for (const job of jobList) {

            if (!job.id) {
                continue;
            }

            const applications =
                await apiRequest(`/company/jobs/${job.id}/applications/`);

            const applicationList = normalizeList(applications);

            allApplications.push(
                ...applicationList.map(application => ({
                    ...application,
                    job_id: job.id,
                    job_title:
                        application.job_title ||
                        job.job_title ||
                        "Job"
                }))
            );
        }

        renderApplications(allApplications);
        renderShortlisted(allApplications);
        await loadInterviewsAndOffers(allApplications);

        updateStatistics(jobList, allApplications);

    } catch (error) {

        console.error("Company dashboard error:", error);

        showEmptyState(
            "applicants-table-body",
            "Unable to load applications."
        );

    }
}

/* =========================
   NORMALIZE API RESPONSE
========================= */

function normalizeList(data) {

    if (Array.isArray(data)) {
        return data;
    }

    if (data && Array.isArray(data.results)) {
        return data.results;
    }

    if (data && Array.isArray(data.data)) {
        return data.data;
    }

    return [];
}

/* =========================
   MY JOBS
========================= */

function renderJobs(jobs) {

    const container =
        document.querySelector("#company-jobs-list");

    if (!container) {
        return;
    }

    if (!jobs.length) {
        container.innerHTML =
            `<p class="loading-state">No jobs found.</p>`;
        return;
    }

    container.innerHTML = jobs.map(job => `
        <div class="job-card">

            <h3>${escapeHtml(job.job_title || "Untitled Job")}</h3>

            <p>
                ${escapeHtml(job.job_location || "Location not specified")}
            </p>

            <p>
                Status:
                <strong>${escapeHtml(job.status || "Unknown")}</strong>
            </p>

            <p>
                Applications:
                ${normalizeList(job.applications).length}
            </p>

        </div>
    `).join("");
}

/* =========================
   APPLICATIONS
========================= */

function renderApplications(applications) {

    const tbody =
        document.querySelector("#applicants-table-body");

    if (!tbody) {
        return;
    }

    if (!applications.length) {

        tbody.innerHTML = `
            <tr>
                <td colspan="12">
                    No applications found.
                </td>
            </tr>
        `;

        return;
    }

    tbody.innerHTML = applications.map(application => {

        const student =
            application.student || {};

        return `
            <tr>

                <td>
                    ${escapeHtml(
                        student.name ||
                        student.full_name ||
                        application.student_name ||
                        "Student"
                    )}
                </td>

                <td>
                    ${escapeHtml(
                        student.email ||
                        application.student_email ||
                        "-"
                    )}
                </td>

                <td>
                    ${escapeHtml(
                        student.department ||
                        application.department ||
                        "-"
                    )}
                </td>

                <td>
                    ${escapeHtml(
                        student.course ||
                        application.course ||
                        "-"
                    )}
                </td>

                <td>
                    ${escapeHtml(
                        String(
                            student.year ||
                            application.year ||
                            "-"
                        )
                    )}
                </td>

                <td>
                    ${escapeHtml(
                        String(
                            student.cgpa ||
                            application.cgpa ||
                            "-"
                        )
                    )}
                </td>

                <td>
                    ${escapeHtml(
                        student.skills ||
                        application.skills ||
                        "-"
                    )}
                </td>

                <td>
                    ${escapeHtml(application.job_title || "-")}
                </td>

                <td>
                    ${formatDate(
                        application.applied_at
                    )}
                </td>

                <td>
                    ${
                        application.resume
                        ? `<a href="${application.resume}" target="_blank">View</a>`
                        : "-"
                    }
                </td>

                <td>
                    ${escapeHtml(
                        application.status || "APPLIED"
                    )}
                </td>

                <td>

                    ${
                        application.status === "APPLIED"
                        ? `
                            <button
                                class="primary-button"
                                onclick="updateApplicationStatus(${application.id}, 'SHORTLISTED')">
                                Shortlist
                            </button>
                        `
                        : ""
                    }

                    ${
                        application.status === "SHORTLISTED"
                        ? `
                            <button
                                class="secondary-button"
                                onclick="updateApplicationStatus(${application.id}, 'SELECTED')">
                                Select
                            </button>

                            <button
                                class="primary-button"
                                onclick="openInterviewModal(${application.id})">
                                Interview
                            </button>
                        `
                        : ""
                    }

                </td>

            </tr>
        `;

    }).join("");
}

/* =========================
   SHORTLISTED STUDENTS
========================= */

function renderShortlisted(applications) {

    const container =
        document.querySelector("#shortlisted-list");

    if (!container) {
        return;
    }

    const shortlisted =
        applications.filter(
            application =>
                application.status === "SHORTLISTED"
        );

    if (!shortlisted.length) {

        container.innerHTML =
            `<p class="loading-state">No shortlisted students.</p>`;

        return;
    }

    container.innerHTML = shortlisted.map(application => {

        const student =
            application.student || {};

        const name =
            student.name ||
            student.full_name ||
            application.student_name ||
            "Student";

        return `
            <div class="student-card">

                <h3>${escapeHtml(name)}</h3>

                <p>
                    Job:
                    ${escapeHtml(application.job_title || "-")}
                </p>

                <p>
                    Department:
                    ${escapeHtml(
                        student.department ||
                        application.department ||
                        "-"
                    )}
                </p>

                <p>
                    CGPA:
                    ${escapeHtml(
                        String(
                            student.cgpa ||
                            application.cgpa ||
                            "-"
                        )
                    )}
                </p>

                <button
                    class="primary-button"
                    onclick="openInterviewModal(${application.id})">
                    Schedule Interview
                </button>

            </div>
        `;

    }).join("");
}

/* =========================
   INTERVIEWS + OFFERS
========================= */

async function loadInterviewsAndOffers(applications) {

    const interviews = [];
    const offers = [];

    for (const application of applications) {

        if (!application.id) {
            continue;
        }

        const interviewData =
            await apiRequest(
                `/company/applications/${application.id}/interviews/`
            );

        normalizeList(interviewData).forEach(interview => {

            interviews.push({
                ...interview,
                application
            });

        });

        const offerData =
            await apiRequest(
                `/company/applications/${application.id}/offer/`
            );

        if (offerData && !Array.isArray(offerData)) {

            if (offerData.id || offerData.offer_letter_number) {

                offers.push({
                    ...offerData,
                    application
                });

            }
        }
    }

    renderInterviews(interviews);
    renderOffers(applications, offers);
}

/* =========================
   INTERVIEWS
========================= */

function renderInterviews(interviews) {

    const container =
        document.querySelector("#company-interview-list");

    if (!container) {
        return;
    }

    if (!interviews.length) {

        container.innerHTML =
            `<p class="loading-state">No interviews scheduled.</p>`;

        return;
    }

    container.innerHTML = interviews.map(item => {

        const application =
            item.application || {};

        const student =
            application.student || {};

        return `
            <div class="interview-card">

                <h3>
                    ${escapeHtml(
                        student.name ||
                        student.full_name ||
                        application.student_name ||
                        "Student"
                    )}
                </h3>

                <p>
                    Job:
                    ${escapeHtml(
                        application.job_title || "-"
                    )}
                </p>

                <p>
                    Round:
                    ${escapeHtml(
                        String(item.round || "-")
                    )}
                </p>

                <p>
                    Type:
                    ${escapeHtml(
                        item.interview_type || "-"
                    )}
                </p>

                <p>
                    Date:
                    ${formatDate(item.scheduled_at)}
                </p>

                <p>
                    Status:
                    ${escapeHtml(
                        item.status || "-"
                    )}
                </p>

            </div>
        `;

    }).join("");
}

/* =========================
   OFFERS
========================= */

function renderOffers(applications, offers) {

    const container =
        document.querySelector("#selected-list");

    if (!container) {
        return;
    }

    const selected =
        applications.filter(
            application =>
                application.status === "SELECTED"
        );

    if (!selected.length) {

        container.innerHTML =
            `<p class="loading-state">No selected students yet.</p>`;

        return;
    }

    container.innerHTML = selected.map(application => {

        const student =
            application.student || {};

        const offer =
            offers.find(
                item =>
                    item.application &&
                    item.application.id === application.id
            );

        return `
            <div class="selected-card">

                <h3>
                    ${escapeHtml(
                        student.name ||
                        student.full_name ||
                        application.student_name ||
                        "Student"
                    )}
                </h3>

                <p>
                    Job:
                    ${escapeHtml(
                        application.job_title || "-"
                    )}
                </p>

                <p>
                    Status:
                    SELECTED
                </p>

                ${
                    offer
                    ? `
                        <p>
                            Offer:
                            ${escapeHtml(
                                offer.offer_letter_number || "Issued"
                            )}
                        </p>

                        <p>
                            CTC:
                            ${escapeHtml(
                                String(offer.ctc || "-")
                            )}
                        </p>

                        <p>
                            Offer status:
                            ${escapeHtml(
                                offer.status || "-"
                            )}
                        </p>
                    `
                    : `
                        <button
                            class="primary-button"
                            onclick="createOffer(${application.id})">
                            Create Offer
                        </button>
                    `
                }

            </div>
        `;

    }).join("");
}

/* =========================
   SHORTLIST / SELECT
========================= */

async function updateApplicationStatus(applicationId, status) {

    try {

        const result =
            await apiRequest(
                `/company/applications/${applicationId}/status/`,
                {
                    method: "PATCH",
                    body: JSON.stringify({ status })
                }
            );

        if (result) {

            alert(
                status === "SHORTLISTED"
                    ? "Student shortlisted successfully."
                    : "Student selected successfully."
            );

            await loadCompanyData();
        }

    } catch (error) {

        console.error(error);
        alert("Unable to update application status.");

    }
}

/* =========================
   INTERVIEW MODAL
========================= */

let selectedApplicationId = null;

function openInterviewModal(applicationId) {

    selectedApplicationId = applicationId;

    const modal =
        document.querySelector("#company-schedule-modal");

    if (modal) {

        modal.setAttribute("aria-hidden", "false");
        modal.classList.add("is-open");

    }
}

document.addEventListener("DOMContentLoaded", () => {

    const closeButton =
        document.querySelector("#schedule-modal-close");

    if (closeButton) {

        closeButton.addEventListener("click", closeInterviewModal);

    }

    const form =
        document.querySelector("#schedule-interview-form");

    if (form) {

        form.addEventListener(
            "submit",
            scheduleInterview
        );

    }

});

/* =========================
   SCHEDULE INTERVIEW
========================= */

async function scheduleInterview(event) {

    event.preventDefault();

    if (!selectedApplicationId) {
        alert("Please select a student first.");
        return;
    }

    const form =
        event.target;

    const date =
        form.querySelector("#interview-date").value;

    const time =
        form.querySelector("#interview-time").value;

    const scheduledAt =
        `${date}T${time}:00`;

    const data = {

        round: Number(
            form.querySelector("#interview-round").value
        ),

        interview_type:
            form.querySelector("#interview-type").value,

        scheduled_at:
            scheduledAt,

        meeting_link:
            form.querySelector("#interview-link").value || "",

        venue:
            form.querySelector("#interview-venue")?.value || "",

        interviewer:
            form.querySelector("#interviewer")?.value || ""

    };
    try {

        const result =
            await apiRequest(
                `/company/applications/${selectedApplicationId}/interviews/`,
                {
                    method: "POST",
                    body: JSON.stringify(data)
                }
            );

        if (result) {

            alert("Interview scheduled successfully.");

            closeInterviewModal();

            await loadCompanyData();

        }

    } catch (error) {

        console.error(error);

        alert("Unable to schedule interview.");

    }
}

function closeInterviewModal() {

    const modal =
        document.querySelector("#company-schedule-modal");

    if (modal) {

        modal.setAttribute("aria-hidden", "true");
        modal.classList.remove("is-open");

    }

    selectedApplicationId = null;
}

/* =========================
   CREATE OFFER
========================= */

async function createOffer(applicationId) {

    const offerLetterNumber =
        prompt("Enter offer letter number:");

    if (!offerLetterNumber) {
        return;
    }

    const ctc =
        prompt("Enter CTC:");

    if (!ctc) {
        return;
    }

    const joiningDate =
        prompt("Enter joining date (YYYY-MM-DD):");

    if (!joiningDate) {
        return;
    }

    try {

        const result =
            await apiRequest(
                `/company/applications/${applicationId}/offer/`,
                {
                    method: "POST",
                    body: JSON.stringify({
                        offer_letter_number:
                            offerLetterNumber,

                        ctc: ctc,

                        joining_date:
                            joiningDate,

                        offer_details:
                            "Offer issued through College Placement Management System."
                    })
                }
            );

        if (result) {

            alert("Offer created successfully.");

            await loadCompanyData();

        }

    } catch (error) {

        console.error(error);

        alert("Unable to create offer.");

    }
}

/* =========================
   STATISTICS
========================= */

function updateStatistics(jobs, applications) {

    const activeJobs =
        jobs.filter(
            job =>
                job.status === "APPROVED" ||
                job.status === "PUBLISHED"
        ).length;

    const applicants =
        applications.length;

    const shortlisted =
        applications.filter(
            item => item.status === "SHORTLISTED"
        ).length;

    const selected =
        applications.filter(
            item => item.status === "SELECTED"
        ).length;

    const activeJobsElement =
        document.querySelector("#stat-active-jobs");

    const applicantsElement =
        document.querySelector("#stat-total-applicants");

    const shortlistedElement =
        document.querySelector("#stat-shortlisted-count");

    const selectedElement =
        document.querySelector("#stat-selected-count");

    if (activeJobsElement) {
        activeJobsElement.textContent = activeJobs;
    }

    if (applicantsElement) {
        applicantsElement.textContent = applicants;
    }

    if (shortlistedElement) {
        shortlistedElement.textContent = shortlisted;
    }

    if (selectedElement) {
        selectedElement.textContent = selected;
    }
}

/* =========================
   HELPERS
========================= */

function formatDate(value) {

    if (!value) {
        return "-";
    }

    const date =
        new Date(value);

    if (Number.isNaN(date.getTime())) {
        return value;
    }

    return date.toLocaleString();
}

function escapeHtml(value) {

    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function showEmptyState(id, message) {

    const element =
        document.getElementById(id);

    if (element) {
        element.innerHTML =
            `<p class="loading-state">${escapeHtml(message)}</p>`;
    }
}