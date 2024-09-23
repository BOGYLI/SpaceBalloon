let isFetching = false;
let phase = 0;
let height = 0;
let speed = 0;

function fetchHeight() {

    if (isFetching) return;
    isFetching = true;

    let url = "https://sm.balloon.nikogenia.de/height";
    fetch(url)
        .then(response => response.json())
        .then(data => {
            phase = data.phase;
            height = data.height;
            speed = data.speed;
            isFetching = false;
            console.log('Fetched height:', data);
            renderHeight();
            setTimeout(fetchHeight, 2000);
        })
        .catch(error => {
            console.error('Error fetching height:', error);
            isFetching = false;
            setTimeout(fetchHeight, 2000);
        });

}

function renderHeight() {

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

}

renderHeight();
fetchHeight();
