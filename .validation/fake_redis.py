from __future__ import annotations

import argparse
import socketserver
from typing import Any

STORE: dict[str, bytes] = {}


def _read_command(handler: socketserver.StreamRequestHandler) -> list[bytes] | None:
    first = handler.rfile.readline()
    if not first:
        return None
    if not first.startswith(b'*'):
        return [first.strip()]
    count = int(first[1:].strip())
    parts: list[bytes] = []
    for _ in range(count):
        length_line = handler.rfile.readline()
        if not length_line or not length_line.startswith(b'$'):
            return None
        length = int(length_line[1:].strip())
        data = handler.rfile.read(length)
        handler.rfile.read(2)
        parts.append(data)
    return parts


class Handler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        while True:
            command = _read_command(self)
            if not command:
                break
            name = command[0].decode('utf-8', errors='ignore').upper()
            if name == 'PING':
                self.wfile.write(b'+PONG\r\n')
            elif name == 'GET' and len(command) >= 2:
                value = STORE.get(command[1].decode())
                if value is None:
                    self.wfile.write(b'$-1\r\n')
                else:
                    self.wfile.write(f'${len(value)}\r\n'.encode() + value + b'\r\n')
            elif name == 'SET' and len(command) >= 3:
                key = command[1].decode()
                value = command[2]
                STORE[key] = value
                self.wfile.write(b'+OK\r\n')
            elif name == 'DEL' and len(command) >= 2:
                deleted = 1 if STORE.pop(command[1].decode(), None) is not None else 0
                self.wfile.write(f':{deleted}\r\n'.encode())
            elif name == 'HELLO':
                self.wfile.write(b'+OK\r\n')
            elif name == 'CLIENT':
                self.wfile.write(b'+OK\r\n')
            elif name == 'QUIT':
                self.wfile.write(b'+OK\r\n')
                break
            else:
                self.wfile.write(b'+OK\r\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--port', type=int, default=6379)
    args = parser.parse_args()
    server = socketserver.ThreadingTCPServer((args.host, args.port), Handler)
    server.daemon_threads = True
    server.allow_reuse_address = True
    server.serve_forever()
