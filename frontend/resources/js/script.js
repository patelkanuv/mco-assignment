
document.addEventListener("DOMContentLoaded", () => {
    const message = document.getElementById("message");
    const button = document.getElementById("clickBtn");
 
    const API_BASE_URL = "http://127.0.0.1:5001";
 
    button.addEventListener("click", async () => {
        message.style.color = "#764ba2";
        message.textContent = "Checking API health...";
 
        try {
            const response = await fetch(`${API_BASE_URL}/api/health`);
 
            if (!response.ok) {
                throw new Error(`Server responded with status ${response.status}`);
            }
 
            const data = await response.json();
            message.style.color = "#2ecc71";
            message.textContent = `API says: ${JSON.stringify(data)}`;
        } catch (error) {
            message.style.color = "#e74c3c";
            message.textContent = "Could not reach the API. Is it running on port 5001?";
            console.error("Health check failed:", error);
        }
    });
});