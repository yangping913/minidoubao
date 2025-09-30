// 全局变量
let isProcessing = false;
let currentModel = 'auto';
let modelStatus = {
    deepseek: false,
    ollama: false
};

// 初始化函数
document.addEventListener('DOMContentLoaded', function() {
    initializeChat();
    setupEventListeners();
    startModelStatusPolling();
    setupModelSelector();
});

function initializeChat() {
    // 确保聊天容器存在
    if (!document.getElementById('chat-box')) {
        const chatBox = document.createElement('div');
        chatBox.id = 'chat-box';
        chatBox.className = 'chat-box';
        document.querySelector('.chat-container').appendChild(chatBox);
    }
}

function setupEventListeners() {
    const userInput = document.getElementById('user-input');
    const sendButton = document.querySelector('button');

    // 发送按钮点击事件
    sendButton.addEventListener('click', sendMessage);

    // 回车键发送消息
    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // 输入框获取焦点时启用按钮
    userInput.addEventListener('input', function() {
        sendButton.disabled = !this.value.trim();
    });

    // 初始禁用按钮
    sendButton.disabled = true;
}

// 模型状态管理
function startModelStatusPolling() {
    checkModelStatus();
    setInterval(checkModelStatus, 30000); // 每30秒检查一次
}

async function checkModelStatus() {
    try {
        const response = await fetch('/api/models/status');
        if (!response.ok) throw new Error('网络响应不正常');

        const data = await response.json();
        updateModelStatusUI(data);
    } catch (error) {
        console.error('获取模型状态失败:', error);
        setModelOffline();
    }
}

function updateModelStatusUI(statusData) {
    modelStatus = {
        deepseek: statusData.deepseek,
        ollama: statusData.ollama
    };

    updateStatusIcon('deepseek', statusData.deepseek);
    updateStatusIcon('ollama', statusData.ollama);

    document.getElementById('request-count').textContent = statusData.request_count;
    document.getElementById('uptime').textContent = formatUptime(statusData.uptime);

    currentModel = statusData.preference;
    updateCurrentModelDisplay(currentModel);
}

function updateStatusIcon(model, isOnline) {
    const icon = document.getElementById(`${model}-status`);
    if (icon) {
        icon.className = isOnline ? 'status-icon online' : 'status-icon offline';
        icon.title = isOnline ? `${model} 在线` : `${model} 离线`;
    }
}

function updateCurrentModelDisplay(modelPreference) {
    const indicator = document.getElementById('current-model');
    let displayText = '';
    let cssClass = '';

    switch(modelPreference) {
        case 'deepseek':
            displayText = modelStatus.deepseek ? 'DeepSeek ✅' : 'DeepSeek (离线) ❌';
            cssClass = modelStatus.deepseek ? 'deepseek' : 'offline';
            break;
        case 'ollama':
            displayText = modelStatus.ollama ? 'Ollama ✅' : 'Ollama (离线) ❌';
            cssClass = modelStatus.ollama ? 'ollama' : 'offline';
            break;
        case 'auto':
            const actualModel = modelStatus.deepseek ? 'DeepSeek' :
                               modelStatus.ollama ? 'Ollama' : '无可用模型';
            displayText = `自动 (${actualModel})`;
            cssClass = 'auto';
            if (!modelStatus.deepseek && !modelStatus.ollama) {
                cssClass = 'offline';
            }
            break;
    }

    indicator.textContent = displayText;
    indicator.className = `model-indicator ${cssClass}`;
}

function setModelOffline() {
    const indicator = document.getElementById('current-model');
    indicator.textContent = '服务离线 ❌';
    indicator.className = 'model-indicator offline';

    updateStatusIcon('deepseek', false);
    updateStatusIcon('ollama', false);
}

function formatUptime(seconds) {
    if (seconds < 60) return `${seconds}秒`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}分钟`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}小时`;
    return `${Math.floor(seconds / 86400)}天`;
}

// 模型选择器
function setupModelSelector() {
    const selector = document.getElementById('model-selector');
    if (selector) {
        selector.value = currentModel;
        selector.addEventListener('change', function() {
            switchModel(this.value);
        });
    }
}

