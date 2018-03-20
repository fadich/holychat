from tornado import websocket, web, ioloop


connections = dict()


class EchoWebSocket(websocket.WebSocketHandler):
    def data_received(self, chunk):
        pass

    def check_origin(self, origin):
        return True

    def open(self):
        connections[self.identifier] = {
            'connection': self,
            'queue': list()
        }

        print('Connected by <{}>'.format(self.request.remote_ip))

    def on_message(self, message):
        self.add_message(message)

        # print({ k: len(connections[k].get('queue')) for k in connections})

        self.write_message({
            'queue': self.get_queue()
        })

    def on_close(self):
        try:
            connections.pop(self.identifier)
        except KeyError as e:
            pass
        print('Disconnected by <{}>'.format(self.request.remote_ip))

    @property
    def identifier(self):
        return self.request.uri[5:]

    def add_message(self, message):
        for _id in connections:
            if _id != self.identifier:
                # if len(connections[_id].get('queue')) > 400:
                #     connections[_id]['queue'] = []
                connections[_id].get('queue').append(message)

    def get_queue(self):
        queue = connections[self.identifier].get('queue')
        connections[self.identifier]['queue'] = list()
        return queue


if __name__ == '__main__':
    application = web.Application([
        (r'/', EchoWebSocket),
    ])
    application.default_host = '192.168.0.100'
    application.listen(8888)

    print('Server started at <{}>'.format('192.168.0.100:8888'))
    try:
        ioloop.IOLoop.current().start()
    except KeyboardInterrupt as e:
        print('Stopping server...')
