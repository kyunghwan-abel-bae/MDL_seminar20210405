import sys
import numpy as np
import cv2
import inova

def camera_setup(camera):

	ver = camera.get_firmware_version()
	print("Firmware Version: " + ver)

	ver = camera.get_system_info()
	print("System Info: " + ver)

	ver = camera.get_serial_number()
	print("Serial Number: " + ver)

	# Set ALC(Auto Luminance Control) - both exposure and gain should be manual.
	camera.set_ALC(False, False, 10, 1000, 10000, 0, 10)

	# Set ALC(Auto Luminance Control) - only exposure is set to auto and the exposure range is between 1000 and 100000 microseconds.
	camera.set_ALC(True, False, 10, 1000, 10000, 0, 10)

	# Set the manual exposure value to 1000 microseconds.
	camera.set_exposure(10000)

	# Set the gain to 2.0. (Equivalent to 6 dB)
	camera.set_gain(2.0)

	# Set the camera to free run mode.
	camera.set_trigger_mode(0, False, 0, 0)

	# Set the camera to trigger mode with polarity low
	#camera.set_trigger_mode(1, False, 0, 0)

	# Set the flash output - enable flash with polarity low
	camera.set_flash(1, False)


if len(sys.argv) < 2:
	print("Usage: % python main.py [Camera's IP address]")
	sys.exit(0)

ip = sys.argv[1]
camera = inova.Camera()

print("Connecting Camera at IP address: ", ip)
#camera.connect_stream(ip, isUDP=False) # Stream in TCP
camera.connect_stream(ip, isUDP=True) # Stream in UDP

camera.connect_command(ip) # Command port for camera control
camera_setup(camera)

print("Grabbing images...")
count = 0
while True:
	image = camera.grab()
	if image is not None:
		print('OK')
		cv2.imshow('image', image)
	else:
		print('Fail to grab')
		
	if cv2.waitKey(1) != -1:
		break
	count += 1

cv2.destroyAllWindows()

print("Disconnecting the camera")
camera.disconnect_stream()
camera.disconnect_command()
