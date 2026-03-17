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
    currentUser: null,
    accessToken: '',
};

window.AITutorApp.makeThreadId = function makeThreadId() {
    const username = (window.AITutorApp.state.currentUser?.username || 'guest').replace(/[^a-z0-9_-]/gi, '');
    return `${username}_session_${Math.random().toString(36).substring(2, 9)}`;
};
