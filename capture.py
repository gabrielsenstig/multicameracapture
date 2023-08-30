#!/usr/bin/env python3
import sys

import cv2
import datetime
from winregistry import WinRegistry as Reg
import argparse
import subprocess
import re
import time
import os

DSHOW_LIST_PATH = f'find_video_devices.exe'
path_cepture_images = f'{os.getcwd()}\\images\\'
isExist = os.path.exists(path_cepture_images)
if not isExist:
    os.makedirs(path_cepture_images)
IQ_IMAGE_PATH =f'{os.getcwd()}\\images\\'+'{}pic.tiff'
print(IQ_IMAGE_PATH)
"""
THIS IS THE IMAGE CAPTURE CLASS. THE cv2.VideoCapture(int(camera_pos)) IS USED TO OPEN
A CAPTURE DEVICE. THE VideoCapture() REQUIRE A INTEGER TO CONNECT TO THE A DEVICE.
THE reg_serialnumbers_class IS USED TO MAP SERIAL NUMBERS TO THE DEVICE ID REQUIRED BY OPENCV.    
"""
class capture_image_class:
    def __init__(self):
        self.cameras_raw_mode = {}
        self.cameras_normal_mode = {}

    def count_cameras(self):
        max_tested = 8
        n = 0
        camera_list = []
        for i in range(max_tested):
            temp_camera = cv2.VideoCapture(i)
            print(int(temp_camera.get(cv2.CAP_PROP_FRAME_WIDTH)))
            if 3000 > (int(temp_camera.get(cv2.CAP_PROP_FRAME_WIDTH))):
                camera_list.append(i)
            temp_camera.release()
        return camera_list[:]

    def registry_sernum(self):
        camera_dict = reg_serialnumbers_class.update_list()
        return camera_dict

    #CAPTURE ONE FRAM AND RETURN
    def capture_cam_normal(self, camera_sn, camera_pos):
        print('CAPTURE FROM THIS CAMERA ' + camera_sn + ' ' + str(camera_pos))
        try:
            cap = cv2.VideoCapture(int(camera_pos), cv2.CAP_DSHOW)
        except cv2.error as error:
            print("[WARNING]: {}".format(error))
            cap = cv2.VideoCapture(int(camera_pos))
        if not cap.isOpened():
            print('cap.VideoCapture() FAILED')
            print('EXPECTING BAD CONNECTION IN FPC CABLE, CONNECTOR ISSUES, OR FAILURE IN LENS MODULE')
            return 'OK'
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_hight = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print("FRAME WIDTH: " + str(frame_width))
        print("FRAME HIGHT: " + str(frame_hight))
        i = 0 # USE TO COUNT THE NUMBER OF FRAMES
        while True:
            ret, frame = cap.read()
            if not ret:
                print('cap.read() FAILED')
                print('EXPECTING BAD CONNECTION IN FPC CABLE, CONNECTOR ISSUES, OR FAILURE IN LENS MODULE')
                return 'OK'
            i = i + 1
            dd = cv2.Laplacian(frame, cv2.CV_64F)
            focus = int(dd.var())  # Calculating variance in the image, if black then the variance is 0
            if focus > 1:
                break
            elif i > 30:  # IF 30 FRAMES ARE CAPURED AND NONE OF THEM HAVE VARIANCE HIGHER THE 1 THEN RETURN
                break
        cv2.destroyAllWindows()
        cap.release()
        now = datetime.datetime.now()
        dev1 = camera_sn
        saved_time = (str(now.year)+'-' + str(now.month) + '-' + str(now.day) + '-' + str(now.hour)+'-'+ str(now.minute) + '-' + str(now.second))
        save_file = IQ_IMAGE_PATH.format(dev1+'_'+saved_time)
        print(save_file)
        if ((frame_width > 0) and (int(focus) > 1)):
            cv2.imwrite(save_file, frame[::])
        elif (frame_width > 0 and int(focus) < 1):
            cv2.imwrite(save_file, frame[::])
            print('IMAGE CAPTURE IS TO DARK FAILED')
            print('EXPECTING BAD CONNECTION IN FPC CABLE, CONNECTOR ISSUES, OR FAILURE IN LENS MODULE')
        else:
            print('IMAGE CAPTURE FAILED WIDTH IS 0')
            print('EXPECTING BAD CONNECTION IN FPC CABLE, CONNECTOR ISSUES, OR FAILURE IN LENS MODULE')
        return 'OK'
