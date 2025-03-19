document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.getElementById('chat-form');
    const messageInput = document.getElementById('message-input');
    const messagesContainer = document.getElementById('messages');
    const imageUpload = document.getElementById('image-upload');
    const uploadBtn = document.querySelector('.upload-btn');
    const imagePreviewContainer = document.getElementById('image-preview-container');
    const imagePreview = document.getElementById('image-preview');
    const removeImageBtn = document.getElementById('remove-image');
    const imageSizeSelect = document.getElementById('image-size');
    const imageQualitySelect = document.getElementById('image-quality');
    const searchModeToggle = document.getElementById('search-mode');
    
    let selectedImage = null;
    let isSubmitting = false;
    
    // 捲動到底部
    function scrollToBottom() {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    // 格式化當前時間
    function formatTime() {
        const now = new Date();
        return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    
    // 添加訊息到介面
    function addMessageToUI(message, isUser = true) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'assistant-message'}`;
        
        let avatarIcon = isUser ? 'fa-user' : 'fa-robot';
        
        // 建立訊息HTML
        let messageHTML = `
            <div class="avatar">
                <i class="fas ${avatarIcon}"></i>
            </div>
            <div class="message-content">
        `;
        
        // 如果有圖片，添加圖片
        if (message.image) {
            // 檢查圖片路徑是否以/開頭
            const imageSrc = message.image.startsWith('/') ? message.image : '/static/' + message.image;
            
            messageHTML += `
                <div class="image-container">
                    <img src="${imageSrc}" alt="上傳的圖片">
                </div>
            `;
        }
        
        // 添加文字內容和時間戳記
        messageHTML += `
                <div class="text">${message.content}</div>
                <div class="timestamp">${formatTime()}</div>
            </div>
        `;
        
        messageDiv.innerHTML = messageHTML;
        messagesContainer.appendChild(messageDiv);
        
        // 移除歡迎訊息，如果存在
        const welcomeMsg = document.querySelector('.welcome-message');
        if (welcomeMsg) {
            welcomeMsg.remove();
        }
        
        scrollToBottom();
    }
    
    // 顯示載入指示器
    function showLoading() {
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'message assistant-message loading';
        loadingDiv.innerHTML = `
            <div class="avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">
                <div class="text">
                    <div class="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>
            </div>
        `;
        messagesContainer.appendChild(loadingDiv);
        scrollToBottom();
        return loadingDiv;
    }
    
    // 上傳圖片監聽
    uploadBtn.addEventListener('click', () => {
        imageUpload.click();
    });
    
    // 圖片上傳改變事件
    imageUpload.addEventListener('change', function() {
        const file = this.files[0];
        if (file) {
            selectedImage = file;
            const reader = new FileReader();
            reader.onload = function(e) {
                imagePreview.src = e.target.result;
                imagePreviewContainer.classList.remove('hidden');
            };
            reader.readAsDataURL(file);
        }
    });
    
    // 移除上傳圖片
    removeImageBtn.addEventListener('click', function() {
        imagePreviewContainer.classList.add('hidden');
        imageUpload.value = '';
        selectedImage = null;
    });
    
    // 修改表單提交處理
    chatForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        if (isSubmitting) return;
        isSubmitting = true;
        
        const messageInput = document.getElementById('message-input');
        const message = messageInput.value.trim();
        
        if (!message && !imageUpload.files.length) {
            isSubmitting = false;
            return;
        }
        
        // 檢查是否在搜尋模式
        if (searchModeToggle.checked) {
            try {
                const response = await fetch('/search', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        query: message
                    })
                });
                
                if (!response.ok) {
                    throw new Error('搜尋請求失敗');
                }
                
                const data = await response.json();
                
                // 添加搜尋結果到對話中
                addMessageToUI({
                    content: `搜尋: ${message}`
                });
                
                addMessageToUI({
                    content: data.result
                }, false);
                
                // 清空輸入框
                messageInput.value = '';
                
            } catch (error) {
                console.error('搜尋錯誤:', error);
                addMessageToUI({
                    content: `搜尋時發生錯誤: ${error.message}`
                }, false);
            } finally {
                isSubmitting = false;
            }
            return;
        }
        
        // 建立FormData物件
        const formData = new FormData();
        if (message) {
            formData.append('message', message);
        }
        
        if (selectedImage) {
            formData.append('image', selectedImage);
            
            // 添加圖片尺寸和品質選項
            const selectedSize = imageSizeSelect.value;
            const selectedQuality = imageQualitySelect.value;
            
            formData.append('image_size', selectedSize);
            formData.append('image_quality', selectedQuality);
        }
        
        // 清空輸入框和圖片預覽
        messageInput.value = '';
        imagePreviewContainer.classList.add('hidden');
        
        // 如果只有文字訊息，立即添加到UI
        if (message && !selectedImage) {
            addMessageToUI({content: message});
        }
        
        // 顯示載入指示器
        const loadingIndicator = showLoading();
        
        // 發送請求
        fetch('/chat', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('網路請求失敗');
            }
            return response.json();
        })
        .then(data => {
            // 移除載入指示器
            loadingIndicator.remove();
            
            // 如果有圖片，添加使用者訊息（包含圖片）
            if (selectedImage) {
                addMessageToUI(data.user_message);
            }
            
            // 添加助手回覆
            addMessageToUI(data.assistant_message, false);
            
            // 重置選擇的圖片
            selectedImage = null;
            imageUpload.value = '';
            
            // 重新聚焦到輸入框
            messageInput.focus();
        })
        .catch(error => {
            // 移除載入指示器
            loadingIndicator.remove();
            
            // 顯示錯誤訊息
            const errorMessage = {
                content: `發生錯誤: ${error.message}`,
            };
            addMessageToUI(errorMessage, false);
            
            console.error('錯誤:', error);
        });
    });
    
    // 頁面載入完成後捲動到底部
    scrollToBottom();
    
    // 聚焦到輸入框
    messageInput.focus();
    
    // 添加鍵盤快捷鍵
    document.addEventListener('keydown', function(e) {
        // 按下ESC鍵清除圖片
        if (e.key === 'Escape' && !imagePreviewContainer.classList.contains('hidden')) {
            removeImageBtn.click();
        }
    });
});

function renderMarkdown(text) {
    // 使用 marked 將 Markdown 轉換為 HTML
    const htmlContent = marked.parse(text);
    
    // 將內容包裝在 markdown-content 類中
    return `<div class="markdown-content">${htmlContent}</div>`;
}

// 當接收到回應時
function displayResponse(response) {
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    messageContent.innerHTML = renderMarkdown(response);
    // ... 其他顯示邏輯 ...
} 