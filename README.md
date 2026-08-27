# KIAUH & Klipper Shake & Tune plugin

<div align="center"><!-- markdownlint-disable-line MD033 -->

| Version | Distributions | Status |
| :---------: | :---------: | :--------: |
| Python  3.9 | ARCH & Debian | ✅ Tested & Supported |
| Python 3.11 | ARCH & Debian | ✅ Tested & Supported |
| Python 3.12 | CachyOS & Ubuntu | ✅ Tested & Supported |
| Python 3.13 | CachyOS & Ubuntu | ✅ Tested & Supported |
| Python 3.14 | CachyOS & Ubuntu | ✅ Tested & Supported |

</div>

## 🦏 Rhino Linux - Kalico Klipper - 🩸 bleeding-edge-v2 - S2DW Accelerometer - Python version 3.14.6

- Shake & Tune is a Klipper plugin from the [Klippain](https://github.com/Frix-x/klippain) ecosystem, designed to create insightful visualizations to help you troubleshoot your mechanical problems and give you tools to better calibrate the input shaper filters on your 3D printer.

### About this branch, do not **Blindly** install

- This is a **Modified** branch is designed to work on Bradford1040 set-up & system, but can be edited to work on yours as well, if you need a modified branch, click this [telegram](https://t.me/JerksOfAllTrades/32) link and ping me @Bradford1040. I am making a dynamic branch [devel-st-v2.0](https://github.com/Bradford1040/kiauh-klippain-shaketune/tree/devel-st-v2.0) that works with custom names when using KIAUH multiple printers option, but it is not completed as of 07/23/2026. I have had issues with the `REG_EX` on top of the re-write

#### KIAUH and Klipper: Installing on multiple printers option issues

- Only thing thats different is when you use KIAUH and install multiple printers, Klipper & Moonraker no longer uses (klipper.service or moonraker.service) it now uses a different naming scheme, like "printer_1_data" or "custom_name_data" which in turn changes (`klipper-printer_1.service`) & (`moonraker-printer_1.service`) or (`klipper-custom_name.service`) & (`moonraker-custom_name.service`). This branch (punisher) is set up for a printer named (punisher) in the `install.sh`

Check out the **[detailed documentation here](https://github.com/Bradford1040/kiauh-klippain-shaketune/wiki)**.

- Want a **Custom Branch**, or need **Help** join [telegram](https://t.me/JerksOfAllTrades/32)
- Here you will get 🤝 Support & 👨‍💻 Developer Contact

![Telegram_Group](./docs/Jerks-Of-All-Trades.png "Telegram Group, Scan QR-code with Phone")

##### 🔧 Installation

I removed the bash install as it would not work for you unless you edited the `install.sh` but I will add it back once I have completed the default install for KIAUH

Follow these steps to install Shake&Tune on your printer:

  1. Be sure to have a working accelerometer on your machine and a `[resonance_tester]` section defined. You can follow the official

  2. [Measuring Resonances Klipper documentation](https://www.klipper3d.org/Measuring_Resonances.html) to configure it.

  3. Install Shake&Tune by running over SSH on your printer:

   ```shell
     git clone -b punisher --single-branch https://github.com/Bradford1040/kiauh-klippain-shaketune.git ~/klippain_shaketune
   ```

   ```shell
     cd ~/klippain_shaketune
   ```
  
   ```shell
     ./install.sh
   ```

  1. I highly doubt your printer name is (punisher), You are more than likely looking at the wrong Branch

  2. Then, append the following to your `printer.cfg` file and restart Klipper:

``` ini
[shaketune]
result_folder: ~/punisher_data/config/ShakeTune_results
#    Path where the processed results will be stored. If the folder doesn't exist,
#    it will be automatically created. You can change this if you'd like to store 
#    results in a different location.
number_of_results_to_keep: 10
#    This setting defines how many results you want to keep in the result folder.
#    Once the specified number is exceeded, older results will be automatically deleted
#    to free up space on the SD card and avoid cluttering the results folder.
keep_raw_data: False
#    If set to True, Shake&Tune will store both the processed graphs and the raw accelerometer
#    .stdata files in the results folder. This can be useful for debugging or archiving purposes.
#    Please always attach them when reporting any issues on GitHub or Discord.
show_macros_in_webui: True
#    Mainsail and Fluidd doesn't create buttons for system commands (macros that are not part
#    of the printer.cfg file). This option allow Shake&Tune to inject them into the webui at runtime.
#    If set to False, the macros will be hidden but still accessible from the console by typing
#    their names manually, which can be useful if you prefer to encapsulate them into your own macros.
timeout: 600
#    This defines the maximum processing time (in seconds) to allows to Shake&Tune for generating 
#    graphs from a .stdata file. 10 minutes should be more than enough in most cases, but if you have
#    slower hardware (e.g., older SD cards or low-performance devices), increase it to prevent timeouts.
measurements_chunk_size: 20
#    Each Shake&Tune command uses the accelerometer to take multiple measurements. By default,
#    Shake&Tune will write a chunk of data to disk every two measurements, and at the end of the
#    command will merge these chunks into the final .stdata file for processing. "2" is a very
#    conservative setting to avoid Klipper Timer Too Close errors on lower end devices with little
#    RAM, and should work for everyone. However, if you are using a powerful computer, you may
#    wish to increase this value to keep more measurements in memory (e.g., 15-20) before writing
#    the chunk and avoid stressing the filesystem too much.
max_freq: 200
#    This setting defines the maximum frequency at which the calculation of the power spectral density
#    is cutoff. The default value should be fine for most machines and accelerometer combinations and
#    avoid touching it unless you know what you're doing.
dpi: 300
#    Controls the resolution of the generated graphs. The default value of 300 dpi was optimized
#    and strikes a balance between performance and readability, ensuring that graphs are clear
#    without using too much RAM to generate them. Usually, you shouldn't need to change this value.
```

> [!TIP]
>
> Don't forget to check out **[Shake&Tune documentation here](https://github.com/Bradford1040/kiauh-klippain-shaketune/wiki)** for more details and how to use the macros or the CLI.
