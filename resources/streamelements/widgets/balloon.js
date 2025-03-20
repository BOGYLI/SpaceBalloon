let isFetching = false;
let phase = 0;
let height = 0;
let speed = 0;
let steps_height = 0;
let steps_speed = 0;
let target_height = 0;
let target_speed = 0;

function fetchHeight() {

    if (isFetching) return;
    isFetching = true;

    let url = "https://sm.balloon.nikogenia.de/height";
    fetch(url)
        .then(response => response.json())
        .then(data => {
            phase = data.phase;
            steps_height = data.height == target_height ? steps_height : 240;
            steps_speed = data.speed == target_speed ? steps_speed : 240;
            target_height = data.height;
            target_speed = data.speed;
            isFetching = false;
            console.log('Fetched height:', data);
            setTimeout(fetchHeight, 2000);
        })
        .catch(error => {
            console.error('Error fetching height:', error);
            isFetching = false;
            setTimeout(fetchHeight, 2000);
        });

}

function renderHeight() {

    if (steps_height > 0) {
        height = height + (target_height - height) / steps_height;
        steps_height--;
    }
    if (steps_speed > 0) {
        speed = speed + (target_speed - speed) / steps_speed;
        steps_speed--;
    }

    heightElement = document.getElementById('height-value');
    speedElement = document.getElementById('speed-value');

    heightElement.innerHTML = height.toFixed(0);
    speedElement.innerHTML = speed.toFixed(1);
  
    speedElement = document.getElementById('speed');
    if (height < 800) {
      	speedElement.style.display = 'none';
    }
  	else {
      	speedElement.style.display = 'block';
    }

    risingElement = document.getElementById('rising');
    fallingElement = document.getElementById('falling');

    if (phase <= 2) {
        risingElement.style.display = 'block';
        fallingElement.style.display = 'none';
    }
    else {
        risingElement.style.display = 'none';
        fallingElement.style.display = 'block';
    }

    posElement = document.getElementById('pos');

    ratio = 220 / 10000;
    diagramHeight = (ratio * (height < 33000 ? height : 33000)).toFixed(0);

    posElement.style.top = 917 - 144 - 45 - diagramHeight + 'px';

    setTimeout(renderHeight, 33);

}

renderHeight();
fetchHeight();
