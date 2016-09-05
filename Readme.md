# Python Based Server that control IR based appliances using ESP8266
This project helps to control any IR based appliances using ESP8266 chip with IR transmitter. 


## Goal
This project ultimate goal is to make any smartphone to control any IR based appliance using low cost IR-command sending setup to less than 5$.

To acheive  goal, I selected [ESP8266 processor](https://en.wikipedia.org/wiki/ESP8266) and [9$ Chip Computer](http://docs.getchip.com/chip.html). ESP8266 code kept as dumb as possible and move all IR-code intelligence (and related IR code database for various possible IR appliances) to a cheap Linux based SoC. For the time being, I chose 9$ Chip, but one can choose Raspberry (or any computer that runs Python and has network connectvity to ESP8266 chip that controls the IR appliance).

## Dependent Projects
 * [PhoneRemote-AndroidApp](https://github.com/GssMahadevan/PhoneRemote-AndroidApp)
 * [PhoneRemote-ESPIRSender](https://github.com/GssMahadevan/PhoneRemote-ESPIRSender)


## Architecture
 * [Use Case Diagram](https://github.com/GssMahadevan/PhoneRemote-Server/blob/master/design/use-case-diagram-by-umlet.png)
 * [My Blog](http://mahadevangorti.blogspot.in/2016/09/15-tv-remote-control-using-smart-phone.html) for more info on goals of this prpject


### Pre Requisitives
 * Install python 2.7
 * apt-get install python-twisted python-twisted-web 

### Third party code/tools used
 * Used [PyIrToy](https://github.com/crleblanc/PyIrToy) code for working IR transmitter for [USB IR Toy](http://www.seeedstudio.com/USB-Infrared-Toy-v2-p-831.html) -- Optional (as I was not using USB IR Toy for sending IR codes, as the USB IR Toy costs 19$ and my goal is to reduce the cost of this DIY project to less than 5$)
 * [UML diagams](http://www.umlet.com/umletino/umletino.html) -- Optional
 

 
### Run Server
 ```
 python phRemote.py --http-url http://esp8266.host.ip/ir
 ```
 
 Logs can be seen at phRemote.log in same directory where we run above program

### UT
 * Test HTTP communications with python server working or not by using curl command like:
 
 ```
curl http://your_python_server_ipurl/ir/change?code=power&model=tv
```

Where 'power' and 'tv' are defined [PhoneRemote-Server/model2file.properties](https://github.com/GssMahadevan/PhoneRemote-Server/blob/master/model2file.properties)


### Add new codes for new TV/IR-Appliance:
 * Follow guide lines as in 
  * [PhoneRemote-Server](https://github.com/GssMahadevan/PhoneRemote-Server)
  * [PhoneRemote-ESPIRSender](https://github.com/GssMahadevan/PhoneRemote-ESPIRSender)

