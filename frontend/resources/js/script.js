document.addEventListener("DOMContentLoaded", () => {
    const API_BASE_URL = window.APP_CONFIG?.BACKEND_API_URL || "http://127.0.0.1:5001";

    // --- Toggle: show/hide the Add Stock panel ---
    const toggleBtn = document.getElementById("addStockToggleBtn");
    const stockPanel = document.getElementById("stockPanel");

    toggleBtn.addEventListener("click", () => {
        const isHidden = stockPanel.classList.toggle("hidden");
        toggleBtn.textContent = isHidden ? "Add Stock" : "Close";
    });

    // --- Add Stock form ---
    const stockForm = document.getElementById("stockForm");
    const stockFormStatus = document.getElementById("stockFormStatus");
    const stockTable = document.getElementById("stockTable");
    const stockTableBody = document.getElementById("stockTableBody");

    stockForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const payload = {
            name: document.getElementById("stockName").value.trim(),
            quantity: Number(document.getElementById("quantity").value),
            price: Number(document.getElementById("price").value),
            purchase_date: document.getElementById("purchaseDate").value,
            category: document.getElementById("category").value.trim() || null,
        };

        setStockStatus("Adding stock...", null);

        try {
            const response = await fetch(`${API_BASE_URL}/api/stocks`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });

            const data = await response.json().catch(() => null);

            if (!response.ok) {
                const errorMsg = data?.error || `Server responded with status ${response.status}`;
                throw new Error(errorMsg);
            }

            setStockStatus(`Added "${payload.name}" to inventory.`, "success");
            addStockRow(payload);
            stockForm.reset();
        } catch (error) {
            setStockStatus(`Failed to add stock: ${error.message}`, "error");
            console.error("Add stock failed:", error);
        }
    });

    function setStockStatus(text, type) {
        stockFormStatus.textContent = text;
        stockFormStatus.className = "status-message" + (type ? ` ${type}` : "");
    }

    function addStockRow(stock) {
        stockTable.classList.remove("hidden");
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${escapeHtml(stock.name)}</td>
            <td>${stock.quantity}</td>
            <td>${stock.price.toFixed(2)}</td>
            <td>${stock.purchase_date}</td>
            <td>${escapeHtml(stock.category || "-")}</td>
        `;
        stockTableBody.prepend(row);
    }

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str;
        return div.innerHTML;
    }
});