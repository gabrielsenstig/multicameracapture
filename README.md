# multicameracapture

Capture image from multiple USB cameras on Windows based on serial numbers from the command line using Python, Open CV.
Tested this using multiple of Huddly USB cameras.

The find_video_devices.exe uses directShow to list the cameras connected to the PC. I use that response and map the serial number in the capture.py script.

Clone repository

cd multicameracapture

pip install requirements

python capture.py -s serialnumberofthecamera


A folder images is created and the image captured is stored in .\mulitcameracapture\images\
