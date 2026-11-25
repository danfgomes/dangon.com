import { getCurrentUser, getToken, clearUserCache } from '/static/js/auth.js';
import { getErrorMessage } from '/static/js/utils.js';
import { showFeedbackModal } from '/static/js/main.js';

document.addEventListener("DOMContentLoaded", async () => {
    const updateProfileForm = document.getElementById('updateProfileForm');
    if (!updateProfileForm) return;

    const apiBaseUrl = '/api/users';
    const user = await getCurrentUser();

    if (!user) {
        window.location.href = "/?login=true";
        return;
    }

    const userId = user.id;
    const inputFullName = document.getElementById('full_name');
    const inputEmail = document.getElementById('email');
    const btnSalvar = document.getElementById('btn-salvar-perfil');

    if (inputFullName) inputFullName.value = user.full_name || user.username || '';
    if (inputEmail) inputEmail.value = user.email || '';

    updateProfileForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const token = getToken();
        const formData = new FormData(updateProfileForm);
        const payload = {
            username: formData.get("full_name"),
            email: formData.get("email")
        };

        try {
            if (btnSalvar) {
                btnSalvar.disabled = true;
                btnSalvar.textContent = 'Salvando...';
            }

            const response = await fetch(`${apiBaseUrl}/${userId}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(payload)
            });

            if (response.ok) {
                clearUserCache();
                showFeedbackModal('successModal', 'successMessage', 'Perfil atualizado com sucesso!');
            } else {
                const errorData = await response.json().catch(() => ({}));
                const mensagem = errorData.detail ? getErrorMessage(errorData) : "Erro ao atualizar perfil.";
                showFeedbackModal('errorModal', 'errorMessage', mensagem);
            }
        } catch (error) {
            console.error('Erro na atualização de perfil:', error);
            alert('Falha na comunicação com o servidor.');
        } finally {
            if (btnSalvar) {
                btnSalvar.disabled = false;
                btnSalvar.textContent = 'Salvar alterações';
            }
        }
    });

    const avatarContainer = document.getElementById('avatar-container');
    const btnAlterar = document.getElementById('btn-alterar-foto');
    const inputFicheiro = document.getElementById('avatar-upload');
    const btnRemover = document.getElementById('btn-remover-foto');

    if (avatarContainer && btnAlterar && inputFicheiro) {
        if (user.image_file) {
            avatarContainer.innerHTML = `<img src="/static/images/${user.image_file}" alt="Avatar" class="photo-avatar" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%;">`;
            if (btnRemover) btnRemover.style.display = "inline-block";
        } else {
            avatarContainer.innerHTML = `<img src="/static/images/default.jpg" alt="Avatar Padrão" class="photo-avatar" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%;">`;
        }

        btnAlterar.addEventListener('click', () => inputFicheiro.click());

        inputFicheiro.addEventListener('change', async (event) => {
            const file = event.target.files[0];
            if (!file) return;

            const formData = new FormData();
            formData.append('file', file);
            const token = getToken();

            try {
                btnAlterar.disabled = true;
                btnAlterar.textContent = 'Enviando...';

                const response = await fetch(`${apiBaseUrl}/${userId}/picture`, {
                    method: 'PATCH',
                    headers: { "Authorization": `Bearer ${token}` },
                    body: formData
                });

                if (response.ok) {
                    window.location.reload();
                } else {
                    const errorData = await response.json().catch(() => ({}));
                    alert(errorData.detail ? getErrorMessage(errorData) : 'Erro ao enviar a imagem.');
                }
            } catch (error) {
                console.error('Erro:', error);
                alert('Falha na conexão com o servidor.');
            } finally {
                btnAlterar.disabled = false;
                btnAlterar.textContent = 'Alterar foto';
                inputFicheiro.value = '';
            }
        });

        if (btnRemover) {
            btnRemover.addEventListener('click', async () => {
                if (!confirm('Tem certeza de que deseja remover sua foto de perfil?')) return;
                const token = getToken();

                try {
                    btnRemover.disabled = true;
                    btnRemover.textContent = 'Removendo...';

                    const response = await fetch(`${apiBaseUrl}/${userId}/picture`, {
                        method: 'DELETE',
                        headers: { "Authorization": `Bearer ${token}` }
                    });

                    if (response.ok) {
                        window.location.reload();
                    } else {
                        const errorData = await response.json().catch(() => ({}));
                        alert(errorData.detail ? getErrorMessage(errorData) : 'Erro ao remover a imagem.');
                        btnRemover.disabled = false;
                        btnRemover.textContent = 'Remover';
                    }
                } catch (error) {
                    console.error('Erro:', error);
                    alert('Falha na conexão com o servidor.');
                    btnRemover.disabled = false;
                    btnRemover.textContent = 'Remover';
                }
            });
        }
    }
});
