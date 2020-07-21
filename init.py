import splinter
# import logging
import selenium
from manager import Manager
from concurrent.futures import ProcessPoolExecutor
import asyncio
import multiprocessing
import ws
import logging
import sys
from config import Config

username = Config.USERNAME
password = Config.PASSWORD

logging.basicConfig(
    level=logging.INFO,
    format='%(processName)10s %(name)18s %(levelname)-8s: %(message)s',
    filename='run.log'
)


def launch_main(queue):
    manager = Manager(username, password)
    manager.queue = queue
    manager.run()


def launch_ws(queue):
    loop_ws = ws.Ws()
    loop_ws.queue = queue
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(loop_ws.run())


if __name__ == "__main__":
    executor = ProcessPoolExecutor(2)
    loop = asyncio.get_event_loop()

    m = multiprocessing.Manager()
    queue = m.Queue()

    asyncio.ensure_future(loop.run_in_executor(executor, launch_main, queue))
    asyncio.ensure_future(loop.run_in_executor(executor, launch_ws, queue))
    loop.run_forever()
