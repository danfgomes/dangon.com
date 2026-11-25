import { getErrorMessage } from '/static/js/utils.js';
import { showFeedbackModal } from '/static/js/main.js';

document.addEventListener("DOMContentLoaded", () => {
    const cadastroForm = document.getElementById("cadastroForm");
    if (!cadastroForm) return;

    cadastroForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const formData = new FormData(cadastroForm);
        const payload = {
            username: formData.get("username"),
            email: formData.get("email"),
            password: formData.get("password")
        };

        const submitBtn = cadastroForm.querySelector(".create-button");
        if (submitBtn) submitBtn.disabled = true;

        try {
            const response = await fetch("/api/users/create", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            if (response.ok) {
                cadastroForm.reset();
                if (document.getElementById('successModal')) {
                    showFeedbackModal('successModal', 'successMessage', 'Conta criada com sucesso! Redirecionando...');
                    document.getElementById('successModal').addEventListener('hidden.bs.modal', () => {
                        window.location.href = "/";
                    }, { once: true });
                } else {
                    alert('Conta criada com sucesso!');
                    window.location.href = "/";
                }
                setTimeout(() => { window.location.href = "/"; }, 2500);
            } else {
                const errorData = await response.json().catch(() => ({}));
                const mensagem = errorData.detail ? getErrorMessage(errorData) : "Erro ao cadastrar usuário.";
                if (document.getElementById('errorModal')) {
                    showFeedbackModal('errorModal', 'errorMessage', mensagem);
                } else {
                    alert('Erro ao cadastrar: ' + mensagem);
                }
            }
        } catch (error) {
            console.error("Erro fatal na requisição de cadastro:", error);
            alert('Falha na comunicação com o servidor.');
        } finally {
            if (submitBtn) submitBtn.disabled = false;
        }
    });
});
