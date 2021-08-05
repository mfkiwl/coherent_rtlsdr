from rtlsdr import RtlSdr
from datetime import datetime
import asyncio
import matplotlib.pyplot as plt
from multiprocessing import Process, Queue


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


def check_samples(q1, q2, noise, samplesperbit):
    while True:
        values = []
        withinnoisecounter = 0
        signal = False
        if q1.qsize() > 10:
            print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                  'CHECKSAMPLES - Warning: Queue depth is', q1.qsize())
        samples = q1.get()
        for sample in samples:
            if not signal:
                # Start when signal breaks out of noise range
                if sample.real > noise or sample.real < -noise:
                    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                          'CHECKSAMPLES - signal detected')
                    signal = True
                    values.append(sample.real)
            else:
                values.append(sample.real)
                if not (sample.real > noise or sample.real < -noise):
                    withinnoisecounter += 1
                elif withinnoisecounter > 0:
                    withinnoisecounter = 0
                if withinnoisecounter > samplesperbit * 3:
                    # Break when signal is within noise range 3 * samplesperbit
                    break
        if signal:
            q2.put(values)


def show_samples(q2, srate):
    while True:
        values = q2.get()
        plt.figure(figsize=(20, 5))
        # Preamble should be in here
        plt.plot(values[:2000])
        plt.show()


def main():
    noise = 0.9
    # 38400 * 30 to get exactly 30 samples per bit.
    srate = 1152000
    samplesperbit = 1000000 / 38400 / (1000000 / srate)

    # open a given rtl sdr
    serial_numbers = RtlSdr.get_device_serial_addresses()
    device_index = RtlSdr.get_device_index_by_serial('00000002')
    sdr = RtlSdr(device_index)

    # Just like in URH
    sdr.freq_correction = 1
    sdr.sample_rate = srate
    sdr.center_freq = 868.200e6
    sdr.gain = 'auto'

    # Run check_samples in another thread to make sure we don't miss any samples
    q1 = Queue()
    q2 = Queue()
    p1 = Process(target=check_samples, args=(q1, q2, noise, samplesperbit))
    p1.start()
    # Run decode_fsk in another thread to make sure we don't miss any samples
    p2 = Process(target=show_samples, args=(q2, srate))
    p2.start()
    # This is the main loop
    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_samples(sdr, q1))


if __name__ == "__main__":
    main()
