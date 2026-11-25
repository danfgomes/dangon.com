import { getToken } from '/static/js/auth.js';
import { getErrorMessage, hideModal } from '/static/js/utils.js';
import { showFeedbackModal } from '/static/js/main.js';

document.addEventListener("DOMContentLoaded", () => {
    const createPostForm = document.getElementById("createPostForm");
    const publishBtn = document.querySelector(".publish-btn");
    if (!createPostForm) return;

    createPostForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const token = getToken();
        const formData = new FormData(createPostForm);

        if (publishBtn) {
            publishBtn.disabled = true;
            publishBtn.innerText = "Publicando...";
        }

        try {
            const response = await fetch("/api/posts/", {
                method: "POST",
                headers: { "Authorization": `Bearer ${token}` },
                body: formData
            });

            hideModal('createPostModal');

            if (response.ok) {
                createPostForm.reset();
                showFeedbackModal('successModal', 'successMessage', 'Publicação criada com sucesso!');
                setTimeout(() => { window.location.reload(); }, 2000);
            } else {
                const errorData = await response.json().catch(() => ({}));
                const mensagem = errorData.detail ? getErrorMessage(errorData) : "Erro ao publicar.";
                showFeedbackModal('errorModal', 'errorMessage', mensagem);
            }
        } catch (error) {
            console.error("Erro fatal na requisição POST:", error);
            hideModal('createPostModal');
            showFeedbackModal('errorModal', 'errorMessage', 'Falha na comunicação com o servidor.');
        } finally {
            if (publishBtn) {
                publishBtn.disabled = false;
                publishBtn.innerHTML = "Publicar &rarr;";
            }
        }
    });
});
