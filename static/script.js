
document.addEventListener('DOMContentLoaded', function() {
    initializeChat();
    setupEventListeners();
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
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    // 输入框获取焦点时启用按钮
    userInput.addEventListener('input', function() {
        sendButton.disabled = !this.value.trim();
    });
}

async function sendMessage() {
    const userInput = document.getElementById('user-input');
    const message = userInput.value.trim();

    if (!message) return;

    // 禁用输入和按钮防止重复发送
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

    // 滚动到底部
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

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullContent = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.substring(6));
                        if (data.content) {
                            fullContent += data.content;
                            renderMarkdown(aiMessageElement, fullContent);
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

    } catch (error) {
        console.error('Error:', error);
        aiMessageElement.textContent = '网络好像出问题了...';
        aiMessageElement.classList.remove('streaming');
    } finally {
        // 重新启用输入和按钮
        userInput.disabled = false;
        userInput.focus();
        document.querySelector('button').disabled = false;
    }
}

function appendMessage(role, content) {
    const chatBox = document.getElementById('chat-box');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    if (role === 'user') {
        messageDiv.textContent = '你: ' + content;
    } else {
        messageDiv.innerHTML = typeof marked !== 'undefined'
            ? marked.parse(content)
            : content;
    }

    chatBox.appendChild(messageDiv);
    scrollToBottom();
    return messageDiv;
}

function renderMarkdown(element, content) {
    if (typeof marked !== 'undefined') {
        element.innerHTML = marked.parse(content);
    } else {
        element.textContent = content;
    }
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