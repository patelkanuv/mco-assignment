document.addEventListener("DOMContentLoaded", () => {
    const API_BASE_URL = window.APP_CONFIG?.BACKEND_API_URL || "http://127.0.0.1:5001";

    const stockListContainer = document.getElementById("stockListContainer");
    const stockTableBody = document.getElementById("stockTableBody");

    // --- Load existing stocks on page load ---
    loadStocks();

    async function loadStocks() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/stocks`);
            if (!response.ok) {
                throw new Error(`Server responded with status ${response.status}`);
            }
            const stocks = await response.json();
            renderStockList(stocks);
        } catch (error) {
            // Backend unreachable or no data yet — keep the list hidden, fail quietly.
            console.error("Failed to load stocks:", error);
        }
    }

    function renderStockList(stocks) {
        stockTableBody.innerHTML = "";

        if (!Array.isArray(stocks) || stocks.length === 0) {
            stockListContainer.classList.add("hidden");
            return;
        }

        stocks.forEach((stock) => addStockRow(stock));
        stockListContainer.classList.remove("hidden");
    }

    function updateListVisibility() {
        const hasRows = stockTableBody.children.length > 0;
        stockListContainer.classList.toggle("hidden", !hasRows);
    }

    // --- Toggle: show/hide the Add Stock panel ---
    const toggleBtn = document.getElementById("addStockToggleBtn");
    const stockPanel = document.getElementById("stockPanel");
    const backToHomeBtn = document.getElementById("backToHomeBtn");
    const closeStockPanelBtn = document.getElementById("closeStockPanelBtn");

    toggleBtn.addEventListener("click", () => {
        if (stockPanel.classList.contains("hidden")) {
            openStockPanel();
        } else {
            closeStockPanel();
        }
    });

    backToHomeBtn.addEventListener("click", () => {
        closeStockPanel();
    });

    closeStockPanelBtn.addEventListener("click", () => {
        closeStockPanel();
    });

    function openStockPanel() {
        stockPanel.classList.remove("hidden");
        toggleBtn.textContent = "Close";
    }

    function closeStockPanel() {
        stockPanel.classList.add("hidden");
        toggleBtn.textContent = "Add Stock";
        document.getElementById("homeTop").scrollIntoView({ behavior: "smooth" });
    }

    // --- Add Stock form ---
    const stockForm = document.getElementById("stockForm");
    const stockFormStatus = document.getElementById("stockFormStatus");

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
            addStockRow(data);
            updateListVisibility();
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

    // --- Row rendering (view mode) ---
    function addStockRow(stock) {
        const row = buildViewRow(stock);
        stockTableBody.prepend(row);
    }

    function buildViewRow(stock) {
        const row = document.createElement("tr");
        row.dataset.id = stock.id;
        row.innerHTML = `
            <td>${escapeHtml(stock.name)}</td>
            <td>${stock.quantity}</td>
            <td>${Number(stock.price).toFixed(2)}</td>
            <td>${stock.purchase_date}</td>
            <td>${escapeHtml(stock.category || "-")}</td>
            <td class="actions-cell">
                <button type="button" class="row-btn edit-btn">Edit</button>
                <button type="button" class="row-btn delete-btn">Delete</button>
            </td>
        `;

        row.querySelector(".edit-btn").addEventListener("click", () => {
            row.replaceWith(buildEditRow(stock, row));
        });

        row.querySelector(".delete-btn").addEventListener("click", () => {
            handleDelete(stock.id, row);
        });

        return row;
    }

    // --- Row rendering (edit mode) ---
    function buildEditRow(stock) {
        const row = document.createElement("tr");
        row.dataset.id = stock.id;
        row.innerHTML = `
            <td><input type="text" class="edit-input edit-name" value="${escapeAttr(stock.name)}"></td>
            <td><input type="number" class="edit-input edit-quantity" min="0" step="1" value="${stock.quantity}"></td>
            <td><input type="number" class="edit-input edit-price" min="0" step="0.01" value="${stock.price}"></td>
            <td><input type="date" class="edit-input edit-date" value="${stock.purchase_date}"></td>
            <td><input type="text" class="edit-input edit-category" value="${escapeAttr(stock.category || "")}"></td>
            <td class="actions-cell">
                <button type="button" class="row-btn save-btn">Save</button>
                <button type="button" class="row-btn cancel-btn">Cancel</button>
            </td>
        `;

        row.querySelector(".save-btn").addEventListener("click", () => {
            handleUpdate(stock.id, row);
        });

        row.querySelector(".cancel-btn").addEventListener("click", () => {
            row.replaceWith(buildViewRow(stock));
        });

        return row;
    }

    async function handleUpdate(stockId, row) {
        const payload = {
            name: row.querySelector(".edit-name").value.trim(),
            quantity: Number(row.querySelector(".edit-quantity").value),
            price: Number(row.querySelector(".edit-price").value),
            purchase_date: row.querySelector(".edit-date").value,
            category: row.querySelector(".edit-category").value.trim() || null,
        };

        try {
            const response = await fetch(`${API_BASE_URL}/api/stocks/${stockId}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });

            const data = await response.json().catch(() => null);

            if (!response.ok) {
                const errorMsg = data?.error || `Server responded with status ${response.status}`;
                throw new Error(errorMsg);
            }

            row.replaceWith(buildViewRow(data));
        } catch (error) {
            alert(`Failed to update stock: ${error.message}`);
            console.error("Update stock failed:", error);
        }
    }

    async function handleDelete(stockId, row) {
        if (!confirm("Delete this stock item?")) {
            return;
        }

        try {
            const response = await fetch(`${API_BASE_URL}/api/stocks/${stockId}`, {
                method: "DELETE",
            });

            const data = await response.json().catch(() => null);

            if (!response.ok) {
                const errorMsg = data?.error || `Server responded with status ${response.status}`;
                throw new Error(errorMsg);
            }

            row.remove();
            updateListVisibility();
        } catch (error) {
            alert(`Failed to delete stock: ${error.message}`);
            console.error("Delete stock failed:", error);
        }
    }

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str;
        return div.innerHTML;
    }

    function escapeAttr(str) {
        return String(str).replace(/"/g, "&quot;");
    }
});