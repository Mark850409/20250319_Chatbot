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
    
    let selectedImage = null;
    
    // 滚动到底部
    function scrollToBottom() {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    // 格式化当前时间
    function formatTime() {
        const now = new Date();
        return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    
    // 添加消息到界面
    function addMessageToUI(message, isUser = true) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'assistant-message'}`;
        
        let avatarIcon = isUser ? 'fa-user' : 'fa-robot';
        
        // 创建消息HTML
        let messageHTML = `
            <div class="avatar">
                <i class="fas ${avatarIcon}"></i>
            </div>
            <div class="message-content">
        `;
        
        // 如果有图片，添加图片
        if (message.image) {
            // 检查图片路径是否以/开头
            const imageSrc = message.image.startsWith('/') ? message.image : '/static/' + message.image;
            
            messageHTML += `
                <div class="image-container">
                    <img src="${imageSrc}" alt="Uploaded image">
                </div>
            `;
        }
        
        // 添加文本内容和时间戳
        messageHTML += `
                <div class="text">${message.content}</div>
                <div class="timestamp">${formatTime()}</div>
            </div>
        `;
        
        messageDiv.innerHTML = messageHTML;
        messagesContainer.appendChild(messageDiv);
        
        // 移除欢迎消息，如果存在
        const welcomeMsg = document.querySelector('.welcome-message');
        if (welcomeMsg) {
            welcomeMsg.remove();
        }
        
        scrollToBottom();
    }
    
    // 显示加载指示器
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
    
    // 上传图片监听
    uploadBtn.addEventListener('click', () => {
        imageUpload.click();
    });
    
    // 图片上传改变事件
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
    
    // 移除上传图片
    removeImageBtn.addEventListener('click', function() {
        imagePreviewContainer.classList.add('hidden');
        imageUpload.value = '';
        selectedImage = null;
    });
    
    // 提交表单处理
    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const message = messageInput.value.trim();
        
        // 如果没有消息且没有图片，则不提交
        if (!message && !selectedImage) {
            return;
        }
        
        // 创建FormData对象
        const formData = new FormData();
        if (message) {
            formData.append('message', message);
        }
        
        if (selectedImage) {
            formData.append('image', selectedImage);
            
            // 添加图片尺寸和质量选项
            const selectedSize = imageSizeSelect.value;
            const selectedQuality = imageQualitySelect.value;
            
            formData.append('image_size', selectedSize);
            formData.append('image_quality', selectedQuality);
        }
        
        // 清空输入框和图片预览
        messageInput.value = '';
        imagePreviewContainer.classList.add('hidden');
        
        // 如果只有文本消息，立即添加到UI
        if (message && !selectedImage) {
            addMessageToUI({content: message});
        }
        
        // 显示加载指示器
        const loadingIndicator = showLoading();
        
        // 发送请求
        fetch('/chat', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('网络请求失败');
            }
            return response.json();
        })
        .then(data => {
            // 移除加载指示器
            loadingIndicator.remove();
            
            // 如果有图片，添加用户消息（包含图片）
            if (selectedImage) {
                addMessageToUI(data.user_message);
            }
            
            // 添加助手回复
            addMessageToUI(data.assistant_message, false);
            
            // 重置选择的图片
            selectedImage = null;
            imageUpload.value = '';
            
            // 重新聚焦到输入框
            messageInput.focus();
        })
        .catch(error => {
            // 移除加载指示器
            loadingIndicator.remove();
            
            // 显示错误消息
            const errorMessage = {
                content: `出错了: ${error.message}`,
            };
            addMessageToUI(errorMessage, false);
            
            console.error('Error:', error);
        });
    });
    
    // 页面加载完成后滚动到底部
    scrollToBottom();
    
    // 聚焦到输入框
    messageInput.focus();
    
    // 添加键盘快捷键
    document.addEventListener('keydown', function(e) {
        // 按下ESC键清除图片
        if (e.key === 'Escape' && !imagePreviewContainer.classList.contains('hidden')) {
            removeImageBtn.click();
        }
    });
}); 