import asyncio
import httpx
import random
from datetime import datetime
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse
from asgiref.sync import sync_to_async
from django.conf import settings

import redis.asyncio as aioredis

from api.models import Record

BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)

_DEFINITIVE_HEAD_CODES = frozenset({200, 401, 403, 404, 410, 429})
_TRANSIENT = (httpx.TimeoutException, httpx.ConnectError, httpx.RemoteProtocolError)
_429_KEY_PREFIX = "url_checker:429:"


def _map_status(code: int) -> str:
    if 200 <= code < 300:
        return "ONLINE"
    if code in (404, 410):
        return "OFFLINE"
    if code in (401, 403):
        return "RESTRICTED"
    return "ERROR"


class _PendingCounter:
    """
    Counts all in-flight work: active tasks AND items waiting in the retry queue.
    join() blocks until everything reaches zero.

    Incrementing when an item enters the retry queue and decrementing when the
    consumer picks it up (then immediately re-incrementing for the spawned task)
    means the counter is never zero while work is still reachable.
    """

    def __init__(self):
        self._n = 0
        self._zero = asyncio.Event()
        self._zero.set()

    def inc(self):
        self._n += 1
        self._zero.clear()

    def dec(self):
        self._n -= 1
        if self._n == 0:
            self._zero.set()

    async def join(self):
        # Loop guards against spurious wakeups when a dec/inc pair straddles
        # the event firing (both are sync so no await sits between them, but the
        # scheduled callback may arrive before the re-inc clears the event).
        while self._n > 0:
            await self._zero.wait()


