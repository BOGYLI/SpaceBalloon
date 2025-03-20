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
let target_tempout = 0;
let target_tempin = 0;
let target_humidity = 0;
let target_pressure = 0;
let target_uv = 0;
let target_co2 = 0;
let steps_tempout = 0;
let steps_tempin = 0;
let steps_humidity = 0;
let steps_pressure = 0;
let steps_uv = 0;
let steps_co2 = 0;

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
            steps_tempout = (data.temp == null ? 0 : data.temp) == target_tempout ? steps_tempout : 240;
            steps_tempin = (data.avg == null ? 0 : data.avg) == target_tempin ? steps_tempin : 240;
            steps_humidity = (data.humidity == null ? 0 : data.humidity) == target_humidity ? steps_humidity : 240;
            steps_pressure = (data.pressure == null ? 0 : data.pressure) == target_pressure ? steps_pressure : 240;
            steps_uv = (data.uv == null ? 0 : data.uv) == target_uv ? steps_uv : 240;
            steps_co2 = (data.co2 == null ? 0 : data.co2) == target_co2 ? steps_co2 : 240;
            target_tempout = data.temp == null ? 0 : data.temp;
            target_tempin = data.avg == null ? 0 : data.avg;
            target_humidity = data.humidity == null ? 0 : data.humidity;
            target_pressure = data.pressure == null ? 0 : data.pressure;
            target_uv = data.uv == null ? 0 : data.uv;
            target_co2 = data.co2 == null ? 0 : data.co2;
            isFetchingSensor = false;
            console.log('Fetched sensor:', data);
            setTimeout(fetchSensor, 2000);
        })
        .catch(error => {
            console.error('Error fetching sensor:', error);
            isFetchingSensor = false;
            setTimeout(fetchSensor, 2000);
        });

}

function renderSensor() {

    if (steps_tempout > 0) {
        tempout = tempout + (target_tempout - tempout) / steps_tempout;
        steps_tempout--;
    }
    if (steps_tempin > 0) {
        tempin = tempin + (target_tempin - tempin) / steps_tempin;
        steps_tempin--;
    }
    if (steps_humidity > 0) {
        humidity = humidity + (target_humidity - humidity) / steps_humidity;
        steps_humidity--;
    }
    if (steps_pressure > 0) {
        pressure = pressure + (target_pressure - pressure) / steps_pressure;
        steps_pressure--;
    }
    if (steps_uv > 0) {
        uv = uv + (target_uv - uv) / steps_uv;
        steps_uv--;
    }
    if (steps_co2 > 0) {
        co2 = co2 + (target_co2 - co2) / steps_co2;
        steps_co2--;
    }

    if ((target_tempout == 0 && target_tempin == 0 &&
        target_humidity == 0 && target_pressure == 0 &&
        target_uv == 0 && target_co2 == 0) || isTitleVisible) {
        document.getElementById('sensor').style.opacity = 0;
        isSensorVisible = false;
        return;
    }

    document.getElementById('sensor').style.opacity = 1;
    isSensorVisible = true;

    document.getElementById('tempout-value').innerText = tempout == 0 ? "N/A" : tempout.toFixed(1);
    document.getElementById('tempin-value').innerText = tempin == 0 ? "N/A" : tempin.toFixed(1);
    document.getElementById('humidity-value').innerText = humidity == 0 ? "N/A" : humidity.toFixed(0);
    document.getElementById('pressure-value').innerText = pressure == 0 ? "N/A" : pressure.toFixed(0);
    document.getElementById('uv-value').innerText = uv == 0 ? "N/A" : uv.toFixed(2);
    document.getElementById('co2-value').innerText = co2 == 0 ? "N/A" : co2.toFixed(0);

}

function render() {

    renderTitle();
    renderSensor();

    if (isSensorVisible || isTitleVisible) {
        document.getElementById('background').style.opacity = 1;
        setTimeout(render, 33);
        return;
    }

    document.getElementById('background').style.opacity = 0;
    setTimeout(render, 33);

}

render();
fetchSensor();
fetchTitle();
