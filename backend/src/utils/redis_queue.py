import socket
from urllib.parse import urlparse
from src.config.settings import REDIS_URL

def command(*parts, timeout=8):
    url = urlparse(REDIS_URL)
    with socket.create_connection((url.hostname, url.port or 6379), timeout) as sock:
        reader = sock.makefile('rb')
        payload = f'*{len(parts)}\r\n'.encode()
        for part in parts:
            b = str(part).encode(); payload += f'${len(b)}\r\n'.encode()+b+b'\r\n'
        sock.sendall(payload)
        def parse():
            line = reader.readline()
            if not line: raise ConnectionError('Redis disconnected')
            tag, body = line[:1], line[1:-2]
            if tag == b'-': raise ConnectionError(body.decode())
            if tag == b'*': return [parse() for _ in range(int(body))] if int(body)>=0 else None
            if tag == b'$':
                n=int(body)
                if n<0: return None
                data=reader.read(n); reader.read(2); return data.decode()
            return body.decode()
        return parse()
def enqueue(run_id): return command('RPUSH','greenhouse:runs',run_id)
def pop():
    result=command('BLPOP','greenhouse:runs',3)
    return result[1] if result else None
