(() => {
    const app = window.AITutorApp || {};

    const localState = {
        currentTab: 'workspace',
        uploadFiles: [],
        selectedUploadFilename: '',
        ocrPreview: null,
        questions: [],
        questionBankItems: [],
        selectedQuestionIds: new Set(),
        selectedPageIndices: [],
        capabilities: null,
        summary: null,
        busyAction: '',
    };

    const TAB_META = {
        workspace: {
            title: '题库加工工作台',
            subtitle: '上传 PDF 后一键执行加工链路，生成的题目会直接沉淀到“已有题库”。',
        },
        uploads: {
            title: '已上传文件',
            subtitle: '这里只保留本批次上传过的 PDF 清单。',
        },
        library: {
            title: '已有题库',
            subtitle: '这里展示已经生成并入库的独立题目卡片，优先保留渲染后的效果与知识标签。',
        },
    };

    function qs(id) {
        return document.getElementById(id);
    }

    function createEl(tag, className, text) {
        const el = document.createElement(tag);
        if (className) el.className = className;
        if (text != null) el.textContent = text;
        return el;
    }

    function getUploadedPdfFiles() {
        return (localState.uploadFiles || []).filter(file => /\.pdf$/i.test(String(file?.filename || '')));
    }

    function syncSelectedUpload() {
        const pdfFiles = getUploadedPdfFiles();
        const current = String(localState.selectedUploadFilename || '').trim();
        if (current && pdfFiles.some(file => String(file?.filename || '').trim() === current)) {
            return;
        }
        localState.selectedUploadFilename = pdfFiles[0]?.filename || '';
    }

    function requireSelectedUpload() {
        const filename = String(localState.selectedUploadFilename || '').trim();
        if (!filename) {
            throw new Error('请先在“已上传文件”里选择一份要加工的 PDF');
        }
        return filename;
    }

    function setWorkbenchStatus(message, tone = '') {
        const el = qs('error-correction-status');
        if (!el) return;
        el.textContent = message || '';
        el.className = `library-status${tone ? ` library-status--${tone}` : ''}`;
    }

    function setBusy(action = '') {
        localState.busyAction = action;
        document.querySelectorAll('#error-correction-overlay .library-upload-btn, #error-correction-overlay .chip-danger-ghost').forEach(button => {
            button.disabled = Boolean(action);
        });
    }

    async function requestJson(url, options = {}) {
        const response = await fetch(url, options);
        const data = await response.json().catch(() => ({}));
        if (!response.ok || data.status === 'error') {
            throw new Error(data.message || `请求失败 (${response.status})`);
        }
        return data;
    }

    function getQuestionExcerpt(question) {
        const blocks = Array.isArray(question?.content_blocks) ? question.content_blocks : [];
        const segments = [];
        for (const block of blocks) {
            if (block?.block_type !== 'text') continue;
            const cleaned = String(block.content || '').replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
            if (!cleaned) continue;
            segments.push(cleaned);
            if (segments.join(' ').length >= 220) break;
        }
        return segments.join(' ').slice(0, 220);
    }

    function getKnowledgeTags(question) {
        const seen = new Set();
        const tags = [];
        const append = (value) => {
            const normalized = String(value || '').replace(/\s+/g, ' ').trim();
            if (!normalized || seen.has(normalized)) return;
            seen.add(normalized);
            tags.push(normalized);
        };
        (Array.isArray(question?.knowledge_tags) ? question.knowledge_tags : []).forEach(append);
        if (!tags.length) append(question?.section_title);
        if (!tags.length) append('待补充知识板块');
        return tags.slice(0, 6);
    }

    function withDisplayTags(question) {
        return {
            ...(question || {}),
            knowledge_tags: getKnowledgeTags(question),
        };
    }

    function escapeHtml(value) {
        return String(value || '')
            .replaceAll('&', '&amp;')
            .replaceAll('<', '&lt;')
            .replaceAll('>', '&gt;')
            .replaceAll('"', '&quot;')
            .replaceAll("'", '&#39;');
    }

    function looksLikeHtml(value) {
        return /<[a-z][\s\S]*>/i.test(String(value || ''));
    }

    function appendRenderedText(container, content, className = '') {
        const block = createEl('div', className || 'error-workbench-rich-text');
        const raw = String(content || '');
        if (looksLikeHtml(raw)) {
            block.innerHTML = app.sanitizeLearningHtml
                ? app.sanitizeLearningHtml(raw)
                : raw;
        } else {
            block.textContent = raw;
        }
        container.appendChild(block);
        app.renderMath?.(block);
    }

    function appendRenderedImage(container, source, altText = '题目图片') {
        const src = String(source || '').trim();
        if (!src) return;
        const figure = createEl('figure', 'error-workbench-image-card');
        const link = document.createElement('a');
        link.className = 'error-workbench-image-link';
        link.href = src;
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        const img = document.createElement('img');
        img.className = 'error-workbench-image';
        img.src = src;
        img.alt = altText;
        img.loading = 'lazy';
        link.appendChild(img);
        figure.appendChild(link);
        container.appendChild(figure);
    }

    function renderQuestionBlocks(question, mount) {
        const blocks = Array.isArray(question?.content_blocks) ? question.content_blocks : [];
        if (!blocks.length) return;
        const body = createEl('div', 'error-workbench-rich-content');
        blocks.forEach((block, index) => {
            if (block?.block_type === 'image') {
                appendRenderedImage(body, block.content, `题目 ${question.question_id || ''} 图片 ${index + 1}`);
                return;
            }
            appendRenderedText(body, block?.content || '', 'error-workbench-rich-text');
        });
        mount.appendChild(body);
    }

    function renderQuestionOptions(question, mount) {
        const options = Array.isArray(question?.options) ? question.options : [];
        if (!options.length) return;
        const optionImages = Array.isArray(question?.option_images) ? question.option_images : [];
        const list = createEl('div', 'error-workbench-option-grid');
        options.forEach((optionText, index) => {
            const item = createEl('div', 'error-workbench-option-card');
            const text = createEl('div', 'error-workbench-option-copy');
            appendRenderedText(text, optionText || '', 'error-workbench-option-text');
            item.appendChild(text);
            if (optionImages[index]) {
                appendRenderedImage(item, optionImages[index], `选项 ${index + 1} 图片`);
            }
            list.appendChild(item);
        });
        mount.appendChild(list);
    }

    function renderQuestionAnswer(question, mount) {
        const answer = String(question?.answer || '').trim();
        if (!answer) return;
        const card = createEl('div', 'error-workbench-answer-card');
        card.appendChild(createEl('div', 'panel-kicker', 'Answer / 解析'));
        appendRenderedText(card, answer, 'error-workbench-answer-copy');
        mount.appendChild(card);
    }

    function renderQuestionMetaBadges(question, mount) {
        const badges = [];
        if (question?.has_formula) badges.push('含公式');
        if (question?.has_image) badges.push('含图片');
        badges.push(...getKnowledgeTags(question));
        if (!badges.length) return;
        const row = createEl('div', 'error-workbench-badge-row');
        badges.forEach(label => row.appendChild(createEl('span', 'error-workbench-badge', label)));
        mount.appendChild(row);
    }

    function buildRenderedQuestionBody(question, options = {}) {
        const { showExcerpt = true, showBadges = true, showAnswer = true } = options;
        const body = createEl('div', 'error-workbench-question-body');
        const excerpt = showExcerpt ? getQuestionExcerpt(question) : '';
        if (excerpt) body.appendChild(createEl('p', 'error-workbench-question-copy', excerpt));
        if (showBadges) renderQuestionMetaBadges(question, body);
        renderQuestionBlocks(question, body);
        renderQuestionOptions(question, body);
        if (showAnswer) renderQuestionAnswer(question, body);
        return body;
    }

    function syncQuestionSelection() {
        // 当前题库加工面板已经移除了“逐题勾选保存”的工作态视图，
        // 新一轮分割后应默认保存全部题目，不能沿用旧批次的 uid 选择结果。
        const ids = new Set(
            (localState.questions || [])
                .map(question => String(question?.uid ?? '').trim())
                .filter(Boolean)
        );
        localState.selectedQuestionIds = ids;
    }

    function syncPageSelection() {
        const layout = localState.ocrPreview?.answer_layout || {};
        const defaults = Array.isArray(layout.question_page_indices) ? layout.question_page_indices.map(Number) : [];
        const allowed = new Set((localState.ocrPreview?.pages || []).map(page => Number(page.page_index)));
        const filtered = (localState.selectedPageIndices || []).map(Number).filter(index => allowed.has(index));
        localState.selectedPageIndices = filtered.length ? filtered : defaults;
    }

    function updateSummaryCopy() {
        const summary = localState.summary || {};
        const parts = [];
        if (summary.upload_count) parts.push(`${summary.upload_count} 份文件`);
        if (summary.question_count) parts.push(`${summary.question_count} 道待入库题`);
        if (summary.question_bank_count) parts.push(`${summary.question_bank_count} 道成品题`);
        qs('error-workbench-summary-text').textContent = parts.length ? parts.join(' · ') : '等待导入题库文件';

        const runtimeCopy = qs('error-workbench-runtime-copy');
        if (!runtimeCopy) return;
        const capabilities = localState.capabilities || {};
        const llmLabel = capabilities.llm_profile ? `${capabilities.llm_profile} / ${capabilities.llm_model_name || '未指定模型'}` : '未检测到 AI 模型';
        const ocrLabel = capabilities.ocr_configured
            ? `PaddleOCR 已配置（${capabilities.paddleocr_model || 'PaddleOCR-VL-1.5'}）`
            : 'PaddleOCR 未配置';
        const endpointHint = capabilities.paddleocr_api_url ? `OCR Endpoint：${capabilities.paddleocr_api_url}` : 'OCR Endpoint：未填写';
        const selectedUpload = String(localState.selectedUploadFilename || '').trim();
        runtimeCopy.textContent = `当前加工对象：${selectedUpload || '尚未选择 PDF'}。当前分割将沿用 AI Tutor 的模型档案：${llmLabel}；${ocrLabel}；${endpointHint}。`;
    }

    function renderSummaryChips() {
        const chipRow = qs('error-workbench-chip-row');
        if (!chipRow) return;
        chipRow.replaceChildren();

        const summary = localState.summary || {};
        const capabilities = localState.capabilities || {};
        const selectedUpload = String(localState.selectedUploadFilename || '').trim();
        const chips = [
            ['已上传', summary.upload_count || 0],
            ['加工对象', selectedUpload || '未选择'],
            ['待入库题目', summary.question_count || 0],
            ['已有题库', summary.question_bank_count || 0],
            ['执行状态', summary.question_count ? '可入库' : '待执行'],
            ['OCR 配置', capabilities.ocr_configured ? '可用' : '缺失'],
        ];

        chips.forEach(([label, value]) => {
            const chip = createEl('div', 'error-workbench-chip');
            chip.appendChild(createEl('span', 'error-workbench-chip-label', label));
            chip.appendChild(createEl('strong', 'error-workbench-chip-value', String(value)));
            chipRow.appendChild(chip);
        });
    }

    function renderUploads() {
        const list = qs('error-correction-upload-list');
        if (!list) return;
        list.replaceChildren();

        const pdfFiles = getUploadedPdfFiles();

        if (!pdfFiles.length) {
            const empty = createEl('div', 'error-workbench-empty');
            empty.appendChild(createEl('div', 'error-workbench-empty-title', '还没有上传 PDF'));
            empty.appendChild(createEl('p', 'error-workbench-empty-copy', '先上传题库 PDF，开始执行后会自动进入识别、分割和题库入库。'));
            list.appendChild(empty);
            return;
        }

        pdfFiles.forEach(file => {
            const isSelected = String(file.filename || '') === String(localState.selectedUploadFilename || '');
            const row = createEl('div', `error-workbench-upload-row${isSelected ? ' is-selected' : ''}`);
            const main = createEl('div', 'error-workbench-upload-main');
            main.appendChild(createEl('div', 'error-workbench-upload-name', file.filename));
            const meta = [];
            if (typeof file.size_bytes === 'number') meta.push(`${(file.size_bytes / 1024).toFixed(file.size_bytes < 1024 ? 0 : 1)} KB`);
            if (file.updated_at) meta.push('已写入工作台');
            if (isSelected) meta.push('当前加工对象');
            main.appendChild(createEl('div', 'error-workbench-upload-meta', meta.join(' · ')));

            const actions = createEl('div', 'error-workbench-upload-actions');
            const targetBtn = createEl(
                'button',
                `error-workbench-mini-btn${isSelected ? ' error-workbench-mini-btn--selected' : ''}`,
                isSelected ? '当前对象' : '设为加工对象'
            );
            targetBtn.type = 'button';
            targetBtn.disabled = isSelected;
            targetBtn.addEventListener('click', () => {
                localState.selectedUploadFilename = file.filename;
                renderWorkspace();
                setWorkbenchStatus(`已将 ${file.filename} 设为当前加工对象`, 'success');
            });
            const downloadBtn = createEl('button', 'error-workbench-mini-btn', '查看');
            downloadBtn.type = 'button';
            downloadBtn.addEventListener('click', () => {
                window.open(`/api/error-correction/files/${encodeURIComponent(file.filename)}`, '_blank', 'noopener,noreferrer');
            });
            const removeBtn = createEl('button', 'error-workbench-mini-btn error-workbench-mini-btn--danger', '移除');
            removeBtn.type = 'button';
            removeBtn.addEventListener('click', () => removeErrorCorrectionFile(file.filename));
            actions.append(targetBtn, downloadBtn, removeBtn);

            row.append(main, actions);
            list.appendChild(row);
        });
    }

    function renderOcrLayoutSummary() {
        const mount = qs('error-correction-layout-summary');
        if (!mount) return;
        mount.replaceChildren();

        const preview = localState.ocrPreview;
        if (!preview?.answer_layout) {
            const empty = createEl('div', 'error-workbench-empty');
            empty.appendChild(createEl('div', 'error-workbench-empty-title', '还没有 OCR 结果'));
            empty.appendChild(createEl('p', 'error-workbench-empty-copy', '上传文件后点击“开始 OCR”，这里会展示答案版式判断和页级预览。'));
            mount.appendChild(empty);
            return;
        }

        const summary = createEl('div', 'error-workbench-layout-card');
        summary.appendChild(createEl('div', 'panel-kicker', 'Answer Layout'));
        summary.appendChild(createEl('div', 'error-workbench-layout-title', preview.answer_layout.label || preview.answer_layout.type || '未识别'));
        const details = [];
        if (preview.answer_layout.first_question_page_index != null) {
            details.push(`首个题目页：第 ${Number(preview.answer_layout.first_question_page_index) + 1} 页`);
        }
        if ((preview.answer_layout.question_page_indices || []).length) {
            details.push(`题目页：${preview.answer_layout.question_page_indices.map(index => index + 1).join('、')}`);
        }
        if ((preview.answer_layout.answer_page_indices || []).length) {
            details.push(`答案页：${preview.answer_layout.answer_page_indices.map(index => index + 1).join('、')}`);
        }
        summary.appendChild(createEl('p', 'error-workbench-layout-copy', details.join(' · ') || '当前未识别到明确答案区。'));
        mount.appendChild(summary);
    }

    function renderPageSelection() {
        const mount = qs('error-correction-page-selection');
        if (!mount) return;
        mount.replaceChildren();

        const layout = localState.ocrPreview?.answer_layout;
        if (!layout || layout.type !== 'separated_tail') return;

        const card = createEl('div', 'error-workbench-page-selection-card');
        card.appendChild(createEl('div', 'panel-kicker', 'Question Page Confirmation'));
        card.appendChild(createEl('p', 'error-workbench-page-selection-copy', '答案集中在后部时，可以在这里微调哪些页面应参与题目分割。'));

        const grid = createEl('div', 'error-workbench-page-toggle-grid');
        (localState.ocrPreview.pages || []).forEach(page => {
            const pageIndex = Number(page.page_index);
            const label = createEl('label', 'error-workbench-page-toggle');
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.checked = localState.selectedPageIndices.includes(pageIndex);
            checkbox.addEventListener('change', () => {
                if (checkbox.checked) {
                    if (!localState.selectedPageIndices.includes(pageIndex)) localState.selectedPageIndices.push(pageIndex);
                } else {
                    localState.selectedPageIndices = localState.selectedPageIndices.filter(index => index !== pageIndex);
                }
            });
            const copy = createEl('span', 'error-workbench-page-toggle-label', `第 ${pageIndex + 1} 页`);
            label.append(checkbox, copy);
            grid.appendChild(label);
        });

        card.appendChild(grid);
        mount.appendChild(card);
    }

    function renderOcrPages() {
        const list = qs('error-correction-ocr-pages');
        if (!list) return;
        list.replaceChildren();

        const pages = localState.ocrPreview?.pages || [];
        if (!pages.length) return;

        pages.forEach(page => {
            const card = createEl('article', 'error-workbench-page-card');
            const header = createEl('div', 'error-workbench-page-card-header');
            header.appendChild(createEl('strong', 'error-workbench-page-title', `第 ${Number(page.page_index) + 1} 页`));
            header.appendChild(createEl('span', 'error-workbench-page-meta', `${page.block_count || 0} 个 block`));
            card.appendChild(header);
            if (page.preview_text) {
                card.appendChild(createEl('p', 'error-workbench-page-preview', page.preview_text));
            }
            const blockList = createEl('div', 'error-workbench-block-list');
            (page.blocks || []).forEach(block => {
                const row = createEl('div', 'error-workbench-block-row');
                row.appendChild(createEl('span', 'error-workbench-block-label', block.label || 'block'));
                row.appendChild(createEl('span', 'error-workbench-block-content', block.content || ''));
                blockList.appendChild(row);
            });
            card.appendChild(blockList);
            list.appendChild(card);
        });
    }

    function renderQuestionBankSummary() {
        const mount = qs('error-correction-library-summary');
        if (!mount) return;
        mount.replaceChildren();

        const summary = createEl('div', 'error-workbench-export-card');
        const totalCount = localState.questionBankItems.length;
        const uploadCount = localState.summary?.upload_count || 0;
        const selectedUpload = String(localState.selectedUploadFilename || '').trim();
        summary.appendChild(createEl('div', 'error-workbench-export-copy', `当前已有 ${totalCount} 道独立题卡，本批次工作台里有 ${uploadCount} 份 PDF。当前加工对象：${selectedUpload || '尚未选择 PDF'}。开始执行后只会处理这 1 份 PDF，并把新分割出的题目直接追加到这里。`));

        const actions = createEl('div', 'error-workbench-upload-actions');
        const runBtn = createEl('button', 'error-workbench-mini-btn', '开始执行');
        runBtn.type = 'button';
        runBtn.addEventListener('click', () => runPipeline());
        const uploadBtn = createEl('button', 'error-workbench-mini-btn', '上传 PDF');
        uploadBtn.type = 'button';
        uploadBtn.addEventListener('click', () => app.triggerErrorCorrectionUpload?.());
        actions.append(runBtn, uploadBtn);
        summary.appendChild(actions);
        mount.appendChild(summary);
    }

    function closeQuestionPreview() {
        qs('error-correction-question-preview')?.remove();
    }

    function buildQuestionPreviewMeta(question) {
        const parts = [];
        const sectionTitle = String(question?.section_title || '').trim();
        const questionType = String(question?.question_type || '').trim();
        if (sectionTitle) parts.push(sectionTitle);
        if (questionType) parts.push(questionType);
        const sourceFiles = Array.isArray(question?.source_files)
            ? question.source_files.map(item => String(item || '').trim()).filter(Boolean)
            : [];
        if (sourceFiles.length) parts.push(`来源：${sourceFiles.join('、')}`);
        return parts.join(' · ');
    }

    function openQuestionPreview(question) {
        const displayQuestion = withDisplayTags(question);
        closeQuestionPreview();

        const questionId = String(displayQuestion.question_id || displayQuestion.library_id || displayQuestion.uid || '').trim();
        const overlay = createEl('div', 'library-preview-overlay error-workbench-preview-overlay');
        overlay.id = 'error-correction-question-preview';
        overlay.setAttribute('aria-hidden', 'false');
        overlay.setAttribute('role', 'dialog');
        overlay.setAttribute('aria-modal', 'true');
        overlay.setAttribute('aria-label', `题目 ${questionId || '详情'}`);
        overlay.tabIndex = -1;
        overlay.addEventListener('click', event => {
            if (event.target === overlay) closeQuestionPreview();
        });

        const content = createEl('div', 'library-preview-content error-workbench-preview-content');
        content.addEventListener('click', event => event.stopPropagation());

        const header = createEl('div', 'library-preview-header error-workbench-preview-header');
        const titleGroup = createEl('div', 'error-workbench-preview-title-group');
        titleGroup.appendChild(createEl('div', 'library-preview-title', `题目 ${questionId || '详情'}`));
        const meta = buildQuestionPreviewMeta(displayQuestion);
        if (meta) titleGroup.appendChild(createEl('div', 'error-workbench-preview-subtitle', meta));
        const closeBtn = createEl('button', 'library-preview-close', '✕');
        closeBtn.type = 'button';
        closeBtn.setAttribute('aria-label', '关闭完整题目');
        closeBtn.addEventListener('click', closeQuestionPreview);
        header.append(titleGroup, closeBtn);

        const body = createEl('div', 'library-preview-body error-workbench-preview-body');
        const card = createEl('article', 'error-workbench-question-card error-workbench-question-card--preview');
        const cardHeader = createEl('div', 'error-workbench-question-header');
        const titleWrap = createEl('div', 'error-workbench-question-title-wrap');
        titleWrap.appendChild(createEl('strong', 'error-workbench-question-title', `题目 ${questionId || '详情'}`));
        if (meta) titleWrap.appendChild(createEl('span', 'error-workbench-question-meta', meta));
        cardHeader.appendChild(titleWrap);
        card.appendChild(cardHeader);
        card.appendChild(buildRenderedQuestionBody(displayQuestion, {
            showExcerpt: false,
            showBadges: true,
            showAnswer: false,
        }));
        body.appendChild(card);

        content.append(header, body);
        overlay.appendChild(content);
        document.body.appendChild(overlay);
        app.renderMath?.(content);
        overlay.focus();
    }

    function renderQuestionBankItems() {
        renderQuestionBankSummary();

        const list = qs('error-correction-library-list');
        if (!list) return;
        list.replaceChildren();

        if (!localState.questionBankItems.length) {
            const empty = createEl('div', 'error-workbench-empty');
            empty.appendChild(createEl('div', 'error-workbench-empty-title', '还没有生成好的题库'));
            empty.appendChild(createEl('p', 'error-workbench-empty-copy', '上传 PDF 后点击“开始执行”，系统会自动生成独立题卡并保存在这里。'));
            list.appendChild(empty);
            return;
        }

        localState.questionBankItems.forEach(question => {
            const questionId = String(question.library_id || question.uid || question.question_id || '');
            const displayQuestion = withDisplayTags(question);
            const card = createEl('article', 'error-workbench-question-card error-workbench-question-card--clickable');
            card.tabIndex = 0;
            card.setAttribute('role', 'button');
            card.setAttribute('aria-label', `查看题目 ${displayQuestion.question_id || questionId} 的完整内容`);
            card.addEventListener('click', event => {
                if (event.target.closest('button, a, input, label')) return;
                openQuestionPreview(displayQuestion);
            });
            card.addEventListener('keydown', event => {
                if (event.key !== 'Enter' && event.key !== ' ') return;
                if (event.target !== card) return;
                event.preventDefault();
                openQuestionPreview(displayQuestion);
            });

            const header = createEl('div', 'error-workbench-question-header');
            const titleWrap = createEl('div', 'error-workbench-question-title-wrap');
            titleWrap.appendChild(createEl('strong', 'error-workbench-question-title', `题目 ${displayQuestion.question_id || questionId}`));
            const metaText = [displayQuestion.section_title, displayQuestion.question_type].filter(Boolean).join(' · ');
            if (metaText) titleWrap.appendChild(createEl('span', 'error-workbench-question-meta', metaText));
            header.appendChild(titleWrap);

            const actions = createEl('div', 'error-workbench-upload-actions');
            const removeBtn = createEl('button', 'error-workbench-mini-btn error-workbench-mini-btn--danger', '移除');
            removeBtn.type = 'button';
            removeBtn.addEventListener('click', event => {
                event.stopPropagation();
                deleteQuestionBankItem(question.library_id);
            });
            actions.appendChild(removeBtn);
            header.appendChild(actions);

            const body = buildRenderedQuestionBody(displayQuestion, {
                showExcerpt: false,
                showBadges: true,
                showAnswer: false,
            });

            card.append(header, body);
            list.appendChild(card);
        });
    }

    function renderCurrentTab() {
        const meta = TAB_META[localState.currentTab] || TAB_META.workspace;
        qs('error-correction-title').textContent = meta.title;
        qs('error-workbench-subtitle').textContent = meta.subtitle;

        document.querySelectorAll('#error-workbench-nav [data-ec-tab]').forEach(button => {
            button.classList.toggle('is-active', button.getAttribute('data-ec-tab') === localState.currentTab);
        });
        document.querySelectorAll('[data-ec-panel]').forEach(panel => {
            const isCurrent = panel.getAttribute('data-ec-panel') === localState.currentTab;
            panel.hidden = !isCurrent;
            panel.style.display = isCurrent ? 'grid' : 'none';
        });
    }

    function renderWorkspace() {
        updateSummaryCopy();
        renderSummaryChips();
        renderUploads();
        renderQuestionBankItems();
        renderCurrentTab();
    }

    async function refreshWorkspace() {
        setBusy('refresh');
        try {
            const [data, questionBankData] = await Promise.all([
                requestJson('/api/error-correction/status'),
                requestJson('/api/knowledge/question-bank'),
            ]);
            localState.uploadFiles = data.upload_files || [];
            localState.ocrPreview = data.ocr_preview || null;
            localState.questions = data.questions || [];
            localState.questionBankItems = questionBankData.items || [];
            localState.summary = data.summary || null;
            if (localState.summary) {
                localState.summary.question_bank_count = localState.questionBankItems.length;
            }
            localState.capabilities = data.capabilities || null;
            syncSelectedUpload();
            syncQuestionSelection();
            syncPageSelection();
            renderWorkspace();
        } catch (error) {
            setWorkbenchStatus(error.message || '加载失败', 'danger');
        } finally {
            setBusy('');
        }
    }

    async function uploadFiles(files) {
        const nextFiles = Array.from(files || []);
        if (!nextFiles.length) return;
        const formData = new FormData();
        nextFiles.forEach(file => formData.append('files', file));
        setBusy('upload');
        setWorkbenchStatus(`正在上传 ${nextFiles.length} 份文件…`, 'processing');
        try {
            const data = await requestJson('/api/error-correction/upload', {
                method: 'POST',
                body: formData,
            });
            setWorkbenchStatus(data.message || '上传完成', 'success');
            localState.currentTab = 'uploads';
            await refreshWorkspace();
            app.setStatusBanner?.(data.message || '题库文件已加入工作台', 'success');
        } catch (error) {
            setWorkbenchStatus(error.message || '上传失败', 'danger');
        } finally {
            setBusy('');
        }
    }

    async function removeErrorCorrectionFile(filename) {
        if (!filename) return;
        setBusy('remove');
        try {
            const data = await requestJson(`/api/error-correction/files/${encodeURIComponent(filename)}`, {
                method: 'DELETE',
            });
            setWorkbenchStatus(data.message || '已移除文件', 'success');
            await refreshWorkspace();
        } catch (error) {
            setWorkbenchStatus(error.message || '移除失败', 'danger');
        } finally {
            setBusy('');
        }
    }

    async function runOcr() {
        let selectedFilename = '';
        try {
            selectedFilename = requireSelectedUpload();
        } catch (error) {
            setWorkbenchStatus(error.message || '请选择加工对象', 'danger');
            return;
        }
        setBusy('ocr');
        setWorkbenchStatus(`正在对 ${selectedFilename} 执行 OCR…`, 'processing');
        try {
            const data = await requestJson('/api/error-correction/ocr', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ selected_filename: selectedFilename }),
            });
            localState.selectedUploadFilename = data.selected_filename || selectedFilename;
            localState.ocrPreview = {
                pages: data.pages || [],
                answer_layout: data.answer_layout || null,
                updated_at: new Date().toISOString(),
            };
            localState.summary = {
                ...(localState.summary || {}),
                ocr_page_count: (data.pages || []).length,
            };
            localState.currentTab = 'workspace';
            syncPageSelection();
            renderWorkspace();
            setWorkbenchStatus(data.message || 'OCR 完成', 'success');
            app.setStatusBanner?.(data.message || '题库 OCR 完成', 'success');
        } catch (error) {
            setWorkbenchStatus(error.message || 'OCR 失败', 'danger');
        } finally {
            setBusy('');
        }
    }

    async function runSplit() {
        let selectedFilename = '';
        try {
            selectedFilename = requireSelectedUpload();
        } catch (error) {
            setWorkbenchStatus(error.message || '请选择加工对象', 'danger');
            return;
        }
        const layout = localState.ocrPreview?.answer_layout || {};
        const payload = {
            confirmed_answer_layout: layout.type || '',
            selected_page_indices: layout.type === 'separated_tail' ? localState.selectedPageIndices : [],
            selected_filename: selectedFilename,
        };
        setBusy('split');
        setWorkbenchStatus(`正在对 ${selectedFilename} 分割题目…`, 'processing');
        try {
            const data = await requestJson('/api/error-correction/split', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            localState.selectedUploadFilename = data.selected_filename || selectedFilename;
            localState.questions = data.questions || [];
            localState.summary = {
                ...(localState.summary || {}),
                question_count: localState.questions.length,
            };
            syncQuestionSelection();
            localState.currentTab = 'workspace';
            renderWorkspace();
            if (Array.isArray(data.warnings) && data.warnings.length) {
                setWorkbenchStatus(data.warnings[0], 'danger');
            } else {
                setWorkbenchStatus(data.message || '分割完成', 'success');
            }
            app.setStatusBanner?.(data.message || '题目分割完成', 'success');
        } catch (error) {
            setWorkbenchStatus(error.message || '分割失败', 'danger');
        } finally {
            setBusy('');
        }
    }

    async function saveQuestionsToLibrary() {
        const sourceFiles = String(localState.selectedUploadFilename || '').trim()
            ? [String(localState.selectedUploadFilename || '').trim()]
            : [];
        setBusy('save');
        setWorkbenchStatus('正在保存到资料库题库…', 'processing');
        try {
            const data = await requestJson('/api/knowledge/question-bank', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    selected_ids: Array.from(localState.selectedQuestionIds),
                    source_files: sourceFiles,
                }),
            });
            localState.questionBankItems = data.items || [];
            localState.summary = {
                ...(localState.summary || {}),
                question_bank_count: localState.questionBankItems.length,
            };
            localState.currentTab = 'library';
            renderWorkspace();
            setWorkbenchStatus(data.message || '已保存到题库', 'success');
            await app.fetchQuestionBankItems?.();
            app.setStatusBanner?.(data.message || '已保存到资料库题库', 'success');
        } catch (error) {
            setWorkbenchStatus(error.message || '保存失败', 'danger');
        } finally {
            setBusy('');
        }
    }

    async function clearWorkspace() {
        setBusy('clear');
        try {
            const data = await requestJson('/api/error-correction/workspace', { method: 'DELETE' });
            localState.uploadFiles = [];
            localState.ocrPreview = null;
            localState.questions = [];
            localState.summary = {
                upload_count: 0,
                ocr_page_count: 0,
                question_count: 0,
                question_bank_count: localState.questionBankItems.length,
            };
            localState.selectedUploadFilename = '';
            localState.selectedQuestionIds = new Set();
            localState.selectedPageIndices = [];
            localState.currentTab = 'workspace';
            renderWorkspace();
            setWorkbenchStatus(data.message || '已清空', 'success');
        } catch (error) {
            setWorkbenchStatus(error.message || '清空失败', 'danger');
        } finally {
            setBusy('');
        }
    }

    async function deleteQuestionBankItem(libraryId) {
        if (!libraryId) return;
        setBusy('remove-library-item');
        try {
            const data = await requestJson(`/api/knowledge/question-bank/${encodeURIComponent(libraryId)}`, {
                method: 'DELETE',
            });
            localState.questionBankItems = localState.questionBankItems.filter(item => String(item.library_id || '') !== String(libraryId));
            localState.summary = {
                ...(localState.summary || {}),
                question_bank_count: localState.questionBankItems.length,
            };
            renderWorkspace();
            setWorkbenchStatus(data.message || '已从题库移除', 'success');
            await app.fetchQuestionBankItems?.();
        } catch (error) {
            setWorkbenchStatus(error.message || '移除失败', 'danger');
        } finally {
            setBusy('');
        }
    }

    async function clearQuestionBank() {
        setBusy('clear-library');
        try {
            const data = await requestJson('/api/knowledge/question-bank', { method: 'DELETE' });
            localState.questionBankItems = [];
            localState.summary = {
                ...(localState.summary || {}),
                question_bank_count: 0,
            };
            renderWorkspace();
            setWorkbenchStatus(data.message || `已清空 ${data.removed || 0} 道题目`, 'success');
            await app.fetchQuestionBankItems?.();
        } catch (error) {
            setWorkbenchStatus(error.message || '清空题库失败', 'danger');
        } finally {
            setBusy('');
        }
    }

    async function runPipeline() {
        let selectedFilename = '';
        try {
            selectedFilename = requireSelectedUpload();
        } catch (error) {
            setWorkbenchStatus(error.message || '请选择加工对象', 'danger');
            return;
        }
        setBusy('pipeline');
        setWorkbenchStatus(`正在处理 ${selectedFilename}…`, 'processing');
        try {
            const ocrData = await requestJson('/api/error-correction/ocr', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ selected_filename: selectedFilename }),
            });
            localState.selectedUploadFilename = ocrData.selected_filename || selectedFilename;
            localState.ocrPreview = {
                pages: ocrData.pages || [],
                answer_layout: ocrData.answer_layout || null,
                updated_at: new Date().toISOString(),
            };
            localState.summary = {
                ...(localState.summary || {}),
                ocr_page_count: (ocrData.pages || []).length,
            };
            syncPageSelection();

            setWorkbenchStatus(`OCR 完成，正在分割 ${selectedFilename}…`, 'processing');
            const layout = localState.ocrPreview?.answer_layout || {};
            const splitData = await requestJson('/api/error-correction/split', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    confirmed_answer_layout: layout.type || '',
                    selected_page_indices: layout.type === 'separated_tail' ? localState.selectedPageIndices : [],
                    selected_filename: selectedFilename,
                }),
            });
            localState.selectedUploadFilename = splitData.selected_filename || selectedFilename;
            localState.questions = splitData.questions || [];
            localState.summary = {
                ...(localState.summary || {}),
                question_count: localState.questions.length,
            };
            syncQuestionSelection();
            if (!localState.questions.length) {
                throw new Error((splitData.warnings && splitData.warnings[0]) || '未生成可保存的题目');
            }

            setWorkbenchStatus(`分割完成，正在把 ${selectedFilename} 写入已有题库…`, 'processing');
            const saveData = await requestJson('/api/knowledge/question-bank', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    selected_ids: Array.from(localState.selectedQuestionIds),
                    source_files: [selectedFilename],
                }),
            });
            localState.questionBankItems = saveData.items || [];
            localState.summary = {
                ...(localState.summary || {}),
                question_bank_count: localState.questionBankItems.length,
            };
            localState.currentTab = 'library';
            renderWorkspace();

            const warning = Array.isArray(splitData.warnings) && splitData.warnings.length ? `（提示：${splitData.warnings[0]}）` : '';
            const successMessage = saveData.message || `已保存 ${saveData.saved_count || 0} 道题到已有题库`;
            setWorkbenchStatus(`${successMessage}${warning}`, 'success');
            await app.fetchQuestionBankItems?.();
            app.setStatusBanner?.(successMessage, 'success');
        } catch (error) {
            setWorkbenchStatus(error.message || '执行失败', 'danger');
        } finally {
            setBusy('');
        }
    }

    function switchTab(tab) {
        localState.currentTab = TAB_META[tab] ? tab : 'workspace';
        renderCurrentTab();
    }

    function openPanel() {
        const overlay = qs('error-correction-overlay');
        if (!overlay) return;
        overlay.classList.add('open');
        overlay.setAttribute('aria-hidden', 'false');
        document.body.style.overflow = 'hidden';
        refreshWorkspace();
    }

    function closePanel(event) {
        if (event && event.target !== event.currentTarget) return;
        closeQuestionPreview();
        const overlay = qs('error-correction-overlay');
        if (!overlay) return;
        overlay.classList.remove('open');
        overlay.setAttribute('aria-hidden', 'true');
        document.body.style.overflow = '';
    }

    function openErrorCorrectionConfig() {
        closePanel();
        window.setTimeout(() => {
            app.openLocalConfigPanel?.('error_correction');
        }, 0);
    }

    function bindDomEvents() {
        const fileInput = qs('error-correction-file-input');
        if (fileInput && fileInput.dataset.bound !== '1') {
            fileInput.dataset.bound = '1';
            fileInput.addEventListener('change', async function handleErrorCorrectionUpload() {
                if (!this.files.length) return;
                await uploadFiles(this.files);
                this.value = '';
            });
        }

        document.addEventListener('keydown', event => {
            if (event.key === 'Escape' && qs('error-correction-overlay')?.classList.contains('open')) {
                if (qs('error-correction-question-preview')) {
                    closeQuestionPreview();
                    return;
                }
                closePanel();
            }
        });
    }

    app.openErrorCorrectionPanel = openPanel;
    app.closeErrorCorrectionPanel = closePanel;
    app.triggerErrorCorrectionUpload = function triggerErrorCorrectionUpload() {
        qs('error-correction-file-input')?.click();
    };
    app.refreshErrorCorrectionWorkspace = refreshWorkspace;
    app.runErrorCorrectionOcr = runOcr;
    app.runErrorCorrectionSplit = runSplit;
    app.runErrorCorrectionPipeline = runPipeline;
    app.exportErrorCorrectionQuestions = saveQuestionsToLibrary;
    app.saveErrorCorrectionQuestionsToLibrary = saveQuestionsToLibrary;
    app.clearErrorCorrectionWorkspace = clearWorkspace;
    app.clearErrorCorrectionQuestionBank = clearQuestionBank;
    app.switchErrorCorrectionTab = switchTab;
    app.openErrorCorrectionConfig = openErrorCorrectionConfig;
    app.buildRenderedQuestionBody = buildRenderedQuestionBody;
    app.renderErrorCorrectionQuestionBlocks = renderQuestionBlocks;
    app.renderErrorCorrectionQuestionOptions = renderQuestionOptions;
    app.renderErrorCorrectionQuestionAnswer = renderQuestionAnswer;
    app.renderErrorCorrectionQuestionMetaBadges = renderQuestionMetaBadges;
    app.openErrorCorrectionQuestionPreview = openQuestionPreview;
    app.closeErrorCorrectionQuestionPreview = closeQuestionPreview;

    window.openErrorCorrectionPanel = () => app.openErrorCorrectionPanel();
    window.closeErrorCorrectionPanel = event => app.closeErrorCorrectionPanel(event);
    window.openErrorCorrectionConfig = () => app.openErrorCorrectionConfig();
    window.triggerErrorCorrectionUpload = () => app.triggerErrorCorrectionUpload();
    window.refreshErrorCorrectionWorkspace = () => app.refreshErrorCorrectionWorkspace();
    window.runErrorCorrectionOcr = () => app.runErrorCorrectionOcr();
    window.runErrorCorrectionSplit = () => app.runErrorCorrectionSplit();
    window.runErrorCorrectionPipeline = () => app.runErrorCorrectionPipeline();
    window.exportErrorCorrectionQuestions = () => app.exportErrorCorrectionQuestions();
    window.saveErrorCorrectionQuestionsToLibrary = () => app.saveErrorCorrectionQuestionsToLibrary();
    window.clearErrorCorrectionWorkspace = () => app.clearErrorCorrectionWorkspace();
    window.clearQuestionBankFromWorkbench = () => app.clearErrorCorrectionQuestionBank();
    window.switchErrorCorrectionTab = tab => app.switchErrorCorrectionTab(tab);

    bindDomEvents();
})();
