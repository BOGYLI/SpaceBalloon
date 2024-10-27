let isFetchingSensor = false;
let isFetchingTitle = false;

let isTitleVisible = false;
let title = "";
let subtitle = "";

let isSensorVisible = false;
let tempout = 0;
let tempin = 0;
let humidity = 0;
let pressure = 0;
let uv = 0;
let co2 = 0;

function fetchTitle() {

    if (isFetchingTitle) return;
    isFetchingTitle = true;

    let url = "https://sm.balloon.nikogenia.de/title";
    fetch(url)
        .then(response => response.json())
        .then(data => {
            title = data.title;
            subtitle = data.subtitle;
            isFetchingTitle = false;
            console.log('Fetched title:', data);
            render();
            setTimeout(fetchTitle, 2000);
        })
        .catch(error => {
            console.error('Error fetching title:', error);
            isFetchingTitle = false;
            setTimeout(fetchTitle, 2000);
        });

}

function renderTitle() {

    if (title == "" && subtitle == "") {
        document.getElementById('title').style.opacity = 0;
        isTitleVisible = false;
        return;
    }

    document.getElementById('title').style.opacity = 1;
    isTitleVisible = true;

    document.getElementById('title-text').innerText = title;
    document.getElementById('subtitle-text').innerText = subtitle;

}

function fetchSensor() {

    if (isFetchingSensor) return;
    isFetchingSensor = true;

    let url = "https://sm.balloon.nikogenia.de/sensors";
    fetch(url)
        .then(response => response.json())
        .then(data => {
            tempout = data.temp == null ? 0 : data.temp.toFixed(1);
            tempin = data.avg == null ? 0 : data.avg.toFixed(1);
            humidity = data.humidity == null ? 0 : data.humidity.toFixed(0);
            pressure = data.pressure == null ? 0 : data.pressure.toFixed(0);
            uv = data.uv == null ? 0 : data.uv.toFixed(2);
            co2 = data.co2 == null ? 0 : data.co2.toFixed(0);
            isFetchingSensor = false;
            console.log('Fetched sensor:', data);
            render();
            setTimeout(fetchSensor, 2000);
        })
        .catch(error => {
            console.error('Error fetching sensor:', error);
            isFetchingSensor = false;
            setTimeout(fetchSensor, 2000);
        });

}

function renderSensor() {

    if ((tempout == 0 && tempin == 0 &&
        humidity == 0 && pressure == 0 &&
        uv == 0 && co2 == 0) || isTitleVisible) {
        document.getElementById('sensor').style.opacity = 0;
        isSensorVisible = false;
        return;
    }

    document.getElementById('sensor').style.opacity = 1;
    isSensorVisible = true;

    document.getElementById('tempout-value').innerText = tempout == 0 ? "N/A" : tempout;
    document.getElementById('tempin-value').innerText = tempin == 0 ? "N/A" : tempin;
    document.getElementById('humidity-value').innerText = humidity == 0 ? "N/A" : humidity;
    document.getElementById('pressure-value').innerText = pressure == 0 ? "N/A" : pressure;
    document.getElementById('uv-value').innerText = uv == 0 ? "N/A" : uv;
    document.getElementById('co2-value').innerText = co2 == 0 ? "N/A" : co2;

}

function render() {

    renderTitle();
    renderSensor();

    if (isSensorVisible || isTitleVisible) {
        document.getElementById('background').style.opacity = 1;
        return;
    }

    document.getElementById('background').style.opacity = 0;

}

render();
fetchSensor();
fetchTitle();
