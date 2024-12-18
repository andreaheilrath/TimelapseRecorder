# Time Lapse Recorder

This code provides a framework for recording and displaying a timelapse for windows or unix systems (including Raspberry PI).


## Materials

* Rapsberry Pi 4 (with SD Card, microHDMI to HDMI Cable and Power Supply)
* OV2710 2MP USB Camera, e.g. [Heaveant USB-Kameramodul](https://www.amazon.de/Heaveant-Kameramodul-USB-Kameramodul-Weitwinkelobjektiv-OV2710-Chip/dp/B08N1L3P3X)
* Light and Holder for the Camera, e.g. [LogiLink AA0150 - LED Ring Light](https://www.amazon.de/LogiLink-AA0150-Smartphone-3-Farbmodi-professionelle-Schwarz/dp/B09993B2PS)
* Arcade Buttons, e.g. [Arcade Buttons, 44mm](https://www.berrybase.de/arcade-button-44mm-beleuchtet-led-12v-dc)
* more Buttons (optional)

A 3D model of the setup can be found [here](/hardware/Zeitmaschine.f3d)
![](/imgs/Zeitmaschine_Render.png)


## Install Python and its libraries

Install OpenCV [The Raspberry PI Guide](https://raspberrypi-guide.github.io/programming/install-opencv)
```
sudo apt-get update
sudo apt-get install python3-opencv
```

## Using USB Camera on Raspberry PI

v4l2-ctl is a command-line tool for controlling video devices on Linux systems. 

To check the available resolutions, use the following console command:
```v4l2-ctl -V```

USB cameras may be tricky on the PI in combination with opencv.
**IMPORTANT: MAKE SURE THE CAMERA IS PLUGGED INTO AN USB 2.0 PORT. USING USB 3.0. WILL THROW AN ERROR!**

Since USB 2.0 is not capable to transfer uncompressed images of high resolution, MJPG encoding has to be used. This happens in the python code during the setup of the opencv capture:
```self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))``` 


## GPIO Buttons as Keyboard

It is possible to link gpio inputs to keyboard strokes. This can be realized using the [device tree](https://en.wikipedia.org/wiki/Devicetree).
I learned about this through the [Blogpost by Martin Strohmayer](https://blog.gc2.at/post/gpio-tasten/).

To realize this, add these lines into the ``/etc/rc.local`` file, just before the line ``exit 0``.

```
sudo dtoverlay gpio-key gpio=2 keycode=30 label="a" gpio_pull=2 
sudo dtoverlay gpio-key gpio=3 keycode=31 label="s" gpio_pull=2
sudo dtoverlay gpio-key gpio=4 keycode=32 label="d" gpio_pull=2
sudo dtoverlay gpio-key gpio=17 keycode=17 label="w" gpio_pull=2 
sudo dtoverlay gpio-key gpio=27 keycode=18 label="e" gpio_pull=2
sudo dtoverlay gpio-key gpio=22 keycode=1 label="Esc" gpio_pull=2
sudo dtoverlay gpio-key gpio=10 keycode=408 label="reboot" gpio_pull=2
```

a / backwards / GPIO 2
s / pause / GPIO 3
d / forward / GPIO 4
w / last project / GPIO 17
e / next project / GPIO 18

Ground also has to be connected to the buttons.

![](/imgs/GPIO-Pinout-Diagram.png)

## Autostart on Raspberry PI

To start the python program automatically at the startup, I used the "Traditional System Method (All Users)" as mentioned in the forum post [STICKY: How to use Autostart - Raspberry Pi OS (Desktop)](https://forums.raspberrypi.com/viewtopic.php?t=294014)
This method does not use an autostart file. It uses filename.desktop files instead.

Raspberry Pi OS uses the ``/etc/xdg/autostart`` directory to start some background apps. 
Go to this directory via the console 

``cd /etc/xdg/autostart``

and create ``timelapse.deskop`` in the ``/etc/xdg/autostart`` folder by executing

``sudo geany timelapse.desktop``

and fill it with the following:

```
[Desktop Entry]
Name=timelapse
Exec=python3 /home/xstage/TimelapseRecorder/timelapse.py
Type=Application
```


**The Exec line has to be adapted, depending on the username and where the timelapse.py is located**
