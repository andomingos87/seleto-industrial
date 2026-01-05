/**
 * Seleto Docs - Application JavaScript
 * Handles navigation, search, theming, and content rendering
 */

// ============================================
// DOM Elements
// ============================================
const elements = {
    sidebar: document.getElementById('sidebar'),
    sidebarNav: document.getElementById('sidebarNav'),
    sidebarClose: document.getElementById('sidebarClose'),
    menuToggle: document.getElementById('menuToggle'),
    overlay: document.getElementById('overlay'),
    content: document.getElementById('content'),
    pageNav: document.getElementById('pageNav'),
    prevPage: document.getElementById('prevPage'),
    nextPage: document.getElementById('nextPage'),
    prevPageTitle: document.getElementById('prevPageTitle'),
    nextPageTitle: document.getElementById('nextPageTitle'),
    themeToggle: document.getElementById('themeToggle'),
    themeToggleMobile: document.getElementById('themeToggleMobile'),
    searchInput: document.getElementById('searchInput'),
    searchModal: document.getElementById('searchModal'),
    searchModalInput: document.getElementById('searchModalInput'),
    searchModalClose: document.getElementById('searchModalClose'),
    searchResults: document.getElementById('searchResults')
};

// ============================================
// State
// ============================================
let currentPage = 'home';
const pageOrder = [
    'home', 'arquitetura', 'api', 'servicos', 'banco-de-dados',
    'integracoes', 'agente-sdr', 'testes', 'deploy', 'seguranca',
    'troubleshooting', 'estrutura-pastas', 'variaveis-ambiente', 'glossario'
];

const pageTitles = {
    'home': 'Início',
    'arquitetura': 'Arquitetura',
    'api': 'API',
    'servicos': 'Serviços',
    'banco-de-dados': 'Banco de Dados',
    'integracoes': 'Integrações',
    'agente-sdr': 'Agente SDR',
    'testes': 'Testes',
    'deploy': 'Deploy',
    'seguranca': 'Segurança',
    'troubleshooting': 'Troubleshooting',
    'estrutura-pastas': 'Estrutura de Pastas',
    'variaveis-ambiente': 'Variáveis de Ambiente',
    'glossario': 'Glossário'
};

