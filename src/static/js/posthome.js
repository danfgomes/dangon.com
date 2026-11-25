import { escapeHtml } from '/static/js/utils.js';

document.addEventListener("DOMContentLoaded", () => {
    const postsContainer = document.getElementById('postsContainer');
    const loadMoreBtn = document.getElementById('loadMoreBtn');

    if (!postsContainer || !loadMoreBtn) return;

    const limit = 5;
    let hasMore = loadMoreBtn.dataset.hasMore === 'true';
    const basePostUrlTemplate = loadMoreBtn.dataset.postUrlTemplate || '/posts/PLACEHOLDER_ID';

    function createPostHTML(post) {
        const category = post.category ? escapeHtml(post.category) : 'Geral';
        const readingTime = post.reading_time_min ? escapeHtml(String(post.reading_time_min)) : '5';
        const postUrl = basePostUrlTemplate.replace('PLACEHOLDER_ID', post.id);

        return `
            <article class="post-card">
                <div class="post-card__body">
                    <span class="article-category">${category}</span>
                    <h2>
                        <a href="${postUrl}">
                            ${escapeHtml(post.title)}
                        </a>
                    </h2>
                    <span class="article-meta">${readingTime} min read</span>
                </div>
            </article>
        `;
    }

    async function loadMorePosts() {
        loadMoreBtn.disabled = true;
        loadMoreBtn.textContent = 'Carregando...';

        const currentOffset = document.querySelectorAll('.post-card').length;

        try {
            const response = await fetch(`/api/posts/?skip=${currentOffset}&limit=${limit}`);

            if (!response.ok) {
                throw new Error('Falha ao buscar posts');
            }

            const data = await response.json();

            for (const post of data.posts) {
                postsContainer.insertAdjacentHTML('beforeend', createPostHTML(post));
            }

            hasMore = data.has_more;

            if (!hasMore) {
                loadMoreBtn.style.display = 'none';
            }
        } catch (error) {
            console.error('Erro ao carregar posts:', error);
            loadMoreBtn.textContent = 'Erro - Tente novamente';
            loadMoreBtn.disabled = false;
            return;
        }

        if (hasMore) {
            loadMoreBtn.disabled = false;
            loadMoreBtn.textContent = 'Carregar mais posts';
        }
    }

    loadMoreBtn.addEventListener('click', loadMorePosts);
});
