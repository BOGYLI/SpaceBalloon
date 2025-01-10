// Select the image element
const img = document.getElementById('image');
const error = document.getElementById('error');

// Assign an onerror event handler
img.onerror = function() {

    // Hide the image and show the error message
    img.style.display = 'none';
    error.style.display = 'block';

};

// Reload the page every 15 seconds
setInterval(() => {

    // Reset the image and error display
    error.style.display = 'none';
    img.style.display = 'block';

    // Update the image URL with a new timestamp
    let timestamp = new Date().getTime();
    let url = new URL(img.src);
    url.searchParams.set('t', timestamp);
    img.src = url.href

}, 15000);
