window.AITutorApp = window.AITutorApp || {};
window.AITutorApp.state = {
    currentThreadId: '',
    eventSource: null,
    isAwaitingInput: false,
    currentAgentMsgEl: null,
    currentTextBuffer: '',
    radarChartInstance: null,
    assessmentQuestions: [],
    answers: {},
    chatProfiles: [],
    vendorCatalogs: [],
    localConfig: null,
    pendingTopicConfirmation: null,
    pendingInterruptConfirmation: false,
};

window.AITutorApp.makeThreadId = function makeThreadId() {
    return 'session_' + Math.random().toString(36).substring(2, 9);
};
