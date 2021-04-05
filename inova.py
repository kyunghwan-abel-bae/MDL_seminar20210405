import socket
import numpy as np
import cv2

class Camera:

	RECV_BUF_SIZE = 65536 * 12
	SKIP_FRAME = 0

	def __init__(self):
		self.strm = None
		self.cmd = None
		self.count = 0
		self.ping = bytearray("PING", encoding='ascii')
		self.isUDP = False

	#
	#	Functions for command port (camera setup)
	# 
	def connect_command(self, host):
		self.cmd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		bufsize = self.cmd.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF) 
		self.cmd.setsockopt( 
				socket.SOL_SOCKET, 
				socket.SO_RCVBUF, 
				Camera.RECV_BUF_SIZE) 
		port = 1335
		self.cmd.connect((host, port)) 
		#self.cmd.settimeout(1) # timeout with 1 second.

	def disconnect_command(self):
		self.cmd.close()

	def send_command(self, command):
		self.cmd.send(bytearray(command + "\r\n", encoding='ascii'))
		response = self.cmd.recv(100)
		resp_str = response.decode("ascii")
		#print("response: ", resp_str)
		return resp_str

	def set_exposure(self, exposure):
		self.send_command("SetExposure " + str(exposure))

	def set_gain(self, gain):
		self.send_command("SetTotalGain " + str(gain))

	def set_trigger_mode(self, mode, is_active_high, minimum_trigger_active_width, minimum_trigger_inactive_width):
		polarity = "H" if is_active_high else "L"
		cmd = "SetTriggerMode {0} {1} {2} {3}".format(mode, polarity, minimum_trigger_active_width, minimum_trigger_inactive_width)
		self.send_command(cmd)

	def set_flash(self, mode, is_active_high):
		polarity = "H" if is_active_high else "L"
		cmd = "SetFlash {0} {1}".format(mode, polarity)
		self.send_command(cmd)

	def set_output_port(self, port, _type):
		cmd = "SetOutputPort {0} {1}".format(port, _type)
		self.send_command(cmd)

	def set_flash_on_delay(self, num):
		cmd = "SetFlashOnDelay {0}".format(num)
		self.send_command(cmd)

	def set_flash_off_delay(self, num):
		cmd = "SetFlashOffDelay {0}".format(num)
		self.send_command(cmd)

	def set_ALC(self, enable_AEC, enable_AGC, target, min_exposure, max_exposure, min_gain, max_gain):
		aec = "ON" if enable_AEC else "OFF"
		agc = "ON" if enable_AGC else "OFF"
		cmd = "SetALC {0} {1} {2} {3} {4} {5} {6}".format(aec, agc, target, min_exposure, max_exposure, min_gain, max_gain)
		self.send_command(cmd)

	def set_monochrome(self, mode):
		cmd = "SetMonochrome {0}".format(mode)
		self.send_command(cmd)

	def set_AWB(self, mode):
		cmd = "SetAWB {0}".format(mode)
		self.send_command(cmd)

	def set_trigger_image_count(self, num):
		cmd = "SetTrigImgNum {0}".format(num)
		self.send_command(cmd)

	def set_forced_trigger(self):
		self.send_command("SetForcedTrigger ON")

	def set_bracket_mode(self, mode, count):
		if mode:
			cmd = "SetBracketMode ON {0}".format(count)
		else:
			cmd = "SetBracketMode OFF"
		self.send_command(cmd)

	def set_bracket_info(self, ch, exposure, again, dgain):
		cmd = "SetBracketInfo {0} {1} {2} {3}".format(ch, exposure, again, dgain)
		self.send_command(cmd)

	def set_bracket_info2(self, ch, exposure, gain):
		cmd = "SetBracketInfo {0} {1} {2}".format(ch, exposure, gain)
		self.send_command(cmd)

	def set_jeg_quality(self, quality):
		cmd = "SetJPEGQuality {0}".format(quality)
		self.send_command(cmd)

	def set_jpeg_cbr(self, enable, bitrate):
		if enable:
			cmd = "SetJPEGCBR ON {0}".format(bitrate)
		else:
			cmd = "SetJPEGCBR OFF"
		self.send_command(cmd)

	def set_h264_quality(self, quality):
		cmd = "SetH264Quality {0}".format(quality)
		self.send_command(cmd)

	def set_zoom_focus_position(self, zoom, focus):
		cmd = "SetZoomFocusPosition {0} {1}".format(zoom, focus)
		self.send_command(cmd)

	def get_firmware_version(self):
		return self.send_command("GetFirmwareVersion")[3:]

	def get_system_info(self):
		return self.send_command("GetSystemInfo")[3:]

	def get_serial_number(self):
		return self.send_command("GetSerialNumber")[3:]

	#
	#	Functions for stream port (image capture)
	#
	def connect_stream(self, host, isUDP=True):
		if isUDP:
			self.isUDP = True
			self.strm = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

			bufsize = self.strm.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF) 
			#print("recv buf size", bufsize)
			self.strm.setsockopt( 
					socket.SOL_SOCKET, 
					socket.SO_RCVBUF, 
					Camera.RECV_BUF_SIZE) 
			dst_port = 1334
			src_port = 1334		# This may have to be changed if you are receiving streams from multiple cameras, each having different source port number.
			self.strm.bind(('', src_port)) 
			self.strm.settimeout(1) # timeout with 1 second.
			
			cmd = bytearray("CONNECT {0}".format(src_port), encoding='ascii')
			self.address = (host, dst_port)		
			self.strm.sendto(cmd, self.address)

		else: # TCP Stream
			self.isUDP = False
			self.strm = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.strm.setsockopt( 
					socket.SOL_SOCKET, 
					socket.SO_RCVBUF, 
					Camera.RECV_BUF_SIZE) 
			port = 1334
			self.strm.connect((host, port)) 
			self.strm.settimeout(1) # timeout with 1 second.
			self.strm.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)

	def disconnect_stream(self):
		if self.isUDP:
			cmd = bytearray("DISCONNECT", encoding='ascii')
			self.strm.sendto(cmd, self.address)
		self.strm.close()

	def grab(self):
		if self.isUDP:
			return self.grab_udp()
		else:
			return self.grab_tcp()

	def grab_udp(self):
		#print("[grab_udp]")
		image = None
		self.strm.sendto(self.ping, self.address)
		pos = 0

		try:
			# read some bytes and find the start of the jpeg data.
			while True:
				data, addr = self.strm.recvfrom(1502)
				#print("recv len:", len(data))
				if len(data) == 256:
					payload_type = ((data[0] * 256 + data[1]) * 256 + data[2]) * 256 + data[3]
					if payload_type == 1:
						size = ((data[4] * 256 + data[5]) * 256 + data[6]) * 256 + data[7]
						break

			# found the start. read the remaining data.
			if len(data) != 256:
				jpeg = bytearray(data[pos:])
			else:
				jpeg = bytearray(0)

			print("recv jpeg size=", size)
			while len(jpeg) < size:
				chunk = size - len(jpeg)
				if chunk > 1460:
					chunk = 1460
				jpeg_chunk, addr = self.strm.recvfrom(chunk)
				jpeg = jpeg + bytearray(jpeg_chunk)

			# check EOI marker
			if jpeg[-2] != 255 or jpeg[-1] != 217 : 
				raise OSError("EOI error")

			# decode the jpeg buffer
			if self.count % (1 + Camera.SKIP_FRAME) == 0:
				jpeg_np = np.frombuffer(jpeg, dtype=np.uint8)
				image = cv2.imdecode(np.fromstring(jpeg_np, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
				
		except socket.timeout:
			print("socket timeout")

		except OSError as error:
			print("Error: ", error)
		
		self.count += 1
		return image

	def grab_tcp(self):
		image = None
		self.strm.send(self.ping)
		pos = 0

		try:
			# read some bytes and find the start of the jpeg data.
			while True:
				data = self.strm.recv(1436)
				if len(data) == 4:
					size = ((data[0] * 256 + data[1]) * 256 + data[2]) * 256 + data[3]
					break
				else:
					pos = 0
					for i in range(len(data)-6):
						if data[i+4] == 255 and data[i+5] == 216: # SOI marker?
							size = ((data[i] * 256 + data[i+1]) * 256 + data[i+2]) * 256 + data[i+3]
							if size < 512000 and size > 50000: # valid size?
								pos = i + 4
								break
							else:
								raise OSError("Invalid size")
					if pos != 0:
						break
				#raise OSError("SOI not found")

			# found the start. read the remaining data.
			if len(data) != 4:
				jpeg = bytearray(data[pos:])
			else:
				jpeg = bytearray(0)

			while len(jpeg) < size:
				jpeg_chunk = self.strm.recv(size - len(jpeg))
				jpeg = jpeg + bytearray(jpeg_chunk)

			# check EOI marker
			if jpeg[-2] != 255 or jpeg[-1] != 217 : 
				raise OSError("EOI error")

			# decode the jpeg buffer
			if self.count % (1 + Camera.SKIP_FRAME) == 0:
				jpeg_np = np.frombuffer(jpeg, dtype=np.uint8)
				image = cv2.imdecode(np.fromstring(jpeg_np, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
				
		except socket.timeout:
			print("socket timeout")

		except OSError as error:
			print("Error: ", error)
		
		self.count += 1
		return image
