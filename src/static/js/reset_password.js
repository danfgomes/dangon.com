const form = document.getElementById("reset-password-form");
const newPasswordInput = document.getElementById("new-password");
const confirmPasswordInput = document.getElementById("confirm-password");
const submitBtn = document.getElementById("submit-btn");
const feedback = document.getElementById("feedback-message");

const urlParams = new URLSearchParams(window.location.search);
const token = urlParams.get("token");

if (!token) {
    feedback.classList.add("error");
    feedback.textContent = "Token de recuperação ausente ou inválido. Solicite um novo link.";
    submitBtn.disabled = true;
}

form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const newPassword = newPasswordInput.value;
    const confirmPassword = confirmPasswordInput.value;

    if (newPassword !== confirmPassword) {
        feedback.classList.add("error");
        feedback.textContent = "As senhas não coincidem.";
        return;
    }

    submitBtn.disabled = true;
    const originalText = submitBtn.querySelector("span").textContent;
    submitBtn.querySelector("span").textContent = "SALVANDO...";
    feedback.textContent = "";
    feedback.classList.remove("error");

    try {
        const response = await fetch("/api/users/reset-password", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                token: token,
                new_password: newPassword,
            }),
        });

        const data = await response.json();

        if (!response.ok) {
            feedback.classList.add("error");
            feedback.textContent = data.detail || "Token inválido ou expirado.";
            return;
        }

        feedback.textContent = "Senha redefinida com sucesso! Redirecionando...";
        form.reset();

        setTimeout(() => {
            window.location.href = "/";
        }, 2000);
    } catch (error) {
        feedback.classList.add("error");
        feedback.textContent = "Erro de conexão com o servidor. Tente novamente.";
    } finally {
        submitBtn.disabled = false;
        submitBtn.querySelector("span").textContent = originalText;
    }
});
