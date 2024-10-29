from scipy.fftpack import rfft
from pydub import AudioSegment
import RPi.GPIO as GPIO
import numpy as np
import threading
import pyaudio
import time

# - GPIO Setup for LEDs
GPIO.setmode(GPIO.BCM)
# - Pins Array
pins = [4, 17, 27, 22, 10, 9, 11, 0, 5, 6, 13, 19, 26]
pins.reverse()
# - Set Up GPIO Pins
for pin in pins:
    GPIO.setup(pin, GPIO.OUT)

# - Load Music File
song = AudioSegment.from_mp3("beat_it.mp3")
# song = song.apply_gain(20)  # - Increase Volume
# - Set Chunk Size
CHUNK = 1024
# - Set Rate
RATE = song.frame_rate
# - Get Raw Data
raw_data = np.array(song.get_array_of_samples())
# - Check for Stereo
if song.channels == 2:
    raw_data = raw_data.reshape((-1, 2)).mean(axis = 1)

# - Initialize Audio Stream
p = pyaudio.PyAudio()
# - Open Stream
stream = p.open(
    format = pyaudio.paInt16,
    channels = 1,
    rate = RATE,
    output = True
)

# - Define Frequency Bands for LED Control
bands = [
    (0, 50), (50, 70), (70, 100), (100, 130),
    (130, 200), (200, 350), (350, 500), (500, 600), (600, 700),
    (700, 850), (850, 1000), (1000, 1500)
]
# bands = [
#     (60, 70), (70, 120), (120, 150), (150, 280),
#     (280, 400), (400, 600), (600, 800), (800, 1200),
#     (1200, 2000), (2000, 3000), (3000, 4000), (4000, 10000)
# ]
# - Initialize Levels
previous_levels = [0] * len(pins)
# - Set Threshold
base_threshold = 500

# - Normalize Levels
def normalize(levels):
    # - Normalize Levels to 0-1 Range
    max_level = max(levels)
    return [(level / max_level) if max_level > 0 else 0 for level in levels]

# - LED Control Function in a Separate Thread
def led_control():
    # - Forward Chase
    for pin in pins:
        GPIO.output(pin, GPIO.HIGH)
        time.sleep(0.01)
        GPIO.output(pin, GPIO.LOW)
    # - Backward Chase
    for pin in reversed(pins):
        GPIO.output(pin, GPIO.HIGH)
        time.sleep(0.01)
        GPIO.output(pin, GPIO.LOW)
    # - Forward Chase
    for pin in pins:
        GPIO.output(pin, GPIO.HIGH)
        time.sleep(0.03)
        GPIO.output(pin, GPIO.LOW)
    # - Backward Chase
    for pin in reversed(pins):
        GPIO.output(pin, GPIO.HIGH)
        time.sleep(0.03)
        GPIO.output(pin, GPIO.LOW)
    # - Blink All at Once
    for _ in range(3):
        for pin in pins:
            GPIO.output(pin, GPIO.HIGH)
        time.sleep(0.04)
        for pin in pins:
            GPIO.output(pin, GPIO.LOW)
        time.sleep(0.04)
        for pin in pins:
            GPIO.output(pin, GPIO.HIGH)
        time.sleep(0.04)
        for pin in pins:
            GPIO.output(pin, GPIO.LOW)
        time.sleep(0.04)
        for pin in pins:
            GPIO.output(pin, GPIO.HIGH)
        time.sleep(0.04)
        for pin in pins:
            GPIO.output(pin, GPIO.LOW)
        time.sleep(0.04)
    # - Define Levels
    global levels
    # - Delay
    time.sleep(2.4)
    # - Main Loop
    while True:
        normalized_levels = normalize(levels)
        for j, norm_level in enumerate(normalized_levels):
            GPIO.output(pins[j], GPIO.HIGH if norm_level > 0.3 else GPIO.LOW) # - 0.3 Sensitivity
        time.sleep(0.001)

# - Start LED Control Thread
levels = [0] * len(pins)
led_thread = threading.Thread(target=led_control)
led_thread.daemon = True
led_thread.start()

# - Play Audio
try:
    for i in range(0, len(raw_data), CHUNK):
        # - Play Audio Chunk
        chunk_data = raw_data[i:i+CHUNK].astype(np.int16).tobytes()
        stream.write(chunk_data)
        # - FFT Processing (Only Every 3 Chunks to Reduce Load and Lag)
        if i // CHUNK % 3 == 0:
            data = raw_data[i:i+CHUNK]
            if len(data) < CHUNK:
                data = np.pad(data, (0, CHUNK - len(data)), 'constant')
            fft_data = np.abs(rfft(data))
            levels = [np.sum(fft_data[low:high]) for low, high in bands]
except KeyboardInterrupt:
    pass

# - Clean up
stream.stop_stream()
stream.close()
p.terminate()
GPIO.cleanup()
led_thread.join()
