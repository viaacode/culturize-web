import asyncio
import httpx
import time
from datetime import datetime
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse
from collections import defaultdict
from asgiref.sync import sync_to_async
from api.models import Record

class RateLimitedChecker:
    def __init__(self, rps=10, max_retries=3):
        self.interval = 1.0 / rps
        self.max_retries = max_retries
        self.client = httpx.AsyncClient(timeout=10.0)
        self.domain_locks = defaultdict(self._event_factory)

    def _event_factory(self):
        event = asyncio.Event()
        event.set()
        return event

    def parse_retry_after(self, response):
        retry_val = response.headers.get("Retry-After")
        if not retry_val:
            return 5.0
        try:
            return float(retry_val)
        except ValueError:
            try:
                target_date = parsedate_to_datetime(retry_val)
                wait_seconds = (target_date - datetime.now(target_date.tzinfo)).total_seconds()
                return max(wait_seconds, 1.0)
            except Exception:
                return 5.0

    async def check_url(self, record_id, url, attempt=0):
        domain = urlparse(url).netloc
        # Wait if the domain is currently in a 429 cooldown
        await self.domain_locks[domain].wait()

        try:
            # Step 1: Try HEAD
            response = await self.client.head(url, follow_redirects=True)
            
            # Step 2: Try GET if HEAD is not 200/429
            if response.status_code != 200 and response.status_code != 429:
                async with self.client.stream("GET", url, follow_redirects=True) as response:
                    # As soon as we enter this block, headers are already downloaded.
                    # response.status_code is now available.
                    pass 
                    # The connection is closed here before any body bytes are consumed.

            # Handle 429 Rate Limiting
            if response.status_code == 429:
                if attempt < self.max_retries:
                    await self.handle_429(domain, response, record_id, url, attempt)
                    return
                else:
                    # Max retries reached, treat as OFFLINE or "RATE_LIMITED"
                    await self.update_db(record_id, "OFFLINE")
                    return

            status = "ONLINE" if response.status_code == 200 else "OFFLINE"
            await self.update_db(record_id, status)

        except (httpx.RequestError, Exception):
            await self.update_db(record_id, "OFFLINE")

    async def handle_429(self, domain, response, record_id, url, attempt):
        lock = self.domain_locks[domain]
        
        # Only the first task to encounter the 429 clears the lock
        if lock.is_set():
            lock.clear()
            wait_time = min(self.parse_retry_after(response), 60.0)
            await asyncio.sleep(wait_time)
            lock.set()
        else:
            # If lock was already cleared, just wait for it to be set again
            await lock.wait()
        
        # Retry with incremented counter
        await self.check_url(record_id, url, attempt=attempt + 1)

    @sync_to_async
    def update_db(self, record_id, status):
        Record.objects.filter(pk=record_id).update(status=status)

    async def run(self):
        # We fetch records in small chunks to keep memory usage near zero
        queryset = Record.objects.all().values_list('id', 'resource_url').iterator(chunk_size=1000)
        
        next_time = time.monotonic()
        tasks = set()

        # Wrap the synchronous generator to use in async loop
        def get_next_record():
            try:
                return next(queryset)
            except StopIteration:
                return None

        while True:
            record = await sync_to_async(get_next_record)()
            if record is None:
                break
            
            record_id, url = record

            # Rate Limiting: Spacing out task creation
            now = time.monotonic()
            delay = next_time - now
            if delay > 0:
                await asyncio.sleep(delay)

            task = asyncio.create_task(self.check_url(record_id, url))
            tasks.add(task)
            task.add_done_callback(tasks.discard)

            next_time += self.interval

        # Final cleanup
        if tasks:
            await asyncio.gather(*tasks)
        await self.client.aclose()
