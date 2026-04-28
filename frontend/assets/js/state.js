window.AITutorApp = window.AITutorApp || {};
window.AITutorApp.state = {
    currentThreadId: '',
    eventSource: null,
    isStreaming: false,
    isAwaitingInput: false,
    currentAgentMsgEl: null,
    currentAgentTurnEl: null,
    currentAgentMainFlowEl: null,
    currentAgentBodyEl: null,
    currentAgentTurnKickerEl: null,
    currentTurnHeartbeatEl: null,
    currentTraceBlockEl: null,
    currentTraceListEl: null,
    currentTraceBadgeEl: null,
    currentTextBuffer: '',
    traceCount: 0,
    radarChartInstance: null,
    assessmentQuestions: [],
    answers: {},
    chatProfiles: [],
    currentChatProfile: '',
    currentModelName: '',
    vendorCatalogs: [],
    localConfig: null,
    pendingTopicConfirmation: null,
    pendingTopicConfirmationDetails: null,
    pendingInterruptConfirmation: false,
    speechRecognition: null,
    isVoiceListening: false,
    voiceInputSupported: null,
    voiceInputBase: '',
    voiceFinalTranscript: '',
    voiceInterimTranscript: '',
    voicePendingNotice: null,
    voiceStopInitiated: false,
    currentTurnId: '',
    currentTurnRole: 'teacher',
    turnHasVisibleOutput: false,
    turnStartedAt: 0,
    lastVisibleAt: 0,
    lastHeartbeatAt: 0,
    visibilityFallbackTimer: null,
    visibilityFallbackCount: 0,
    latestProgressSummary: '',
    latestNodeStartMessage: '',
    latestRouteDecisionSummary: '',
    knowledgeFiles: [],
    knowledgeBackend: '',
    headerCollapsed: false,
    profilePanelCollapsed: false,
    currentTopic: '',
    currentTopicFocus: '',
    graphTopicHint: '',
    learningProgressStep: 1,
    learningProgressLabel: '准备中',
    latestRadarData: null,
    knowledgeGraphModalOpen: false,
    radarModalOpen: false,
    userKnowledgeGraph: {},       // {nodeTitle: {status, calibrated, gap_type, turn_count}}
    userKgMapOpen: true,          // 掌握图区块是否展开
    currentGraphNode: '',         // 当前正在教的图谱节点标题
    currentGraphNodeId: '',       // 当前正在教的图谱节点 ID
};

window.AITutorApp._stateSubscribers = new Set();

window.AITutorApp.subscribeState = function subscribeState(listener) {
    if (typeof listener !== 'function') return () => {};
    window.AITutorApp._stateSubscribers.add(listener);
    return () => window.AITutorApp._stateSubscribers.delete(listener);
};

window.AITutorApp.patchState = function patchState(partial, source = 'unknown') {
    if (!partial || typeof partial !== 'object') return;
    Object.assign(window.AITutorApp.state, partial);
    window.AITutorApp._stateSubscribers.forEach(listener => {
        try {
            listener(window.AITutorApp.state, source);
        } catch (_error) {
            // Keep state fan-out resilient; one subscriber failure should not block others.
        }
    });
};

window.AITutorApp.makeThreadId = function makeThreadId() {
    return 'session_' + Math.random().toString(36).substring(2, 9);
};
