// Select the image element
const img = document.getElementById('image');
const error = document.getElementById('error');

// Assign an onerror event handler
img.onerror = function() {
    img.style.display = 'none';
    error.style.display = 'block';
    setTimeout(() => {
        location.reload();
    }, 5000);
};

// Reload the page every 15 seconds
setTimeout(() => {
    location.reload();
}, 15000);
