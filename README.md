# KIAUH & Klipper Shake & Tune plugin

Shake&Tune is a Klipper plugin from the [Klippain](https://github.com/Frix-x/klippain) ecosystem, designed to create insightful visualizations to help you troubleshoot your mechanical problems and give you tools to better calibrate the input shaper filters on your 3D printer. It can be installed on any Klipper machine and is not limited to those using the full Klippain.

This is a moddified version basically designed to work on my system, but can be edited to work on yours as well, if you need a hand just let me know, I plan on making a version that works with just one KIAUH installed printer without a custom name, the Branch will be named KIAUH_DEFAULT, but it is not completed as of yet.

Only thing thats different is when you use KIAUH and install multiple printers, KIAUH no longer uses (klipper.service or moonraker.service) it now uses a different naming scheme, like "printer_1_data" or "custom*name_data" which in turn changes (```klipper-printer_1.service```) & (```moonraker-printer_1.service```) or (```klipper-custom*name.service```) & (```moonraker-custom*name.service```). My branch `punisher` version is set up for one of my printers in the ```install.sh``` but is very easy to change to your proper naming scheme. I will try and make it more REGEX friendly so it automaticaly looks for the folders and service names but this is just a quick fix for one of my printers that I have an S2DW acceloromitor on perminately. 

Check out the **[detailed documentation here](./docs/README.md)**.

![logo banner](./docs/banner.png)


## Installation

I removed the bash install as it would not work for you unless you edited the `install.sh` but I will add it back once I have completed the default install for KIAUH

Follow these steps to install Shake&Tune on your printer:
  1. Be sure to have a working accelerometer on your machine and a `[resonance_tester]` section defined. You can follow the official [Measuring Resonances Klipper documentation](https://www.klipper3d.org/Measuring_Resonances.html) to configure it.
  1. Install Shake&Tune by running over SSH on your printer:
  2. `git clone https://github.com/Bradford1040/kiauh-klippain-shaketune.git ~/klippain_shaketune`
  3. ```cd ~/klippain_shaketune```
  4. ```./install.sh```
  5. I highly doubt your printer name is punisher, so you are going to have to edit the install.sh 
  1. Then, append the following to your `printer.cfg` file and restart Klipper:
```
[shaketune]
 result_folder: ~/punisher_data/config/ShakeTune_results
#    The folder where the results will be stored. It will be created if it doesn't exist.
 number_of_results_to_keep: 10
#    The number of results to keep in the result_folder. The oldest results will
#    be automatically deleted after each runs.
 keep_raw_csv: False
#    If True, the raw CSV files will be kept in the result_folder alongside the
#    PNG graphs. If False, they will be deleted and only the graphs will be kept.
 show_macros_in_webui: True
#    Mainsail and Fluidd doesn't create buttons for "system" macros that are not in the
#    printer.cfg file. If you want to see the macros in the webui, set this to True.
 timeout: 300
#    The maximum time in seconds to let Shake&Tune process the CSV files and generate the graphs.
```

Don't forget to check out **[Shake&Tune documentation here](./docs/README.md)**.
