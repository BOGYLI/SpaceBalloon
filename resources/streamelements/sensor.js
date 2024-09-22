let isFetching = false;
let tempout = 0;
let tempin = 0;
let humidity = 0;
let pressure = 0;
let uv = 0;
let co2 = 0;

function fetchSensor() {

    if (isFetching) return;
    isFetching = true;

    let url = "https://sm.balloon.nikogenia.de/sensors";
    fetch(url)
        .then(response => response.json())
        .then(data => {
            tempout = data.temp.toFixed(1);
            tempin = data.avg.toFixed(1);
            humidity = data.humidity.toFixed(0);
            pressure = data.pressure.toFixed(0);
            uv = (data.uv * 1000).toFixed(0);
            co2 = data.co2.toFixed(0);
            isFetching = false;
            console.log('Fetched sensor:', data);
            renderSensor();
            setTimeout(fetchSensor, 2000);
        })
        .catch(error => {
            console.error('Error fetching sensor:', error);
            isFetching = false;
            setTimeout(fetchSensor, 2000);
        });

}

function renderSensor() {

    document.getElementById('tempout-value').innerText = tempout;
    document.getElementById('tempin-value').innerText = tempin;
    document.getElementById('humidity-value').innerText = humidity;
    document.getElementById('pressure-value').innerText = pressure;
    document.getElementById('uv-value').innerText = uv;
    document.getElementById('co2-value').innerText = co2;

}

renderSensor();
fetchSensor();
