const form = document.getElementById("changePasswordForm");
const currentPasswordInput = document.getElementById("current_password");
const newPasswordInput = document.getElementById("new_password");
const confirmPasswordInput = document.getElementById("confirm_password");
const feedback = document.getElementById("password-feedback");
const submitBtn = document.getElementById("savePasswordBtn");

form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const currentPassword = currentPasswordInput.value;
    const newPassword = newPasswordInput.value;
    const confirmPassword = confirmPasswordInput.value;

    feedback.textContent = "";
    feedback.style.color = "";

    if (newPassword !== confirmPassword) {
        feedback.style.color = "#dc3545";
        feedback.textContent = "A nova senha e a confirmação não coincidem.";
        return;
    }

    submitBtn.disabled = true;
    const originalText = submitBtn.textContent;
    submitBtn.textContent = "Atualizando...";

    try {
        const token = localStorage.getItem("access_token");
        const headers = {
            "Content-Type": "application/json",
        };
        if (token) {
            headers["Authorization"] = `Bearer ${token}`;
        }

        const response = await fetch("/api/users/me/password", {
            method: "PATCH",
            headers: headers,
            credentials: "include",
            body: JSON.stringify({
                current_password: currentPassword,
                new_password: newPassword,
            }),
        });

        const data = await response.json();

        if (!response.ok) {
            feedback.style.color = "#dc3545";
            feedback.textContent = data.detail || "Não foi possível atualizar a senha.";
            return;
        }

        feedback.style.color = "#198754";
        feedback.textContent = "Senha atualizada com sucesso!";
        form.reset();
    } catch (error) {
        feedback.style.color = "#dc3545";
        feedback.textContent = "Erro de conexão com o servidor.";
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
    }
});
