![Space Balloon](resources/images/spaceballoon.png "Space Balloon")

# Space Balloon
scientific stratosphere balloon with live measurements and video stream

### Homepage
https://spaceballoon.bodensee-gymnasium.de/

### YouTube
https://www.youtube.com/@spaceballoonbogy

### TikTok
https://www.tiktok.com/@spaceballoonbogy

### Wiki
Read the detailed documentation [here](https://github.com/BOGYLI/SpaceBalloon/wiki)!

### Modules
- [adc](/adc/) responsible for the UV and methane sensors
- [cammanager](/cammanager/) coordinating camera operation and system status
- [climate](/climate/) sensor measuring temperature, humidity and pressure (+ estimated altitude)
- [co2](/co2/) sensor for CO2 and VOC
- [datamanager](/datamanager/) collecting all sensor data and sending it via APRS and WiFi
- [gps](/gps/) sensor tracking location and altitude
- [magnet](/magnet/) sensor monitoring some magnetic activity
- [spectral](/spectral/) sensor checking the intensity of different IR wavelengths
- [system](/system/) monitoring system metrics
- [thermal](/thermal/) camera capturing thermal images of the interior
- [webcam](/webcam/) implementing camera photos, videos and livestreaming

### Containers
- [thermalrenderer](/thermalrenderer/) fetching pixel data from InfluxDB and rendering a thermal image to storage box
- [spotcollector](/spotcollector/) reading the newest GPS data from the SPOT API and sending it to InfluxDB
- [streammanager](/streammanager/) API controlling the state of the stream and communicating with Streamelements

### Extras
- [cmd](/cmd/) is the Mission Control Console
- [aprsreceiver](/aprsreceiver/) running on the APRS ground antenna station to receive data and save it to InfluxDB
- [utils](/utils/) are python modules with handy utilities to be imported
- [tests](/tests/) contains various tests throughout the development
- [resources](/resources/) hosts repository related files like images and the default configuration
- [docs](/docs/) stores documentation related stuff
- [template](/template/) is a example for a module to be run on board
- [grafana](/grafana/) holds all dashboard configurations for Grafana
- [setup.sh](/setup.sh) setups the repository environment on board
- [reset.sh](/reset.sh) clears all data and initialize new storage directories
- [startall.sh](/startall.sh), [stopall.sh](/stopall.sh), [restartall.sh](/restartall.sh) change module service execution state respectively
- [backup.sh](/backup.sh) is a guided script to backup all data to an USB stick
- [logall.sh](/logall.sh) shows the logs of all module services one after another

### Sponsors
- [Rütgers Stiftung](https://ruetgers-stiftung.de/)
- [Liebherr](https://www.liebherr.com/)
- [Sparkasse](https://www.sparkasse.de/)
- [Lindauer DORNIER](https://www.lindauerdornier.com/de)
- [Thomann](https://thomann.biz/)
- [Vögeli Kälte- und Klimatechnik](https://voegeli-thomas-kuehl-u-klimatechnik.weblocator.de/)

\
**© 2024 Bodensee-Gymnasium Lindau**\
\
![BOGY](resources/images/bogy.jpg "BOGY")
