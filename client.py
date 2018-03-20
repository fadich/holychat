import pyaudio
import json, time
from tornado.ioloop import IOLoop, PeriodicCallback
from tornado import gen, iostream
from tornado.websocket import websocket_connect


CLIENT_TIMEOUT = 3000

AUDIO_FORMAT = pyaudio.paInt16
AUDIO_CHANNELS = 1
AUDIO_RATE_IN = 22000
AUDIO_RATE_OUT = 22100
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

audio_out = pyaudio.PyAudio()
format_out = audio_out.get_format_from_width(AUDIO_WIDTH)
stream_out = audio_out.open(
    format=format_out,
    channels=AUDIO_CHANNELS,
    rate=AUDIO_RATE_OUT,
    output=True,
    frames_per_buffer=AUDIO_CHUNK
)


class Client(object):
    def __init__(self, url, timeout):
        self.url = url
        self.timeout = timeout
        self.ioloop = IOLoop.instance()
        self.ws = None
        self.connect()
        PeriodicCallback(self.keep_alive, self.timeout).start()
        self.ioloop.start()

    @gen.coroutine
    def connect(self):
        try:
            self.ws = yield websocket_connect(self.url)
            print('Connected to <{}>'.format(self.url))
            self.run()
        except Exception as e:
            # print('Reconnecting...')
            print('Disconnected...')
            exit()

    @gen.coroutine
    def run(self):
        while True:
            rec = stream_in.read(AUDIO_CHUNK * 8)
            try:
                self.ws.write_message(rec.hex())
            except Exception as e:
                print(e)
                self.ws = None
                break

            msgs = yield self.ws.read_message()
            if msgs is None:
                self.ws = None
                break

            for msg in json.loads(msgs).get('queue'):
                stream_out.write(bytes.fromhex(msg))


    def keep_alive(self):
        if self.ws is None:
            # self.connect()
            print('Disconnected...')
            exit()


if __name__ == '__main__':
    try:
        print(time.time())
        client = Client('ws://localhost:8888?id={}'.format(time.time()), CLIENT_TIMEOUT)
    except (iostream.StreamClosedError, ) as e:
        print('Disconnected...')
    except KeyboardInterrupt as e:
        print('Stopping app...')
    finally:
        stream_in.stop_stream()
        stream_in.close()
        audio_in.terminate()

        stream_out.stop_stream()
        stream_out.close()
        audio_out.terminate()
