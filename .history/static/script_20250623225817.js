document.addEventListener("DOMContentLoaded", function () {
    console.log("DOM fully loaded");

    const themeToggle = document.querySelector(".theme-toggle");
    const uploadArea = document.getElementById("upload-area");
    const fileInput = document.getElementById("resume-files");
    const form = document.getElementById("resume-form");
    const resultsPanel = document.getElementById("results-panel");
    const resultsDiv = document.getElementById("results");
    const loading = document.getElementById("loading");
    const topNInput = document.getElementById("top-n");
    let lastResults = [];

    // Attach Clear All button handler first
    const clearBtn = document.getElementById("clear-btn");
    if (clearBtn) {
        clearBtn.addEventListener("click", clearAll);
    } else {
        console.error("Clear button not found!");
    }

    // Info modal handlers
    document.getElementById("info-btn").addEventListener("click", () => {
        document.getElementById("info-modal").style.display = "block";
    });

    document.getElementById("close-info").addEventListener("click", () => {
        document.getElementById("info-modal").style.display = "none";
    });

    window.addEventListener("click", (e) => {
        const modal = document.getElementById("info-modal");
        if (e.target === modal) {
            modal.style.display = "none";
        }
    });

    // Theme handling
    function applyTheme(theme) {
        if (theme === "light") {
            document.body.classList.remove("dark");
            document.body.classList.add("light");
            themeToggle.innerHTML = "🌞 Light";
        } else {
            document.body.classList.remove("light");
            document.body.classList.add("dark");
            themeToggle.innerHTML = "🌌 Dark";
        }
    }

    const savedTheme = localStorage.getItem("theme") || "dark";
    applyTheme(savedTheme);

    themeToggle.addEventListener("click", () => {
        const newTheme = document.body.classList.contains("light") ? "dark" : "light";
        localStorage.setItem("theme", newTheme);
        applyTheme(newTheme);
    });

    // File input handling
    uploadArea.addEventListener("click", () => fileInput.click());

    fileInput.addEventListener("change", (e) => {
        const files = e.target.files;
        const tooLarge = Array.from(files).some(file => file.size > 5 * 1024 * 1024);
        if (tooLarge) {
            alert("One or more files exceed 5MB. Please upload smaller files.");
            fileInput.value = ""; // Clear input
            uploadArea.innerHTML = `<p>No files selected</p>`;
            return;
        }
        uploadArea.innerHTML = `<p>${files.length} file(s) selected</p>`;
    });

    // Handle Top-N selector changes
    topNInput.addEventListener("change", () => {
        const newTopN = parseInt(topNInput.value, 10);
        if (lastResults.length > 0) {
            renderResults(lastResults, newTopN);
            resultsPanel.style.display = "block";
        }
    });

    // Lock/unlock form elements
    function lockForm(lock = true) {
        const inputs = document.querySelectorAll("#resume-files, #jd-text, .process-btn, #top-n");
        inputs.forEach(input => {
            input.disabled = lock;
        });
        if (uploadArea) {
            uploadArea.style.pointerEvents = lock ? "none" : "auto";
            uploadArea.style.opacity = lock ? "0.6" : "1";
        }
    }

    // Submit handler
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        lockForm(true);

        const files = fileInput.files;
        const jdText = document.getElementById("jd-text").value;
        const topN = topNInput.value;

        if (!files.length) {
            alert("Please upload at least one resume.");
            lockForm(false);
            return;
        }

        const formData = new FormData();
        for (let i = 0; i < files.length; i++) {
            formData.append("resume", files[i]);
        }
        formData.append("jd_text", jdText);
        formData.append("top_n", topN);

        // Reset preview panel
        document.getElementById("preview-panel").style.display = "none";
        document.getElementById("resume-preview").src = "";

        loading.style.display = "flex";
        document.getElementById("spinner-percent").innerText = "0%";
        resultsPanel.style.display = "none";
        resultsDiv.innerHTML = "";

        let currentStep = 0;
        const totalSteps = 100;
        const interval = setInterval(() => {
            currentStep++;
            const percent = Math.min(100, Math.round((currentStep / totalSteps) * 100));
            document.getElementById("spinner-percent").innerText = `${percent}%`;
            if (percent >= 100) clearInterval(interval);
        }, 30);

        try {
            const res = await fetch("/analyze", {
                method: "POST",
                body: formData,
            });

            if (!res.ok) {
                const errorData = await res.json();
                throw new Error(errorData.detail || "Failed to process resumes");
            }

            const allResults = await res.json();
            lastResults = allResults;
            const topNVal = parseInt(topNInput.value, 10);
            renderResults(lastResults, topNVal);

        } catch (err) {
            resultsDiv.innerHTML = `<p style='color:red;'>❌ ${err.message}</p>`;
            resultsPanel.style.display = "block";
        } finally {
            loading.style.display = "none";
            clearInterval(interval);
            document.getElementById("spinner-percent").innerText = "100%";
            lockForm(false);
        }
    });

    // Delegated click listeners
    document.addEventListener("click", function (event) {
        if (event.target.matches(".details-btn")) {
            const index = event.target.getAttribute("data-index");
            const detailsEl = document.getElementById(`details-${index}`);
            if (detailsEl) detailsEl.classList.toggle("show");
        } else if (event.target.matches(".export-btn")) {
            exportToCSV();
        }
    });

    // Render results
    function renderResults(data, topN) {
        const topResults = data.slice(0, topN);
        let html = "";
        if (!data || !Array.isArray(data)) {
            resultsDiv.innerHTML = "<p>No results to display.</p>";
            resultsPanel.style.display = "block";
            return;
        }

        topResults.forEach((res, i) => {
            html += `
                <div class="result-item">
                    <h3>
                        <span>${i + 1}. ${res.name || "Unknown"}</span>
                        <span class="match-score" style="color: ${
                            res.match_percent > 70 ? "#60a5fa" :
                            (res.match_percent >= 40 && res.match_percent <= 69) ? "#f97316" : "#ef4444"
                        }">${(res.match_percent || 0).toFixed(2)}%</span>
                    </h3>
                    <div class="stats-line">
                        ⭐ Skills: ${(res.skills_score || 0).toFixed(2)}% | 💼 Experience: ${(res.experience_score || 0).toFixed(2)}%
                    </div>
                    <div class="stats-line">
                        🎓 Education: ${(res.education_score || 0).toFixed(2)}% | 💻 Projects: ${(res.project_score || 0).toFixed(2)}%
                    </div>
                    <div class="button-group">
                        <button class="details-btn" data-index="${i}">Details</button>
                        <button class="download-btn" title="Download Resume" onclick="downloadOriginalResume('${res.original_file_url || "#"}')">⬇ Download</button>
                        <button class="preview-btn" title="Preview ${res.original_file_name}" onclick="previewOriginalResume('${res.original_file_url || "#"}')">🔍 Preview</button>
                    </div>
                    <div class="details-content" id="details-${i}">
                        <strong>📧 Email:</strong> ${res.email || "N/A"}<br/>
                        <strong>📞 Phone:</strong> ${res.phone || "N/A"}<br/>
                        <strong>🚫 Missing Skills:</strong>
                        <div class="missing-skills">${
                            Array.isArray(res.missing_skills) && res.missing_skills.length > 0
                                ? res.missing_skills.join(", ")
                                : "None"
                        }</div>
                    </div>
                </div>`;
        });

        resultsDiv.innerHTML = html;
        resultsPanel.style.display = "block";
    }

    // Global functions
    window.downloadOriginalResume = function (fileUrl) {
        if (!fileUrl || fileUrl === "#") {
            alert("Original file not available.");
            return;
        }
        const a = document.createElement("a");
        a.href = fileUrl;
        a.download = "";
        a.click();
        a.remove();
    };

    window.previewOriginalResume = function (fileUrl) {
        if (!fileUrl || fileUrl === "#") {
            alert("Original file not available.");
            return;
        }
        window.open(fileUrl, "_blank");
    };

    window.exportToCSV = function () {
        if (!lastResults || lastResults.length === 0) {
            alert("No results to export.");
            return;
        }

        const rows = [
            ["Rank", "Name", "Match %", "Email", "Phone", "Skills Score", "Experience Score", "Education Score", "Project Score", "Domain Match Score", "Missing Skills"]
        ];

        lastResults.slice(0, parseInt(topNInput.value, 10)).forEach((res, i) => {
            rows.push([
                i + 1,
                `"${res.name || "Unknown"}"`,
                (res.match_percent || 0).toFixed(2),
                res.email || "",
                res.phone || "",
                (res.skills_score || 0).toFixed(2),
                (res.experience_score || 0).toFixed(2),
                (res.education_score || 0).toFixed(2),
                (res.project_score || 0).toFixed(2),
                (res.domain_match_score || 0).toFixed(2),
                `"${(res.missing_skills || []).join(" | ") || ""}"`,
            ]);
        });

        const csvContent = "data:text/csv;charset=utf-8," + rows.map(r => r.join(",")).join("\n");
        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", "resume_analysis_results.csv");
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };
});

// Define clearAll globally so it can be called from HTML
window.clearAll = function () {
    console.log("CLEAR ALL CALLED ✅");
    if (!confirm("Are you sure you want to clear everything?")) return;

    const statusText = document.getElementById("status-text");
    const spinnerPercent = document.getElementById("spinner-percent");
    const uploadArea = document.getElementById("upload-area");

    // Clear form
    document.getElementById("resume-form").reset();

    // Clear status text and progress
    if (statusText) statusText.textContent = "";
    if (spinnerPercent) spinnerPercent.textContent = "0%";

    // Hide panels
    document.getElementById("results-panel").style.display = "none";
    document.getElementById("preview-panel").style.display = "none";

    // Clear result content
    document.getElementById("results").innerHTML = "";
    document.getElementById("resume-preview").src = "";

    // Reset upload area
    if (uploadArea) {
        uploadArea.innerHTML = `
            <p>
                Click to select files or drag and drop<br />Supports
                PDF, DOCX files up to 5MB each
            </p>
        `;
    }
};