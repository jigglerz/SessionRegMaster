import asyncio
import re

import aiohttp
from typing import List
from PyQt6.QtCore import QThread, pyqtSignal

from failed_request_handler import FailedRequests


class RequestThread(QThread):
    progress_signal = pyqtSignal(int)
    link_signal = pyqtSignal(str, int, str)
    finished_signal = pyqtSignal()

    def __init__(self, access_token: str, url_list: List[str], request_method: str = "PUT", max_concurrent_requests: int = 25):
        super().__init__()
        self.access_token = access_token
        self.url_list = url_list
        self.request_method = request_method
        self._max_concurrent_requests = max_concurrent_requests
        self.failed_requests = FailedRequests()
        self.running = True

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.run_concurrent_requests())
        finally:
            loop.close()
        self.finished_signal.emit()

    async def run_concurrent_requests(self):
        semaphore = asyncio.Semaphore(self._max_concurrent_requests)

        async with aiohttp.ClientSession() as session:
            tasks = [self.send_request(session, url, semaphore) for url in self.url_list]
            for idx, coro in enumerate(asyncio.as_completed(tasks)):
                if not self.running:
                    break
                await coro
                self.progress_signal.emit(idx + 1)

    async def send_request(self, session, url, semaphore):
        async with semaphore:
            headers = {"Authorization": f"Bearer {self.access_token}"}

            try:
                if self.request_method == "PUT":
                    request_func = session.put
                elif self.request_method == "DELETE":
                    request_func = session.delete
                else:
                    raise ValueError(f"Invalid request_method: {self.request_method}")

                async with request_func(url, headers=headers) as response:
                    response_text = await response.text()

                    if response.status < 200 or response.status >= 300:
                        session_id, ticket_id = self.parse_session_and_ticket_from_url(url)
                        self.failed_requests.add_failed_request(session_id, ticket_id)

                    self.link_signal.emit(url, response.status, response_text)
                    return response.status
            except aiohttp.ClientError as e:
                self.link_signal.emit(url, 0, str(e))
                return 0

    @staticmethod
    def parse_session_and_ticket_from_url(url):
        match = re.search(r"/sessions/(\d+)/registrations/(\d+)", url)
        if match:
            return int(match.group(1)), int(match.group(2))
        return None, None

    def cancel(self):
        self.running = False

