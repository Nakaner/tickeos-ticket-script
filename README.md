# Script to Retrieve Combotickets from the TICKeos API

In Germany, many Verkehrsverbünde offer so-called "Kombitickets" to event organisers which allows these event organisers
to sell a ticket for public transport together with the ticket for admission. This repository contains a script to retrieve
the public transport ticket to be included in a event ticket from API provided by the [TICKeos KombiTicket API](https://www.eos-uptrade.de/de/online-mobile-ticketing). This script is useful if your ticket sales system is not able to retrieve the tickets itself.

This script is used for State of the Map 2019 and HOT Summit 2019 in Heidelberg.


## Usage

Run `python3 retrieve_tickets.py --help`.

A sample configuration file with some comments is part of this repository and called [sample-config.ini](sample-config.ini).


## License

* source code: see [LICENSE.txt](LICENSE.txt)
* logos: OpenStreetMap Foundation for State of the Map logo, HOT US Inc. for HOT Summit logo
* "OpenStreetMap" is a registred trademark of the OpenStreetMap Foundation
* maps: © OpenStreetMap contributors, see https://osm.org/copyright for details
