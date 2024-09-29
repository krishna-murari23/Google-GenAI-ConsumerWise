document.addEventListener('DOMContentLoaded', () => {
    const sendButton = document.getElementById('send_btn');
    const userInput = document.getElementById('user_input');
    const chatbox = document.getElementById('chatbox');

    sendButton.addEventListener('click', () => {
        const message = userInput.value;
        // Append message to chatbox and clear input
        chatbox.innerHTML += `<p><strong>You:</strong> ${message}</p>`;
        userInput.value = '';
        
        // Here, you would send the message to your backend and append the response
    });
});
