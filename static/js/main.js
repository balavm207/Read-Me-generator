document.addEventListener("DOMContentLoaded", () => {
    const folderInput = document.getElementById("folderInput");
    const scanBtn = document.getElementById("scanBtn");
    const statusDiv = document.getElementById("status");
    const outputArea = document.getElementById("outputArea");
    const downloadBtn = document.getElementById("downloadBtn");

    let currentFiles = [];

    const MANIFEST_NAMES = new Set([
        "package.json", "requirements.txt", "pyproject.toml",
        "license", "license.txt", "license.md", "dockerfile",
        "docker-compose.yml"
    ]);

    folderInput.addEventListener("change", (e) => {
        currentFiles = Array.from(e.target.files);
        if (currentFiles.length > 0) {
            statusDiv.textContent = `Selected directory with ${currentFiles.length} files. Ready to analyze.`;
        }
    });

    scanBtn.addEventListener("click", async () => {
        if (!currentFiles.length) {
            alert("Please choose a project folder first.");
            return;
        }

        scanBtn.disabled = true;
        statusDiv.textContent = "Agent Step 1: Scanning file paths & inspecting manifest files...";

        try {
            const paths = currentFiles.map(f => f.webkitRelativePath || f.name);
            const projectName = paths[0]?.split("/")[0] || "My Project";

            const manifests = {};
            for (const file of currentFiles) {
                const baseName = file.name.toLowerCase();
                if (MANIFEST_NAMES.has(baseName) && file.size < 100 * 1024) {
                    manifests[file.webkitRelativePath] = await file.text();
                }
            }

            statusDiv.textContent = "Agent Step 2: Synthesizing facts, drafting README, and validating claims...";

            const response = await fetch("/api/scan", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ paths, manifests, projectName })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Generation failed.");
            }

            outputArea.value = data.readme;
            downloadBtn.disabled = false;

            if (data.validation?.was_rectified) {
                statusDiv.textContent = `Complete. Agent rectified ${data.validation.flaws_removed.length} unverified assumptions during validation.`;
            } else {
                statusDiv.textContent = `Complete. README generated and verified against project facts. (License: ${data.license})`;
            }

        } catch (err) {
            statusDiv.textContent = `Error: ${err.message}`;
        } finally {
            scanBtn.disabled = false;
        }
    });

    downloadBtn.addEventListener("click", () => {
        const blob = new Blob([outputArea.value], { type: "text/markdown" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "README.md";
        a.click();
        URL.revokeObjectURL(url);
    });
});