let isFetching = false;
let isRendering = false;
let countdown = 0;

function fetchCountdown() {

    if (isFetching) return;
    isFetching = true;

    let url = "https://sm.balloon.nikogenia.de/stream/countdown";
    fetch(url)
        .then(response => response.json())
        .then(data => {
            countdown = data.time == null ? 0 : data.time;
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
    
    let currentTime = new Date().getTime() / 1000;

    timeElement.innerText = secondsToTime(Math.floor(countdown - currentTime));

    isRendering = false;
    setTimeout(renderCountdown, 100);

}

function secondsToTime(secs) {
  
  	if (secs < 0) return "00:00";

    let minutes = Math.floor((secs % (60 * 60)) / 60);
    let seconds = secs % 60;

    let pad = (val) => { return val < 10 ? "0" + val : val; };
    return "" + pad(minutes) + ":" + pad(seconds);

}

renderCountdown();
fetchCountdown();


