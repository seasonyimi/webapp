import logging
logging.basicConfig(level=logging.INFO)
import asyncio
from aiohttp import web

def index(request):
    return web.Response(body=b'<h1>hello world</h1>',content_type='text/html')

async def init():
    app =web.Application()
    # 方法为GET，路径为/时，执行回调函数index，显示hello world
    app.router.add_route('GET','/',index)  #获取页面内容
    # 下面这段是为了跑起来然后记录日志写的
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner,'localhost',9000)
    await site.start()
    logging.info("server started at http://127.0.0.1:9000")  # 输出到日志信息到控制台
    # 虽然init函数是异步方式实现的，但只有一个协程在消息里循环，现在还是顺序执行
# 从asyncio模板中直接获取一个EventLoop的引用
loop = asyncio.get_event_loop()
# 把需要执行的协程丢到EventLoop中执行，就实现了异步IO
# 接收init函数内容，run_until_complete 来运行 loop ，等到 future 完成， run_until_complete 也就返回了
loop.run_until_complete(init())
loop.run_forever()

