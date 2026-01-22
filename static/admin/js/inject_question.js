// Admin question injection JavaScript
function injectQuestion(roomCode) {
    const questionText = prompt('Enter your custom question:');
    if (!questionText) return;
    
    const questionType = prompt('Enter question type (truth/dare):', 'truth');
    if (!questionType || !['truth', 'dare'].includes(questionType.toLowerCase())) {
        alert('Invalid question type');
        return;
    }
    
    const formData = new FormData();
    formData.append('question_text', questionText);
    formData.append('question_type', questionType.toLowerCase());
    
    fetch(`/api/admin/room/${roomCode}/inject-question/`, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert('Error: ' + data.error);
        } else {
            alert('Question injected successfully!');
            location.reload();
        }
    })
    .catch(error => {
        alert('Failed to inject question');
    });
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
