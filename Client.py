#!/usr/bin/python
import pyrealsense2 as rs
import sys, getopt
import asyncore
import numpy as np
import zlib
import socket
import struct
import time
import cv2


print('Number of arguments:', len(sys.argv), 'arguments.')
print('Argument List:', str(sys.argv))
mc_ip_address = '192.168.0.100'
port = 1024
chunk_size = 4096

def main(argv):
    multi_cast_message(mc_ip_address, port, 'EtherSensePing')
        

#UDP client for each camera server 
class ImageClient(asyncore.dispatcher):
    def __init__(self, server, source):   
        asyncore.dispatcher.__init__(self, server)
        self.address = server.getsockname()[0]
        self.port = source[1]
        self.colorbuffer = bytearray()
        self.depthbuffer = bytearray()
        self.windowName = self.port
        # open cv window which is unique to the port 
        cv2.namedWindow("window"+str(self.windowName))
        self.remainingColorBytes = 0
        self.remainingDepthBytes = 0
        self.time = 0
            
    def handle_read(self):
        if self.remainingColorBytes == 0 and self.remainingDepthBytes == 0:
            self.time = time.time()
            # get the expected frame size
            self.color_frame_length = struct.unpack('<I', self.recv(4))[0]
            self.depth_frame_length = struct.unpack('<I', self.recv(4))[0]
            self.remainingColorBytes = self.color_frame_length
            self.remainingDepthBytes = self.depth_frame_length
        # request the frame data until the frame is completely in buffer
        if self.remainingColorBytes > 0:
            colordata = self.recv(self.remainingColorBytes)
            self.colorbuffer += colordata
            self.remainingColorBytes -= len(colordata)
        else:
            depthdata = self.recv(self.remainingDepthBytes) # not receiving
            self.depthbuffer += depthdata
            self.remainingDepthBytes -= len(depthdata)
        # once the frame is fully recived, process/display it
        if len(self.colorbuffer) == self.color_frame_length and len(self.depthbuffer) == self.depth_frame_length:
            self.handle_frame()
            print('time taken =', time.time() - self.time)
            self.time = time.time()
    
    def handle_frame(self):
        # convert the frame from string to numerical data
        color = np.fromstring(zlib.decompress(self.colorbuffer),np.dtype('uint8')).reshape(480,848,3)
        depth = np.fromstring(zlib.decompress(self.depthbuffer),np.dtype('uint16')).reshape(480,848)
        depth = cv2.applyColorMap(cv2.convertScaleAbs(depth, alpha=0.03), cv2.COLORMAP_JET)
        colorndepth = np.hstack((color, depth))
        cv2.imshow("window"+str(self.windowName), colorndepth)
        cv2.waitKey(1)
        self.colorbuffer = bytearray()
        self.depthbuffer = bytearray()
    def readable(self):
        return True

    
class EtherSenseClient(asyncore.dispatcher):
    def __init__(self):
        asyncore.dispatcher.__init__(self)
        self.server_address = ('', 1024)
        # create a socket for TCP connection between the client and server
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(5)
        
        self.bind(self.server_address) 	
        self.listen(10)

    def writable(self): 
        return False # don't want write notifies

    def readable(self):
        return True
        
    def handle_connect(self):
        print("connection recvied")

    def handle_accept(self):
        pair = self.accept()
        #print(self.recv(10))
        if pair is not None:
            sock, addr = pair
            print ('Incoming connection from %s' % repr(addr))
            # when a connection is attempted, delegate image receival to the ImageClient 
            handler = ImageClient(sock, addr)

def multi_cast_message(ip_address, port, message):
    # send the multicast message
    multicast_group = (ip_address, port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    connections = {}
    try:
        # Send data to the multicast group
        print('sending "%s"' % message + str(multicast_group))
        sent = sock.sendto(message.encode(), multicast_group)
   
        # defer waiting for a response using Asyncore
        client = EtherSenseClient()
        asyncore.loop()

        # Look for responses from all recipients
        
    except socket.timeout:
        print('timed out, no more responses')
    finally:
        print(sys.stderr, 'closing socket')
        sock.close()

if __name__ == '__main__':
    main(sys.argv[1:])
