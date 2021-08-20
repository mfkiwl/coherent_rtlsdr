from rtlsdr import RtlSdr
import matplotlib.pyplot as plt
from datetime import datetime
from multiprocessing import Process, Queue
import asyncio

async def get_samples(sdr, q1):
    counter = 0
    timestamp1 = datetime.now()
    # Get this many samples every time
    async for samples in sdr.stream():
        q1.put(samples)
        counter += 1
        timestamp2 = datetime.now()
        if (timestamp2 - timestamp1).total_seconds() > 1:
            # To see if we missed any samples. Should be close to srate samples p/s
            print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'GETSAMPLES -',
                  int((counter * 131072) / (timestamp2 - timestamp1).total_seconds()), 'samples p/s')
            counter = 0
            timestamp1 = datetime.now()


def show_samples(q1):
    while True:
        values = q1.get()
        fig, ax = plt.subplots()
        ax.plot(values[:20])
        #print(values[:20])
        plt.show()


def main():
    serial_numbers = RtlSdr.get_device_serial_addresses()
    device_index = RtlSdr.get_device_index_by_serial('00000002')

    sdr = RtlSdr(device_index)

    # configure device
    sdr.sample_rate = 2.048e6  # Hz
    sdr.center_freq = 70e6     # Hz
    sdr.freq_correction = 60   # PPM
    sdr.gain = 'auto'

    q1 = Queue()
    p1 = Process(target=show_samples, args=(q1, ))
    p1.start()
    # This is the main loop
    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_samples(sdr, q1))

    # values = sdr.read_samples(256)

    # plt.figure(figsize=(8, 5))
    # # Preamble should be in here
    # plt.plot(values)
    # plt.show()


if __name__ == "__main__":
    main()