// ============================================
// Theme Management
// ============================================
function initTheme() {
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const theme = savedTheme || (prefersDark ? 'dark' : 'light');
    document.documentElement.setAttribute('data-theme', theme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
}

// ============================================
// Sidebar Management
// ============================================
function openSidebar() {
    elements.sidebar.classList.add('active');
    elements.overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeSidebar() {
    elements.sidebar.classList.remove('active');
    elements.overlay.classList.remove('active');
    document.body.style.overflow = '';
}

// ============================================
// Navigation
// ============================================
function navigateTo(pageId) {
    if (!DOCS_CONTENT[pageId]) {
        console.error(`Page not found: ${pageId}`);
        return;
    }

    currentPage = pageId;

    // Update active nav link
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
        if (link.dataset.page === pageId) {
            link.classList.add('active');
        }
    });

    // Render content
    renderContent(pageId);

    // Update page navigation
    updatePageNav(pageId);

    // Update URL hash
    history.pushState(null, '', `#${pageId}`);

    // Close sidebar on mobile
    if (window.innerWidth <= 1024) {
        closeSidebar();
    }

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function updatePageNav(pageId) {
    const currentIndex = pageOrder.indexOf(pageId);
    const prevIndex = currentIndex - 1;
    const nextIndex = currentIndex + 1;

    // Previous page
    if (prevIndex >= 0) {
        const prevId = pageOrder[prevIndex];
        elements.prevPage.classList.remove('hidden');
        elements.prevPage.dataset.page = prevId;
        elements.prevPageTitle.textContent = pageTitles[prevId];
    } else {
        elements.prevPage.classList.add('hidden');
    }

    // Next page
    if (nextIndex < pageOrder.length) {
        const nextId = pageOrder[nextIndex];
        elements.nextPage.classList.remove('hidden');
        elements.nextPage.dataset.page = nextId;
        elements.nextPageTitle.textContent = pageTitles[nextId];
    } else {
        elements.nextPage.classList.add('hidden');
    }
}

// ============================================
// Content Rendering
// ============================================
function renderContent(pageId) {
    const content = DOCS_CONTENT[pageId];
    if (!content) return;

    let html = '';

    // Title
    html += `<h1>${content.title}</h1>`;

    // Client note
    if (content.clientNote) {
        html += `
            <div class="client-note">
                <div class="client-note-title">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/>
                        <path d="M12 16v-4"/>
                        <path d="M12 8h.01"/>
                    </svg>
                    Para o Cliente
                </div>
                <p>${content.clientNote}</p>
            </div>
        `;
    }

    // Sections
    if (content.sections) {
        content.sections.forEach(section => {
            html += renderSection(section);
        });
    }

    elements.content.innerHTML = html;

    // Apply syntax highlighting to code blocks
    highlightCode();
}

function renderSection(section) {
    let html = '';

    if (section.title) {
        const level = section.level || 2;
        html += `<h${level}>${section.title}</h${level}>`;
    }

    if (section.content) {
        html += section.content;
    }

    if (section.subsections) {
        section.subsections.forEach(sub => {
            html += renderSection({ ...sub, level: (section.level || 2) + 1 });
        });
    }

    return html;
}

function highlightCode() {
    // Simple syntax highlighting for code blocks
    document.querySelectorAll('pre code').forEach(block => {
        let code = block.innerHTML;

        // Python/JavaScript keywords
        const keywords = ['def', 'class', 'import', 'from', 'return', 'async', 'await',
                         'if', 'else', 'elif', 'for', 'while', 'try', 'except', 'finally',
                         'function', 'const', 'let', 'var', 'export', 'default'];

        keywords.forEach(kw => {
            const regex = new RegExp(`\\b(${kw})\\b`, 'g');
            code = code.replace(regex, '<span style="color: #c792ea;">$1</span>');
        });

        // Strings
        code = code.replace(/(["'`])(?:(?!\1)[^\\]|\\.)*?\1/g, '<span style="color: #c3e88d;">$&</span>');

        // Comments
        code = code.replace(/(#.*$|\/\/.*$)/gm, '<span style="color: #546e7a;">$1</span>');

        // Numbers
        code = code.replace(/\b(\d+)\b/g, '<span style="color: #f78c6c;">$1</span>');

        block.innerHTML = code;
    });
}

// ============================================
// Search
// ============================================
function openSearch() {
    elements.searchModal.classList.add('active');
    elements.searchModalInput.focus();
    elements.searchModalInput.value = '';
    elements.searchResults.innerHTML = '<p class="search-hint">Digite para buscar...</p>';
}

function closeSearch() {
    elements.searchModal.classList.remove('active');
    elements.searchModalInput.value = '';
}

function performSearch(query) {
    if (!query || query.length < 2) {
        elements.searchResults.innerHTML = '<p class="search-hint">Digite pelo menos 2 caracteres...</p>';
        return;
    }

    const results = [];
    const queryLower = query.toLowerCase();

    // Search through all pages
    Object.entries(DOCS_CONTENT).forEach(([pageId, content]) => {
        const titleMatch = content.title.toLowerCase().includes(queryLower);
        const noteMatch = content.clientNote && content.clientNote.toLowerCase().includes(queryLower);

        let contentMatch = false;
        let excerpt = '';

        // Search in sections
        if (content.sections) {
            for (const section of content.sections) {
                const sectionText = extractText(section);
                if (sectionText.toLowerCase().includes(queryLower)) {
                    contentMatch = true;
                    // Get excerpt around match
                    const index = sectionText.toLowerCase().indexOf(queryLower);
                    const start = Math.max(0, index - 50);
                    const end = Math.min(sectionText.length, index + query.length + 50);
                    excerpt = (start > 0 ? '...' : '') +
                              sectionText.slice(start, end) +
                              (end < sectionText.length ? '...' : '');
                    break;
                }
            }
        }

        if (titleMatch || noteMatch || contentMatch) {
            results.push({
                pageId,
                title: content.title,
                excerpt: excerpt || content.clientNote?.slice(0, 100) + '...' || ''
            });
        }
    });

    // Render results
    if (results.length === 0) {
        elements.searchResults.innerHTML = `
            <div class="search-no-results">
                <p>Nenhum resultado encontrado para "${query}"</p>
            </div>
        `;
    } else {
        elements.searchResults.innerHTML = results.map(r => `
            <div class="search-result-item" data-page="${r.pageId}">
                <div class="search-result-title">${r.title}</div>
                <div class="search-result-excerpt">${highlightMatch(r.excerpt, query)}</div>
            </div>
        `).join('');

        // Add click handlers
        elements.searchResults.querySelectorAll('.search-result-item').forEach(item => {
            item.addEventListener('click', () => {
                navigateTo(item.dataset.page);
                closeSearch();
            });
        });
    }
}

function extractText(section) {
    let text = '';
    if (section.title) text += section.title + ' ';
    if (section.content) {
        // Strip HTML tags
        text += section.content.replace(/<[^>]*>/g, ' ') + ' ';
    }
    if (section.subsections) {
        section.subsections.forEach(sub => {
            text += extractText(sub) + ' ';
        });
    }
    return text;
}

function highlightMatch(text, query) {
    const regex = new RegExp(`(${escapeRegExp(query)})`, 'gi');
    return text.replace(regex, '<mark>$1</mark>');
}

function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// ============================================
// Event Listeners
// ============================================
function initEventListeners() {
    // Theme toggle
    elements.themeToggle?.addEventListener('click', toggleTheme);
    elements.themeToggleMobile?.addEventListener('click', toggleTheme);

    // Sidebar
    elements.menuToggle?.addEventListener('click', openSidebar);
    elements.sidebarClose?.addEventListener('click', closeSidebar);
    elements.overlay?.addEventListener('click', closeSidebar);

    // Navigation links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            navigateTo(link.dataset.page);
        });
    });

    // Page navigation
    elements.prevPage?.addEventListener('click', (e) => {
        e.preventDefault();
        navigateTo(e.currentTarget.dataset.page);
    });

    elements.nextPage?.addEventListener('click', (e) => {
        e.preventDefault();
        navigateTo(e.currentTarget.dataset.page);
    });

    // Search
    elements.searchInput?.addEventListener('focus', openSearch);
    elements.searchModalClose?.addEventListener('click', closeSearch);
    elements.searchModal?.addEventListener('click', (e) => {
        if (e.target === elements.searchModal) closeSearch();
    });

    elements.searchModalInput?.addEventListener('input', (e) => {
        performSearch(e.target.value);
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        // Ctrl+K or Cmd+K to open search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            openSearch();
        }

        // Escape to close modals
        if (e.key === 'Escape') {
            closeSearch();
            closeSidebar();
        }

        // Arrow keys for navigation
        if (e.key === 'ArrowLeft' && !elements.prevPage.classList.contains('hidden')) {
            navigateTo(elements.prevPage.dataset.page);
        }
        if (e.key === 'ArrowRight' && !elements.nextPage.classList.contains('hidden')) {
            navigateTo(elements.nextPage.dataset.page);
        }
    });

    // Handle hash changes
    window.addEventListener('hashchange', () => {
        const hash = window.location.hash.slice(1);
        if (hash && DOCS_CONTENT[hash]) {
            navigateTo(hash);
        }
    });

    // Handle initial hash
    const initialHash = window.location.hash.slice(1);
    if (initialHash && DOCS_CONTENT[initialHash]) {
        navigateTo(initialHash);
    } else {
        navigateTo('home');
    }
}

// ============================================
// Initialize
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initEventListeners();
});
