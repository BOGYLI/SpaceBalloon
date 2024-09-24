let isFetching = false;
let height = 0;

function fetchHeight() {

    if (isFetching) return;
    isFetching = true;

    let url = "https://sm.balloon.nikogenia.de/height";
    fetch(url)
        .then(response => response.json())
        .then(data => {
            height = data.height;
            isFetching = false;
            console.log('Fetched height (antenna):', data);
            renderHeight();
            setTimeout(fetchHeight, 2000);
        })
        .catch(error => {
            console.error('Error fetching height (antenna):', error);
            isFetching = false;
            setTimeout(fetchHeight, 2000);
        });

}

function renderHeight() {

    ratio = 220 / 10000;
    diagramHeight = (ratio * (height < 33000 ? height : 33000)).toFixed(0);
    distance = 105;

    angle = 270 + Math.atan(diagramHeight / distance) * 180 / Math.PI;
    if (angle < 310) angle = 310;

    antennaElement = document.getElementById('antenna');
    antennaElement.style.transform = 'rotate(' + angle + 'deg)';

}

renderHeight();
fetchHeight();
