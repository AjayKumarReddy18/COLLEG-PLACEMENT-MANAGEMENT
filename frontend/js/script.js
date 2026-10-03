const API_BASE_URL = "http://127.0.0.1:8000/api";

function isValidEmailAddress(value) {
    const email = value.trim();
    const parts = email.split("@");

    if (parts.length !== 2 || email.includes("..")) return false;

    const [localPart, domain] = parts;
    const emailPattern = /^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)+$/;

    return !localPart.startsWith(".") && !localPart.endsWith(".") && emailPattern.test(email);
}

function setStatusMessage(element, message, type = "info") {
    if (!element) return;

    element.textContent = message || "";
    element.style.display = message ? "block" : "none";
    element.classList.remove("success", "error");

    if (type === "success") {
        element.classList.add("success");
    }

    if (type === "error") {
        element.classList.add("error");
    }
}

function getErrorMessage(errorData, fallback = "Request failed.") {
    if (!errorData) return fallback;
    if (typeof errorData === "string") return errorData;
    if (errorData.detail) return errorData.detail;
    if (errorData.message) return errorData.message;

    for (const key of Object.keys(errorData)) {
        const value = errorData[key];

        if (Array.isArray(value) && value.length) return String(value[0]);
        if (typeof value === "string" && value.trim()) return value;
        if (typeof value === "object" && value) {
            const nested = getErrorMessage(value, "");
            if (nested) return nested;
        }
    }

    return fallback;
}

function normalizeApiList(payload) {
    if (Array.isArray(payload)) return payload;
    if (!payload || typeof payload !== "object") return [];

    for (const key of ["results", "data", "items"]) {
        if (Array.isArray(payload[key])) return payload[key];
    }

    return [];
}

function setText(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = value ?? "-";
    }
}

function showToast(message, isError = false) {
    const toast = document.getElementById("toast");
    if (!toast) return;

    toast.textContent = message;
    toast.classList.toggle("show", true);
    toast.style.background = isError ? "#b91c1c" : "#0f172a";

    clearTimeout(showToast.timeoutId);
    showToast.timeoutId = setTimeout(function () {
        toast.classList.toggle("show", false);
    }, 2600);
}

function logoutUser() {
    localStorage.removeItem("access");
    localStorage.removeItem("refresh");
    localStorage.removeItem("currentUser");
    localStorage.removeItem("loggedInUser");
    localStorage.removeItem("userRole");
    sessionStorage.clear();
    window.location.href = "index.html";
}

function renderStudentProfile(profile) {
    const firstName = profile?.first_name || "";
    const lastName = profile?.last_name || "";
    const fullName = `${firstName} ${lastName}`.trim() || profile?.user_email || "Student";

    setText("student-name-display", fullName);
    setText("student-course-display", profile.course || "-");
    setText("profile-name", fullName);
    setText("profile-student-id", profile.student_id || "-");
    setText("profile-email", profile.user_email || "-");
    setText("profile-phone", profile.phone_number || "-");
    setText("profile-department", profile.department || "-");
    setText("profile-course", profile.course || "-");
    setText("profile-year", profile.year ?? "-");
    setText("profile-cgpa", profile.cgpa ?? "-");
    setText("profile-skills", profile.skills || "-");
    setText("profile-resume-status", profile.resume ? "Uploaded" : "Not Uploaded");

    const avatar = document.getElementById("student-avatar");
    if (avatar) {
        const initials = fullName.split(/\s+/).filter(Boolean).map((word) => word.charAt(0)).join("").toUpperCase();
        avatar.textContent = initials || "ST";
    }
}

function renderDashboardStats(stats) {
    const safeStats = {
        available_jobs: 0,
        applied_jobs: 0,
        shortlisted: 0,
        interviews: 0,
        placement_status: "Not available",
        ...stats,
    };

    setText("stat-jobs", safeStats.available_jobs ?? 0);
    setText("stat-applied", safeStats.applied_jobs ?? 0);
    setText("stat-shortlisted", safeStats.shortlisted ?? 0);
    setText("stat-interviews", safeStats.interviews ?? 0);

    const placementStatus = document.getElementById("stat-placement");
    const placementMeta = document.getElementById("stat-placement-meta");

    if (placementStatus) {
        placementStatus.textContent = safeStats.placement_status || "Not available";
    }
    setText("profile-student-status", safeStats.placement_status || "Not available");

    if (placementMeta) {
        placementMeta.textContent = safeStats.placement_status === "Placed"
            ? "Offer accepted and placement confirmed"
            : safeStats.placement_status === "Selected"
                ? "Selected for final recruitment stage"
                : safeStats.placement_status === "Eligible"
                    ? "Currently eligible for placements"
                    : safeStats.placement_status === "Not Eligible"
                        ? "Below current placement eligibility"
                        : "Placement status not available";
    }
}

