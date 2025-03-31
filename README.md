# KINARM
This repository contains all the code needed to run an experiment task with aVNS on the KINARM device and also features code to analyze the KINARM data.

To set up the environment, use pip install -r requirements.py.

The data storage is coded in the scripts and uses P-Drive to save files. In order to continue working on the experiment,
the device has to be connected to the P-Drive so that the files can be stored there and there is no confusion.

Steps to set up the conda environment (MAC):

  1.  Download conda
  2.  open the terminal
  3.  "conda create -n your_name python=3.10"
  4.  conda activate your_name
  5.  cd "enter file path of KINARM"
  6.  "pip install -r requirements.txt"
  7.  The stimulator ports have to be added manually
     - Connect the Arduino device
       - "ls /dev/tty.*"
       - copy the full name of the device starting with /dev...
     - repeat for both stimulator devices
  8. Enter the names in the gui_test.py script

The environment is now ready to run all the scripts!
