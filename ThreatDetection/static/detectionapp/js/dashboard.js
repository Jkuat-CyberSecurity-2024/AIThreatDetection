// Example for handling feedback submission on anomaly review page
function submitFeedback(ipAddress, feedbackType) {
    const feedbackElement = document.getElementById('feedback_' + ipAddress);
    const feedbackData = {
        [ipAddress]: feedbackType
    };

    fetch('/api/review-anomalies/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(feedbackData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.message === 'All anomalies reviewed successfully.') {
            // Update UI after successful feedback submission
            feedbackElement.innerHTML = feedbackType === 'true_positive' ? 'True Positive' : 'False Positive';
        } else {
            alert('Failed to submit feedback');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while submitting feedback');
    });
}
