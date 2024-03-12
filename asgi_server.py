import asyncio
from fast_api_app import app

class MyUvicorn:
    def __init__(self, host: str, port: int, app):
        self.host = host
        self.port = port
        self.status = 200
        self.headers = []
        self.body = b''
        self.app = app

    # 서버 시작
    async def start_server(self):
        self.server = await asyncio.start_server(self._request_handle, self.host, self.port)

        async with self.server:
            await self.server.serve_forever()
    
    # HTTP 요청 처리
    async def _request_handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        data = b''
        while True:
            data += await reader.read(100)
            
            # 데이터를 읽고, feed_eof를 매번 호출해주어야 at_eof를 확인할 수 있음.
            # 참고) https://docs.python.org/3.10/library/asyncio-stream.html#asyncio.StreamReader.at_eof
            reader.feed_eof()
            if reader.at_eof():
                break
                
        # 만약 빈 값을 받았다면, 연결 종료
        if data == b'':
            writer.close()
            await writer.wait_closed()
            return

        data = data.replace(b'\r\n', b'\n')
        splited_data = data.split(b'\n\n', 1)

        # body, header, http_info 추출        
        if len(splited_data) == 2:
            b_header, b_body = splited_data
        else:
            b_header = splited_data[0]
            b_body = b''
        
        _, b_path, _ = b_header.split(b'\n')[0].split(b' ')
        if b'?' in b_path:
            b_uri, b_query_string = b_path.split(b'?')
        else:
            b_uri, b_query_string = b_path, b''

        headers = b_header.split(b'\n')

        http_info = headers[0].decode()
        method, _, http_scheme_and_version = http_info.split(' ')
        uri, query_string = b_uri.decode(), b_query_string.decode()
        http_scheme, http_version = http_scheme_and_version.split('/')

        headers = headers[1:]

        headers = list(map(lambda x: x.split(b': ', 1), headers))
        headers = [[key, value] for key, value in headers]

        # asgi scope 제작
        # 참고) https://asgi.readthedocs.io/en/latest/specs/www.html#http-connection-scope
        scope = {
            'type': 'http',
            'asgi':{
                'version':'2.4',
                'spec_version':'2.0'
            },
            'http_version': http_version,
            'method': method,
            'scheme': http_scheme,
            'path': uri,
            'raw_path': b_uri,
            'query_string': query_string,
            'headers': headers,
            'client': writer.get_extra_info('peername'),
            'server':('127.0.0.1', 9000),
        }
        
        # receive 함수 제작
        # asgi app은 해당 함수를 통해 body 데이터를 수신함
        # 참고) https://asgi.readthedocs.io/en/latest/specs/www.html#request-receive-event
        async def receive():
            return {
                'type': 'http.request',
                'body': b_body
            }

        # send 함수 제작
        # asgi app은 해당 함수를 통해 response를 반환함
        # 참고) http.response.start => https://asgi.readthedocs.io/en/latest/specs/www.html#response-start-send-event
        # 참고) http.response.body => https://asgi.readthedocs.io/en/latest/specs/www.html#response-body-send-event
        async def send(options:dict):
            if options['type'] == 'http.response.start':
                self.status = options['status']
                self.headers = options['headers']
            elif options['type'] == 'http.response.body':
                self.body = options['body']

        # app에게 처리하라고 전달
        await self.app(scope, receive, send)
        
        # 처리 종료 후 response 제작
        response_first = f"{http_scheme_and_version} {self.status}\r\n"
        response_header = b"\r\n".join(
            list(map(lambda x:x[0]+b": "+x[1], self.headers))
        )
        response = response_first.encode() + response_header + b'\r\n\r\n' + self.body

        # 소켓을 통해서 응답 
        writer.write(response)
        writer.close()
        await writer.wait_closed() 
            

uvicorn = MyUvicorn('127.0.0.1', 1026, app)
asyncio.run(uvicorn.start_server())
