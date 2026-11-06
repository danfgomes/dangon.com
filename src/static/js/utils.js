// Usar /static garante que ele busque na raiz do servidor, independente da rota atual
import { getCurrentUser, setToken, logout, getToken, clearUserCache } from '/static/js/auth.js';

function obterMensagemErro(statusHttp) {
    switch (statusHttp) {
        case 400: return "Os dados enviados são inválidos ou usuário/e-mail já cadastrado.";
        case 401: return "Sessão expirada ou credenciais inválidas.";
        case 403: return "Não tem permissão para executar esta ação.";
        case 404: return "O recurso solicitado não foi encontrado.";
        case 422: return "Erro de validação nos dados enviados. Verifique os campos.";
        case 500: return "Ocorreu um erro interno no servidor. Tente novamente mais tarde.";
        default: return "Ocorreu um erro na operação.";
    }
}

document.addEventListener("DOMContentLoaded", async () => {
    const loginForm = document.getElementById("loginForm");
    const cadastroForm = document.getElementById("cadastroForm");
    const openModalBtn = document.getElementById("open-modal-btn");
    const accountBtn = document.getElementById("account-btn");
    const logoutBtn = document.getElementById("logout-btn");
    const loginBtn = document.getElementById("login-btn");
    const createPostForm = document.getElementById("createPostForm");
    const publishBtn = document.querySelector(".publish-btn");

    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('login') === 'true') {
        const loginModalElement = document.getElementById('loginModal');
        if (loginModalElement && typeof bootstrap !== 'undefined') {
            const loginModal = new bootstrap.Modal(loginModalElement);
            loginModal.show();
            window.history.replaceState({}, document.title, window.location.pathname);
        }
    }

    function showFeedbackModal(modalId, messageId, messageText) {
        if (messageId && messageText) {
            const messageElement = document.getElementById(messageId);
            if (messageElement) {
                messageElement.textContent = messageText;
            }
        }
        const modalElement = document.getElementById(modalId);
        if (modalElement && typeof bootstrap !== 'undefined') {
            const modalInstance = bootstrap.Modal.getOrCreateInstance(modalElement);
            modalInstance.show();
        }
    }

    function hideModal(modalId) {
        const modalElement = document.getElementById(modalId);
        if (modalElement && typeof bootstrap !== 'undefined') {
            const modalInstance = bootstrap.Modal.getInstance(modalElement);
            if (modalInstance) {
                modalInstance.hide();
            }
        }
    }

    async function updateUI() {
        const user = await getCurrentUser();

        if (user) {
            if (loginBtn) loginBtn.style.display = "none";
            if (logoutBtn) logoutBtn.style.display = "inline-block";
            if (accountBtn) accountBtn.style.display = "inline-block";

            if (openModalBtn) {
                if (user.role === "admin" || user.is_admin === true) {
                    openModalBtn.style.display = "inline-block";
                } else {
                    openModalBtn.style.display = "none";
                }
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
        logoutBtn.addEventListener("click", () => {
            logout();
        });
    }

    if (loginForm) {
        loginForm.addEventListener("submit", async (e) => {
            e.preventDefault();

            const emailInput = document.getElementById("email");
            const passwordInput = document.getElementById("password");

            if (!emailInput || !passwordInput) return;

            const email = emailInput.value;
            const password = passwordInput.value;

            const formData = new URLSearchParams();
            formData.append("username", email);
            formData.append("password", password);

            try {
                const response = await fetch("/api/users/token", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/x-www-form-urlencoded"
                    },
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
                    const mensagem = obterMensagemErro(response.status);
                    showFeedbackModal('errorModal', 'errorMessage', mensagem);
                }
            } catch (error) {
                console.error("Erro na requisição de login:", error);
                hideModal('loginModal');
                showFeedbackModal('errorModal', 'errorMessage', 'Erro de comunicação com o servidor.');
            }
        });
    }

    if (cadastroForm) {
        cadastroForm.addEventListener("submit", async (e) => {
            e.preventDefault();

            const formData = new FormData(cadastroForm);
            const emailValue = formData.get("email");

            const payload = {
                username: formData.get("username"),
                email: emailValue,
                password: formData.get("password")
            };

            const submitBtn = cadastroForm.querySelector(".create-button");
            if (submitBtn) submitBtn.disabled = true;

            try {
                const response = await fetch("/api/users/create", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify(payload)
                });

                if (response.ok) {
                    cadastroForm.reset();

                    if (document.getElementById('successModal')) {
                        showFeedbackModal('successModal', 'successMessage', 'Conta criada com sucesso! Redirecionando...');
                        const successModalEl = document.getElementById('successModal');
                        successModalEl.addEventListener('hidden.bs.modal', () => {
                            window.location.href = "/";
                        }, { once: true });
                    } else {
                        alert('Conta criada com sucesso!');
                        window.location.href = "/";
                    }

                    setTimeout(() => {
                        window.location.href = "/";
                    }, 2500);

                } else {
                    const errorData = await response.json();
                    const mensagem = errorData.detail || obterMensagemErro(response.status);

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
    }

    if (createPostForm) {
        createPostForm.addEventListener("submit", async (e) => {
            e.preventDefault();

            const token = getToken();
            const formData = new FormData(createPostForm);
            const postData = Object.fromEntries(formData.entries());

            if (postData.category_id) {
                postData.category_id = parseInt(postData.category_id, 10);
            }

            if (publishBtn) {
                publishBtn.disabled = true;
                publishBtn.innerText = "Publicando...";
            }

            try {
                const response = await fetch("/api/posts/", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${token}`
                    },
                    body: JSON.stringify(postData)
                });

                hideModal('createPostModal');

                if (response.ok) {
                    createPostForm.reset();
                    showFeedbackModal('successModal', 'successMessage', 'Publicação criada com sucesso!');

                    const successModalEl = document.getElementById('successModal');
                    if (successModalEl) {
                        successModalEl.addEventListener('hidden.bs.modal', () => {
                            window.location.reload();
                        }, { once: true });
                    }
                } else {
                    const mensagem = obterMensagemErro(response.status);
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
    }

    // ==========================================
    // Gerenciamento da Página de Perfil (Foto e Dados)
    // ==========================================
    const photoLine = document.getElementById('photo-line-container');
    const updateProfileForm = document.getElementById('updateProfileForm');

    if (photoLine || updateProfileForm) {
        const apiBaseUrl = '/api/users';

        const user = await getCurrentUser();

        if (!user) {
            window.location.href = "/?login=true";
            return;
        }

        const userId = user.id;

        // --- LÓGICA DO FORMULÁRIO DE DADOS ---
        if (updateProfileForm) {
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

                        if (document.getElementById('successModal')) {
                            showFeedbackModal('successModal', 'successMessage', 'Perfil atualizado com sucesso!');
                        } else {
                            alert('Perfil atualizado com sucesso!');
                        }
                    } else {
                        const errorData = await response.json();
                        const mensagem = errorData.detail || obterMensagemErro(response.status);

                        if (document.getElementById('errorModal')) {
                            showFeedbackModal('errorModal', 'errorMessage', mensagem);
                        } else {
                            alert('Erro ao atualizar: ' + mensagem);
                        }
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
        }

        // --- LÓGICA DA FOTO DE PERFIL ---
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

            btnAlterar.addEventListener('click', () => {
                inputFicheiro.click();
            });

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
                        headers: {
                            "Authorization": `Bearer ${token}`
                        },
                        body: formData
                    });

                    if (response.ok) {
                        window.location.reload();
                    } else {
                        const errorData = await response.json();
                        alert(errorData.detail || 'Erro ao enviar a imagem.');
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
                            headers: {
                                "Authorization": `Bearer ${token}`
                            }
                        });

                        if (response.ok) {
                            window.location.reload();
                        } else {
                            const errorData = await response.json();
                            alert(errorData.detail || 'Erro ao remover a imagem.');
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
    }
});
