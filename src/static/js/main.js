import { getCurrentUser, setToken, logout, clearUserCache } from '/static/js/auth.js';
import { getErrorMessage, showModal, hideModal } from '/static/js/utils.js';

export function showFeedbackModal(modalId, messageId, messageText) {
    if (messageId && messageText) {
        const messageElement = document.getElementById(messageId);
        if (messageElement) {
            messageElement.textContent = messageText;
        }
    }
    showModal(modalId);
}

document.addEventListener("DOMContentLoaded", async () => {
    const loginForm = document.getElementById("loginForm");
    const openModalBtn = document.getElementById("open-modal-btn");
    const accountBtn = document.getElementById("account-btn");
    const logoutBtn = document.getElementById("logout-btn");
    const loginBtn = document.getElementById("login-btn");

    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('login') === 'true') {
        showModal('loginModal');
        window.history.replaceState({}, document.title, window.location.pathname);
    }

    async function updateUI() {
        const user = await getCurrentUser();

        if (user) {
            if (loginBtn) loginBtn.style.display = "none";
            if (logoutBtn) logoutBtn.style.display = "inline-block";
            if (accountBtn) accountBtn.style.display = "inline-block";

            if (openModalBtn) {
                openModalBtn.style.display = (user.role === "admin" || user.is_admin === true)
                    ? "inline-block"
                    : "none";
            }
        } else {
            if (loginBtn) loginBtn.style.display = "inline-block";
            if (logoutBtn) logoutBtn.style.display = "none";
            if (accountBtn) accountBtn.style.display = "none";
            if (openModalBtn) openModalBtn.style.display = "none";
        }
    }

    await updateUI();

    if (logoutBtn) {
        logoutBtn.addEventListener("click", () => logout());
    }

    if (loginForm) {
        loginForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const emailInput = document.getElementById("email");
            const passwordInput = document.getElementById("password");
            if (!emailInput || !passwordInput) return;

            const formData = new URLSearchParams();
            formData.append("username", emailInput.value);
            formData.append("password", passwordInput.value);

            try {
                const response = await fetch("/api/users/token", {
                    method: "POST",
                    headers: { "Content-Type": "application/x-www-form-urlencoded" },
                    body: formData
                });

                if (response.ok) {
                    const data = await response.json();
                    setToken(data.access_token);
                    clearUserCache();
                    hideModal('loginModal');
                    loginForm.reset();
                    await updateUI();
                } else {
                    hideModal('loginModal');
                    const errorData = await response.json().catch(() => ({}));
                    const mensagem = errorData.detail ? getErrorMessage(errorData) : "Credenciais inválidas.";
                    showFeedbackModal('errorModal', 'errorMessage', mensagem);
                }
            } catch (error) {
                console.error("Erro na requisição de login:", error);
                hideModal('loginModal');
                showFeedbackModal('errorModal', 'errorMessage', 'Erro de comunicação com o servidor.');
            }
        });
    }
});
