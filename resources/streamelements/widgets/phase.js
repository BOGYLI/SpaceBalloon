let isFetching = false;
let phase = 0;

function fetchPhase() {

    if (isFetching) return;
    isFetching = true;

    let url = "https://sm.balloon.nikogenia.de/phase";
    fetch(url)
        .then(response => response.json())
        .then(data => {
            phase = data.phase;
            isFetching = false;
            console.log('Fetched phase:', data);
            renderPhase();
            setTimeout(fetchPhase, 1000);
        })
        .catch(error => {
            console.error('Error fetching phase:', error);
            isFetching = false;
            setTimeout(fetchPhase, 1000);
        });

}

function renderPhase() {

    for (let i = 0; i < 5; i++) {

        let phaseElement = document.getElementById('p' + i);
        
        if (i == phase) {
            phaseElement.style.color = '#FFFFFF';
        }
        else {
            phaseElement.style.color = '#C0C0C0';
        }

    }

}

renderPhase();
fetchPhase();
