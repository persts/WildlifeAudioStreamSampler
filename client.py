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
import os
import sys
import socket
import time
import librosa
import librosa.display
import numpy as np
import soundfile as sf
import matplotlib.pyplot as plt
from multiprocessing import Process

LENGTH = 60 # Seconds
SAMPLE_RATE = 44100
SAMPLE_LENGTH = 4 # Seconds
OVERLAP = 2  # Seconds
DELAY = 5  # Minutes
VMAX = 10 # Max dB for constant scaling across samples
MAX_HZ = 8000 # Limit the y-axis of the output image

HOST = sys.argv[1]
PORT = 8888

def process_data(socket):
    timestamp = time.strftime('%Y-%m-%d_%H-%M-%S')
    os.mkdir(timestamp)

    socket.send(LENGTH.to_bytes(2, byteorder='big'))
    buffer = bytearray()
    while len(buffer) < (SAMPLE_RATE * 4) * LENGTH:
        buffer += socket.recv(4096)
    
    audio = np.frombuffer(buffer, dtype=np.int32)
    iterations = (LENGTH // (SAMPLE_LENGTH - OVERLAP)) - 1
    for s in range(iterations):
        start = SAMPLE_RATE * (s * (SAMPLE_LENGTH - OVERLAP))
        end = start + (SAMPLE_RATE * SAMPLE_LENGTH)
        data = audio[start:end]
        file_name = os.path.join(timestamp, 'sample_{:03d}.wav'.format(s))
        sf.write(file_name, data, SAMPLE_RATE)

        data, _ = librosa.load(file_name, SAMPLE_RATE)
        data = np.abs(librosa.stft(data, window='hann')) ** 1.6
        data = 10 * np.log10(data)

        fig = plt.figure(frameon=False)
        fig.set_size_inches(10,10)
        ax = plt.Axes(fig, [0., 0., 1., 1.])
        ax.set_axis_off()
        _ = fig.add_axes(ax)
        librosa.display.specshow(data, ax=ax, y_axis='linear', cmap='viridis', vmin=-80, vmax=VMAX)
        ax.set_ylim([0, MAX_HZ])
        fig.savefig('{}jpg'.format(file_name[:-3], 100))
        plt.close()

socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket.connect((HOST, PORT))

while True:
    p = Process(target=process_data, args=(socket,))
    p.start()
    time.sleep(DELAY * 60)
