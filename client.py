import pyaudio
from tornado.ioloop import IOLoop, PeriodicCallback
from tornado import gen, iostream
from tornado.websocket import websocket_connect
from threading import Thread


CLIENT_TIMEOUT = 3000

AUDIO_FORMAT = pyaudio.paInt16
AUDIO_CHANNELS = 1
AUDIO_RATE_IN = 80100
AUDIO_RATE_OUT = 82100
AUDIO_WIDTH = 2
AUDIO_CHUNK = 128


audio_in = pyaudio.PyAudio()

stream_in = audio_in.open(
    format=AUDIO_FORMAT,
    channels=AUDIO_CHANNELS,
    rate=AUDIO_RATE_IN,
    input=True,
    frames_per_buffer=AUDIO_CHUNK
)


class Client(object):
    def __init__(self, url, timeout):
        self.url = url
        self.timeout = timeout
        self.ioloop = IOLoop.instance()
        self.ws = None
        self.connect()
        PeriodicCallback(self.keep_alive, CLIENT_TIMEOUT).start()
        self.ioloop.start()

    @gen.coroutine
    def connect(self):
        print('Connecting...')

        try:
            self.ws = yield websocket_connect(self.url)
            print('Connected to <{}>'.format(self.url))
            self.run()
        except Exception as e:
            print('Disconnected...')

    @gen.coroutine
    def run(self):
        while True:
            # self.ws.write_message('{}'.format(time()))
            self.ws.write_message(stream_in.read(AUDIO_CHUNK), True)
            msg = yield self.ws.read_message()
            if msg is None:
                print('No message...')
                print('Reconnecting...')
                self.ws = None
                break

            th = Thread(target=self.write_message, args=(msg,))
            th.start()
            th.join()

    def keep_alive(self):
        if self.ws is None:
            self.connect()

    def write_message(self, message):
        print('Playing...')
        print(message)
        audio_out = pyaudio.PyAudio()
        format_out = audio_out.get_format_from_width(AUDIO_WIDTH)

        stream_out = audio_out.open(
            format=format_out,
            channels=AUDIO_CHANNELS,
            rate=AUDIO_RATE_OUT,
            output=True,
            frames_per_buffer=AUDIO_CHUNK
        )
        stream_out.write(message)
        stream_out.stop_stream()
        stream_out.close()
        audio_out.terminate()
        exit()


if __name__ == '__main__':
    try:
        client = Client('ws://localhost:8888', 5)
    except (iostream.StreamClosedError, ) as e:
        print('Disconnected...')
    except KeyboardInterrupt as e:
        print('Stopping app...')
    finally:
        stream_in.stop_stream()
        stream_in.close()
        audio_in.terminate()