'''
THIS LIST IS USED TO FIND A LIST BY EXCUTING THE BACKEND FOR OPENCV DHSOW
THEN THE LIST ARE SEARCHING THE REGISTRY TO FIND THE SERIALNUMBER OF THE DSHOW DEVICE PATH LIST
THE LIST RETURNED IS USED TO CAPTURE FROM THE DEVICE WITH THE RIGTH SERIALNUMBER
'''
class reg_serialnumbers_class:

    def __init__(self):
        self.cameras_returned={}
        self.path_enum = r'HKLM\SYSTEM\ControlSet001\Services\usbvideo\Enum'
        self.path_container = 'HKLM\\SYSTEM\\CurrentControlSet\\Enum\\'
        self.path_basecontainer = 'HKLM\\SYSTEM\\ControlSet001\\Control\\DeviceContainers\\'
        self.reg = Reg()
        self.camera_dict = self.reg.read_key(self.path_enum)
        self.cameras = []
        self.run_dshow_subprocess = DSHOW_LIST_PATH
        self.camera_list = self.camera_dict['values']

    @staticmethod  # Testable without an instance. Creating this instance is problematic with GitHub actions.
    def _extract_value_data(line: str):
        found = re.findall(r"value:(\d{1,2}).*(usb.*00#)", line)
        if found:
            return {"value": found[0][0],
                    "data": found[0][1].replace('#', '\\').upper()}

    def get_camera_list_with_serialnumbers(self):
        try:
            response = subprocess.Popen(self.run_dshow_subprocess,
                                        stderr=subprocess.STDOUT,
                                        stdout=subprocess.PIPE)
        except WindowsError as e:
            if e.winerror == 2:
                print('Cannot find this file find_video_devices.exe')
                print("Try adding the path to this catalog to the path")
                exit(0)
            else:
                print("WindowsError")
                exit(0)

        if response:
            print('find_video_devices.exe returned this camera list')
        else:
            print('find_video_devices.exe not found')
            print('FAIL')
   
        while True:
            line = response.stdout.readline().decode('utf-8')
            extracted = self._extract_value_data(line)
            if extracted:
                #print('%.42s' % str(extracted['data'])) #Print to give more debug information
                self.cameras.append(extracted)
            else:
                break
     
        for camera in self.cameras:
            try:
                self.containers = self.reg.read_value(self.path_container+camera['data'],'ContainerID')
            except:
                print(camera['data'])
            self.basecontainer = self.reg.read_key(self.path_basecontainer+self.containers['data']+'\\BaseContainers\\'+self.containers['data'])
            for cameras in self.basecontainer['values']:
                if (camera['data'][0:21]+ '\\') in cameras['value']:
                    self.cameras_returned.update({camera['value']:cameras['value'][22:]})
                    containers=False
            if(not self.containers):
                print('DID NOT FIND DEVICE PATH FOR THAT SERIAL NUMBER IN REGISTRY')
                exit(1)
        return self.cameras_returned

def main():
    parser = argparse.ArgumentParser(description='Input the serial number')
    parser.add_argument('-s', dest='unit_serial', help='Input unit serial number')
    results = parser.parse_args()
    a = reg_serialnumbers_class()
    camera_dict = a.get_camera_list_with_serialnumbers()
    print(camera_dict)
    if not results.unit_serial:
        print('MISSING SERIAL NUMBER -s ARGUMENT SEE IN LIST ABOVE IF YOUR CAMERA IS LISTED THERE, AND TRY THIS:')
        print('python capture.py -s yourserial')
        print('FAIL')
        exit(1)
    else:
        for k in camera_dict:
            if camera_dict[k] == results.unit_serial: #Check if unit_serial number is found in the exe file list
                b = capture_image_class()
                if results.unit_serial:
                    c = b.capture_cam_normal(camera_dict[k], k)
                else:
                    exit(1)
                a = False
                print(c)
        if a:
            print('SERIAL NUMBER ' + str(results.unit_serial) + ' NOT FOUND')
            print('TRY ONE OF THESE: ')
            print(camera_dict)
            print("FAIL")
            exit(1)

if __name__ == "__main__":
    main()