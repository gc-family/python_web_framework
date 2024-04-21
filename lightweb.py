from http.client import responses
import asynchat
import asyncore
import os
import mimetypes
import socket
from configuration import *


class FindTemplate:
    def __init__(self, url):
        self.url = url
        if os.name == "nt":
            self.url = self.url.replace("/", "\\")

    def _find_template(self):
        _return = None
        for path in TEMPLATE_DIRS:
            _full_path = os.path.join(path, self.url)
            if os.path.exists(_full_path):
                _return = _full_path
                break
        return _return

    def find_template(self):
        _template = self._find_template()
        return _template

    def _is_file(self, path):
        if os.path.isfile(path):
            return True
        else:
            return False

    def is_file(self, path):
        return self._is_file(path)


class AsyncHttp(asyncore.dispatcher):
    def __init__(self, port):
        asyncore.dispatcher.__init__(self, sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM))
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.set_reuse_addr()
        self.bind(('', port))
        self.listen(5)

    def handle_accept(self) -> None:
        client, address = self.accept()
        print("connection is created with {}".format(address))
        return AsyncHttpHandler(client)


class AsyncHttpHandler(asynchat.async_chat):
    def __init__(self, conn=None):
        asynchat.async_chat.__init__(self, conn)
        self.data = []
        self.got_header = False
        self.set_terminator(b"\r\n\r\n")

    def collect_incoming_data(self, data):
        if not self.got_header:
            self.data.append(data)

    def found_terminator(self):
        self.got_header = True
        header_data = b"".join(self.data)
        header_text = header_data.decode("latin-1")
        header_lines = header_text.splitlines()
        request = header_lines[0].split()
        op = request[0]
        url = request[1][1:]
        self.process_request(op, url)

    def process_request(self, op, url):
        if op.upper() == "GET":
            templateEngine = FindTemplate(url)
            template = templateEngine.find_template()
            if not template:
                self.send_error(404, "File %s not found\r\n")
            else:
                type, encoding = mimetypes.guess_type(template)
                size = os.path.getsize(template)
                self.push_text("HTTP/1.0 200 OK\r\n")
                self.push_text("Content-length: %s\r\n" % size)
                self.push_text("Content-type: %s\r\n" % type)
                self._push_end_of_header()
                # send the actual data
                self.push_with_producer(FileProducer(template, url))
        else:
            self.send_error(501, "%s method not implemented" % op)
        self.close_when_done()

    def _push_end_of_header(self):
        self.push_text("\r\n")

    def push_text(self, data):
        self.push(data.encode("latin-1"))

    def send_error(self, code, message):
        self.push_text("HTTP/1.0 %s %s\r\n" % (code, responses[code]))
        self.push_text("Content-type: text/plain\r\n")
        self._push_end_of_header()
        self.push_text(message)


class FileProducer(object):
    def __init__(self, actualpath, url, buffer_size=512):
        self.path = actualpath
        self.url = url
        print("processing - {} [status 200 OK]".format(self.url))
        try:
            self.f = open(self.path, mode="rb")
        except Exception as e:
            print(e)
            exit()
        self.buffer_size = buffer_size

    def more(self):
        data = self.f.read(self.buffer_size)
        if not data:
            self.f.close()

        return data


if __name__ == '__main__':
    port = 8000
    print(f"the server is running on {port}")
    a = AsyncHttp(port=port)
    # print([attrib for attrib in dir(a) if "event" in attrib])
    asyncore.loop()