async function switchModel(model) {
    try {
        const response = await fetch('/api/models/switch', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ model: model })
        });

        if (!response.ok) throw new Error('网络响应不正常');

        const data = await response.json();
        if (data.status === 'success') {
            currentModel = data.preference;
            updateCurrentModelDisplay(currentModel);
            addSystemMessage(`已切换到${getModelDisplayName(model)}模式`);
        } else {
            throw new Error(data.error || '切换失败');
        }
    } catch (error) {
        console.error('切换模型错误:', error);
        alert('切换失败: ' + error.message);
    }
}

function getModelDisplayName(model) {
    switch(model) {
        case 'auto': return '自动选择';
        case 'deepseek': return 'DeepSeek优先';
        case 'ollama': return 'Ollama优先';
        default: return model;
    }
}

// 消息处理功能
async function sendMessage() {
    if (isProcessing) return;

    const userInput = document.getElementById('user-input');
    const message = userInput.value.trim();

    if (!message) return;

    // 禁用输入和按钮防止重复发送
    isProcessing = true;
    userInput.disabled = true;
    document.querySelector('button').disabled = true;

    // 添加用户消息
    appendMessage('user', message);
    userInput.value = '';

    // 创建AI消息容器
    const aiMessageElement = document.createElement('div');
    aiMessageElement.className = 'message assistant streaming';
    aiMessageElement.innerHTML = '<div class="thinking">思考中...</div>';
    document.getElementById('chat-box').appendChild(aiMessageElement);

    scrollToBottom();

    try {
        const response = await fetch('/api/stream-chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        });

        if (!response.ok) {
            throw new Error('网络响应不正常');
        }

        const modelUsed = await getCurrentActiveModel();
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullContent = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n\n');

            for (const line of lines) {
                if (line.startsWith('data:')) {
                    try {
                        const data = JSON.parse(line.substring(6));
                        if (data.content) {
                            fullContent += data.content;
                            renderMarkdown(aiMessageElement, fullContent, modelUsed);
                        } else if (data.error) {
                            throw new Error(data.error);
                        }
                    } catch (e) {
                        console.error('解析错误:', e);
                    }
                }
            }
        }

        aiMessageElement.classList.remove('streaming');
        renderMarkdown(aiMessageElement, fullContent, modelUsed);

    } catch (error) {
        console.error('Error:', error);
        aiMessageElement.textContent = '网络好像出问题了...';
        aiMessageElement.classList.remove('streaming');
    } finally {
        isProcessing = false;
        userInput.disabled = false;
        userInput.focus();
        document.querySelector('button').disabled = !userInput.value.trim();
    }
}

function appendMessage(role, content, modelUsed = null) {
    const chatBox = document.getElementById('chat-box');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    let displayContent = content;
    if (role === 'user') {
        displayContent = '你: ' + content;
    } else {
        displayContent = typeof marked !== 'undefined'
            ? marked.parse(content)
            : content;

        if (modelUsed) {
            displayContent += `<span class="model-badge">${modelUsed}</span>`;
        }
    }

    messageDiv.innerHTML = displayContent;
    chatBox.appendChild(messageDiv);
    scrollToBottom();
    return messageDiv;
}

function addSystemMessage(text) {
    const chatBox = document.getElementById('chat-box');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message system';
    messageDiv.innerHTML = `<small>🔧 ${text}</small>`;
    chatBox.appendChild(messageDiv);
    scrollToBottom();
}

async function getCurrentActiveModel() {
    try {
        const response = await fetch('/api/models/status');
        if (!response.ok) throw new Error('网络响应不正常');

        const data = await response.json();
        if (data.preference === 'deepseek' && data.deepseek) return 'DeepSeek';
        if (data.preference === 'ollama' && data.ollama) return 'Ollama';
        if (data.preference === 'auto') {
            if (data.deepseek) return 'DeepSeek';
            if (data.ollama) return 'Ollama';
        }
        return '未知';
    } catch {
        return '未知';
    }
}

function renderMarkdown(element, content, modelUsed = null) {
    let renderedContent = typeof marked !== 'undefined'
        ? marked.parse(content)
        : content;

    if (modelUsed && !element.innerHTML.includes('model-badge')) {
        renderedContent += `<span class="model-badge">${modelUsed}</span>`;
    }

    element.innerHTML = renderedContent;
    scrollToBottom();
}

function scrollToBottom() {
    const chatBox = document.getElementById('chat-box');
    chatBox.scrollTop = chatBox.scrollHeight;
}

// 动态加载Marked.js（如果未加载）
if (typeof marked === 'undefined') {
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/marked/marked.min.js';
    document.head.appendChild(script);
}