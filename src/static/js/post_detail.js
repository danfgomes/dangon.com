import { getCurrentUser, getToken } from './auth.js';

document.addEventListener("DOMContentLoaded", async () => {
    const deletePostBtn = document.getElementById("delete-post-btn");

    if (deletePostBtn) {
        // Busca o usuário validado pelo backend em vez de ler o token bruto
        const user = await getCurrentUser();

        if (user) {
            const authorId = deletePostBtn.getAttribute("data-author-id");
            const userId = user.id;

            const isOwner = String(userId) === String(authorId);
            const isAdmin = user.role === "admin" || user.is_admin === true;

            if (isOwner && isAdmin) {
                deletePostBtn.style.display = "inline-block";
            }
        }

        deletePostBtn.addEventListener("click", async () => {
            const confirmacao = confirm("Confirmar exclusão da publicação?");
            if (!confirmacao) return;

            deletePostBtn.disabled = true;
            deletePostBtn.innerText = "Excluindo...";

            const postId = deletePostBtn.getAttribute("data-post-id");
            const token = getToken();

            try {
                const response = await fetch(`/api/posts/${postId}`, {
                    method: "DELETE",
                    headers: { "Authorization": `Bearer ${token}` }
                });

                if (response.ok || response.status === 204) {
                    window.location.href = "/posts";
                } else {
                    alert("Erro ao excluir publicação. Verifique as suas permissões.");
                    deletePostBtn.disabled = false;
                    deletePostBtn.innerText = "Excluir Publicação";
                }
            } catch (error) {
                alert("Falha na comunicação com o servidor.");
                deletePostBtn.disabled = false;
                deletePostBtn.innerText = "Excluir Publicação";
            }
        });
    }
});