(() => {
    const app = window.AITutorApp;

    let currentFilter = 'all';
    let currentSearch = '';
    let questionBankItems = [];

    const FILE_TYPES = [
        { type: 'pdf',   exts: ['pdf'],                            color: '#e03e3e', bg: 'rgba(224,62,62,0.12)',   border: 'rgba(224,62,62,0.22)',  label: 'PDF' },
        { type: 'doc',   exts: ['doc','docx','txt','md'],          color: '#2563eb', bg: 'rgba(37,99,235,0.12)',   border: 'rgba(37,99,235,0.22)',  label: 'DOC' },
        { type: 'excel', exts: ['xls','xlsx'],                     color: '#16a34a', bg: 'rgba(22,163,74,0.12)',   border: 'rgba(22,163,74,0.22)',  label: 'XLS' },
        { type: 'ppt',   exts: ['ppt','pptx'],                     color: '#ea580c', bg: 'rgba(234,88,12,0.12)',   border: 'rgba(234,88,12,0.22)',  label: 'PPT' },
        { type: 'image', exts: ['png','jpg','jpeg','gif','webp'],   color: '#7c3aed', bg: 'rgba(124,58,237,0.12)',  border: 'rgba(124,58,237,0.22)', label: 'IMG' },
    ];
    const FALLBACK_TYPE = { type: 'other', color: '#64748b', bg: 'rgba(100,116,139,0.10)', border: 'rgba(100,116,139,0.20)', label: '文件' };

    function getFileType(filename) {
        if (!filename || typeof filename !== 'string') return { ...FALLBACK_TYPE, ext: '?' };
        const ext = filename.split('.').pop().toLowerCase();
        const found = FILE_TYPES.find(t => t.exts.includes(ext));
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
        if (item && item.__libraryType === 'question_bank') return 'question_bank';
        return getFileType(item && item.filename ? item.filename : '').type;
    }

    function matchesFilter(item) {
        if (currentFilter === 'all') return true;
        if (currentFilter === 'question_bank') return getItemType(item) === 'question_bank';
        const type = getItemType(item);
        if (currentFilter === 'other') return !['pdf','doc','excel','ppt','image'].includes(type);
        if (currentFilter === 'doc') return ['doc','ppt'].includes(type);
        return type === currentFilter;
    }

    function matchesSearch(item) {
        if (!currentSearch.trim()) return true;
        const name = (item && (item.filename || item.title || item.question_id || item.content_text))
            ? String(item.filename || item.title || item.question_id || item.content_text).toLowerCase()
            : '';
        return name.includes(currentSearch.trim().toLowerCase());
    }

    function showEl(el) { if (el) { el.removeAttribute('hidden'); el.style.display = ''; } }
    function hideEl(el) { if (el) { el.setAttribute('hidden', ''); el.style.display = 'none'; } }

    function renderLibraryPanel() {
        const files = (app.state && app.state.knowledgeFiles) ? app.state.knowledgeFiles : [];
        const libraryItems = currentFilter === 'question_bank'
            ? questionBankItems.map(item => ({ ...item, __libraryType: 'question_bank' }))
            : files;
        const fileList   = document.getElementById('library-file-list');
        const dropzone   = document.getElementById('library-dropzone');
        const clearBtn   = document.getElementById('library-clear-btn');
        const storageText = document.getElementById('library-storage-text');

        if (!fileList) return;

        updateBadges(files);
        if (storageText) storageText.textContent = currentFilter === 'question_bank'
            ? `共 ${questionBankItems.length} 道题`
            : `共 ${files.length} 份文件`;
        if (clearBtn) clearBtn.hidden = currentFilter === 'question_bank' || files.length === 0;

        let filtered;
        try {
            filtered = libraryItems.filter(f => f && matchesFilter(f) && matchesSearch(f));
        } catch (e) {
            filtered = [];
        }

        if (filtered.length === 0) {
            fileList.innerHTML = '';
            showEl(dropzone);
        } else {
            hideEl(dropzone);
            fileList.innerHTML = filtered.map(item => (
                getItemType(item) === 'question_bank' ? renderQuestionBankCard(item) : buildFileRow(item)
            )).join('');
        }
    }

    function renderQuestionBankCard(item) {
        const title = item.title || item.question_id || '待补充知识板块';
        const body = item.content_text || item.stem || item.question_text || '待补充知识板块';
        const tags = Array.isArray(item.tags) ? item.tags.slice(0, 4).join(' · ') : '';
        return `<article class="lib-file-row question-bank-row" role="listitem" data-library-id="${escapeHtml(item.library_id || '')}">
            <div class="lib-file-icon" style="background:rgba(22,163,74,0.12);border:1px solid rgba(22,163,74,0.22)" aria-hidden="true">
                <span class="lib-file-ext" style="color:#16a34a">题</span>
            </div>
            <div class="lib-file-info">
                <div class="lib-file-name" title="${escapeHtml(title)}">${escapeHtml(title)}</div>
                <div class="lib-file-meta">${escapeHtml(tags || body).slice(0, 120)}</div>
            </div>
        </article>`;
    }

    function buildFileRow(item) {
        const { color, bg, border, ext } = getFileType(item.filename);
        const type = getItemType(item);
        const safeDisplay = escapeHtml(item.filename);
        const rawFilename  = item.filename;
        const size   = formatFileSize(item.size_bytes);
        const chunks = Number.isInteger(item.chunk_count) ? `${item.chunk_count} 段` : '';
        const meta   = [size, chunks].filter(Boolean).join(' · ');
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

    function updateBadges(files) {
        const counts = { all: files.length, pdf: 0, doc: 0, excel: 0, image: 0, other: 0, question_bank: questionBankItems.length };
        for (const f of files) {
            if (!f) continue;
            const type = getItemType(f);
            if (type === 'pdf') counts.pdf++;
            else if (type === 'doc' || type === 'ppt') counts.doc++;
            else if (type === 'excel') counts.excel++;
            else if (type === 'image') counts.image++;
            else counts.other++;
        }
        for (const [key, val] of Object.entries(counts)) {
            const el = document.getElementById(`lib-count-${key}`);
            if (el) { el.textContent = val > 0 ? String(val) : ''; el.hidden = val === 0; }
        }
    }

    function setLibraryStatus(msg, type = '') {
        const el = document.getElementById('library-status');
        if (!el) return;
        el.textContent = msg;
        el.className = `library-status${type ? ` library-status--${type}` : ''}`;
        if (msg) setTimeout(() => { if (el.textContent === msg) el.textContent = ''; }, 4000);
    }

    function setUploadBusy(busy) {
        document.querySelectorAll('.library-upload-btn').forEach(btn => {
            btn.disabled = busy;
            btn.style.opacity = busy ? '0.55' : '';
            btn.style.cursor  = busy ? 'not-allowed' : '';
        });
    }

    async function fetchKnowledgeFiles() {
        const fileList = document.getElementById('library-file-list');
        if (fileList && !fileList.children.length) {
            fileList.innerHTML = `<div class="lib-loading">
                <span class="lib-loading-dot"></span>
                <span class="lib-loading-dot"></span>
                <span class="lib-loading-dot"></span>
            </div>`;
        }
        try {
            const res  = await fetch('/api/knowledge/files');
            const data = await res.json();
            app.patchState({ knowledgeFiles: data.items || [] }, 'knowledge.fetch');
        } catch (_) {
            app.patchState({ knowledgeFiles: [] }, 'knowledge.fetch.error');
            setLibraryStatus('加载失败，请检查网络连接', 'danger');
        }
    }

    async function fetchQuestionBankItems() {
        try {
            const res = await fetch('/api/knowledge/question-bank');
            const data = await res.json();
            questionBankItems = Array.isArray(data.items) ? data.items : [];
            renderLibraryPanel();
            return questionBankItems;
        } catch (_) {
            questionBankItems = [];
            return [];
        }
    }

    async function deleteKnowledgeFile(filename) {
        if (!filename) return;
        if (!confirm(`确定移除这份资料吗？\n${filename}`)) return;
        setLibraryStatus('正在移除…', 'processing');
        try {
            const res  = await fetch(`/api/knowledge/files/${encodeURIComponent(filename)}`, { method: 'DELETE' });
            const data = await res.json();
            if (data.status !== 'success') { setLibraryStatus(data.message || '移除失败', 'danger'); return; }
            setLibraryStatus(`已移除 ${filename}`, 'success');
            await fetchKnowledgeFiles();
        } catch (_) {
            setLibraryStatus('移除失败', 'danger');
        }
    }

    function previewFile(filename) {
        const url = `/api/knowledge/file/${encodeURIComponent(filename)}`;
        const ext = filename.split('.').pop().toLowerCase();
        const isImage = ['png','jpg','jpeg','gif','webp','svg'].includes(ext);

        const modal = document.createElement('div');
        modal.className = 'library-preview-overlay';
        modal.setAttribute('aria-hidden', 'false');
        modal.onclick = function(e) {
            if (e.target === modal) modal.remove();
        };

        const content = document.createElement('div');
        content.className = 'library-preview-content';
        content.onclick = function(e) { e.stopPropagation(); };

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

        content.appendChild(header);
        content.appendChild(body);
        content.appendChild(footer);
        modal.appendChild(content);
        document.body.appendChild(modal);
        document.body.style.overflow = 'hidden';

        modal.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
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
            const res  = await fetch('/api/upload', { method: 'POST', body: formData });
            const data = await res.json();
            if (data.status === 'success') {
                const msg = data.message || `${data.filename} 已加入资料库`;
                setLibraryStatus(msg, 'success');
                await fetchKnowledgeFiles();
            } else {
                setLibraryStatus(data.message || '上传失败', 'danger');
                await fetchKnowledgeFiles();
            }
        } catch (_) {
            setLibraryStatus('上传失败，请检查网络', 'danger');
        } finally {
            setUploadBusy(false);
        }
    }

    async function clearKnowledgeFiles() {
        const files = (app.state && app.state.knowledgeFiles) || [];
        if (!files.length) { setLibraryStatus('资料库为空', 'muted'); return; }
        if (!confirm('确定清空所有资料吗？这会同时删除对应向量索引。')) return;
        setLibraryStatus('正在清空…', 'processing');
        try {
            const res  = await fetch('/api/knowledge/files', { method: 'DELETE' });
            const data = await res.json();
            if (data.status !== 'success') { setLibraryStatus(data.message || '清空失败', 'danger'); return; }
            setLibraryStatus(`已清空 ${data.removed || 0} 份资料`, 'success');
            await fetchKnowledgeFiles();
        } catch (_) {
            setLibraryStatus('清空失败', 'danger');
        }
    }

    function switchLibraryFilter(filter) {
        currentFilter = filter;
        document.querySelectorAll('#library-nav [data-lib-filter]').forEach(btn => {
            btn.classList.toggle('is-active', btn.getAttribute('data-lib-filter') === filter);
        });
        const TITLES = { all:'全部文件', pdf:'PDF', doc:'文档', excel:'表格', image:'图片', question_bank:'题库', other:'其他' };
        const title = document.getElementById('library-title');
        if (title) title.textContent = TITLES[filter] || '全部文件';
        renderLibraryPanel();
    }

    function filterLibrarySearch(val) {
        currentSearch = val || '';
        renderLibraryPanel();
    }

    app.fetchKnowledgeFiles  = fetchKnowledgeFiles;
    app.fetchQuestionBankItems = fetchQuestionBankItems;
    app.uploadKnowledgeFile  = uploadKnowledgeFile;
    app.clearKnowledgeFiles  = clearKnowledgeFiles;
    app.switchLibraryFilter  = switchLibraryFilter;
    app.filterLibrarySearch  = filterLibrarySearch;
    app.renderKnowledgeShelf = renderLibraryPanel;

    app.subscribeState((_state, source) => {
        if (!source.startsWith('knowledge.')) return;
        renderLibraryPanel();
    });

    document.addEventListener('click', event => {
        const btn = event.target.closest('.lib-file-delete');
        if (!btn) return;
        const rawName = btn.getAttribute('data-raw') || '';
        const filename = rawName
            .replaceAll('&amp;',  '&')
            .replaceAll('&lt;',   '<')
            .replaceAll('&gt;',   '>')
            .replaceAll('&quot;', '"')
            .replaceAll('&#39;',  "'");
        deleteKnowledgeFile(filename);
    });

    window.switchLibraryFilter = switchLibraryFilter;
    window.filterLibrarySearch = filterLibrarySearch;
    window.clearKnowledgeFiles = clearKnowledgeFiles;
    window.previewFile = previewFile;
    window.downloadFile = downloadFile;
})();
