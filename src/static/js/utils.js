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
    const logoutBtn = document.getElementById("logout-btn");
    const loginBtn = document.getElementById("login-btn");
    const createPostForm = document.getElementById("createPostForm");
    const publishBtn = document.querySelector(".publish-btn");

    // ==========================================
    // CÓDIGO NOVO: Checa se deve abrir o login
    // ==========================================
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('login') === 'true') {
        const loginModalElement = document.getElementById('loginModal');
        if (loginModalElement && typeof bootstrap !== 'undefined') {
            const loginModal = new bootstrap.Modal(loginModalElement);
            loginModal.show();

            // Limpa o parâmetro da URL para não reabrir se atualizar a página
            window.history.replaceState({}, document.title, window.location.pathname);
        }
    }
    // ==========================================

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

            const email = document.getElementById("email").value;
            const password = document.getElementById("password").value;

            const formData = new URLSearchParams();
            formData.append("username", email);
            formData.append("password", password);

            try {
                // Caminho absoluto para a rota de token
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
                username: formData.get("username"), // Passando o email como username para preencher a validação do Pydantic
                email: emailValue,
                password: formData.get("password")
            };

            const submitBtn = cadastroForm.querySelector(".create-button");
            if (submitBtn) submitBtn.disabled = true;

            try {
                // Caminho absoluto apontando para o prefixo do router (/api/users) + rota (/create)
                const response = await fetch("/api/users/create", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify(payload)
                });

                if (response.ok) {
                    cadastroForm.reset();

                    // Fallback para caso os modais não existam ou não carreguem na árvore do DOM da página
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
});
