(() => {
    const app = window.AITutorApp;

    let currentFilter = 'all';
    let currentSearch = '';

    const FILE_TYPES = [
        { type: 'pdf', exts: ['pdf'], color: '#e03e3e', bg: 'rgba(224,62,62,0.12)', border: 'rgba(224,62,62,0.22)', label: 'PDF' },
        { type: 'doc', exts: ['doc', 'docx', 'txt', 'md'], color: '#2563eb', bg: 'rgba(37,99,235,0.12)', border: 'rgba(37,99,235,0.22)', label: 'DOC' },
        { type: 'excel', exts: ['xls', 'xlsx'], color: '#16a34a', bg: 'rgba(22,163,74,0.12)', border: 'rgba(22,163,74,0.22)', label: 'XLS' },
        { type: 'ppt', exts: ['ppt', 'pptx'], color: '#ea580c', bg: 'rgba(234,88,12,0.12)', border: 'rgba(234,88,12,0.22)', label: 'PPT' },
        { type: 'image', exts: ['png', 'jpg', 'jpeg', 'gif', 'webp'], color: '#7c3aed', bg: 'rgba(124,58,237,0.12)', border: 'rgba(124,58,237,0.22)', label: 'IMG' },
    ];
    const FALLBACK_TYPE = { type: 'other', color: '#64748b', bg: 'rgba(100,116,139,0.10)', border: 'rgba(100,116,139,0.20)', label: '文件' };

    function getFileType(filename) {
        if (!filename || typeof filename !== 'string') return { ...FALLBACK_TYPE, ext: '?' };
        const ext = filename.split('.').pop().toLowerCase();
        const found = FILE_TYPES.find(item => item.exts.includes(ext));
        return found ? { ...found, ext: ext.toUpperCase() } : { ...FALLBACK_TYPE, ext: ext.toUpperCase() || '?' };
    }

    function formatFileSize(bytes) {
        if (typeof bytes !== 'number' || Number.isNaN(bytes) || bytes < 0) return '';
        if (bytes < 1024) return `${bytes} B`;
        const kb = bytes / 1024;
        if (kb < 1024) return `${kb.toFixed(1)} KB`;
        return `${(kb / 1024).toFixed(1)} MB`;
    }

    function escapeHtml(text) {
        return String(text)
            .replaceAll('&', '&amp;')
            .replaceAll('<', '&lt;')
            .replaceAll('>', '&gt;')
            .replaceAll('"', '&quot;')
            .replaceAll("'", '&#39;');
    }

    function getItemType(item) {
        return getFileType(item && item.filename ? item.filename : '').type;
    }

    function getQuestionSearchText(item) {
        const blocks = Array.isArray(item?.content_blocks) ? item.content_blocks : [];
        const blockText = blocks
            .filter(block => block?.block_type === 'text')
            .map(block => String(block?.content || '').replace(/<[^>]+>/g, ' '))
            .join(' ');
        const options = Array.isArray(item?.options) ? item.options.join(' ') : '';
        const tags = Array.isArray(item?.knowledge_tags) ? item.knowledge_tags.join(' ') : '';
        return [
            item?.question_id,
            item?.section_title,
            item?.question_type,
            blockText,
            options,
            tags,
        ].filter(Boolean).join(' ').toLowerCase();
    }

    function getDisplayKnowledgeTags(item) {
        const seen = new Set();
        const tags = [];
        const append = (value) => {
            const normalized = String(value || '').replace(/\s+/g, ' ').trim();
            if (!normalized || seen.has(normalized)) return;
            seen.add(normalized);
            tags.push(normalized);
        };
        (Array.isArray(item?.knowledge_tags) ? item.knowledge_tags : []).forEach(append);
        if (!tags.length) append(item?.section_title);
        if (!tags.length) append('待补充知识板块');
        return tags.slice(0, 6);
    }

    function matchesSearchForFile(item) {
        if (!currentSearch.trim()) return true;
        return String(item?.filename || '').toLowerCase().includes(currentSearch.trim().toLowerCase());
    }

    function matchesSearchForQuestion(item) {
        if (!currentSearch.trim()) return true;
        return getQuestionSearchText(item).includes(currentSearch.trim().toLowerCase());
    }

    function showEl(el) {
        if (el) {
            el.removeAttribute('hidden');
            el.style.display = '';
        }
    }

    function hideEl(el) {
        if (el) {
            el.setAttribute('hidden', '');
            el.style.display = 'none';
        }
    }

    function libraryHeaderButton() {
        return document.querySelector('#library-overlay .library-content-header .library-upload-btn');
    }

    function librarySearchInput() {
        return document.getElementById('library-search-input');
    }

    function updateBadges(files, questions) {
        const counts = {
            all: files.length,
            question_bank: questions.length,
            pdf: 0,
            doc: 0,
            excel: 0,
            image: 0,
            other: 0,
        };
        for (const file of files) {
            if (!file) continue;
            const type = getItemType(file);
            if (type === 'pdf') counts.pdf += 1;
            else if (type === 'doc' || type === 'ppt') counts.doc += 1;
            else if (type === 'excel') counts.excel += 1;
            else if (type === 'image') counts.image += 1;
            else counts.other += 1;
        }
        Object.entries(counts).forEach(([key, value]) => {
            const el = document.getElementById(`lib-count-${key}`);
            if (!el) return;
            el.textContent = value > 0 ? String(value) : '';
            el.hidden = value === 0;
        });
    }

    function updateLibraryHeaderState(files, questions) {
        const title = document.getElementById('library-title');
        const storageText = document.getElementById('library-storage-text');
        const uploadBtn = libraryHeaderButton();
        const searchInput = librarySearchInput();
        const titleMap = {
            all: '全部文件',
            question_bank: '题库',
            pdf: 'PDF',
            doc: '文档',
            excel: '表格',
            image: '图片',
            other: '其他',
        };
        if (title) title.textContent = titleMap[currentFilter] || '全部文件';

        if (currentFilter === 'question_bank') {
            if (storageText) storageText.textContent = `共 ${questions.length} 道题目`;
            if (uploadBtn) uploadBtn.hidden = true;
            if (searchInput) searchInput.placeholder = '搜索题号、题干或知识点…';
            return;
        }

        if (storageText) storageText.textContent = `共 ${files.length} 份文件`;
        if (uploadBtn) uploadBtn.hidden = false;
        if (searchInput) searchInput.placeholder = '搜索文件名…';
    }

    function setLibraryStatus(msg, type = '') {
        const el = document.getElementById('library-status');
        if (!el) return;
        el.textContent = msg;
        el.className = `library-status${type ? ` library-status--${type}` : ''}`;
        if (msg) setTimeout(() => {
            if (el.textContent === msg) el.textContent = '';
        }, 4000);
    }

    function setUploadBusy(busy) {
        document.querySelectorAll('.library-upload-btn').forEach(btn => {
            btn.disabled = busy;
            btn.style.opacity = busy ? '0.55' : '';
            btn.style.cursor = busy ? 'not-allowed' : '';
        });
    }

    function buildFileRow(item) {
        const { color, bg, border, ext } = getFileType(item.filename);
        const type = getItemType(item);
        const safeDisplay = escapeHtml(item.filename);
        const rawFilename = item.filename;
        const size = formatFileSize(item.size_bytes);
        const chunks = Number.isInteger(item.chunk_count) ? `${item.chunk_count} 段` : '';
        const meta = [size, chunks].filter(Boolean).join(' · ');
        const isImage = type === 'image';

        return `<div class="lib-file-row" role="listitem" data-filename="${escapeHtml(rawFilename)}">
            <div class="lib-file-icon ${isImage ? 'lib-file-icon--clickable' : ''}" ${isImage ? `onclick="previewFile('${escapeHtml(rawFilename)}')"` : ''} style="background:${bg};border:1px solid ${border}" aria-hidden="true">
                <span class="lib-file-ext" style="color:${color}">${escapeHtml(ext)}</span>
            </div>
            <div class="lib-file-info">
                <div class="lib-file-name ${isImage ? 'lib-file-name--clickable' : ''}" ${isImage ? `onclick="previewFile('${escapeHtml(rawFilename)}')"` : ''} title="${safeDisplay}">${safeDisplay}</div>
                ${meta ? `<div class="lib-file-meta">${escapeHtml(meta)}</div>` : ''}
            </div>
            <div class="lib-file-actions">
                <button type="button" class="lib-file-download" onclick="downloadFile('${escapeHtml(rawFilename)}')" aria-label="下载 ${safeDisplay}" title="下载">
                    <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M7 2.5V9.5M4 6.5L7 9.5L10 6.5M2.5 11.5H11.5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
                </button>
                <button type="button" class="lib-file-delete" data-raw="${escapeHtml(rawFilename)}" aria-label="删除 ${safeDisplay}">
                    <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M2.5 3.5H11.5M5.5 3.5V2.5H8.5V3.5M4.5 3.5V11.5H9.5V3.5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
                </button>
            </div>
        </div>`;
    }

    function renderQuestionBankCard(item) {
        const displayItem = {
            ...(item || {}),
            knowledge_tags: getDisplayKnowledgeTags(item),
        };
        const card = document.createElement('article');
        card.className = 'error-workbench-question-card library-question-bank-card';

        const header = document.createElement('div');
        header.className = 'error-workbench-question-header';
        const titleWrap = document.createElement('div');
        titleWrap.className = 'error-workbench-question-title-wrap';
        titleWrap.appendChild(document.createTextNode(''));
        const title = document.createElement('strong');
        title.className = 'error-workbench-question-title';
        title.textContent = `题目 ${displayItem.question_id || displayItem.library_id || ''}`.trim();
        titleWrap.replaceChildren(title);
        const metaText = [displayItem.section_title, displayItem.question_type].filter(Boolean).join(' · ');
        if (metaText) {
            const meta = document.createElement('span');
            meta.className = 'error-workbench-question-meta';
            meta.textContent = metaText;
            titleWrap.appendChild(meta);
        }
        header.appendChild(titleWrap);

        const actions = document.createElement('div');
        actions.className = 'lib-file-actions';
        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'lib-file-delete';
        removeBtn.dataset.libraryId = String(item.library_id || '');
        removeBtn.setAttribute('aria-label', `删除题目 ${item.question_id || item.library_id || ''}`);
        removeBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M2.5 3.5H11.5M5.5 3.5V2.5H8.5V3.5M4.5 3.5V11.5H9.5V3.5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>';
        actions.appendChild(removeBtn);
        header.appendChild(actions);

        card.appendChild(header);
        if (typeof app.buildRenderedQuestionBody === 'function') {
            card.appendChild(app.buildRenderedQuestionBody(displayItem, {
                showExcerpt: false,
                showBadges: true,
                showAnswer: false,
            }));
        }
        return card;
    }

    function renderFileLibrary(fileList, dropzone, files) {
        const filtered = files.filter(item => {
            if (!item) return false;
            if (currentFilter === 'all') return matchesSearchForFile(item);
            const type = getItemType(item);
            if (currentFilter === 'other') return !['pdf', 'doc', 'excel', 'ppt', 'image'].includes(type) && matchesSearchForFile(item);
            if (currentFilter === 'doc') return ['doc', 'ppt'].includes(type) && matchesSearchForFile(item);
            return type === currentFilter && matchesSearchForFile(item);
        });

        if (!filtered.length) {
            fileList.innerHTML = '';
            const title = dropzone.querySelector('.library-dropzone-title');
            const hint = dropzone.querySelector('.library-dropzone-hint');
            const btn = dropzone.querySelector('.library-upload-btn');
            if (title) title.textContent = '还没有文件';
            if (hint) hint.textContent = '点击“上传文件”或拖拽文件到这里';
            if (btn) btn.hidden = false;
            showEl(dropzone);
            return;
        }

        hideEl(dropzone);
        fileList.innerHTML = filtered.map(item => buildFileRow(item)).join('');
    }

    function renderQuestionBankLibrary(fileList, dropzone, questions) {
        const filtered = questions.filter(item => item && matchesSearchForQuestion(item));
        fileList.innerHTML = '';

        if (!filtered.length) {
            const title = dropzone.querySelector('.library-dropzone-title');
            const hint = dropzone.querySelector('.library-dropzone-hint');
            const btn = dropzone.querySelector('.library-upload-btn');
            if (title) title.textContent = '题库还是空的';
            if (hint) hint.textContent = '先去题库加工里完成分割，再点击“保存到资料库”。';
            if (btn) btn.hidden = true;
            showEl(dropzone);
            return;
        }

        const btn = dropzone.querySelector('.library-upload-btn');
        if (btn) btn.hidden = false;
        hideEl(dropzone);
        filtered.forEach(item => fileList.appendChild(renderQuestionBankCard(item)));
    }

    function renderLibraryPanel() {
        const files = (app.state && app.state.knowledgeFiles) ? app.state.knowledgeFiles : [];
        const questions = (app.state && app.state.questionBankItems) ? app.state.questionBankItems : [];
        const fileList = document.getElementById('library-file-list');
        const dropzone = document.getElementById('library-dropzone');
        const clearBtn = document.getElementById('library-clear-btn');

        if (!fileList || !dropzone) return;

        updateBadges(files, questions);
        updateLibraryHeaderState(files, questions);
        if (clearBtn) clearBtn.hidden = currentFilter === 'question_bank' ? questions.length === 0 : files.length === 0;

        if (currentFilter === 'question_bank') {
            renderQuestionBankLibrary(fileList, dropzone, questions);
            return;
        }
        renderFileLibrary(fileList, dropzone, files);
    }

    async function fetchKnowledgeFiles() {
        const fileList = document.getElementById('library-file-list');
        if (fileList && !fileList.children.length && currentFilter !== 'question_bank') {
            fileList.innerHTML = `<div class="lib-loading">
                <span class="lib-loading-dot"></span>
                <span class="lib-loading-dot"></span>
                <span class="lib-loading-dot"></span>
            </div>`;
        }
        try {
            const res = await fetch('/api/knowledge/files');
            const data = await res.json();
            app.patchState({ knowledgeFiles: data.items || [] }, 'knowledge.fetch');
        } catch (_error) {
            app.patchState({ knowledgeFiles: [] }, 'knowledge.fetch.error');
            setLibraryStatus('加载失败，请检查网络连接', 'danger');
        }
    }

    async function fetchQuestionBankItems() {
        try {
            const res = await fetch('/api/knowledge/question-bank');
            const data = await res.json();
            app.patchState({ questionBankItems: data.items || [] }, 'question-bank.fetch');
        } catch (_error) {
            app.patchState({ questionBankItems: [] }, 'question-bank.fetch.error');
            setLibraryStatus('题库加载失败', 'danger');
        }
    }

    async function deleteKnowledgeFile(filename) {
        if (!filename) return;
        if (!confirm(`确定移除这份资料吗？\n${filename}`)) return;
        setLibraryStatus('正在移除…', 'processing');
        try {
            const res = await fetch(`/api/knowledge/files/${encodeURIComponent(filename)}`, { method: 'DELETE' });
            const data = await res.json();
            if (data.status !== 'success') {
                setLibraryStatus(data.message || '移除失败', 'danger');
                return;
            }
            setLibraryStatus(`已移除 ${filename}`, 'success');
            await fetchKnowledgeFiles();
        } catch (_error) {
            setLibraryStatus('移除失败', 'danger');
        }
    }

    async function deleteQuestionBankItem(libraryId) {
        if (!libraryId) return;
        if (!confirm('确定从题库中移除这道题吗？')) return;
        setLibraryStatus('正在移除题目…', 'processing');
        try {
            const res = await fetch(`/api/knowledge/question-bank/${encodeURIComponent(libraryId)}`, { method: 'DELETE' });
            const data = await res.json();
            if (data.status !== 'success') {
                setLibraryStatus(data.message || '移除失败', 'danger');
                return;
            }
            setLibraryStatus('已从题库移除', 'success');
            await fetchQuestionBankItems();
        } catch (_error) {
            setLibraryStatus('移除失败', 'danger');
        }
    }

    function previewFile(filename) {
        const url = `/api/knowledge/file/${encodeURIComponent(filename)}`;
        const ext = filename.split('.').pop().toLowerCase();
        const isImage = ['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'].includes(ext);

        const modal = document.createElement('div');
        modal.className = 'library-preview-overlay';
        modal.setAttribute('aria-hidden', 'false');
        modal.onclick = function handleOverlayClick(event) {
            if (event.target === modal) modal.remove();
        };

        const content = document.createElement('div');
        content.className = 'library-preview-content';
        content.onclick = function stopPropagation(event) { event.stopPropagation(); };

        const header = document.createElement('div');
        header.className = 'library-preview-header';
        header.innerHTML = `<div class="library-preview-title">${escapeHtml(filename)}</div><button type="button" class="library-preview-close" onclick="this.closest('.library-preview-overlay').remove()" aria-label="关闭">✕</button>`;

        const body = document.createElement('div');
        body.className = 'library-preview-body';

        if (isImage) {
            const img = document.createElement('img');
            img.src = url;
            img.alt = escapeHtml(filename);
            img.className = 'library-preview-image';
            body.appendChild(img);
        } else {
            const iframe = document.createElement('iframe');
            iframe.src = url;
            iframe.className = 'library-preview-iframe';
            body.appendChild(iframe);
        }

        const footer = document.createElement('div');
        footer.className = 'library-preview-footer';
        footer.innerHTML = `<a href="${url}" download="${escapeHtml(filename)}" class="library-preview-download-btn">下载文件</a>`;

        content.append(header, body, footer);
        modal.appendChild(content);
        document.body.appendChild(modal);
        document.body.style.overflow = 'hidden';
        modal.addEventListener('keydown', event => {
            if (event.key === 'Escape') {
                modal.remove();
                document.body.style.overflow = '';
            }
        });
    }

    function downloadFile(filename) {
        const url = `/api/knowledge/file/${encodeURIComponent(filename)}`;
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
    }

    async function uploadKnowledgeFile(file) {
        if (!file) return;
        const formData = new FormData();
        formData.append('file', file);
        setLibraryStatus(`正在上传 ${file.name}…`, 'processing');
        setUploadBusy(true);
        try {
            const res = await fetch('/api/upload', { method: 'POST', body: formData });
            const data = await res.json();
            if (data.status === 'success') {
                setLibraryStatus(data.message || `${data.filename} 已加入资料库`, 'success');
                await fetchKnowledgeFiles();
            } else {
                setLibraryStatus(data.message || '上传失败', 'danger');
                await fetchKnowledgeFiles();
            }
        } catch (_error) {
            setLibraryStatus('上传失败，请检查网络', 'danger');
        } finally {
            setUploadBusy(false);
        }
    }

    async function clearKnowledgeFiles() {
        if (currentFilter === 'question_bank') {
            const questions = (app.state && app.state.questionBankItems) || [];
            if (!questions.length) {
                setLibraryStatus('题库为空', 'muted');
                return;
            }
            if (!confirm('确定清空资料库里的全部题库题目吗？')) return;
            setLibraryStatus('正在清空题库…', 'processing');
            try {
                const res = await fetch('/api/knowledge/question-bank', { method: 'DELETE' });
                const data = await res.json();
                if (data.status !== 'success') {
                    setLibraryStatus(data.message || '清空失败', 'danger');
                    return;
                }
                setLibraryStatus(`已清空 ${data.removed || 0} 道题目`, 'success');
                await fetchQuestionBankItems();
            } catch (_error) {
                setLibraryStatus('清空失败', 'danger');
            }
            return;
        }

        const files = (app.state && app.state.knowledgeFiles) || [];
        if (!files.length) {
            setLibraryStatus('资料库为空', 'muted');
            return;
        }
        if (!confirm('确定清空所有资料吗？这会同时删除对应向量索引。')) return;
        setLibraryStatus('正在清空…', 'processing');
        try {
            const res = await fetch('/api/knowledge/files', { method: 'DELETE' });
            const data = await res.json();
            if (data.status !== 'success') {
                setLibraryStatus(data.message || '清空失败', 'danger');
                return;
            }
            setLibraryStatus(`已清空 ${data.removed || 0} 份资料`, 'success');
            await fetchKnowledgeFiles();
        } catch (_error) {
            setLibraryStatus('清空失败', 'danger');
        }
    }

    function switchLibraryFilter(filter) {
        currentFilter = filter;
        document.querySelectorAll('#library-nav [data-lib-filter]').forEach(btn => {
            btn.classList.toggle('is-active', btn.getAttribute('data-lib-filter') === filter);
        });
        renderLibraryPanel();
    }

    function filterLibrarySearch(value) {
        currentSearch = value || '';
        renderLibraryPanel();
    }

    app.fetchKnowledgeFiles = fetchKnowledgeFiles;
    app.fetchQuestionBankItems = fetchQuestionBankItems;
    app.uploadKnowledgeFile = uploadKnowledgeFile;
    app.clearKnowledgeFiles = clearKnowledgeFiles;
    app.switchLibraryFilter = switchLibraryFilter;
    app.filterLibrarySearch = filterLibrarySearch;
    app.renderKnowledgeShelf = renderLibraryPanel;

    app.subscribeState((_state, source) => {
        if (!source.startsWith('knowledge.') && !source.startsWith('question-bank.')) return;
        renderLibraryPanel();
    });

    document.addEventListener('click', event => {
        const fileDeleteBtn = event.target.closest('.lib-file-delete[data-raw]');
        if (fileDeleteBtn) {
            const rawName = fileDeleteBtn.getAttribute('data-raw') || '';
            const filename = rawName
                .replaceAll('&amp;', '&')
                .replaceAll('&lt;', '<')
                .replaceAll('&gt;', '>')
                .replaceAll('&quot;', '"')
                .replaceAll('&#39;', "'");
            deleteKnowledgeFile(filename);
            return;
        }
        const questionDeleteBtn = event.target.closest('.lib-file-delete[data-library-id]');
        if (questionDeleteBtn) {
            deleteQuestionBankItem(questionDeleteBtn.getAttribute('data-library-id') || '');
        }
    });

    window.switchLibraryFilter = switchLibraryFilter;
    window.filterLibrarySearch = filterLibrarySearch;
    window.clearKnowledgeFiles = clearKnowledgeFiles;
    window.previewFile = previewFile;
    window.downloadFile = downloadFile;
})();
