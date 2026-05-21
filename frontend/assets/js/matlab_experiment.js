(() => {
    const app = window.AITutorApp || {};
    let activeAgentJobId = '';

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
        const cancelButton = qs('matlab-cancel-btn');
        if (cancelButton) {
            cancelButton.hidden = !busy;
            cancelButton.disabled = !busy || !activeAgentJobId;
        }
    }

    function renderTrace(trace = []) {
        const mount = qs('matlab-experiment-results');
        if (!mount) return;
        if (!trace.length) return;
        mount.innerHTML = '';
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
        mount.appendChild(list);
    }

    function phaseLabel(phase) {
        const labels = {
            start: '开始',
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

    function startRunTimer() {
        const startedAt = Date.now();
        return window.setInterval(() => {
            const seconds = Math.floor((Date.now() - startedAt) / 1000);
            setStatus(`正在启动 MATLAB 并执行仿真... ${seconds}s`, 'info');
        }, 1000);
    }

    async function requestJson(url, options = {}) {
        const response = await fetch(url, options);
        const data = await response.json().catch(() => ({}));
        if (!response.ok || data.status === 'error') {
            throw new Error(data.message || `请求失败 (${response.status})`);
        }
        return data;
    }

    async function refreshStatus() {
        try {
            const data = await requestJson('/api/matlab-experiment/status');
            const install = data.available ? '可用' : '未找到';
            setStatus(`MATLAB ${install}：${data.matlab_executable}`, data.available ? 'success' : 'warning');
            return data;
        } catch (error) {
            setStatus(`环境检测失败：${error.message}`, 'danger');
            return null;
        }
    }

    function readNumber(id, fallback) {
        const raw = qs(id)?.value;
        const value = Number(raw);
        return Number.isFinite(value) ? value : fallback;
    }

    function fillExamplePrompt() {
        const input = qs('matlab-agent-prompt-input');
        if (!input) return;
        input.value = '生成一个单位负反馈二阶系统的阶跃响应仿真，阻尼比 0.4，自然频率 3 rad/s，画出响应曲线并计算超调量、峰值时间、调节时间。';
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
            sample_count: '采样点',
        };
        const entries = Object.entries(metrics || {});
        const items = entries.length
            ? entries.map(([key, value]) => [labelMap[key] || key, value])
            : [['指标', '-']];
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

    function renderResult(payload) {
        const mount = qs('matlab-experiment-results');
        if (!mount) return;
        mount.innerHTML = '';

        const result = payload.result || {};
        const titleRow = createEl('div', 'matlab-experiment-result-header');
        titleRow.appendChild(createEl('div', 'panel-kicker', payload.run_id || 'MATLAB run'));
        const links = createEl('div', 'matlab-experiment-links');
        const artifacts = payload.artifacts || {};
        [
            ['脚本', artifacts.active_script || artifacts.script],
            ['JSON', artifacts.result_json],
            ['曲线图', artifacts.plot_png],
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
        mount.appendChild(titleRow);

        const plotSrc = artifacts.plot_png || (artifacts.plots || [])[0];
        if (plotSrc) {
            const figure = createEl('figure', 'matlab-experiment-figure');
            const img = document.createElement('img');
            img.src = plotSrc;
            img.alt = 'MATLAB 仿真结果图';
            figure.appendChild(img);
            mount.appendChild(figure);
        }

        mount.appendChild(buildMetricGrid(result.metrics || {}));

        if (payload.analysis) {
            const analysis = createEl('div', 'matlab-experiment-analysis');
            analysis.textContent = payload.analysis;
            mount.appendChild(analysis);
        }

        if (Array.isArray(payload.attempts) && payload.attempts.length) {
            const attempts = createEl('div', 'matlab-experiment-attempts');
            payload.attempts.forEach(item => {
                const details = document.createElement('details');
                details.className = 'matlab-experiment-attempt';
                const summary = document.createElement('summary');
                summary.textContent = `第 ${item.attempt} 次：${item.status}`;
                details.appendChild(summary);
                if (item.message || item.stderr || item.stdout) {
                    const log = createEl('pre', 'matlab-experiment-log');
                    log.textContent = [item.message, item.stderr, item.stdout].filter(Boolean).join('\n');
                    details.appendChild(log);
                }
                const code = createEl('pre', 'matlab-experiment-code');
                code.textContent = item.code || '本次未返回代码内容。';
                details.appendChild(code);
                attempts.appendChild(details);
            });
            mount.appendChild(attempts);
        }

        const stdout = String(payload.stdout || '').trim();
        const stderr = String(payload.stderr || '').trim();
        if (stdout || stderr) {
            const log = createEl('pre', 'matlab-experiment-log');
            log.textContent = [stdout, stderr].filter(Boolean).join('\n');
            mount.appendChild(log);
        }
    }

    async function runPresetExperiment() {
        setBusy(true);
        setStatus('正在启动 MATLAB 并执行仿真...', 'info');
        const timer = startRunTimer();
        try {
            const payload = {
                preset: 'first_order_step',
                gain: readNumber('matlab-gain-input', 1),
                time_constant: readNumber('matlab-tau-input', 1),
                duration: readNumber('matlab-duration-input', 8),
                step_size: readNumber('matlab-step-input', 0.02),
                timeout_seconds: 300,
            };
            const data = await requestJson('/api/matlab-experiment/run', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            renderResult(data);
            setStatus(`执行完成：${data.elapsed_ms || 0} ms`, 'success');
        } catch (error) {
            setStatus(`执行失败：${error.message}`, 'danger');
        } finally {
            window.clearInterval(timer);
            setBusy(false);
        }
    }

    async function runExperiment() {
        const userPrompt = String(qs('matlab-agent-prompt-input')?.value || '').trim();
        if (!userPrompt) {
            setStatus('请先输入自然语言仿真需求。', 'warning');
            return;
        }
        setBusy(true);
        setStatus('Agent 正在生成 MATLAB 代码并执行仿真...', 'info');
        const startedAt = Date.now();
        const timer = window.setInterval(() => {
            const seconds = Math.floor((Date.now() - startedAt) / 1000);
            setStatus(`Agent 正在生成/执行/必要时修复代码... ${seconds}s`, 'info');
        }, 1000);
        let pollTimer = null;
        try {
            const started = await requestJson('/api/matlab-experiment/agent-jobs', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
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
                            renderResult(job.result);
                            setStatus(`Agent 执行完成：${job.result?.run_id || ''}`, 'success');
                            resolve();
                        } else if (job.status === 'failed') {
                            window.clearInterval(pollTimer);
                            if (job.result) renderResult(job.result);
                            reject(new Error(job.error || job.result?.message || 'Agent 执行失败'));
                        } else if (job.status === 'cancelled') {
                            window.clearInterval(pollTimer);
                            if (job.result) renderResult(job.result);
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

    function openPanel() {
        const overlay = qs('matlab-experiment-overlay');
        if (!overlay) return;
        overlay.classList.add('open');
        overlay.setAttribute('aria-hidden', 'false');
        document.body.style.overflow = 'hidden';
        refreshStatus();
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

    window.openMatlabExperimentPanel = () => app.openMatlabExperimentPanel();
    window.closeMatlabExperimentPanel = event => app.closeMatlabExperimentPanel(event);
    window.refreshMatlabExperimentStatus = () => app.refreshMatlabExperimentStatus();
    window.runMatlabExperiment = () => app.runMatlabExperiment();
    window.runMatlabPresetExperiment = () => app.runMatlabPresetExperiment();
    window.fillMatlabExamplePrompt = () => app.fillMatlabExamplePrompt();
    window.cancelMatlabExperiment = () => app.cancelMatlabExperiment();
})();
