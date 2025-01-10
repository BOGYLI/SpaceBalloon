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
This entire project is well documented!
[Get started reading ...](https://github.com/BOGYLI/SpaceBalloon/wiki)

If you already know what you are looking for, we have some shortcuts for you:
- General Documentation \
  [Balloon](https://github.com/BOGYLI/SpaceBalloon/wiki/Balloon) | 
  [Ground](https://github.com/BOGYLI/SpaceBalloon/wiki/Ground) | 
  [Cloud](https://github.com/BOGYLI/SpaceBalloon/wiki/Cloud) | 
  [Communication](https://github.com/BOGYLI/SpaceBalloon/wiki/Communication)
- Usage Guides \
  [Hardware Guide](https://github.com/BOGYLI/SpaceBalloon/wiki/Hardware-Guide) | 
  [Software Guide](https://github.com/BOGYLI/SpaceBalloon/wiki/Software-Guide)

### Modules
- [adc](/adc/) responsible for the UV and methane sensors
- [cammanager](/cammanager/) coordinating camera operation and system status
- [climate](/climate/) sensor measuring temperature, humidity and pressure (+ estimated altitude)
- [co2](/co2/) sensor for CO₂ and VOC
- [datamanager](/datamanager/) collecting all sensor data and sending it via APRS and WiFi
- [gps](/gps/) sensor tracking location and altitude
- [magnet](/magnet/) sensor monitoring some magnetic activity
- [spectral](/spectral/) sensor checking the intensity of different IR wavelengths
- [system](/system/) monitoring system metrics
- [thermal](/thermal/) camera capturing thermal images of the interior
- [webcam](/webcam/) implementing camera photos, videos and livestreaming

### Containers
- [thermalrenderer](/thermalrenderer/) fetching pixel data from InfluxDB and rendering a thermal image to storage box ([dockerhub](https://hub.docker.com/repository/docker/nikogenia/sp-thermalrenderer))
- [spotcollector](/spotcollector/) reading the newest GPS data from the SPOT API and sending it to InfluxDB ([dockerhub](https://hub.docker.com/repository/docker/nikogenia/sp-spotcollector))
- [streammanager](/streammanager/) API controlling the state of the stream and communicating with Stream Elements ([dockerhub](https://hub.docker.com/repository/docker/nikogenia/sp-streammanager))

### Extras
- [console](/console/) is the Mission Control Console
- [aprsreceiver](/aprsreceiver/) running on the APRS ground antenna station to receive data and save it to InfluxDB
- [utils](/utils/) are python modules with handy utilities to be imported
- [resources](/resources/)
  - [diagrams](/resources/diagrams/) documentation diagram related stuff
  - [grafana](/resources/grafana/) holds all dashboard configurations for Grafana
  - [images](/resources/images/) hosts various images for the repository and documentation
  - [streamelements](/resources/streamelements/) holds custom widgets and their assets for Stream Elements
  - [tests](/resources/tests/) contains various tests throughout the development
  - [templates](/resources/templates/) are the default configuration and example module
- [tools](/tools/) is a mix of scripts to manage the repository instance on board
  - [setup.sh](/tools/setup.sh) setups the repository environment on board
  - [reset.sh](/tools/reset.sh) clears all data and initialize new storage directories
  - [start.sh](/tools/start.sh), [stop.sh](/tools/stop.sh), [restart.sh](/tools/restart.sh) change module service execution state respectively
  - [enable.sh](/tools/enable.sh), [disable.sh](/tools/disable.sh) change module service autostart configuration respectively
  - [uninstall.sh](/tools/uninstall.sh) uninstalls the repository environment on board
  - [logall.sh](/tools/logall.sh) shows the logs of all module services one after another
  - [backup.sh](/tools/backup.sh) is a guided script to backup all data to an USB stick
  - [backup.bat](/tools/backup.bat) is a guided script to be run on Windows to backup all data via SSH over WiFi

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
