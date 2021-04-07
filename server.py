# -*- coding: utf-8 -*-
#
# Wildlife Audio Stream Sampler
# Author: Peter Ersts (ersts@amnh.org)
#
# --------------------------------------------------------------------------
#
# This file is part of Wildlife Audio Stream Sampler
#
# Wildlife Audio Stream Sampler is free software: you can redistribute it 
# and/or modify it under the terms of the GNU General Public License as 
# published by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Wildlife Audio Stream Sampler is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.
#
# --------------------------------------------------------------------------
import sys
import socket
import pyaudio
from multiprocessing import Process

PORT = 8888
DEVICE = 'snd_rpi_simple_card: simple-card_codec_link snd-soc-dummy-dai-0 (hw:2,0)'
# Uncomment the line below if you don't know the name of the sound device
# to be presented with a list of devices to choose from
# DEVICE = ''

def stream_audio(conn, device):
    audio = pyaudio.PyAudio()
    stream = audio.open(format=pyaudio.paInt32,rate=44100,channels=1, input_device_index=device, input=True, frames_per_buffer=44100)
    stream.stop_stream()
    while True:
        data = conn.recv(64)
        if not data:
            break
        seconds = int.from_bytes(data, byteorder='big')
        stream.start_stream()
        for i in range(seconds):
            stream_data = stream.read(44100, exception_on_overflow=False)
            try:
                conn.sendall(stream_data)
            except BrokenPipeError:
                return        
        stream.stop_stream()


sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind(('', PORT))
sock.listen()

device = -1
audio = pyaudio.PyAudio()
if DEVICE == '':
    devices = audio.get_device_count()
    for dev in range(devices):
        info = audio.get_device_info_by_index(dev)
        print('{}: {}'.format(info['index'], info['name']))
    device = input('Enter the device number to use for input: ')
    try:
        device = int(device)
    except ValueError:
        device = -1
else:
    for dev in range(audio.get_device_count()):
        info = audio.get_device_info_by_index(dev)
        if info['name'] == DEVICE:
            device = info['index']

if device == -1:
    print('Audio device not found.')
    sys.exit(0)

print('Server listening on port {}'.format(PORT))
while True:
    conn, addr = sock.accept()
    with conn:
        p = Process(target=stream_audio, args=(conn, device,))
        p.start()
        # Block other incomming connections for now as device is
        # only accessible to one process at a time
        p.join()
    