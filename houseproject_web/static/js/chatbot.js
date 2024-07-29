// 打開對話框
function openDialog() {
    document.getElementById('dialogBox').style.display = 'block';
}

// 隱藏對話框
function hideDialog() {
    var dialogBox = document.getElementById('dialogBox');
    dialogBox.style.display = 'none';
}
document.getElementById('hideButton').addEventListener('click', hideDialog);

// 關閉對話框，並清空 session
function closeDialog() {
    var dialogBox = document.getElementById('dialogBox');
    dialogBox.style.display = 'none';

    // 清空對話框內容
    var chatMessages = document.getElementById('chatMessages');
    chatMessages.innerHTML = '';

    // 清空輸入框
    var question = document.getElementById('question');
    question.value = '';

    // 清空 session
    fetch('/clear_session', {
        method: 'POST'
    });
}

// 在窗口卸載時清空 session
window.addEventListener('beforeunload', function() {
    fetch('/clear_session', {
        method: 'POST'
    });
});

function adjustInputSize(inputElement) {
    var newSize = 200 + Math.max(0, (inputElement.value.length - 20) * 10);
    inputElement.style.width = newSize + 'px';
}

// 自動捲動到 chatArea 的最底部
function scrollToBottom() {
    const chatArea = document.getElementById('chatArea');
    chatArea.scrollTop = chatArea.scrollHeight;
}

// 顯示讀取動畫
function showLoading() {
    const loadingImage = document.getElementById('loadingImage');
    loadingImage.classList.remove('hidden');

     // 自動捲動到 chatArea 底部
     scrollToBottom();
}

// 隱藏讀取動畫
function hideLoading() {
    const loadingImage = document.getElementById('loadingImage');
    loadingImage.classList.add('hidden');
}

function formatBotResponse(response) {
    const lines = response
        .split('\n')
        .map(line => line.trim()) // 移除每行前後的空白
        .filter(line => line.length > 0); // 移除空行

    const formattedResponse = lines.map((line, index) => {
        // 判斷是否為新項目開頭
        if (line.match(/^\d+\./)) {
            return `<div class="item-block"><p>${line}</p>`;
        } else if (line.match(/^優點/)) {
            // 檢查是否為最後一行
            if (index === lines.length - 1) {
                return `<p>${line}</p></div>`; // 結束項目
            } else {
                return `<p>${line}</p></div><br>`; // 結束項目並添加段落間隔
            }
        } else {
            return `<p>${line}</p>`;
        }
    }).join(''); // 合併成一個字符串

    return formattedResponse.trim(); // 確保最終結果沒有空格
}

// 對話區域的對話顯示區
function sendQuestion() {
    const questionInput = document.getElementById('question');
    const question = questionInput.value;
    if (question.trim() === '') return;

    // 在對話訊息區域顯示用戶輸入
    const chatMessages = document.getElementById('chatMessages');

    // 添加使用者訊息
    const userMessage = document.createElement('div');
    userMessage.textContent = question;
    userMessage.className = 'message user-message';
    chatMessages.appendChild(userMessage);

    // 清空輸入框
    questionInput.value = '';

    // 顯示讀取動畫
    showLoading();
    
    chatMessages.scrollTop = chatMessages.scrollHeight;

    // 發送AJAX請求到伺服器
    fetch('/chatbot', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ question: question })
    })
    .then(response => response.json())
    .then(data => {
        // 隱藏讀取動畫
        hideLoading();

        // 在對話訊息區域顯示機器人回應
        if (data.response) {
            const botResponse = document.createElement('div');
            botResponse.innerHTML = formatBotResponse(data.response); // 使用格式化函數處理回應
            // botResponse.textContent = data.response;
            botResponse.className = 'message bot-message';
            chatMessages.appendChild(botResponse);
        } else{
            // 顯示錯誤訊息
            const errorMessage = document.createElement('div');
            errorMessage.textContent = '搜尋失敗，請再試一次';
            errorMessage.className = 'message bot-message';
            chatMessages.appendChild(errorMessage);
        }

        // 自動捲動到 chatArea 底部
        scrollToBottom();
    })
    .catch(error => {
        console.error('Error:', error);
        // 隱藏讀取動畫
        hideLoading();

        // 顯示錯誤訊息
        const errorMessage = document.createElement('div');
        errorMessage.textContent = '搜尋失敗，請再試一次';
        errorMessage.className = 'message bot-message';
        chatMessages.appendChild(errorMessage);

        // 自動捲動到 chatArea 底部
        scrollToBottom();
    });
}