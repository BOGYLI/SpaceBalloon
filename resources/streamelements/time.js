let isFetching = false;
let isRendering = false;
let countdown = 0;

function fetchCountdown() {

    if (isFetching) return;
    isFetching = true;

    let url = "https://sm.balloon.nikogenia.de/countdown";
    fetch(url)
        .then(response => response.json())
        .then(data => {
            countdown = data.time;
            isFetching = false;
            console.log('Fetched time:', data);
            setTimeout(fetchCountdown, 2000);
        })
        .catch(error => {
            console.error('Error fetching time:', error);
            isFetching = false;
            setTimeout(fetchCountdown, 2000);
        });

}

function renderCountdown() {

    if (isRendering) return;
    isRendering = true;

    let timeElement = document.getElementById('time');
    let descriptionElement = document.getElementById('description');
    
    let currentTime = new Date().getTime() / 1000;

    if (countdown - currentTime > 0) {
        descriptionElement.innerText = "Countdown";
        timeElement.innerText = "T-" + secondsToTime(Math.floor(countdown - currentTime));
    }
    else {
        descriptionElement.innerText = "Flugzeit";
        timeElement.innerText = "T+" + secondsToTime(Math.floor(currentTime - countdown));
    }

    isRendering = false;
    setTimeout(renderCountdown, 100);

}

function secondsToTime(secs) {

    let hours = Math.floor((secs % (60 * 60 * 24)) / (60 * 60));
    let minutes = Math.floor((secs % (60 * 60)) / 60);
    let seconds = secs % 60;

    let pad = (val) => { return val < 10 ? "0" + val : val; };
    return pad(hours) + ":" + pad(minutes) + ":" + pad(seconds);

}

renderCountdown();
fetchCountdown();