async function refreshAccessToken() {
    const refreshToken = localStorage.getItem("refresh");
    if (!refreshToken) return null;

    try {
        const response = await fetch(`${API_BASE_URL}/auth/token/refresh/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ refresh: refreshToken }),
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok || !data.access) return null;

        localStorage.setItem("access", data.access);
        if (data.refresh) localStorage.setItem("refresh", data.refresh);
        return data.access;
    } catch (error) {
        console.error("Session refresh failed:", error);
        return null;
    }
}

async function fetchAuthenticatedJson(path, token, options = {}, hasRetried = false) {
    const response = await fetch(`${API_BASE_URL}${path}`, {
        ...options,
        headers: {
            Authorization: `Bearer ${token}`,
            ...(options.body && !(typeof FormData !== "undefined" && options.body instanceof FormData)
                ? { "Content-Type": "application/json" }
                : {}),
            ...options.headers,
        },
    });
    const data = await response.json().catch(() => ({}));

    if (response.status === 401 && !hasRetried) {
        const refreshedToken = await refreshAccessToken();
        if (refreshedToken) {
            return fetchAuthenticatedJson(path, refreshedToken, options, true);
        }
        logoutUser();
        throw new Error("Your session has expired. Please sign in again.");
    }

    if (!response.ok) {
        const fallback = response.status === 401
            ? "Your session has expired. Please sign in again."
            : response.status === 403
                ? "You do not have permission to access this information."
                : response.status === 404
                    ? "The requested information was not found."
                    : response.status >= 500
                        ? "The server could not complete the request."
                        : "Unable to complete the request.";
        const error = new Error(getErrorMessage(data, fallback));
        error.status = response.status;
        throw error;
    }

    return data;
}

function renderStudentJobs(jobs, token) {
    const jobList = document.getElementById("job-list");
    if (!jobList) return;

    jobList.replaceChildren();
    if (!jobs.length) {
        const empty = document.createElement("p");
        empty.className = "empty-state";
        empty.textContent = "No approved jobs are currently available.";
        jobList.appendChild(empty);
        return;
    }

    jobs.forEach((job) => {
        const card = document.createElement("article");
        card.className = "job-card";
        const company = document.createElement("span");
        company.className = "company-tag";
        company.textContent = job.company_name || "Company";

        const title = document.createElement("h3");
        title.textContent = job.job_title || "Untitled position";
        const description = document.createElement("p");
        description.textContent = job.description || "";

        const metadata = document.createElement("div");
        metadata.className = "job-meta";
            const jobDetails = [
                `Location: ${job.job_location || "Not specified"}`,
                `Type: ${(job.job_type || "Not specified").replace(/_/g, " ")}`,
                `Package: ${job.salary || "Not specified"}`,
                `Minimum CGPA: ${job.minimum_cgpa ?? "Not specified"}`,
                `Deadline: ${job.application_deadline ? new Date(job.application_deadline).toLocaleDateString() : "Not specified"}`,
                `Posted: ${job.created_at ? new Date(job.created_at).toLocaleDateString() : "Not specified"}`,
            ];
            jobDetails.forEach((value) => {
            const line = document.createElement("p");
            line.textContent = value;
            metadata.appendChild(line);
        });

        const action = document.createElement("button");
        action.type = "button";
        action.className = job.has_applied ? "secondary-button" : "primary-button";
        action.textContent = job.has_applied ? "Applied" : job.is_eligible ? "Apply" : "Not eligible";
        action.disabled = job.has_applied || !job.is_eligible;
        action.addEventListener("click", async function () {
            action.disabled = true;
            action.textContent = "Applying...";
            try {
                await fetchAuthenticatedJson(`/student/jobs/${job.id}/apply/`, token, { method: "POST" });
                showToast("Application submitted successfully.");
                await loadStudentPlacementData();
            } catch (error) {
                console.error("Job application failed:", error);
                action.disabled = false;
                action.textContent = "Apply";
                showToast(error.message || "Unable to apply for this job.", true);
            }
        });

        if (!job.is_eligible && Array.isArray(job.eligibility_reasons) && job.eligibility_reasons.length) {
            const reason = document.createElement("p");
            reason.className = "form-status is-error";
            reason.textContent = job.eligibility_reasons.join(" ");
            card.append(company, title, description, metadata, reason, action);
        } else {
            card.append(company, title, description, metadata, action);
        }
        jobList.appendChild(card);
    });
}

function renderStudentApplications(applications, interviews) {
    const tableBody = document.getElementById("applications-table-body");
    if (!tableBody) return;

    tableBody.replaceChildren();
    if (!applications.length) {
        const row = document.createElement("tr");
        const cell = document.createElement("td");
        cell.colSpan = 5;
        cell.className = "empty-state";
        cell.textContent = "You have not applied to any jobs yet.";
        row.appendChild(cell);
        tableBody.appendChild(row);
        return;
    }

    applications.forEach((application) => {
        const interview = interviews.find((item) => item.application_id === application.id);
        const row = document.createElement("tr");
        [
            application.company_name || "-",
            application.job_title || "-",
            application.applied_at ? new Date(application.applied_at).toLocaleDateString() : "-",
            (application.status || "-").replace(/_/g, " "),
            interview ? `Round ${interview.round}: ${new Date(interview.scheduled_at).toLocaleString()}` : "-",
        ].forEach((value) => {
            const cell = document.createElement("td");
            cell.textContent = value;
            row.appendChild(cell);
        });
        tableBody.appendChild(row);
    });
}

function renderStudentInterviews(interviews) {
    const interviewList = document.getElementById("interview-list");
    if (!interviewList) return;

    interviewList.replaceChildren();
    if (!interviews.length) {
        const empty = document.createElement("p");
        empty.className = "empty-state";
        empty.textContent = "No interviews have been scheduled.";
        interviewList.appendChild(empty);
        return;
    }

    interviews.forEach((interview) => {
        const item = document.createElement("article");
        item.className = "offer-card";
        const title = document.createElement("h3");
        title.textContent = `${interview.company_name || "Company"} · ${interview.job_title || "Position"}`;
        const details = document.createElement("p");
        const venue = interview.interview_type === "ONLINE"
            ? interview.meeting_link || "Meeting link unavailable"
            : interview.venue || "Venue unavailable";
        details.textContent = `Round ${interview.round} · ${new Date(interview.scheduled_at).toLocaleString()} · ${interview.interview_type} · ${venue} · Interviewer: ${interview.interviewer || "Not specified"} · ${interview.status}`;
        item.append(title, details);
        interviewList.appendChild(item);
    });
}

function renderStudentOffers(offers, token) {
    const offerList = document.getElementById("offer-list");
    if (!offerList) return;

    offerList.replaceChildren();
    if (!offers.length) {
        const empty = document.createElement("p");
        empty.className = "empty-state";
        empty.textContent = "No offers have been received.";
        offerList.appendChild(empty);
        return;
    }

    offers.forEach((offer) => {
        const card = document.createElement("article");
        card.className = "offer-card";
        const title = document.createElement("h3");
        title.textContent = `${offer.company_name || "Company"} · ${offer.job_title || "Position"}`;
        const details = document.createElement("p");
        details.textContent = `Offer ${offer.offer_letter_number} · CTC ${offer.ctc} · Joining ${offer.joining_date} · Status ${offer.status} · ${offer.offer_details || ""}`;
        card.append(title, details);

        if (offer.status === "PENDING") {
            ["ACCEPTED", "REJECTED"].forEach((status) => {
                const button = document.createElement("button");
                button.type = "button";
                button.className = status === "ACCEPTED" ? "primary-button" : "secondary-button";
                button.textContent = status === "ACCEPTED" ? "Accept offer" : "Decline offer";
                button.addEventListener("click", async function () {
                    button.disabled = true;
                    try {
                        await fetchAuthenticatedJson(`/student/offers/${offer.id}/respond/`, token, {
                            method: "PATCH",
                            body: JSON.stringify({ status }),
                        });
                        await loadStudentPlacementData();
                    } catch (error) {
                        console.error("Offer response failed:", error);
                        button.disabled = false;
                        showToast(error.message || "Unable to update offer.", true);
                    }
                });
                card.appendChild(button);
            });
        }

        offerList.appendChild(card);
    });
}

function renderStudentCompanies(companies) {
    const list = document.getElementById("student-company-list");
    if (!list) return;

    list.replaceChildren();
    if (!companies.length) {
        const empty = document.createElement("p");
        empty.className = "empty-state";
        empty.textContent = "No approved companies are available yet.";
        list.appendChild(empty);
        return;
    }

    companies.forEach((company) => {
        const card = document.createElement("article");
        card.className = "job-card";
        const name = document.createElement("h3");
        name.textContent = company.company_name || "Company";
        const industry = document.createElement("p");
        industry.textContent = company.industry || "Industry not provided";
        const location = document.createElement("p");
        location.textContent = company.location || "Location not provided";
        const description = document.createElement("p");
        description.textContent = company.company_description || "No company description provided.";
        const jobs = document.createElement("p");
        jobs.textContent = `${company.available_jobs ?? 0} active job${company.available_jobs === 1 ? "" : "s"}`;
        card.append(name, industry, location, description, jobs);

        if (company.website) {
            const website = document.createElement("a");
            website.href = company.website;
            website.target = "_blank";
            website.rel = "noopener noreferrer";
            website.textContent = "Company website";
            card.appendChild(website);
        }
        list.appendChild(card);
    });
}

async function loadStudentPlacementData() {
    const jobList = document.getElementById("job-list");
    if (!jobList) return;

    const token = localStorage.getItem("access");
    if (!token) {
        window.location.href = "index.html";
        return;
    }

    try {
        const [jobsResponse, applicationsResponse, interviewsResponse, offersResponse, companiesResponse] = await Promise.all([
            fetchAuthenticatedJson("/student/jobs/", token),
            fetchAuthenticatedJson("/student/applications/", token),
            fetchAuthenticatedJson("/student/interviews/", token),
            fetchAuthenticatedJson("/student/offers/", token),
            fetchAuthenticatedJson("/student/companies/", token),
        ]);
        const jobs = normalizeApiList(jobsResponse);
        const applications = normalizeApiList(applicationsResponse);
        const interviews = normalizeApiList(interviewsResponse);
        const offers = normalizeApiList(offersResponse);
        const companies = normalizeApiList(companiesResponse);
        renderStudentJobs(jobs, token);
        renderStudentCompanies(companies);
        renderStudentApplications(applications, interviews);
        renderStudentInterviews(interviews);
        renderStudentOffers(offers, token);
        await loadNotificationBadge("student-notification-badge");
    } catch (error) {
        console.error("Student placement data load failed:", error);
        const message = error.message || "Unable to load placement information.";
        ["job-list", "student-company-list", "interview-list", "offer-list"].forEach((id) => {
            const element = document.getElementById(id);
            if (element) element.textContent = message;
        });
        const applicationsBody = document.getElementById("applications-table-body");
        if (applicationsBody) {
            const row = document.createElement("tr");
            const cell = document.createElement("td");
            cell.colSpan = 5;
            cell.className = "error-state";
            cell.textContent = message;
            row.appendChild(cell);
            applicationsBody.replaceChildren(row);
        }
    }
}

async function loadStudentDashboard() {
    const studentAvatar = document.getElementById("student-avatar");
    const profileName = document.getElementById("profile-name");
    const statJobs = document.getElementById("stat-jobs");

    if (!studentAvatar && !profileName && !statJobs) {
        return;
    }

    const token = localStorage.getItem("access");
    if (!token) {
        window.location.href = "index.html";
        return;
    }

    try {
        const [profile, stats] = await Promise.all([
            fetchAuthenticatedJson("/student/profile/", token),
            fetchAuthenticatedJson("/student/dashboard-stats/", token),
        ]);
        renderStudentProfile(profile || {});
        renderDashboardStats(stats || {});
    } catch (error) {
        console.error("Student dashboard load error:", error);
        setStudentStatsError("Unable to load placement statistics.");
    }
}

function setStudentStatsError(message) {
    ["stat-jobs", "stat-applied", "stat-shortlisted", "stat-interviews", "stat-placement"].forEach((id) => {
        setText(id, "Unavailable");
    });
    setText("stat-placement-meta", message);
    setText("profile-student-status", "Unavailable");
}

function setCompanyFeedback(elementId, message, type = "info") {
    const element = document.getElementById(elementId);
    if (!element) return;

    element.textContent = message || "";
    element.classList.toggle("is-error", type === "error");
    element.classList.toggle("is-success", type === "success");
}

function setCompanyModalOpen(modalId, isOpen) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    modal.classList.toggle("is-open", isOpen);
    modal.setAttribute("aria-hidden", String(!isOpen));
}

function openCompanyInterviewModal(applicationId) {
    const form = document.getElementById("schedule-interview-form");
    if (!form) return;
    form.dataset.applicationId = applicationId;
    form.reset();
    setCompanyModalOpen("company-schedule-modal", true);
}

function openCompanyOfferModal(applicationId) {
    const form = document.getElementById("company-offer-form");
    if (!form) return;
    form.dataset.applicationId = applicationId;
    form.reset();
    setCompanyModalOpen("company-offer-modal", true);
}

function renderCompanyProfile(profile) {
    const companyName = profile.company_name || "";
    setText("company-name-display", companyName);
    setText("company-verification-status", profile.verification_status || "Not available");
    setCompanyFeedback("company-verification-remarks", profile.verification_remarks || "");

    const avatar = document.getElementById("company-avatar");
    if (avatar) {
        avatar.textContent = companyName
            .split(/\s+/)
            .filter(Boolean)
            .slice(0, 2)
            .map((word) => word.charAt(0))
            .join("")
            .toUpperCase() || "CO";
    }

    const profileFields = {
        "company-profile-name": profile.company_name,
        "company-profile-industry": profile.industry,
        "company-profile-location": profile.location,
        "company-profile-email": profile.contact_email,
        "company-profile-phone": profile.contact_phone,
        "company-profile-size": profile.company_size,
        "company-profile-description": profile.company_description,
        "company-profile-website": profile.website,
    };

    Object.entries(profileFields).forEach(([id, value]) => {
        const field = document.getElementById(id);
        if (field) field.value = value || "";
    });

    setCompanyFeedback("company-profile-load-status", "");
}

function renderCompanyJobs(jobs, companyName) {
    const jobsList = document.getElementById("company-jobs-list");
    if (!jobsList) return;

    jobsList.replaceChildren();
    if (!jobs.length) {
        const emptyMessage = document.createElement("p");
        emptyMessage.className = "empty-state";
        emptyMessage.textContent = "No jobs have been posted yet.";
        jobsList.appendChild(emptyMessage);
    }

    jobs.forEach((job) => {
        const card = document.createElement("article");
        card.className = "job-card";

        const companyTag = document.createElement("span");
        companyTag.className = "company-tag";
        companyTag.textContent = job.company_name || companyName;

        const title = document.createElement("h3");
        title.textContent = job.job_title || "Untitled position";

        const description = document.createElement("p");
        description.textContent = job.description || "";

        const details = document.createElement("div");
        details.className = "job-meta";
            const jobDetails = [
                `Location: ${job.job_location || "Not specified"}`,
                `Status: ${(job.status || "Not available").replace(/_/g, " ")}`,
                `Salary: ${job.salary || "Not specified"}`,
                `Posted: ${job.created_at ? new Date(job.created_at).toLocaleDateString() : "Not specified"}`,
            ];
            jobDetails.forEach((text) => {
            const detail = document.createElement("p");
            detail.textContent = text;
            details.appendChild(detail);
        });

            const actions = document.createElement("div");
            actions.className = "form-actions";
            actions.appendChild(createTpoButton("Edit job", () => openCompanyJobEditor(job)));
            if (job.status === "APPROVED") {
                actions.appendChild(createTpoButton("Close job", async () => {
                    if (!window.confirm(`Close ${job.job_title}? Students will no longer be able to apply.`)) return;
                    try {
                        await fetchAuthenticatedJson(`/company/jobs/${job.id}/`, localStorage.getItem("access"), {
                            method: "PATCH",
                            body: JSON.stringify({ status: "CLOSED" }),
                        });
                        await loadCompanyDashboard();
                        showToast("Job closed successfully.");
                    } catch (error) {
                        showToast(error.message || "Unable to close this job.", true);
                    }
                }));
            }
            card.append(companyTag, title, description, details, actions);
        jobsList.appendChild(card);
    });
}

    function openCompanyJobEditor(job) {
        const form = document.getElementById("job-form");
        if (!form) return;

        form.dataset.jobId = String(job.id);
        form.querySelector('[name="jobTitle"]').value = job.job_title || "";
        form.querySelector('[name="jobLocation"]').value = job.job_location || "";
        form.querySelector('[name="jobPackage"]').value = job.salary ?? "";
        form.querySelector('[name="employmentType"]').value = job.job_type || "FULL_TIME";
        form.querySelector('[name="jobStatus"]').value = job.status === "DRAFT" ? "DRAFT" : "PENDING_TPO_APPROVAL";
        form.querySelector('[name="jobDescription"]').value = job.description || "";
        form.querySelector('[name="minCgpa"]').value = job.minimum_cgpa ?? "0.00";
        form.querySelector('[name="eligibleDepartments"]').value = Array.isArray(job.eligible_departments)
            ? job.eligible_departments.join(", ")
            : "";
        form.querySelector('[name="eligibleCourses"]').value = Array.isArray(job.eligible_courses)
            ? job.eligible_courses.join(", ")
            : "";
        form.querySelector('[name="applicationDeadline"]').value = job.application_deadline
            ? new Date(job.application_deadline).toISOString().slice(0, 10)
            : "";

        const submitButton = document.getElementById("job-submit-button");
        if (submitButton) submitButton.textContent = "Save Changes";
        setCompanyFeedback("job-form-status", "Editing this job will send approved listings back for TPO review.");
        document.querySelector('[data-company-section="post-job-section"]')?.click();
    }

function renderCompanyApplicants(applications, offersByApplication) {
    const tableBody = document.getElementById("applicants-table-body");
    if (!tableBody) return;

    tableBody.replaceChildren();
    if (!applications.length) {
        const row = document.createElement("tr");
        const cell = document.createElement("td");
        cell.colSpan = 12;
        cell.className = "empty-state";
        cell.textContent = "No applications have been received yet.";
        row.appendChild(cell);
        tableBody.appendChild(row);
        return;
    }

    applications.forEach((application) => {
        const row = document.createElement("tr");
        [
            `${application.student_name || "Student"} (${application.student_id || "-"})`,
            application.email || "-",
            application.department || "-",
            application.course || "-",
            application.year ?? "-",
            application.cgpa ?? "-",
            application.skills || "-",
            application.job_title || "-",
            application.applied_at ? new Date(application.applied_at).toLocaleDateString() : "-",
        ].forEach((value) => {
            const cell = document.createElement("td");
            cell.textContent = value;
            row.appendChild(cell);
        });

        const resumeCell = document.createElement("td");
        if (application.resume) {
            const resumeLink = document.createElement("a");
            resumeLink.href = new URL(application.resume, API_BASE_URL).href;
            resumeLink.target = "_blank";
            resumeLink.rel = "noopener noreferrer";
            resumeLink.textContent = "View resume";
            resumeCell.appendChild(resumeLink);
        } else {
            resumeCell.textContent = "-";
        }
        row.appendChild(resumeCell);

        const statusCell = document.createElement("td");
        statusCell.textContent = (application.status || "-").replace(/_/g, " ");
        row.appendChild(statusCell);

        const actionsCell = document.createElement("td");
        const addAction = (label, action, value) => {
            const button = document.createElement("button");
            button.type = "button";
            button.className = "secondary-button small";
            button.textContent = label;
            button.addEventListener("click", async function () {
                button.disabled = true;
                try {
                    if (action === "status") {
                        await fetchAuthenticatedJson(`/company/applications/${application.id}/status/`, localStorage.getItem("access"), {
                            method: "PATCH",
                            body: JSON.stringify({ status: value }),
                        });
                        await loadCompanyDashboard();
                    } else if (action === "interview") {
                        openCompanyInterviewModal(application.id);
                    } else if (action === "offer") {
                        openCompanyOfferModal(application.id);
                    }
                } catch (error) {
                    console.error("Company applicant action failed:", error);
                    button.disabled = false;
                    showToast(error.message || "Unable to update applicant.", true);
                }
            });
            actionsCell.appendChild(button);
        };

        if (application.status === "APPLIED") {
            addAction("Shortlist", "status", "SHORTLISTED");
            addAction("Reject", "status", "REJECTED");
        } else if (application.status === "SHORTLISTED") {
            addAction("Select", "status", "SELECTED");
            addAction("Reject", "status", "REJECTED");
            addAction("Schedule interview", "interview");
        } else if (application.status === "SELECTED") {
            if (offersByApplication.has(application.id)) {
                const offer = offersByApplication.get(application.id);
                const offerStatus = document.createElement("span");
                offerStatus.textContent = `Offer: ${offer.offer_letter_number} (${offer.status})`;
                actionsCell.appendChild(offerStatus);
            } else {
                addAction("Issue offer", "offer");
            }
        }
        row.appendChild(actionsCell);
        tableBody.appendChild(row);
    });
}

function renderCompanyApplicationList(elementId, applications, emptyMessage, offersByApplication = new Map()) {
    const list = document.getElementById(elementId);
    if (!list) return;

    list.replaceChildren();
    if (!applications.length) {
        const empty = document.createElement("p");
        empty.className = "empty-state";
        empty.textContent = emptyMessage;
        list.appendChild(empty);
        return;
    }

    applications.forEach((application) => {
        const item = document.createElement("article");
        item.className = "job-card";
        const name = document.createElement("h3");
        name.textContent = application.student_name || application.student_id || "Student";
        const details = document.createElement("p");
        details.textContent = `${application.job_title || "Position"} · ${application.student_id || ""}`;
        item.append(name, details);
        const offer = offersByApplication.get(application.id);
        if (offer) {
            const offerDetails = document.createElement("p");
            offerDetails.textContent = `Offer ${offer.offer_letter_number} · CTC ${offer.ctc} · Joining ${offer.joining_date} · ${offer.status}`;
            item.appendChild(offerDetails);
        }
        list.appendChild(item);
    });
}

function renderCompanyInterviews(interviews) {
    const list = document.getElementById("company-interview-list");
    if (!list) return;

    list.replaceChildren();
    if (!interviews.length) {
        const empty = document.createElement("p");
        empty.className = "empty-state";
        empty.textContent = "No interviews have been scheduled.";
        list.appendChild(empty);
        return;
    }

    interviews.forEach((interview) => {
        const item = document.createElement("article");
        item.className = "job-card";
        const title = document.createElement("h3");
        title.textContent = interview.student_name || interview.student_id || "Student";
        const detail = document.createElement("p");
        const scheduledAt = interview.scheduled_at
            ? new Date(interview.scheduled_at).toLocaleString()
            : "Time not specified";
        const location = interview.interview_type === "ONLINE"
            ? interview.meeting_link || "Meeting link unavailable"
            : interview.venue || "Venue unavailable";
        detail.textContent = `${interview.job_title || "Position"} · Round ${interview.round} · ${scheduledAt} · ${interview.interview_type} · ${location} · Interviewer: ${interview.interviewer || "Not specified"} · ${interview.status}`;
        item.append(title, detail);
        if (interview.status === "SCHEDULED") {
            const actions = document.createElement("div");
            actions.className = "form-actions";
            [["Mark complete", "COMPLETED"], ["Cancel interview", "CANCELLED"]].forEach(([label, status]) => {
                actions.appendChild(createTpoButton(label, async () => {
                    if (status === "CANCELLED" && !window.confirm("Cancel this interview?")) return;
                    try {
                        await fetchAuthenticatedJson(`/company/interviews/${interview.id}/`, localStorage.getItem("access"), {
                            method: "PATCH",
                            body: JSON.stringify({ status }),
                        });
                        await loadCompanyDashboard();
                    } catch (error) {
                        showToast(error.message || "Unable to update interview.", true);
                    }
                }));
            });
            item.appendChild(actions);
        }
        list.appendChild(item);
    });
}

async function loadCompanyDashboard() {
    const companyNameDisplay = document.getElementById("company-name-display");
    if (!companyNameDisplay) return;

    const token = localStorage.getItem("access");
    if (!token) {
        window.location.href = "index.html";
        return;
    }

    let profileData;
    try {
        profileData = await fetchAuthenticatedJson("/company/profile/", token);
        renderCompanyProfile(profileData);
    } catch (error) {
        console.error("Company profile load failed:", error);
        setText("company-name-display", "Unable to load company details.");
        setCompanyFeedback("company-profile-load-status", "Unable to load company details.", "error");
        setText("company-verification-status", "Unavailable");
        return;
    }

    try {
        const jobsData = normalizeApiList(await fetchAuthenticatedJson("/company/jobs/", token));

        renderCompanyJobs(jobsData, profileData.company_name);
        setText("stat-active-jobs", jobsData.filter((job) => (
            job.status === "APPROVED" && Date.parse(job.application_deadline) > Date.now()
        )).length);

        const applicationGroups = await Promise.all(jobsData.map(async (job) => {
            const data = await fetchAuthenticatedJson(`/company/jobs/${job.id}/applications/`, token);
            return normalizeApiList(data).map((application) => ({
                ...application,
                job_id: job.id,
                job_title: job.job_title,
            }));
        }));
        const applications = applicationGroups.flat();

        const selected = applications.filter((application) => application.status === "SELECTED");
        const offerResults = await Promise.all(selected.map(async (application) => {
            try {
                return await fetchAuthenticatedJson(`/company/applications/${application.id}/offer/`, token);
            } catch (error) {
                if (error.status === 404) return null;
                throw error;
            }
        }));
        const offersByApplication = new Map(
            offerResults.filter(Boolean).map((offer) => [offer.application_id, offer])
        );
        const selectedWithOffers = selected.filter((application) => offersByApplication.has(application.id));
        renderCompanyApplicants(applications, offersByApplication);

        const interviewGroups = await Promise.all(applications.map(async (application) => {
            const data = await fetchAuthenticatedJson(`/company/applications/${application.id}/interviews/`, token);
            return normalizeApiList(data);
        }));
        const interviews = interviewGroups.flat();

        const shortlisted = applications.filter((application) => application.status === "SHORTLISTED");
        setText("stat-total-applicants", applications.length);
        setText("stat-shortlisted-count", shortlisted.length);
        setText("stat-interview-count", interviews.length);
        setText("stat-selected-count", selected.length);
        renderCompanyApplicationList("shortlisted-list", shortlisted, "No students have been shortlisted.");
        renderCompanyApplicationList("selected-list", selectedWithOffers, "No offers have been issued.", offersByApplication);
        renderCompanyInterviews(interviews);
        await loadNotificationBadge("company-notification-badge");
    } catch (error) {
        console.error("Company recruitment data load failed:", error);
        [
            "stat-total-applicants",
            "stat-shortlisted-count",
            "stat-interview-count",
            "stat-selected-count",
        ].forEach((id) => setText(id, "-"));
        const jobsList = document.getElementById("company-jobs-list");
        if (jobsList) jobsList.textContent = error.message || "Unable to load company jobs.";
        const applicantsTable = document.getElementById("applicants-table-body");
        if (applicantsTable) applicantsTable.textContent = "";
    }
}

let currentTpoDashboardData = null;

function getTpoSearchQuery() {
    return document.getElementById("tpo-global-search")?.value.trim().toLowerCase() || "";
}

function matchesTpoSearch(query, ...values) {
    return !query || values.filter((value) => value !== null && value !== undefined)
        .join(" ").toLowerCase().includes(query);
}

function createTpoButton(label, onClick) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "secondary-button small";
    button.textContent = label;
    button.addEventListener("click", onClick);
    return button;
}

function setTpoTableMessage(tableId, message, columnCount, isError = false) {
    const body = document.getElementById(tableId);
    if (!body) return;
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = columnCount;
    cell.className = isError ? "error-state" : "empty-state";
    cell.textContent = message;
    row.appendChild(cell);
    body.replaceChildren(row);
}

function openTpoModal(title, content, actions) {
    setText("tpo-modal-title", title);
    const modal = document.getElementById("tpo-modal");
    const modalContent = document.getElementById("tpo-modal-content");
    const modalActions = document.getElementById("tpo-modal-actions");
    if (!modal || !modalContent || !modalActions) return;
    modalContent.replaceChildren(content);
    modalActions.replaceChildren(...actions);
    modal.classList.add("is-open");
    modal.setAttribute("aria-hidden", "false");
}

function closeTpoModal() {
    const modal = document.getElementById("tpo-modal");
    if (!modal) return;
    modal.classList.remove("is-open");
    modal.setAttribute("aria-hidden", "true");
}

function renderTpoDrives(drives) {
    const driveGrid = document.getElementById("drives-list");
    if (!driveGrid) return;
    driveGrid.replaceChildren();
    if (!drives.length) {
        const empty = document.createElement("p");
        empty.className = "empty-state";
        empty.textContent = "No placement drives have been created.";
        driveGrid.appendChild(empty);
        return;
    }

    drives.forEach((drive) => {
        const card = document.createElement("article");
        card.className = "drive-card";
        const heading = document.createElement("h3");
        heading.textContent = drive.job_title || "Placement drive";
        const company = document.createElement("p");
        company.className = "drive-meta";
        company.textContent = drive.company_name || "Company unavailable";
        const details = document.createElement("p");
        details.className = "drive-meta";
        details.textContent = `Drive date: ${drive.drive_date} · Deadline: ${new Date(drive.application_deadline).toLocaleString()} · Minimum CGPA: ${drive.minimum_cgpa} · Status: ${drive.status}`;
        card.append(heading, company, details);

        if (drive.status !== "CLOSED") {
            const nextStatus = drive.status === "DRAFT" ? "PUBLISHED" : "CLOSED";
            card.appendChild(createTpoButton(nextStatus === "PUBLISHED" ? "Publish" : "Close drive", async () => {
                try {
                    await fetchAuthenticatedJson(`/tpo/placement-drives/${drive.id}/`, localStorage.getItem("access"), {
                        method: "PATCH",
                        body: JSON.stringify({ status: nextStatus }),
                    });
                    await loadTpoDashboard();
                } catch (error) {
                    showToast(error.message || "Unable to update placement drive.", true);
                }
            }));
        }
        driveGrid.appendChild(card);
    });
}

function openPlacementDriveForm(data) {
    const form = document.createElement("form");
    form.className = "schedule-form";
    const fields = {};

    function addControl(name, labelText, type = "text") {
        const wrapper = document.createElement("div");
        wrapper.className = "form-field";
        const label = document.createElement("label");
        label.textContent = labelText;
        const control = document.createElement(type === "select" ? "select" : type === "textarea" ? "textarea" : "input");
        control.name = name;
        control.required = ["company", "job", "drive_date", "application_deadline"].includes(name);
        if (type !== "select" && type !== "textarea") control.type = type;
        if (type === "textarea") control.rows = 2;
        wrapper.append(label, control);
        form.appendChild(wrapper);
        fields[name] = control;
        return control;
    }

    const companySelect = addControl("company", "Company", "select");
    data.companies.forEach((company) => {
        const option = document.createElement("option");
        option.value = company.id;
        option.textContent = company.company_name;
        companySelect.appendChild(option);
    });
    const jobSelect = addControl("job", "Job", "select");

    function refreshDriveJobs() {
        jobSelect.replaceChildren();
        data.jobs.filter((job) => String(job.company_id) === companySelect.value).forEach((job) => {
            const option = document.createElement("option");
            option.value = job.id;
            option.textContent = `${job.job_title} (${job.status})`;
            jobSelect.appendChild(option);
        });
    }

    companySelect.addEventListener("change", refreshDriveJobs);
    refreshDriveJobs();
    addControl("drive_date", "Drive date", "date");
    addControl("eligible_departments", "Eligible departments (comma-separated)");
    addControl("eligible_courses", "Eligible courses (comma-separated)");
    const minimumCgpa = addControl("minimum_cgpa", "Minimum CGPA", "number");
    minimumCgpa.min = "0";
    minimumCgpa.max = "10";
    minimumCgpa.step = "0.01";
    minimumCgpa.value = "0.00";
    addControl("application_deadline", "Application deadline", "datetime-local");
    const driveStatus = addControl("status", "Status", "select");
    ["DRAFT", "PUBLISHED", "CLOSED"].forEach((status) => {
        const option = document.createElement("option");
        option.value = status;
        option.textContent = status;
        driveStatus.appendChild(option);
    });

    const feedback = document.createElement("p");
    feedback.className = "form-status";
    feedback.setAttribute("role", "status");
    form.appendChild(feedback);

    const cancelButton = document.createElement("button");
    cancelButton.type = "button";
    cancelButton.className = "secondary-button";
    cancelButton.textContent = "Cancel";
    cancelButton.addEventListener("click", closeTpoModal);

    const createButton = document.createElement("button");
    createButton.type = "submit";
    createButton.className = "primary-button";
    createButton.textContent = "Create Drive";

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        if (!data.companies.length || !jobSelect.value) {
            setStatusMessage(feedback, "A company and job are required to create a drive.", "error");
            return;
        }

        const deadline = new Date(fields.application_deadline.value);
        const payload = {
            company: Number(fields.company.value),
            job: Number(fields.job.value),
            drive_date: fields.drive_date.value,
            eligible_departments: fields.eligible_departments.value.split(",").map((item) => item.trim()).filter(Boolean),
            eligible_courses: fields.eligible_courses.value.split(",").map((item) => item.trim()).filter(Boolean),
            minimum_cgpa: fields.minimum_cgpa.value,
            application_deadline: deadline.toISOString(),
            status: fields.status.value,
        };

        try {
            await fetchAuthenticatedJson("/tpo/placement-drives/", localStorage.getItem("access"), {
                method: "POST",
                body: JSON.stringify(payload),
            });
            closeTpoModal();
            await loadTpoDashboard();
        } catch (error) {
            setStatusMessage(feedback, error.message || "Unable to create placement drive.", "error");
        }
    });

    if (!data.companies.length || !jobSelect.value) {
        createButton.disabled = true;
        const warning = document.createElement("p");
        warning.className = "empty-state";
        warning.textContent = "Create a company profile and job before scheduling a drive.";
        form.appendChild(warning);
    }
    openTpoModal("Create Placement Drive", form, [cancelButton, createButton]);
}

function renderTpoNotifications(notifications) {
    const list = document.getElementById("notifications-list");
    if (!list) return;
    list.replaceChildren();
    if (!notifications.length) {
        const empty = document.createElement("p");
        empty.className = "empty-state";
        empty.textContent = "No notifications.";
        list.appendChild(empty);
        return;
    }

    notifications.forEach((notification) => {
        const item = document.createElement("article");
        item.className = "notification-item";
        const title = document.createElement("h3");
        title.textContent = notification.title;
        const message = document.createElement("p");
        message.textContent = notification.message;
        const created = document.createElement("p");
        created.textContent = new Date(notification.created_at).toLocaleString();
        item.append(title, message, created);
        if (!notification.is_read) {
            item.appendChild(createTpoButton("Mark read", async () => {
                try {
                    await fetchAuthenticatedJson(`/notifications/${notification.id}/read/`, localStorage.getItem("access"), { method: "PATCH" });
                    await loadTpoDashboard();
                } catch (error) {
                    showToast(error.message || "Unable to mark notification as read.", true);
                }
            }));
        }
        list.appendChild(item);
    });
}

function updateNotificationBadge(elementId, unreadCount) {
    const badge = document.getElementById(elementId);
    if (!badge) return;
    badge.textContent = unreadCount ? String(unreadCount) : "";
    badge.hidden = !unreadCount;
}

async function loadNotificationBadge(elementId) {
    if (!document.getElementById(elementId)) return;
    const token = localStorage.getItem("access");
    if (!token) return;
    try {
        const data = await fetchAuthenticatedJson("/notifications/", token);
        updateNotificationBadge(elementId, Number(data?.unread_count) || 0);
        renderNotificationList("student-notifications-list", data?.notifications);
        renderNotificationList("company-notifications-list", data?.notifications);
    } catch (error) {
        console.error("Notification count load failed:", error);
        showToast(error.message || "Unable to load notifications.", true);
    }
}

function renderNotificationList(elementId, notifications) {
    const list = document.getElementById(elementId);
    if (!list) return;

    const entries = normalizeApiList(notifications);
    list.replaceChildren();
    if (!entries.length) {
        const empty = document.createElement("p");
        empty.className = "empty-state";
        empty.textContent = "No notifications.";
        list.appendChild(empty);
        return;
    }

    entries.forEach((notification) => {
        const item = document.createElement("article");
        item.className = "notification-item";
        const title = document.createElement("h3");
        title.textContent = notification.title || "Update";
        const message = document.createElement("p");
        message.textContent = notification.message || "";
        const created = document.createElement("p");
        created.textContent = notification.created_at
            ? new Date(notification.created_at).toLocaleString()
            : "";
        item.append(title, message, created);

        if (!notification.is_read && notification.id) {
            item.appendChild(createTpoButton("Mark read", async () => {
                try {
                    await fetchAuthenticatedJson(`/notifications/${notification.id}/read/`, localStorage.getItem("access"), { method: "PATCH" });
                    await loadNotificationBadge(elementId.startsWith("student-")
                        ? "student-notification-badge"
                        : "company-notification-badge");
                } catch (error) {
                    showToast(error.message || "Unable to mark notification as read.", true);
                }
            }));
        }
        list.appendChild(item);
    });
}

function renderTpoStudents(data) {
    const body = document.getElementById("students-table-body");
    if (!body) return;

    const query = [
        document.getElementById("student-search")?.value.trim().toLowerCase() || "",
        getTpoSearchQuery(),
    ].filter(Boolean);
    const department = document.getElementById("student-department-filter")?.value || "";
    const placementStatus = document.getElementById("student-status-filter")?.value || "";
    const records = data.students.map((student) => {
        const applications = data.applications.filter((application) => application.student_id === student.student_id);
        const placement = data.placements.find((record) => record.student_id === student.student_id);
        const status = placement
            ? placement.placement_status === "PLACED" ? "Placed" : "Withdrawn"
            : applications.some((application) => application.status === "SHORTLISTED")
                ? "Shortlisted"
                : "Seeking";
        return { ...student, placementStatus: status, placementRecord: placement };
    }).filter((student) => {
        const searchable = `${student.student_id} ${student.first_name} ${student.last_name} ${student.email}`.toLowerCase();
        return query.every((term) => searchable.includes(term))
            && (!department || student.department === department)
            && (!placementStatus || student.placementStatus === placementStatus);
    });

    body.replaceChildren();
    if (!records.length) {
        setTpoTableMessage("students-table-body", "No students match the current filters.", 9);
        return;
    }

    records.forEach((student) => {
        const row = document.createElement("tr");
        [
            student.student_id,
            `${student.first_name} ${student.last_name}`.trim(),
            student.department,
            student.course,
            student.cgpa,
            student.year ?? "-",
            student.placementStatus,
            student.is_active ? "Active" : "Inactive",
        ].forEach((value) => {
            const cell = document.createElement("td");
            cell.textContent = value ?? "-";
            row.appendChild(cell);
        });

        const actions = document.createElement("td");
        if (student.placementRecord) {
            const statusSelect = document.createElement("select");
            ["PLACED", "WITHDRAWN"].forEach((status) => {
                const option = document.createElement("option");
                option.value = status;
                option.textContent = status === "PLACED" ? "Placed" : "Withdrawn";
                option.selected = student.placementRecord.placement_status === status;
                statusSelect.appendChild(option);
            });
            actions.appendChild(statusSelect);
            actions.appendChild(createTpoButton("Update", async () => {
                try {
                    await fetchAuthenticatedJson(`/tpo/placements/${student.placementRecord.id}/`, localStorage.getItem("access"), {
                        method: "PATCH",
                        body: JSON.stringify({ placement_status: statusSelect.value }),
                    });
                    await loadTpoDashboard();
                } catch (error) {
                    showToast(error.message || "Unable to update student placement status.", true);
                }
            }));
        } else {
            actions.textContent = "No placement record";
        }
        row.appendChild(actions);
        body.appendChild(row);
    });
}

function renderTpoCompanies(data) {
    const body = document.getElementById("companies-table-body");
    if (!body) return;
    const statusFilter = document.querySelector("#company-filters .filter-tab.is-active")?.dataset.filter || "";
    const query = getTpoSearchQuery();
    const records = data.companies.filter((company) => (
        (!statusFilter || company.verification_status === statusFilter.toUpperCase())
        && matchesTpoSearch(query, company.company_name, company.industry, company.contact_email, company.location)
    ));
    body.replaceChildren();
    if (!records.length) {
        setTpoTableMessage("companies-table-body", "No companies match this filter.", 9);
        return;
    }

    records.forEach((company) => {
        const companyJobs = data.jobs.filter((job) => job.company_id === company.id);
        const jobIds = new Set(companyJobs.map((job) => job.id));
        const applicantsCount = data.applications.filter((application) => jobIds.has(application.job_id)).length;
        const row = document.createElement("tr");
        [
            company.company_name,
            company.industry,
            company.contact_email,
            company.location,
            companyJobs.length,
            applicantsCount,
            company.verification_status,
            company.verification_remarks || "-",
        ].forEach((value) => {
            const cell = document.createElement("td");
            cell.textContent = value ?? "-";
            row.appendChild(cell);
        });

        const actions = document.createElement("td");
        if (company.verification_status === "PENDING") {
            ["APPROVED", "REJECTED"].forEach((verificationStatus) => {
                actions.appendChild(createTpoButton(
                    verificationStatus === "APPROVED" ? "Approve" : "Reject",
                    async () => {
                        const remarks = window.prompt("Verification remarks:", company.verification_remarks || "");
                        if (remarks === null) return;
                        try {
                            await fetchAuthenticatedJson(`/tpo/companies/${company.id}/verify/`, localStorage.getItem("access"), {
                                method: "PATCH",
                                body: JSON.stringify({ verification_status: verificationStatus, remarks }),
                            });
                            await loadTpoDashboard();
                        } catch (error) {
                            showToast(error.message || "Unable to update company verification.", true);
                        }
                    }
                ));
            });
        } else {
            actions.textContent = "-";
        }
        row.appendChild(actions);
        body.appendChild(row);
    });
}

function renderTpoJobs(data) {
    const body = document.getElementById("jobs-table-body");
    if (!body) return;
    body.replaceChildren();
    const query = getTpoSearchQuery();
    const jobs = data.jobs.filter((job) => matchesTpoSearch(
        query,
        job.job_title,
        job.company_name,
        job.job_location,
        job.status,
    ));
    if (!jobs.length) {
        setTpoTableMessage("jobs-table-body", "No job listings are available.", 10);
        return;
    }

    jobs.forEach((job) => {
        const applicantCount = data.applications.filter((application) => application.job_id === job.id).length;
        const row = document.createElement("tr");
        [
            job.job_title,
            job.company_name,
            job.job_location,
            job.salary ?? "-",
            `CGPA ${job.minimum_cgpa ?? "-"}`,
            job.created_at ? new Date(job.created_at).toLocaleDateString() : "-",
            job.application_deadline ? new Date(job.application_deadline).toLocaleDateString() : "-",
            applicantCount,
            job.status,
        ].forEach((value) => {
            const cell = document.createElement("td");
            cell.textContent = value ?? "-";
            row.appendChild(cell);
        });

        const actions = document.createElement("td");
        if (job.status === "PENDING_TPO_APPROVAL") {
            ["APPROVED", "REJECTED"].forEach((newStatus) => {
                actions.appendChild(createTpoButton(newStatus === "APPROVED" ? "Approve" : "Reject", async () => {
                    const remarks = window.prompt("Review remarks:", job.approval_remarks || "");
                    if (remarks === null) return;
                    try {
                        await fetchAuthenticatedJson(`/tpo/jobs/${job.id}/verify/`, localStorage.getItem("access"), {
                            method: "PATCH",
                            body: JSON.stringify({ status: newStatus, remarks }),
                        });
                        await loadTpoDashboard();
                    } catch (error) {
                        showToast(error.message || "Unable to update job status.", true);
                    }
                }));
            });
        } else {
            actions.textContent = "-";
        }
        row.appendChild(actions);
        body.appendChild(row);
    });
}

function renderTpoApplications(data) {
    const body = document.getElementById("applications-admin-body");
    if (!body) return;
    body.replaceChildren();
    const query = getTpoSearchQuery();
    const applications = data.applications.filter((application) => matchesTpoSearch(
        query,
        application.student_name,
        application.student_id,
        application.company_name,
        application.job_title,
        application.status,
    ));
    if (!applications.length) {
        setTpoTableMessage("applications-admin-body", "No applications have been submitted.", 9);
        return;
    }
    applications.forEach((application) => {
        const applicationInterviews = data.interviews.filter((interview) => interview.application_id === application.id);
        const row = document.createElement("tr");
        [
            `${application.student_name} (${application.student_id})`,
            application.company_name,
            application.job_title,
            application.applied_at ? new Date(application.applied_at).toLocaleDateString() : "-",
            application.cgpa,
            application.status,
            application.status === "SHORTLISTED" ? "Yes" : "No",
            applicationInterviews.length,
            "Read only",
        ].forEach((value) => {
            const cell = document.createElement("td");
            cell.textContent = value ?? "-";
            row.appendChild(cell);
        });
        body.appendChild(row);
    });
}

function renderTpoInterviews(data) {
    const body = document.getElementById("interviews-admin-body");
    if (!body) return;
    body.replaceChildren();
    if (!data.interviews.length) {
        setTpoTableMessage("interviews-admin-body", "No interviews have been scheduled.", 10);
        return;
    }
    data.interviews.forEach((interview) => {
        const scheduled = interview.scheduled_at ? new Date(interview.scheduled_at) : null;
        const row = document.createElement("tr");
        [
            `${interview.student_name} (${interview.student_id})`,
            interview.company_name,
            interview.job_title,
            interview.round,
            scheduled ? scheduled.toLocaleDateString() : "-",
            scheduled ? scheduled.toLocaleTimeString() : "-",
            interview.interview_type,
            interview.interviewer || "-",
            interview.status,
            "Read only",
        ].forEach((value) => {
            const cell = document.createElement("td");
            cell.textContent = value ?? "-";
            row.appendChild(cell);
        });
        body.appendChild(row);
    });
}

function renderTpoOffers(data) {
    const body = document.getElementById("offers-table-body");
    if (!body) return;
    body.replaceChildren();
    if (!data.offers.length) {
        setTpoTableMessage("offers-table-body", "No offers have been issued.", 7);
        return;
    }
    data.offers.forEach((offer) => {
        const row = document.createElement("tr");
        [
            `${offer.student_name} (${offer.student_id})`,
            offer.company_name,
            offer.job_title,
            offer.ctc,
            offer.issued_at ? new Date(offer.issued_at).toLocaleDateString() : "-",
            offer.joining_date,
            offer.status,
        ].forEach((value) => {
            const cell = document.createElement("td");
            cell.textContent = value ?? "-";
            row.appendChild(cell);
        });
        body.appendChild(row);
    });
}

function renderTpoPlacements(data) {
    const body = document.getElementById("records-table-body");
    if (body) {
        body.replaceChildren();
        if (!data.placements.length) {
            setTpoTableMessage("records-table-body", "No placement records are available.", 8);
        } else {
            data.placements.forEach((record) => {
                const row = document.createElement("tr");
                [
                    `${record.student_name} (${record.student_id})`,
                    record.company_name,
                    record.job_title,
                    record.ctc,
                    record.placed_at ? new Date(record.placed_at).toLocaleDateString() : "-",
                    "-",
                    record.placement_status,
                ].forEach((value) => {
                    const cell = document.createElement("td");
                    cell.textContent = value ?? "-";
                    row.appendChild(cell);
                });
                const actions = document.createElement("td");
                const statusSelect = document.createElement("select");
                ["PLACED", "WITHDRAWN"].forEach((placementStatus) => {
                    const option = document.createElement("option");
                    option.value = placementStatus;
                    option.textContent = placementStatus;
                    option.selected = record.placement_status === placementStatus;
                    statusSelect.appendChild(option);
                });
                actions.appendChild(statusSelect);
                actions.appendChild(createTpoButton("Update", async () => {
                    try {
                        await fetchAuthenticatedJson(`/tpo/placements/${record.id}/`, localStorage.getItem("access"), {
                            method: "PATCH",
                            body: JSON.stringify({ placement_status: statusSelect.value }),
                        });
                        await loadTpoDashboard();
                    } catch (error) {
                        showToast(error.message || "Unable to update placement status.", true);
                    }
                }));
                row.appendChild(actions);
                body.appendChild(row);
            });
        }
    }

    const reportGrid = document.getElementById("reports-grid");
    if (reportGrid) {
        reportGrid.replaceChildren();
        [
            ["Total placements", data.summary.total_placements],
            ["Companies with placements", data.summary.total_companies],
            ["Placement percentage", data.students.length
                ? `${((data.summary.total_students_placed / data.students.length) * 100).toFixed(1)}%`
                : "0.0%"],
            ["Average CTC", data.summary.average_ctc],
            ["Highest CTC", data.summary.highest_ctc],
        ].forEach(([label, value]) => {
            const report = document.createElement("article");
            report.className = "report-card";
            const heading = document.createElement("h3");
            heading.textContent = label;
            const metric = document.createElement("strong");
            metric.textContent = value ?? "-";
            report.append(heading, metric);
            reportGrid.appendChild(report);
        });
    }

    const placementBars = document.getElementById("placement-bars");
    if (placementBars) {
        placementBars.replaceChildren();
        const maxCount = Math.max(1, ...data.summary.department_wise.map((entry) => entry.count));
        data.summary.department_wise.forEach((entry) => {
            const row = document.createElement("div");
            row.className = "placement-bar-row";
            const label = document.createElement("span");
            label.textContent = entry.department || "Unspecified";
            const bar = document.createElement("span");
            bar.className = "placement-bar";
            bar.style.width = `${(entry.count / maxCount) * 100}%`;
            const count = document.createElement("strong");
            count.textContent = entry.count;
            row.append(label, bar, count);
            placementBars.appendChild(row);
        });
        if (!data.summary.department_wise.length) {
            placementBars.textContent = "No placement records are available.";
        }
    }
}

function renderTpoDashboard(data) {
    const summary = data.summary && typeof data.summary === "object" ? data.summary : {};
    const notifications = data.notifications && typeof data.notifications === "object"
        ? data.notifications
        : {};
    data = {
        ...data,
        user: data.user || {},
        students: normalizeApiList(data.students),
        companies: normalizeApiList(data.companies),
        jobs: normalizeApiList(data.jobs),
        applications: normalizeApiList(data.applications),
        interviews: normalizeApiList(data.interviews),
        offers: normalizeApiList(data.offers),
        placements: normalizeApiList(data.placements),
        drives: normalizeApiList(data.drives),
        summary: {
            total_students_placed: summary.total_students_placed ?? 0,
            total_placements: summary.total_placements ?? 0,
            total_companies: summary.total_companies ?? 0,
            average_ctc: summary.average_ctc ?? 0,
            highest_ctc: summary.highest_ctc ?? 0,
            department_wise: normalizeApiList(summary.department_wise),
        },
        notifications: {
            notifications: normalizeApiList(notifications.notifications),
            unread_count: notifications.unread_count ?? 0,
        },
    };
    currentTpoDashboardData = data;
    const user = data.user;
    const fullName = `${user.first_name || ""} ${user.last_name || ""}`.trim() || user.email;
    setText("tpo-name-display", fullName || "TPO");
    setText("tpo-avatar", fullName ? fullName.split(/\s+/).map((part) => part[0]).join("").slice(0, 2).toUpperCase() : "TP");

    setText("tpo-stat-students", data.students.length);
    setText("tpo-stat-companies", data.companies.length);
    setText("tpo-stat-jobs", data.jobs.filter((job) => (
        job.status === "APPROVED" && Date.parse(job.application_deadline) > Date.now()
    )).length);
    setText("tpo-stat-applications", data.applications.length);
    setText("tpo-stat-shortlisted", data.applications.filter((application) => application.status === "SHORTLISTED").length);
    setText("tpo-stat-placed", data.summary.total_students_placed);
    const placementPercent = data.students.length
        ? ((data.summary.total_students_placed / data.students.length) * 100).toFixed(1)
        : "0.0";
    setText("tpo-stat-percentage", `${placementPercent}%`);
    const weekAhead = Date.now() + 7 * 24 * 60 * 60 * 1000;
    setText("tpo-stat-interviews", data.interviews.filter((interview) => {
        const scheduledAt = Date.parse(interview.scheduled_at);
        return interview.status === "SCHEDULED" && scheduledAt >= Date.now() && scheduledAt <= weekAhead;
    }).length);

    renderTpoStudents(data);
    renderTpoCompanies(data);
    renderTpoJobs(data);
    renderTpoApplications(data);
    renderTpoInterviews(data);
    renderTpoOffers(data);
    renderTpoPlacements(data);
    renderTpoDrives(data.drives);
    renderTpoNotifications(data.notifications.notifications);
    updateNotificationBadge("tpo-notification-badge", data.notifications.unread_count);
}

async function loadTpoDashboard() {
    if (!document.getElementById("tpo-name-display")) return;
    const token = localStorage.getItem("access");
    if (!token) {
        window.location.href = "index.html";
        return;
    }

    try {
        const [user, students, companies, jobs, applications, interviews, offers, placements, summary, drives, notifications] = await Promise.all([
            fetchAuthenticatedJson("/auth/me/", token),
            fetchAuthenticatedJson("/tpo/students/", token),
            fetchAuthenticatedJson("/tpo/companies/", token),
            fetchAuthenticatedJson("/tpo/jobs/", token),
            fetchAuthenticatedJson("/tpo/applications/", token),
            fetchAuthenticatedJson("/tpo/interviews/", token),
            fetchAuthenticatedJson("/tpo/offers/", token),
            fetchAuthenticatedJson("/tpo/placements/", token),
            fetchAuthenticatedJson("/tpo/placements/summary/", token),
            fetchAuthenticatedJson("/tpo/placement-drives/", token),
            fetchAuthenticatedJson("/notifications/", token),
        ]);
        if (user.role !== "TPO") {
            window.location.href = "index.html";
            return;
        }
        renderTpoDashboard({ user, students, companies, jobs, applications, interviews, offers, placements, summary, drives, notifications });
    } catch (error) {
        console.error("TPO dashboard load failed:", error);
        const message = error.message || "Unable to load TPO data.";
        [
            ["students-table-body", 9],
            ["companies-table-body", 9],
            ["jobs-table-body", 10],
            ["applications-admin-body", 9],
            ["interviews-admin-body", 10],
            ["offers-table-body", 7],
            ["records-table-body", 8],
        ].forEach(([id, count]) => setTpoTableMessage(id, message, count, true));
        const drivesList = document.getElementById("drives-list");
        if (drivesList) drivesList.textContent = message;
        const notificationsList = document.getElementById("notifications-list");
        if (notificationsList) notificationsList.textContent = message;
        [
            "tpo-stat-students",
            "tpo-stat-companies",
            "tpo-stat-jobs",
            "tpo-stat-applications",
            "tpo-stat-shortlisted",
            "tpo-stat-placed",
            "tpo-stat-percentage",
            "tpo-stat-interviews",
        ].forEach((id) => setText(id, "Unavailable"));
        setText("tpo-name-display", "Unable to load TPO profile.");
    }
}

function bindRoleSelection() {
    const roleTabs = document.querySelectorAll(".role-tab");
    const selectedRoleLabel = document.getElementById("selected-role-label");
    const loginHeading = document.getElementById("login-heading");
    let selectedRole = "STUDENT";

    function updateRoleDisplay(role) {
        selectedRole = role;

        roleTabs.forEach((button) => {
            const isActive = button.dataset.role === role;
            button.classList.toggle("active", isActive);
            button.classList.toggle("is-selected", isActive);
        });

        if (selectedRoleLabel) {
            const labels = { STUDENT: "Student", COMPANY: "Company", TPO: "TPO" };
            selectedRoleLabel.textContent = `Sign in as ${labels[role] || "Student"}`;
        }

        if (loginHeading) {
            const titles = { STUDENT: "Student Sign In", COMPANY: "Company Sign In", TPO: "TPO Sign In" };
            loginHeading.textContent = titles[role] || "Student Sign In";
        }
    }

    roleTabs.forEach((button) => {
        button.addEventListener("click", function () {
            updateRoleDisplay(button.dataset.role);
        });
    });

    return {
        getSelectedRole() {
            return selectedRole;
        },
        showRegistrationForm() {
            const loginPanel = document.getElementById("login-panel");
            const registrationPanel = document.getElementById("registration-panel");
            const studentForm = document.getElementById("registration-form");
            const companyForm = document.getElementById("company-registration-form");
            const tpoForm = document.getElementById("tpo-registration-form");

            if (loginPanel) loginPanel.hidden = true;
            if (registrationPanel) registrationPanel.hidden = false;
            if (studentForm) studentForm.hidden = selectedRole !== "STUDENT";
            if (companyForm) companyForm.hidden = selectedRole !== "COMPANY";
            if (tpoForm) tpoForm.hidden = selectedRole !== "TPO";
        },
        returnToLogin() {
            const loginPanel = document.getElementById("login-panel");
            const registrationPanel = document.getElementById("registration-panel");
            const studentForm = document.getElementById("registration-form");
            const companyForm = document.getElementById("company-registration-form");
            const tpoForm = document.getElementById("tpo-registration-form");

            if (registrationPanel) registrationPanel.hidden = true;
            if (loginPanel) loginPanel.hidden = false;
            if (studentForm) studentForm.hidden = true;
            if (companyForm) companyForm.hidden = true;
            if (tpoForm) tpoForm.hidden = true;
        },
    };
}

document.addEventListener("DOMContentLoaded", function () {
    const roleManager = bindRoleSelection();

    document.querySelectorAll('input[type="email"]').forEach(function (emailInput) {
        function validateEmailInput() {
            const value = emailInput.value.trim();
            emailInput.setCustomValidity(
                !value || isValidEmailAddress(value)
                    ? ""
                    : "Please enter a valid email address."
            );
        }

        emailInput.addEventListener("input", validateEmailInput);
        emailInput.addEventListener("change", validateEmailInput);
    });

    const loginForm = document.getElementById("login-form");
    const showRegistration = document.getElementById("show-registration");
    const showLogin = document.getElementById("show-login");
    const companyShowLogin = document.querySelector(".company-show-login");
    const tpoShowLogin = document.querySelector(".tpo-show-login");
    const forgotPasswordButton = document.getElementById("forgot-password");
    const forgotPasswordPanel = document.getElementById("forgot-password-panel");
    const forgotPasswordForm = document.getElementById("forgot-password-form");
    const forgotBackLogin = document.getElementById("forgot-back-login");
    const resetPasswordForm = document.getElementById("reset-password-form");
    const passwordInput = document.getElementById("password");
    const passwordToggle = document.getElementById("password-toggle");
    const companyProfileForm = document.getElementById("company-profile-form");
    const tpoRegistrationForm = document.getElementById("tpo-registration-form");
    const standaloneStudentForm = document.getElementById("student-registration-page-form");
    const standaloneCompanyForm = document.getElementById("companyForm");

    function splitPersonName(fullName) {
        const parts = fullName.trim().split(/\s+/).filter(Boolean);
        return {
            first_name: parts.shift() || "",
            last_name: parts.join(" "),
        };
    }

    if (standaloneStudentForm) {
        standaloneStudentForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            const values = Object.fromEntries(new FormData(standaloneStudentForm));
            const statusElement = document.getElementById("student-registration-page-status");
            const names = splitPersonName(values.full_name || "");
            const payload = {
                ...names,
                email: (values.email || "").trim(),
                student_id: (values.student_id || "").trim(),
                phone_number: (values.phone_number || "").trim(),
                department: (values.department || "").trim(),
                course: (values.course || "").trim(),
                year: Number(values.year),
                cgpa: Number(values.cgpa),
                skills: (values.skills || "").trim(),
                password: values.password,
                password_confirm: values.password_confirm,
            };
            if (payload.password !== payload.password_confirm) {
                setStatusMessage(statusElement, "Passwords do not match.", "error");
                return;
            }

            setStatusMessage(statusElement, "Creating student account...");
            const submitButton = standaloneStudentForm.querySelector('[type="submit"]');
            if (submitButton) submitButton.disabled = true;
            try {
                const response = await fetch(`${API_BASE_URL}/auth/register/student/`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload),
                });
                const data = await response.json().catch(() => ({}));
                if (!response.ok) throw new Error(getErrorMessage(data, "Student registration failed."));
                standaloneStudentForm.reset();
                setStatusMessage(statusElement, "Student account created. You can now sign in.", "success");
            } catch (error) {
                setStatusMessage(statusElement, error.message || "Unable to create student account.", "error");
            } finally {
                if (submitButton) submitButton.disabled = false;
            }
        });
    }

    if (standaloneCompanyForm) {
        standaloneCompanyForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            const values = Object.fromEntries(new FormData(standaloneCompanyForm));
            const statusElement = document.getElementById("company-registration-page-status");
            const names = splitPersonName(values.contact_person || "");
            const email = (values.email || "").trim();
            const payload = {
                ...names,
                email,
                password: values.password,
                password_confirm: values.password_confirm,
                company_name: (values.company_name || "").trim(),
                company_description: (values.company_description || "").trim(),
                industry: (values.industry || "").trim(),
                location: (values.location || "").trim(),
                contact_email: email,
                contact_phone: (values.contact_phone || "").trim(),
            };
            if (payload.password !== payload.password_confirm) {
                setStatusMessage(statusElement, "Passwords do not match.", "error");
                return;
            }

            setStatusMessage(statusElement, "Creating company account...");
            const submitButton = standaloneCompanyForm.querySelector('[type="submit"]');
            if (submitButton) submitButton.disabled = true;
            try {
                const response = await fetch(`${API_BASE_URL}/auth/register/company/`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload),
                });
                const data = await response.json().catch(() => ({}));
                if (!response.ok) throw new Error(getErrorMessage(data, "Company registration failed."));
                standaloneCompanyForm.reset();
                setStatusMessage(statusElement, "Company account created. You can now sign in.", "success");
            } catch (error) {
                setStatusMessage(statusElement, error.message || "Unable to create company account.", "error");
            } finally {
                if (submitButton) submitButton.disabled = false;
            }
        });
    }

    if (tpoRegistrationForm) {
        tpoRegistrationForm.addEventListener("submit", async function (event) {
            event.preventDefault();

            const payload = {
                first_name: tpoRegistrationForm.querySelector('[name="first_name"]').value.trim(),
                last_name: tpoRegistrationForm.querySelector('[name="last_name"]').value.trim(),
                email: tpoRegistrationForm.querySelector('[name="email"]').value.trim(),
                password: tpoRegistrationForm.querySelector('[name="password"]').value,
                password_confirm: tpoRegistrationForm.querySelector('[name="password_confirm"]').value,
            };
            const statusElement = document.getElementById("tpo-registration-status");

            if (!payload.first_name || !payload.last_name || !payload.email || !payload.password || !payload.password_confirm) {
                setStatusMessage(statusElement, "Please complete all TPO registration fields.", "error");
                return;
            }
            if (payload.password !== payload.password_confirm) {
                setStatusMessage(statusElement, "Passwords do not match.", "error");
                return;
            }

            setStatusMessage(statusElement, "Creating TPO account...");
            try {
                const response = await fetch(`${API_BASE_URL}/auth/register/tpo/`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload),
                });
                const data = await response.json().catch(() => ({}));
                if (!response.ok) {
                    throw new Error(getErrorMessage(data, "TPO registration failed."));
                }

                tpoRegistrationForm.reset();
                setStatusMessage(
                    statusElement,
                    data.message || "TPO account created successfully. You can now sign in.",
                    "success"
                );
            } catch (error) {
                console.error("TPO registration failed:", error);
                setStatusMessage(statusElement, error.message || "Unable to create TPO account.", "error");
            }
        });
    }

    if (companyProfileForm) {
        companyProfileForm.addEventListener("submit", async function (event) {
            event.preventDefault();
            const token = localStorage.getItem("access");
            if (!token) {
                window.location.href = "index.html";
                return;
            }

            const saveButton = document.getElementById("company-profile-save");
            if (saveButton) saveButton.disabled = true;
            setCompanyFeedback("company-profile-load-status", "Saving company details...");

            try {
                const data = await fetchAuthenticatedJson("/company/profile/", token, {
                    method: "PATCH",
                    body: JSON.stringify(Object.fromEntries(new FormData(companyProfileForm))),
                });

                renderCompanyProfile(data.profile || data);
                setCompanyFeedback(
                    "company-profile-load-status",
                    data.message || "Company profile updated successfully.",
                    "success"
                );
            } catch (error) {
                console.error("Company profile update failed:", error);
                setCompanyFeedback(
                    "company-profile-load-status",
                    error.message || "Unable to save company details.",
                    "error"
                );
            } finally {
                if (saveButton) saveButton.disabled = false;
            }
        });
    }

    const companyJobForm = document.getElementById("job-form");
    if (companyJobForm) {
        companyJobForm.addEventListener("submit", async function (event) {
            event.preventDefault();
            const token = localStorage.getItem("access");
            if (!token) {
                window.location.href = "index.html";
                return;
            }

            const values = Object.fromEntries(new FormData(companyJobForm));
            const payload = {
                job_title: values.jobTitle.trim(),
                description: values.jobDescription.trim(),
                job_type: values.employmentType,
                salary: values.jobPackage || null,
                job_location: values.jobLocation.trim(),
                minimum_cgpa: values.minCgpa,
                eligible_departments: values.eligibleDepartments.split(",").map((value) => value.trim()).filter(Boolean),
                eligible_courses: values.eligibleCourses.split(",").map((value) => value.trim()).filter(Boolean),
                application_deadline: new Date(`${values.applicationDeadline}T23:59:00`).toISOString(),
                status: values.jobStatus,
            };

            const statusElement = document.getElementById("job-form-status");
            const submitButton = document.getElementById("job-submit-button");
            if (submitButton) submitButton.disabled = true;
            setCompanyFeedback("job-form-status", "Submitting job for TPO review...");

            try {
                const editingJobId = companyJobForm.dataset.jobId;
                const data = await fetchAuthenticatedJson(
                    editingJobId ? `/company/jobs/${editingJobId}/` : "/company/jobs/",
                    token,
                    {
                        method: editingJobId ? "PATCH" : "POST",
                    body: JSON.stringify(payload),
                    }
                );
                companyJobForm.reset();
                setCompanyFeedback("job-form-status", data.message || "Job posted successfully.", "success");
                await loadCompanyDashboard();
            } catch (error) {
                console.error("Company job creation failed:", error);
                setCompanyFeedback(statusElement.id, error.message || "Unable to post job.", "error");
            } finally {
                if (submitButton) submitButton.disabled = false;
            }
        });
    }

    const scheduleInterviewForm = document.getElementById("schedule-interview-form");
    if (scheduleInterviewForm) {
        scheduleInterviewForm.addEventListener("submit", async function (event) {
            event.preventDefault();
            const token = localStorage.getItem("access");
            const applicationId = scheduleInterviewForm.dataset.applicationId;
            if (!token) {
                window.location.href = "index.html";
                return;
            }

            const values = Object.fromEntries(new FormData(scheduleInterviewForm));
            const payload = {
                round: Number(values.round),
                interview_type: values.interviewType,
                scheduled_at: new Date(`${values.interviewDate}T${values.interviewTime}`).toISOString(),
                meeting_link: values.meetingLink.trim(),
                venue: values.venue.trim(),
                interviewer: values.interviewer.trim(),
            };

            try {
                const data = await fetchAuthenticatedJson(`/company/applications/${applicationId}/interviews/`, token, {
                    method: "POST",
                    body: JSON.stringify(payload),
                });
                setCompanyModalOpen("company-schedule-modal", false);
                showToast(data.message || "Interview scheduled.");
                await loadCompanyDashboard();
            } catch (error) {
                console.error("Interview scheduling failed:", error);
                showToast(error.message || "Unable to schedule interview.", true);
            }
        });
    }

    const companyOfferForm = document.getElementById("company-offer-form");
    if (companyOfferForm) {
        companyOfferForm.addEventListener("submit", async function (event) {
            event.preventDefault();
            const token = localStorage.getItem("access");
            const applicationId = companyOfferForm.dataset.applicationId;
            if (!token) {
                window.location.href = "index.html";
                return;
            }

            const payload = Object.fromEntries(new FormData(companyOfferForm));
            try {
                const data = await fetchAuthenticatedJson(`/company/applications/${applicationId}/offer/`, token, {
                    method: "POST",
                    body: JSON.stringify(payload),
                });
                setCompanyModalOpen("company-offer-modal", false);
                showToast(data.message || "Offer issued successfully.");
                await loadCompanyDashboard();
            } catch (error) {
                console.error("Offer creation failed:", error);
                showToast(error.message || "Unable to issue offer.", true);
            }
        });
    }

    const studentSearch = document.getElementById("student-search");
    const tpoGlobalSearch = document.getElementById("tpo-global-search");
    if (tpoGlobalSearch) {
        tpoGlobalSearch.addEventListener("input", () => {
            if (!currentTpoDashboardData) return;
            renderTpoStudents(currentTpoDashboardData);
            renderTpoCompanies(currentTpoDashboardData);
            renderTpoJobs(currentTpoDashboardData);
            renderTpoApplications(currentTpoDashboardData);
        });
    }

    const studentDepartmentFilter = document.getElementById("student-department-filter");
    const studentStatusFilter = document.getElementById("student-status-filter");
    [studentSearch, studentDepartmentFilter, studentStatusFilter].forEach((control) => {
        if (control) {
            control.addEventListener("input", () => {
                if (currentTpoDashboardData) renderTpoStudents(currentTpoDashboardData);
            });
            control.addEventListener("change", () => {
                if (currentTpoDashboardData) renderTpoStudents(currentTpoDashboardData);
            });
        }
    });

    document.querySelectorAll("#company-filters .filter-tab").forEach((button) => {
        button.addEventListener("click", function () {
            document.querySelectorAll("#company-filters .filter-tab").forEach((tab) => {
                tab.classList.toggle("is-active", tab === button);
            });
            if (currentTpoDashboardData) renderTpoCompanies(currentTpoDashboardData);
        });
    });

    const createDriveButton = document.querySelector('[data-action="create-drive"]');
    if (createDriveButton) {
        createDriveButton.addEventListener("click", () => {
            if (currentTpoDashboardData) openPlacementDriveForm(currentTpoDashboardData);
        });
    }

    const markNotificationsReadButton = document.querySelector('[data-action="mark-notifications-read"]');
    if (markNotificationsReadButton) {
        markNotificationsReadButton.addEventListener("click", async function () {
            try {
                await fetchAuthenticatedJson("/notifications/read-all/", localStorage.getItem("access"), { method: "PATCH" });
                await loadTpoDashboard();
            } catch (error) {
                showToast(error.message || "Unable to update notifications.", true);
            }
        });
    }

    const tpoModalClose = document.getElementById("tpo-modal-close");
    if (tpoModalClose) tpoModalClose.addEventListener("click", closeTpoModal);
    const tpoModal = document.getElementById("tpo-modal");
    if (tpoModal) {
        tpoModal.addEventListener("click", function (event) {
            if (event.target === tpoModal) closeTpoModal();
        });
    }

    [
        ["[data-section]", "data-section"],
        ["[data-company-section]", "data-company-section"],
        ["[data-tpo-section]", "data-tpo-section"],
    ].forEach(([selector, attribute]) => {
        document.querySelectorAll(selector).forEach((button) => {
            button.addEventListener("click", function () {
                const target = document.getElementById(button.getAttribute(attribute));
                if (target) {
                    target.scrollIntoView({ behavior: "smooth", block: "start" });
                    document.body.classList.remove("sidebar-open");
                    document.querySelectorAll(".mobile-menu-toggle").forEach((toggle) => {
                        toggle.setAttribute("aria-expanded", "false");
                    });
                }
            });
        });
    });

    document.querySelectorAll(".mobile-menu-toggle").forEach((toggle) => {
        toggle.addEventListener("click", () => {
            const isOpen = document.body.classList.toggle("sidebar-open");
            toggle.setAttribute("aria-expanded", String(isOpen));
            toggle.setAttribute("aria-label", isOpen ? "Close menu" : "Open menu");
        });
    });

    [
        ["schedule-modal-close", "schedule-modal-cancel", "company-schedule-modal"],
        ["company-offer-close", "company-offer-cancel", "company-offer-modal"],
    ].forEach(([closeId, cancelId, modalId]) => {
        [closeId, cancelId].forEach((buttonId) => {
            const button = document.getElementById(buttonId);
            if (button) button.addEventListener("click", () => setCompanyModalOpen(modalId, false));
        });
    });

    if (resetPasswordForm) {
        const params = new URLSearchParams(window.location.search);
        const token = params.get("token");
        const email = params.get("email");
        const emailInput = document.getElementById("reset-email");
        const status = document.getElementById("reset-status");
        const submitButton = resetPasswordForm.querySelector('button[type="submit"]');

        if (emailInput) emailInput.value = email || "";

        if (!token || !email) {
            setStatusMessage(status, "This password reset link is invalid or has expired.", "error");
            if (submitButton) submitButton.disabled = true;
        }

        resetPasswordForm.addEventListener("submit", async function (event) {
            event.preventDefault();

            const password = document.getElementById("reset-password")?.value || "";
            const passwordConfirm = document.getElementById("reset-password-confirm")?.value || "";

            if (!password || !passwordConfirm) {
                setStatusMessage(status, "Please enter and confirm your new password.", "error");
                return;
            }

            if (password !== passwordConfirm) {
                setStatusMessage(status, "Passwords do not match.", "error");
                return;
            }

            if (!token || !email) {
                setStatusMessage(status, "This password reset link is invalid or has expired.", "error");
                return;
            }

            setStatusMessage(status, "Resetting your password...");

            try {
                const response = await fetch(`${API_BASE_URL}/auth/password/reset/`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        email,
                        token,
                        password,
                        password_confirm: passwordConfirm,
                    }),
                });

                const data = await response.json().catch(() => ({}));
                if (!response.ok) {
                    throw new Error(getErrorMessage(data, "Unable to reset the password."));
                }

                setStatusMessage(status, data.detail || "Password reset successful. You can now sign in.", "success");
                resetPasswordForm.reset();

                const backLink = document.getElementById("reset-back-login");
                if (backLink) {
                    backLink.href = "index.html";
                }
            } catch (error) {
                console.error("Password reset failed:", error);
                setStatusMessage(status, error.message || "Unable to reset the password.", "error");
            }
        });
    }

    if (passwordToggle && passwordInput) {
        passwordToggle.addEventListener("click", function () {
            const shouldShow = passwordInput.type === "password";
            passwordInput.type = shouldShow ? "text" : "password";
            passwordToggle.textContent = shouldShow ? "🙈" : "👁️";
        });
    }

    if (showRegistration) {
        showRegistration.addEventListener("click", function (event) {
            event.preventDefault();
            roleManager.showRegistrationForm();
        });
    }

    if (showLogin) {
        showLogin.addEventListener("click", function (event) {
            event.preventDefault();
            roleManager.returnToLogin();
        });
    }

    if (companyShowLogin) {
        companyShowLogin.addEventListener("click", function (event) {
            event.preventDefault();
            roleManager.returnToLogin();
        });
    }

    if (tpoShowLogin) {
        tpoShowLogin.addEventListener("click", function (event) {
            event.preventDefault();
            roleManager.returnToLogin();
        });
    }

    if (forgotPasswordButton) {
        forgotPasswordButton.addEventListener("click", function (event) {
            event.preventDefault();

            const loginPanel = document.getElementById("login-panel");
            const registrationPanel = document.getElementById("registration-panel");

            if (loginPanel) loginPanel.hidden = true;
            if (registrationPanel) registrationPanel.hidden = true;
            if (forgotPasswordPanel) forgotPasswordPanel.hidden = false;
        });
    }

    if (forgotBackLogin) {
        forgotBackLogin.addEventListener("click", function (event) {
            event.preventDefault();
            const loginPanel = document.getElementById("login-panel");
            const forgotPanel = document.getElementById("forgot-password-panel");
            if (loginPanel) loginPanel.hidden = false;
            if (forgotPanel) forgotPanel.hidden = true;
        });
    }

    if (forgotPasswordForm) {
        forgotPasswordForm.addEventListener("submit", async function (event) {
            event.preventDefault();

            const emailInput = document.getElementById("forgot-email");
            const status = document.getElementById("forgot-status");
            const email = emailInput ? emailInput.value.trim() : "";

            if (!email) {
                setStatusMessage(status, "Please enter your email address.", "error");
                return;
            }

            setStatusMessage(status, "Sending password reset link...");

            try {
                const response = await fetch(`${API_BASE_URL}/auth/password/forgot/`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email }),
                });

                const data = await response.json().catch(() => ({}));
                if (!response.ok) {
                    throw new Error(getErrorMessage(data, "Unable to process password reset request."));
                }

                const message = data.detail || "If an account exists for this email, a password reset link has been sent.";
                setStatusMessage(status, message, "success");
            } catch (error) {
                console.error("Forgot password request failed:", error);
                setStatusMessage(status, error.message || "Unable to process password reset request.", "error");
            }
        });
    }

    if (loginForm) {
        loginForm.addEventListener("submit", async function (event) {
            event.preventDefault();

            const identifier = document.getElementById("identifier")?.value.trim();
            const passwordValue = document.getElementById("password")?.value.trim();
            const formStatus = document.getElementById("form-status");

            if (!identifier || !passwordValue) {
                setStatusMessage(formStatus, "Please enter your email or student ID and password.", "error");
                return;
            }

            const isEmailIdentifier = identifier.includes("@") || /\s/.test(identifier);
            if (isEmailIdentifier && !isValidEmailAddress(identifier)) {
                setStatusMessage(formStatus, "Please enter a valid email address.", "error");
                return;
            }

            setStatusMessage(formStatus, "Signing in...");

            try {
                const response = await fetch(`${API_BASE_URL}/auth/login/`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ identifier, password: passwordValue }),
                });

                const data = await response.json().catch(() => ({}));

                if (!response.ok) {
                    throw new Error(getErrorMessage(data, "Invalid login details."));
                }

                localStorage.setItem("access", data.access || "");
                localStorage.setItem("refresh", data.refresh || "");
                localStorage.setItem("currentUser", JSON.stringify(data.user || {}));
                localStorage.setItem("loggedInUser", identifier);

                const userRole = (data.user && data.user.role) || roleManager.getSelectedRole();
                localStorage.setItem("userRole", userRole);

                setStatusMessage(formStatus, "Login successful. Opening dashboard...", "success");

                setTimeout(function () {
                    if (userRole === "STUDENT") {
                        window.location.href = "student-dashboard.html";
                    } else if (userRole === "COMPANY") {
                        window.location.href = "company-dashboard.html";
                    } else if (userRole === "TPO") {
                        window.location.href = "tpo-dashboard.html";
                    } else {
                        setStatusMessage(formStatus, "Unknown account role.", "error");
                    }
                }, 300);
            } catch (error) {
                console.error("Login request failed:", error);
                setStatusMessage(formStatus, error.message || "Unable to connect to the server.", "error");
            }
        });
    }

    const studentForm = document.getElementById("registration-form");
    if (studentForm) {
        studentForm.addEventListener("submit", async function (event) {
            event.preventDefault();

            const payload = {
                first_name: studentForm.querySelector('[name="first_name"]').value.trim(),
                last_name: studentForm.querySelector('[name="last_name"]').value.trim(),
                email: studentForm.querySelector('[name="email"]').value.trim(),
                student_id: studentForm.querySelector('[name="student_id"]')?.value.trim() || "",
                phone_number: studentForm.querySelector('[name="phone_number"]')?.value.trim() || "",
                password: studentForm.querySelector('[name="password"]').value,
                password_confirm: studentForm.querySelector('[name="password_confirm"]').value,
                department: studentForm.querySelector('[name="department"]').value.trim(),
                course: studentForm.querySelector('[name="course"]').value.trim(),
                year: Number(studentForm.querySelector('[name="year"]').value),
                cgpa: Number(studentForm.querySelector('[name="cgpa"]').value),
                skills: studentForm.querySelector('[name="skills"]').value.trim(),
            };

            const statusElement = document.getElementById("registration-status");
            if (!payload.first_name || !payload.last_name || !payload.email || !payload.student_id || !payload.password || !payload.password_confirm || !payload.department || !payload.course || !payload.year || !payload.cgpa || !payload.skills) {
                setStatusMessage(statusElement, "Please complete all student registration fields.", "error");
                return;
            }

            if (payload.password !== payload.password_confirm) {
                setStatusMessage(statusElement, "Passwords do not match.", "error");
                return;
            }

            setStatusMessage(statusElement, "Creating student account...");

            try {
                const response = await fetch(`${API_BASE_URL}/auth/register/student/`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload),
                });

                const data = await response.json().catch(() => ({}));

                if (!response.ok) {
                    throw new Error(getErrorMessage(data, "Student registration failed."));
                }

                studentForm.reset();
                setStatusMessage(statusElement, data.message || "Student account created successfully. You can now sign in.", "success");
                showToast("Student account created successfully.");
            } catch (error) {
                console.error("Student registration failed:", error);
                setStatusMessage(statusElement, error.message || "Unable to create student account.", "error");
            }
        });
    }

    const companyForm = document.getElementById("company-registration-form");
    if (companyForm) {
        companyForm.addEventListener("submit", async function (event) {
            event.preventDefault();

            const payload = {
                first_name: companyForm.querySelector('[name="first_name"]').value.trim(),
                last_name: companyForm.querySelector('[name="last_name"]').value.trim(),
                email: companyForm.querySelector('[name="email"]').value.trim(),
                password: companyForm.querySelector('[name="password"]').value,
                password_confirm: companyForm.querySelector('[name="password_confirm"]').value,
                company_name: companyForm.querySelector('[name="company_name"]').value.trim(),
                company_description: companyForm.querySelector('[name="company_description"]').value.trim(),
                industry: companyForm.querySelector('[name="industry"]').value.trim(),
                location: companyForm.querySelector('[name="location"]').value.trim(),
                contact_email: companyForm.querySelector('[name="contact_email"]').value.trim(),
                contact_phone: companyForm.querySelector('[name="contact_phone"]').value.trim(),
                company_size: companyForm.querySelector('[name="company_size"]').value,
            };

            const statusElement = document.getElementById("company-registration-status");
            if (!payload.first_name || !payload.last_name || !payload.email || !payload.password || !payload.password_confirm || !payload.company_name || !payload.company_description || !payload.industry || !payload.location || !payload.contact_email || !payload.contact_phone || !payload.company_size) {
                setStatusMessage(statusElement, "Please complete all company registration fields.", "error");
                return;
            }

            if (payload.password !== payload.password_confirm) {
                setStatusMessage(statusElement, "Passwords do not match.", "error");
                return;
            }

            setStatusMessage(statusElement, "Creating company account...");

            try {
                const response = await fetch(`${API_BASE_URL}/auth/register/company/`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload),
                });

                const data = await response.json().catch(() => ({}));

                if (!response.ok) {
                    throw new Error(getErrorMessage(data, "Company registration failed."));
                }

                companyForm.reset();
                setStatusMessage(statusElement, data.message || "Company account created successfully. You can now sign in.", "success");
                showToast("Company account created successfully.");
            } catch (error) {
                console.error("Company registration failed:", error);
                setStatusMessage(statusElement, error.message || "Unable to create company account.", "error");
            }
        });
    }

    const editButton = document.querySelector("#profile-section .secondary-button.small");
    const editModal = document.getElementById("edit-profile-modal");
    const editForm = document.getElementById("edit-profile-form");
    const editClose = document.getElementById("edit-profile-close");
    const editCancel = document.getElementById("edit-profile-cancel");

    function openEditProfileModal() {
        const profileValues = {
            department: document.getElementById("profile-department")?.textContent || "",
            course: document.getElementById("profile-course")?.textContent || "",
            year: document.getElementById("profile-year")?.textContent || "",
            cgpa: document.getElementById("profile-cgpa")?.textContent || "",
            skills: document.getElementById("profile-skills")?.textContent || "",
        };

        document.getElementById("edit-department").value = profileValues.department === "-" ? "" : profileValues.department;
        document.getElementById("edit-course").value = profileValues.course === "-" ? "" : profileValues.course;
        document.getElementById("edit-year").value = profileValues.year === "-" ? "" : profileValues.year;
        document.getElementById("edit-cgpa").value = profileValues.cgpa === "-" ? "" : profileValues.cgpa;
        document.getElementById("edit-skills").value = profileValues.skills === "-" ? "" : profileValues.skills;

        if (editModal) {
            editModal.classList.add("is-open");
            editModal.setAttribute("aria-hidden", "false");
        }

        setStatusMessage(document.getElementById("edit-profile-status"), "", "info");
    }

    function closeEditProfileModal() {
        if (editModal) {
            editModal.classList.remove("is-open");
            editModal.setAttribute("aria-hidden", "true");
        }
    }

    if (companyJobForm) {
        companyJobForm.addEventListener("reset", () => {
            window.setTimeout(() => {
                delete companyJobForm.dataset.jobId;
                const submitButton = document.getElementById("job-submit-button");
                if (submitButton) submitButton.textContent = "Create Job";
            }, 0);
        });
    }

    if (editButton) {
        editButton.addEventListener("click", openEditProfileModal);
    }

    if (editClose) {
        editClose.addEventListener("click", closeEditProfileModal);
    }

    if (editCancel) {
        editCancel.addEventListener("click", closeEditProfileModal);
    }

    if (editModal) {
        editModal.addEventListener("click", function (event) {
            if (event.target === editModal) {
                closeEditProfileModal();
            }
        });
    }

    if (editForm) {
        editForm.addEventListener("submit", async function (event) {
            event.preventDefault();

            const token = localStorage.getItem("access");
            if (!token) {
                logoutUser();
                return;
            }

            const payload = {
                department: document.getElementById("edit-department").value.trim(),
                course: document.getElementById("edit-course").value.trim(),
                year: Number(document.getElementById("edit-year").value),
                cgpa: Number(document.getElementById("edit-cgpa").value),
                skills: document.getElementById("edit-skills").value.trim(),
            };

            const statusElement = document.getElementById("edit-profile-status");
            if (!payload.department || !payload.course || !payload.year || !payload.cgpa || !payload.skills) {
                setStatusMessage(statusElement, "Please fill in all profile fields before saving.", "error");
                return;
            }

            setStatusMessage(statusElement, "Saving profile update...");

            try {
                const profileData = new FormData();
                Object.entries(payload).forEach(([key, value]) => profileData.append(key, String(value)));
                const resumeFile = document.getElementById("edit-resume")?.files?.[0];
                if (resumeFile) profileData.append("resume", resumeFile);

                const data = await fetchAuthenticatedJson("/student/profile/", token, {
                    method: "PATCH",
                    body: profileData,
                });

                const profile = data.profile || data;
                renderStudentProfile(profile);
                closeEditProfileModal();
                showToast("Profile updated successfully.");
            } catch (error) {
                console.error("Profile update failed:", error);
                setStatusMessage(statusElement, error.message || "Unable to update profile.", "error");
            }
        });
    }

    document.querySelectorAll('[data-action="logout"]').forEach(function (button) {
        button.addEventListener("click", function () {
            logoutUser();
        });
    });

    loadCompanyDashboard();
    loadStudentDashboard();
    loadStudentPlacementData();
    loadTpoDashboard();
    loadNotificationBadge("student-notification-badge");
    loadNotificationBadge("company-notification-badge");
});