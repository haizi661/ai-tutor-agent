(() => {
    const app = window.AITutorApp || {};
    let activeAgentJobId = '';
    let activeRecordId = '';
    let lastAgentTrace = [];
    let recordsCache = [];

    function qs(id) {
        return document.getElementById(id);
    }

    function createEl(tag, className, text) {
        const el = document.createElement(tag);
        if (className) el.className = className;
        if (text != null) el.textContent = text;
        return el;
    }

    function setStatus(message, tone = '') {
        const el = qs('matlab-experiment-status');
        if (!el) return;
        el.textContent = message || '';
        el.className = `matlab-experiment-status${tone ? ` matlab-experiment-status--${tone}` : ''}`;
    }

    function setBusy(busy) {
        const runButton = qs('matlab-run-btn');
        if (runButton) runButton.disabled = Boolean(busy);
        const newButton = qs('matlab-new-record-btn');
        if (newButton) newButton.disabled = Boolean(busy);
        const cancelButton = qs('matlab-cancel-btn');
        if (cancelButton) {
            cancelButton.hidden = !busy;
            cancelButton.disabled = !busy || !activeAgentJobId;
        }
    }

    async function requestJson(url, options = {}) {
        const response = await fetch(url, options);
        const data = await response.json().catch(() => ({}));
        if (!response.ok || data.status === 'error') {
            throw new Error(data.message || `请求失败 (${response.status})`);
        }
        return data;
    }

    function phaseLabel(phase) {
        const labels = {
            start: '开始',
            environment: '环境检查',
            generate_code: '生成代码',
            code_saved: '保存代码',
            execute: '执行 MATLAB',
            execution_error: '报错反馈',
            policy_reject: '校验反馈',
            policy_warning: '校验提示',
            collect_results: '收集结果',
            analyze: '分析结果',
            done: '完成',
            cancelled: '中断',
            failed: '失败',
        };
        return labels[phase] || '流程';
    }

    function buildTracePanel(trace = [], open = false) {
        if (!trace.length) return null;
        const details = document.createElement('details');
        details.className = 'matlab-experiment-trace-panel';
        details.open = Boolean(open);
        const summary = document.createElement('summary');
        summary.textContent = `执行过程（${trace.length} 步）`;
        details.appendChild(summary);
        const list = createEl('div', 'matlab-experiment-trace');
        trace.forEach(item => {
            const row = createEl('div', `matlab-experiment-trace-item matlab-experiment-trace-item--${item.phase || 'step'}`);
            row.appendChild(createEl('span', 'matlab-experiment-trace-phase', phaseLabel(item.phase)));
            row.appendChild(createEl('span', 'matlab-experiment-trace-copy', item.message || '处理中'));
            if (item.error_summary) {
                const error = createEl('pre', 'matlab-experiment-trace-error');
                error.textContent = item.error_summary;
                row.appendChild(error);
            }
            list.appendChild(row);
        });
        details.appendChild(list);
        return details;
    }

    function renderTrace(trace = []) {
        const mount = qs('matlab-experiment-results');
        if (!mount || !trace.length) return;
        lastAgentTrace = trace.slice();
        mount.innerHTML = '';
        const panel = buildTracePanel(lastAgentTrace, true);
        if (panel) mount.appendChild(panel);
    }

    async function refreshStatus() {
        try {
            const data = await requestJson('/api/matlab-experiment/status');
            const install = data.available ? '可用' : '未找到';
            setStatus(`MATLAB ${install}：${data.matlab_executable || ''}`, data.available ? 'success' : 'warning');
            return data;
        } catch (error) {
            setStatus(`环境检测失败：${error.message}`, 'danger');
            return null;
        }
    }

    function fillExamplePrompt() {
        const input = qs('matlab-agent-prompt-input');
        if (!input) return;
        input.value = '建立一个单位负反馈闭环控制系统。前向通道由比例控制器 K=10 和被控对象 G(s)=1/(s^2+2s+5) 串联组成。请先绘制系统方块图，标注参考输入、误差、控制器、被控对象、反馈支路；然后用 Control System Toolbox 计算闭环传递函数 T(s)，输出分子分母、多项式形式、极点和零点；最后绘制阶跃响应曲线，并计算超调量、峰值时间、调节时间和稳态误差。';
        input.focus();
    }

    function buildMetricGrid(metrics) {
        const grid = createEl('div', 'matlab-experiment-metrics');
        const labelMap = {
            final_value: '终值',
            steady_state_error: '稳态误差',
            rise_time: '上升时间',
            rise_time_10to90: '上升时间',
            overshoot: '超调',
            overshoot_percent: '超调',
            peak_time: '峰值时间',
            settling_time: '调节时间',
            settling_time_2percent: '调节时间',
            settling_time_2pct: '调节时间',
            sample_count: '采样点',
        };
        const entries = Object.entries(metrics || {});
        const items = entries.length ? entries.map(([key, value]) => [labelMap[key] || key, value]) : [['指标', '-']];
        items.forEach(([label, value]) => {
            const card = createEl('div', 'matlab-experiment-metric');
            card.appendChild(createEl('span', '', label));
            const formatted = typeof value === 'number' && Number.isFinite(value)
                ? value.toFixed(label === '采样点' ? 0 : 4)
                : String(value ?? '-');
            card.appendChild(createEl('strong', '', formatted));
            grid.appendChild(card);
        });
        return grid;
    }

    function appendRunPayload(container, payload, options = {}) {
        const trace = Array.isArray(payload.trace) && payload.trace.length ? payload.trace : [];
        const tracePanel = buildTracePanel(trace, Boolean(options.openTrace));
        if (tracePanel) container.appendChild(tracePanel);
        if (!tracePanel && payload.mode === 'agent') {
            const missingTrace = document.createElement('details');
            missingTrace.className = 'matlab-experiment-trace-panel';
            const summary = document.createElement('summary');
            summary.textContent = '执行过程（未返回）';
            missingTrace.appendChild(summary);
            missingTrace.appendChild(createEl('div', 'matlab-experiment-trace-missing', '本次结果未包含执行过程。请查看本地 run_trace.json，或刷新页面后重新运行。'));
            container.appendChild(missingTrace);
        }

        const result = payload.result || {};
        const titleRow = createEl('div', 'matlab-experiment-result-header');
        titleRow.appendChild(createEl('div', 'panel-kicker', payload.run_id || 'MATLAB run'));
        const links = createEl('div', 'matlab-experiment-links');
        const artifacts = payload.artifacts || {};
        [
            ['脚本', artifacts.active_script || artifacts.script],
            ['JSON', artifacts.result_json],
            ['主图', artifacts.plot_png],
        ].forEach(([label, href]) => {
            if (!href) return;
            const link = document.createElement('a');
            link.href = href;
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
            link.textContent = label;
            links.appendChild(link);
        });
        (artifacts.plots || []).forEach((href, index) => {
            const link = document.createElement('a');
            link.href = href;
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
            link.textContent = `图 ${index + 1}`;
            links.appendChild(link);
        });
        titleRow.appendChild(links);
        container.appendChild(titleRow);

        const plotSrc = artifacts.plot_png || (artifacts.plots || [])[0];
        if (plotSrc) {
            const figure = createEl('figure', 'matlab-experiment-figure');
            const img = document.createElement('img');
            img.src = plotSrc;
            img.alt = 'MATLAB 仿真结果图';
            figure.appendChild(img);
            container.appendChild(figure);
        }

        container.appendChild(buildMetricGrid(result.metrics || {}));

        if (payload.analysis) {
            const analysis = createEl('div', 'matlab-experiment-analysis');
            analysis.textContent = payload.analysis;
            container.appendChild(analysis);
        }

        if (Array.isArray(payload.attempts) && payload.attempts.length) {
            const attempts = createEl('div', 'matlab-experiment-attempts');
            payload.attempts.forEach(item => {
                const details = document.createElement('details');
                details.className = 'matlab-experiment-attempt';
                const summary = document.createElement('summary');
                summary.textContent = `第 ${item.attempt} 次：${item.status}`;
                details.appendChild(summary);
                if (item.message || item.stderr || item.stdout || item.policy_warning) {
                    const log = createEl('pre', 'matlab-experiment-log');
                    log.textContent = [item.policy_warning, item.message, item.stderr, item.stdout].filter(Boolean).join('\n');
                    details.appendChild(log);
                }
                const code = createEl('pre', 'matlab-experiment-code');
                code.textContent = item.code || '本次未返回代码内容。';
                details.appendChild(code);
                attempts.appendChild(details);
            });
            container.appendChild(attempts);
        }

        const stdout = String(payload.stdout || '').trim();
        const stderr = String(payload.stderr || '').trim();
        if (stdout || stderr) {
            const log = createEl('pre', 'matlab-experiment-log');
            log.textContent = [stdout, stderr].filter(Boolean).join('\n');
            container.appendChild(log);
        }
    }

    function renderResult(payload) {
        const mount = qs('matlab-experiment-results');
        if (!mount) return;
        mount.innerHTML = '';
        const trace = Array.isArray(payload.trace) && payload.trace.length ? payload.trace : lastAgentTrace;
        if (trace.length) payload = { ...payload, trace };
        appendRunPayload(mount, payload, { openTrace: false });
    }

    function renderRecordList(records = []) {
        const list = qs('matlab-record-list');
        if (!list) return;
        list.innerHTML = '';
        if (!records.length) {
            list.appendChild(createEl('div', 'matlab-record-empty', '暂无历史记录'));
            return;
        }
        records.forEach(record => {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = `matlab-record-item${record.record_id === activeRecordId ? ' active' : ''}`;
            button.onclick = () => selectMatlabRecord(record.record_id);
            button.appendChild(createEl('strong', '', record.title || record.record_id));
            const meta = `${record.status || 'draft'} · ${(record.runs || []).length} 次`;
            button.appendChild(createEl('span', '', meta));
            list.appendChild(button);
        });
    }

    async function refreshRecords() {
        try {
            const data = await requestJson('/api/matlab-experiment/records');
            recordsCache = data.records || [];
            renderRecordList(recordsCache);
            return recordsCache;
        } catch (error) {
            const list = qs('matlab-record-list');
            if (list) {
                list.innerHTML = '';
                list.appendChild(createEl('div', 'matlab-record-empty', `历史加载失败：${error.message}`));
            }
            return [];
        }
    }

    function renderRecordDetail(data) {
        const mount = qs('matlab-experiment-results');
        if (!mount) return;
        const record = data.record || {};
        const runs = data.runs || [];
        mount.innerHTML = '';
        const promptInput = qs('matlab-agent-prompt-input');
        if (promptInput) promptInput.value = record.user_prompt || data.latest?.user_prompt || promptInput.value || '';

        const heading = createEl('div', 'matlab-record-detail-heading');
        heading.appendChild(createEl('strong', '', record.title || record.record_id || '新仿真'));
        heading.appendChild(createEl('span', '', `${runs.length} 次运行记录`));
        mount.appendChild(heading);

        if (!runs.length) {
            mount.appendChild(createEl('div', 'matlab-experiment-empty', '这是一个新的仿真记录。输入或修改需求后点击“发送并执行”。'));
            return;
        }

        runs.forEach((run, index) => {
            const isLatest = index === runs.length - 1;
            const details = document.createElement('details');
            details.className = 'matlab-record-run';
            details.open = isLatest;
            const summary = document.createElement('summary');
            summary.textContent = `${run.run_id || `第 ${index + 1} 次运行`} · ${run.status || 'unknown'}`;
            details.appendChild(summary);
            const body = createEl('div', 'matlab-record-run-body');
            appendRunPayload(body, run, { openTrace: false });
            details.appendChild(body);
            mount.appendChild(details);
        });
    }

    async function createMatlabRecord() {
        const prompt = String(qs('matlab-agent-prompt-input')?.value || '').trim();
        setBusy(true);
        try {
            const data = await requestJson('/api/matlab-experiment/records', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_prompt: prompt }),
            });
            activeRecordId = data.record.record_id;
            await refreshRecords();
            renderRecordDetail({ record: data.record, runs: [], latest: null });
            setStatus(`已创建新仿真记录：${activeRecordId}`, 'success');
        } catch (error) {
            setStatus(`创建记录失败：${error.message}`, 'danger');
        } finally {
            setBusy(false);
        }
    }

    async function selectMatlabRecord(recordId) {
        if (!recordId) return;
        activeRecordId = recordId;
        renderRecordList(recordsCache);
        try {
            const data = await requestJson(`/api/matlab-experiment/records/${encodeURIComponent(recordId)}`);
            renderRecordDetail(data);
            setStatus(`已恢复仿真记录：${data.record?.title || recordId}`, 'success');
        } catch (error) {
            setStatus(`恢复记录失败：${error.message}`, 'danger');
        }
    }

    async function ensureActiveRecord(userPrompt) {
        if (activeRecordId) return activeRecordId;
        const data = await requestJson('/api/matlab-experiment/records', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_prompt: userPrompt }),
        });
        activeRecordId = data.record.record_id;
        await refreshRecords();
        return activeRecordId;
    }

    async function runPresetExperiment() {
        setBusy(true);
        setStatus('正在启动 MATLAB 并执行预设仿真...', 'info');
        try {
            const data = await requestJson('/api/matlab-experiment/run', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    preset: 'first_order_step',
                    gain: 1,
                    time_constant: 1,
                    duration: 8,
                    step_size: 0.02,
                    timeout_seconds: 300,
                }),
            });
            renderResult(data);
            setStatus(`预设仿真完成：${data.run_id || ''}`, 'success');
        } catch (error) {
            setStatus(`预设仿真失败：${error.message}`, 'danger');
        } finally {
            setBusy(false);
        }
    }

    async function runExperiment() {
        const userPrompt = String(qs('matlab-agent-prompt-input')?.value || '').trim();
        if (!userPrompt) {
            setStatus('请先输入自然语言仿真需求。', 'warning');
            return;
        }
        lastAgentTrace = [];
        setBusy(true);
        setStatus('Agent 正在生成 MATLAB 代码并执行仿真...', 'info');
        const startedAt = Date.now();
        const timer = window.setInterval(() => {
            const seconds = Math.floor((Date.now() - startedAt) / 1000);
            setStatus(`Agent 正在生成/执行/必要时修复代码... ${seconds}s`, 'info');
        }, 1000);
        let pollTimer = null;
        try {
            const recordId = await ensureActiveRecord(userPrompt);
            const started = await requestJson('/api/matlab-experiment/agent-jobs', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    record_id: recordId,
                    user_prompt: userPrompt,
                    max_iterations: 3,
                    timeout_seconds: 300,
                }),
            });
            const jobId = started.job_id;
            activeAgentJobId = jobId;
            setBusy(true);
            await new Promise((resolve, reject) => {
                pollTimer = window.setInterval(async () => {
                    try {
                        const job = await requestJson(`/api/matlab-experiment/agent-jobs/${encodeURIComponent(jobId)}`);
                        renderTrace(job.trace || []);
                        if (job.latest_message) setStatus(job.latest_message, 'info');
                        if (job.status === 'completed') {
                            window.clearInterval(pollTimer);
                            if (job.result?.record_id) activeRecordId = job.result.record_id;
                            renderResult(job.result);
                            await refreshRecords();
                            setStatus(`Agent 执行完成：${job.result?.run_id || ''}`, 'success');
                            resolve();
                        } else if (job.status === 'failed') {
                            window.clearInterval(pollTimer);
                            if (job.result?.record_id) activeRecordId = job.result.record_id;
                            if (job.result) renderResult(job.result);
                            await refreshRecords();
                            reject(new Error(job.error || job.result?.message || 'Agent 执行失败'));
                        } else if (job.status === 'cancelled') {
                            window.clearInterval(pollTimer);
                            if (job.result?.record_id) activeRecordId = job.result.record_id;
                            if (job.result) renderResult(job.result);
                            await refreshRecords();
                            setStatus('Agent 已中断。', 'warning');
                            resolve();
                        }
                    } catch (error) {
                        window.clearInterval(pollTimer);
                        reject(error);
                    }
                }, 1200);
            });
        } catch (error) {
            setStatus(`Agent 执行失败：${error.message}`, 'danger');
        } finally {
            window.clearInterval(timer);
            if (pollTimer) window.clearInterval(pollTimer);
            activeAgentJobId = '';
            setBusy(false);
        }
    }

    async function cancelExperiment() {
        if (!activeAgentJobId) return;
        const cancelButton = qs('matlab-cancel-btn');
        if (cancelButton) cancelButton.disabled = true;
        try {
            const job = await requestJson(`/api/matlab-experiment/agent-jobs/${encodeURIComponent(activeAgentJobId)}/cancel`, {
                method: 'POST',
            });
            renderTrace(job.trace || []);
            setStatus(job.latest_message || '已请求中断 MATLAB Agent。', 'warning');
        } catch (error) {
            setStatus(`中断失败：${error.message}`, 'danger');
            if (cancelButton) cancelButton.disabled = false;
        }
    }

    async function openPanel() {
        const overlay = qs('matlab-experiment-overlay');
        if (!overlay) return;
        overlay.classList.add('open');
        overlay.setAttribute('aria-hidden', 'false');
        document.body.style.overflow = 'hidden';
        refreshStatus();
        const records = await refreshRecords();
        if (!activeRecordId && records.length) {
            selectMatlabRecord(records[0].record_id);
        }
    }

    function closePanel(event) {
        if (event && event.target !== event.currentTarget) return;
        const overlay = qs('matlab-experiment-overlay');
        if (!overlay) return;
        overlay.classList.remove('open');
        overlay.setAttribute('aria-hidden', 'true');
        document.body.style.overflow = '';
    }

    app.openMatlabExperimentPanel = openPanel;
    app.closeMatlabExperimentPanel = closePanel;
    app.refreshMatlabExperimentStatus = refreshStatus;
    app.runMatlabExperiment = runExperiment;
    app.runMatlabPresetExperiment = runPresetExperiment;
    app.fillMatlabExamplePrompt = fillExamplePrompt;
    app.cancelMatlabExperiment = cancelExperiment;
    app.createMatlabRecord = createMatlabRecord;
    app.selectMatlabRecord = selectMatlabRecord;

    window.openMatlabExperimentPanel = () => app.openMatlabExperimentPanel();
    window.closeMatlabExperimentPanel = event => app.closeMatlabExperimentPanel(event);
    window.refreshMatlabExperimentStatus = () => app.refreshMatlabExperimentStatus();
    window.runMatlabExperiment = () => app.runMatlabExperiment();
    window.runMatlabPresetExperiment = () => app.runMatlabPresetExperiment();
    window.fillMatlabExamplePrompt = () => app.fillMatlabExamplePrompt();
    window.cancelMatlabExperiment = () => app.cancelMatlabExperiment();
    window.createMatlabRecord = () => app.createMatlabRecord();
    window.selectMatlabRecord = recordId => app.selectMatlabRecord(recordId);
})();
