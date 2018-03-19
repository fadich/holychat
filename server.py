from tornado import websocket, web, ioloop


connections = []


class EchoWebSocket(websocket.WebSocketHandler):
    def data_received(self, chunk):
        pass

    def check_origin(self, origin):
        return True

    def open(self):
        connections.append(self)
        print('WebSocket opened')

    def on_message(self, message, *args, **kwargs):
        for connection in connections:
            if connection == self:
                connection.write_message(message, True)

    def on_close(self):
        connections.remove(self)
        print('WebSocket closed')


if __name__ == '__main__':
    application = web.Application([
        (r'/', EchoWebSocket),
    ])
    application.listen(8888)

    try:
        ioloop.IOLoop.current().start()
    except KeyboardInterrupt as e:
        print('Stopping app...')
