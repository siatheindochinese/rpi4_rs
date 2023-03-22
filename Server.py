#!/usr/bin/python
import pyrealsense2.pyrealsense2 as rs
import sys, getopt
import asyncore
import numpy as np
import zlib
import socket
import struct
import time


print('Number of arguments:', len(sys.argv), 'arguments.')
print('Argument List:', str(sys.argv))
mc_ip_address = '192.168.0.100'
port = 1024
chunk_size = 4096
#rs.log_to_console(rs.log_severity.debug)

align = rs.align(rs.stream.color)

def getRGBD(pipeline, depth_filter):
	frames = pipeline.wait_for_frames()
	aligned_frames = align.process(frames)
	aligned_depth_frame = aligned_frames.get_depth_frame()
	color_frame = aligned_frames.get_color_frame()
	if not aligned_depth_frame or not color_frame:
		return None, None
	depth_image = np.asanyarray(aligned_depth_frame.get_data())
	color_image = np.asanyarray(color_frame.get_data())
	return color_image, depth_image
    
def openPipeline():
	cfg = rs.config()
	cfg.enable_stream(rs.stream.depth, 848, 480, rs.format.z16, 30)
	cfg.enable_stream(rs.stream.color, 848, 480, rs.format.bgr8, 30)
	pipeline = rs.pipeline()
	pipeline_profile = pipeline.start(cfg)
	sensor = pipeline_profile.get_device().first_depth_sensor()
	return pipeline

class DevNullHandler(asyncore.dispatcher_with_send):
	def handle_read(self):
		print(self.recv(1024))

	def handle_close(self):
		self.close()
           
		
class EtherSenseServer(asyncore.dispatcher):
	def __init__(self, address):
		asyncore.dispatcher.__init__(self)
		print("Launching Realsense Camera Server")
		try:
			self.pipeline = openPipeline()
		except:
			print("Unexpected error: ", sys.exc_info()[1])
			sys.exit(1)
		self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
		print('sending acknowledgement to', address)
        
		# reduce the resolution of the depth image using post processing
		self.decimate_filter = rs.decimation_filter()
		self.decimate_filter.set_option(rs.option.filter_magnitude, 2)
		self.frame_data = ''
		self.connect((address[0], 1024))
		self.packet_id = 0
		self.time = 0

	def handle_connect(self):
		print("connection received")

	def writable(self):
		return True

	def update_frame(self):
		color, depth = getRGBD(self.pipeline, self.decimate_filter)
		if depth is not None and color is not None:
			colordata = zlib.compress(color,1)
			colorlen = struct.pack('<I', len(colordata))
			depthdata = zlib.compress(depth,1)
			depthlen = struct.pack('<I', len(depthdata))
			self.frame_data = b''.join([colorlen, depthlen, colordata, depthdata])

	def handle_write(self):
		# first time the handle_write is called
		if not hasattr(self, 'frame_data'):
			self.update_frame()
		# the frame has been sent in it entirety so get the latest frame
		if len(self.frame_data) == 0:
			print('time taken =', time.time() - self.time)
			self.update_frame()
			self.time = time.time()
		else:
			# send the remainder of the frame_data until there is no data remaining for transmition
			remaining_size = self.send(self.frame_data)
			self.frame_data = self.frame_data[remaining_size:]

	def handle_close(self):
		self.close()
            
class MulticastServer(asyncore.dispatcher):
	def __init__(self, host = mc_ip_address, port=1024):
		asyncore.dispatcher.__init__(self)
		server_address = ('', port)
		self.create_socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.bind(server_address) 	

	def handle_read(self):
		data, addr = self.socket.recvfrom(42)
		print('Recived Multicast message %s bytes from %s' % (data, addr))
		# Once the server recives the multicast signal, open the frame server
		EtherSenseServer(addr)
		print(sys.stderr, data)

	def writable(self): 
		return False # don't want write notifies

	def handle_close(self):
		self.close()

	def handle_accept(self):
		channel, addr = self.accept()
		print('received %s bytes from %s' % (data, addr))


def main(argv):
	# initalise the multicast receiver 
	server = MulticastServer()
	# hand over excicution flow to asyncore
	asyncore.loop()

if __name__ == '__main__':
	main(sys.argv[1:])

