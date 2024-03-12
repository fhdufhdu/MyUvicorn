# MyGunicorn
나만의 ASGI 서버입니다.
최대한 Uvicorn 처럼 만드는 것이 목표입니다.

## 특징
- 서드파티 라이브러리 NO! 모두 빌트인 라이브러리를 이용(django 제외)
- asyncio의 소켓 연결 활용(`start_server`)
    - python의 selector 기반
- 프로세스는 하나만 사용, 향후 [MyGunicorn](https://github.com/fhdufhdu/MyGunicorn)과 연계해서 멀티프로세스로 띄울 수 있게 만들 예정

## 설치(의존성)
``` bash
pip install fastapi
```

## 실행방법
``` bash
python asgi_server.py
```