class RateLimitedChecker:
    """
    Checks resource URLs with per-host concurrency control and Redis-backed
    429 backoff so that different Celery workers (or retry waves) share state.

    Architecture
    ────────────
    run() iterates the DB and dispatches one _check_one task at a time per
    host, up to max_concurrent distinct hosts in flight simultaneously.

    When a host returns 429:
      • A Redis key  url_checker:429:<host>  is set with TTL = Retry-After.
      • The URL is pushed onto an asyncio retry queue.
      • A background _retry_consumer task watches the queue and re-spawns
        _check_one tasks; those tasks spin-wait on the Redis key (polling
        every 5-10 s with jitter) before touching the network again.

    Per-host concurrency is enforced by a Semaphore(1) stored in host_pool,
    so at most one HTTP request is in flight per distinct hostname at any time.
    """

    def __init__(self, rps: int = 10, max_retries: int = 3, max_concurrent: int = 50):
        # rps is kept for API compatibility; rate control is now per-host/Redis.
        self.rps = rps
        self.max_retries = max_retries
        # max_concurrent doubles as the cap on distinct hosts in the pool.
        self.max_host_pool = 100
        self.max_concurrent = rps
        self.client = httpx.AsyncClient(
            timeout=10.0,
            headers={"User-Agent": BROWSER_USER_AGENT},
            #limits=httpx.Limits(
            #    max_connections=max_concurrent,
            #    max_keepalive_connections=max_concurrent // 2,
            #),
        )

    # ------------------------------------------------------------------ helpers

    def _parse_retry_after(self, response) -> float:
        val = response.headers.get("Retry-After")
        if not val:
            return 5.0
        try:
            return float(val)
        except ValueError:
            try:
                dt = parsedate_to_datetime(val)
                return max((dt - datetime.now(dt.tzinfo)).total_seconds(), 1.0)
            except Exception:
                return 5.0

    async def _wait_for_host_backoff(self, redis: aioredis.Redis, hostname: str) -> None:
        """
        Spin until the 429 Redis key for this host has expired.
        Each iteration sleeps for max(remaining_ttl, rand(5-10)) seconds so
        that even a very short TTL gets at least a 5-10 s cooldown window,
        and jitter spreads tasks that wake at the same time.
        """
        key = f"{_429_KEY_PREFIX}{hostname}"
        while True:
            ttl = await redis.ttl(key)
            if ttl < 0:   # -2 key gone, -1 no expiry (shouldn't happen)
                return
            wait = max(ttl, random.uniform(5, 10))
            await asyncio.sleep(wait)

    def _spawn(
        self,
        record_id: int,
        url: str,
        hostname: str,
        semaphore: asyncio.Semaphore,
        retry_queue: asyncio.Queue,
        redis: aioredis.Redis,
        attempt: int,
        host_active: dict,
        pending: _PendingCounter,
    ) -> asyncio.Task:
        """Create a _check_one task and wire the shared tracking callbacks."""
        pending.inc()
        host_active[hostname] = host_active.get(hostname, 0) + 1
        task = asyncio.create_task(
            self._check_one(
                record_id, url, hostname,
                semaphore, retry_queue, redis, attempt, pending,
            )
        )

        def _done(t, hn=hostname):
            host_active[hn] -= 1
            if host_active[hn] == 0:
                del host_active[hn]
            pending.dec()

        task.add_done_callback(_done)
        return task

    # ---------------------------------------------------------------- core task

    async def _check_one(
        self,
        record_id: int,
        url: str,
        hostname: str,
        semaphore: asyncio.Semaphore,
        retry_queue: asyncio.Queue,
        redis: aioredis.Redis,
        attempt: int,
        pending: _PendingCounter,
    ) -> None:
        """Single URL check. On 429: sets Redis backoff key and enqueues retry."""
        # Block until any active 429 backoff for this host has expired.
        await self._wait_for_host_backoff(redis, hostname)

        async with semaphore:
            try:
                response = await self.client.head(url, follow_redirects=True)

                if response.status_code not in _DEFINITIVE_HEAD_CODES:
                    async with self.client.stream("GET", url, follow_redirects=True) as resp:
                        response = resp

                if response.status_code == 429:
                    ttl = max(1, int(min(self._parse_retry_after(response), 60)))
                    key = f"{_429_KEY_PREFIX}{hostname}"
                    await redis.set(key, "1", ex=ttl)
                    if attempt < self.max_retries:
                        pending.inc()
                        await retry_queue.put((record_id, url, hostname, attempt + 1, 0))
                    else:
                        await self.update_db(record_id, "ERROR")
                    return

                await self.update_db(record_id, _map_status(response.status_code))

            except _TRANSIENT:
                if attempt < self.max_retries:
                    delay = min(2 ** attempt, 30)
                    pending.inc()
                    await retry_queue.put((record_id, url, hostname, attempt + 1, delay))
                else:
                    await self.update_db(record_id, "ERROR")
            except Exception:
                await self.update_db(record_id, "ERROR")

    # --------------------------------------------------------- retry consumer

    async def _retry_consumer(
        self,
        retry_queue: asyncio.Queue,
        host_pool: dict,
        host_active: dict,
        redis: aioredis.Redis,
        pending: _PendingCounter,
    ) -> None:
        """
        Consume the retry queue until a None sentinel is received.

        Each item is (record_id, url, hostname, attempt, delay_seconds).
        delay_seconds > 0 only for transient-error retries; 429 retries use
        the Redis key to gate themselves inside _check_one.
        """
        while True:
            item = await retry_queue.get()
            if item is None:
                retry_queue.task_done()
                break

            record_id, url, hostname, attempt, delay = item

            if delay > 0:
                await asyncio.sleep(delay)

            if hostname not in host_pool:
                host_pool[hostname] = asyncio.Semaphore(self.max_concurrent)

            # Replace the queued-item count with an active-task count atomically
            # (no await between dec and the inc inside _spawn).
            pending.dec()
            self._spawn(
                record_id, url, hostname,
                host_pool[hostname], retry_queue, redis, attempt,
                host_active, pending,
            )
            retry_queue.task_done()

    # -------------------------------------------------------------------- run

    async def run(self) -> None:
        # db=1 keeps our keys out of Celery's db=0 namespace.
        redis = aioredis.from_url(settings.CELERY_BROKER_URL, db=1)

        retry_queue: asyncio.Queue = asyncio.Queue()
        host_pool: dict[str, asyncio.Semaphore] = {}  # hostname → Semaphore(1)
        host_active: dict[str, int] = {}              # hostname → active task count
        pending = _PendingCounter()

        retry_task = asyncio.create_task(
            self._retry_consumer(retry_queue, host_pool, host_active, redis, pending)
        )

        queryset = (
            Record.objects
            .filter(enabled=True)
            .values_list("id", "resource_url")
            .iterator(chunk_size=1000)
        )

        def _get_next():
            try:
                return next(queryset)
            except StopIteration:
                return None

        while True:
            record = await sync_to_async(_get_next)()
            if record is None:
                break

            record_id, url = record
            hostname = urlparse(url).hostname or url

            # Pause if the host pool is full and this is a new host.
            while hostname not in host_active and len(host_active) >= self.max_host_pool:
                await asyncio.sleep(0.5)

            # Pause if this host already has an in-flight task from the initial
            # dispatch — retry tasks bypass this gate and use the semaphore instead.
            while host_active.get(hostname, 0) >= 100:
                await asyncio.sleep(0.2)

            if hostname not in host_pool:
                host_pool[hostname] = asyncio.Semaphore(self.max_concurrent)

            self._spawn(
                record_id, url, hostname,
                host_pool[hostname], retry_queue, redis, attempt=0,
                host_active=host_active, pending=pending,
            )

        # Wait for all tasks (initial + all retries) to complete.
        await pending.join()

        # Signal the retry consumer to shut down.
        await retry_queue.put(None)
        await retry_task

        await self.client.aclose()
        await redis.close()

    # ------------------------------------------------------------------ DB

    @sync_to_async
    def update_db(self, record_id: int, status: str) -> None:
        Record.objects.filter(pk=record_id).update(status=status)
