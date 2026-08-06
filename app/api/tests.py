"""
CultURIze-web backend test suite.

Run:  python manage.py test api
"""
import asyncio
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
from django.test import Client, TestCase, override_settings

from api.models import Export, Record, RequestLog, URLCheck
from api.serializers import RecordSerializer
from api.url_checker import RateLimitedChecker, _PendingCounter, _map_status

TEST_KEY = "test-access-key"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_record(**kwargs):
    defaults = dict(
        resource_url="https://example.com/resource",
        persistent_url="testserver/default",
        enabled=True,
    )
    defaults.update(kwargs)
    return Record.objects.create(**defaults)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class RecordModelTests(TestCase):
    def test_default_status_is_not_tested(self):
        r = make_record(persistent_url="testserver/r1")
        self.assertEqual(r.status, "NOT_TESTED")

    def test_default_enabled_is_true(self):
        r = make_record(persistent_url="testserver/r2")
        self.assertTrue(r.enabled)

    def test_persistent_url_must_be_unique(self):
        from django.db import IntegrityError
        make_record(persistent_url="testserver/dup")
        with self.assertRaises(IntegrityError):
            make_record(persistent_url="testserver/dup")

    def test_all_status_choices_are_accepted(self):
        for status in ("NOT_TESTED", "ONLINE", "OFFLINE", "RESTRICTED", "ERROR"):
            r = make_record(persistent_url=f"testserver/{status}", status=status)
            self.assertEqual(r.status, status)

    def test_request_log_cascade_delete(self):
        r = make_record(persistent_url="testserver/cascade")
        RequestLog.objects.create(record=r)
        self.assertEqual(RequestLog.objects.count(), 1)
        r.delete()
        self.assertEqual(RequestLog.objects.count(), 0)

    def test_str_contains_both_urls(self):
        r = make_record(persistent_url="testserver/abc", resource_url="https://dest.example.com")
        self.assertIn("testserver/abc", str(r))
        self.assertIn("dest.example.com", str(r))


class ExportModelTests(TestCase):
    def test_last_returns_most_recent(self):
        Export.objects.create(export_type="R", filename="first.zip")
        Export.objects.create(export_type="R", filename="second.zip")
        self.assertEqual(Export.objects.filter(export_type="R").last().filename, "second.zip")

    def test_log_and_record_exports_are_independent(self):
        Export.objects.create(export_type="R", filename="records.zip")
        Export.objects.create(export_type="L", filename="logs.zip")
        self.assertEqual(Export.objects.filter(export_type="R").count(), 1)
        self.assertEqual(Export.objects.filter(export_type="L").count(), 1)


# ---------------------------------------------------------------------------
# Serializers
# ---------------------------------------------------------------------------

class RecordSerializerTests(TestCase):
    def test_create_valid_record(self):
        s = RecordSerializer(data={"resource_url": "https://new.example.com", "persistent_url": "testserver/new"})
        self.assertTrue(s.is_valid(), s.errors)
        record = s.save()
        self.assertEqual(record.persistent_url, "testserver/new")

    def test_duplicate_persistent_url_updates_existing(self):
        """POST with an existing persistent_url must upsert, not error."""
        make_record(persistent_url="testserver/dup", resource_url="https://old.example.com")
        s = RecordSerializer(data={"resource_url": "https://new.example.com", "persistent_url": "testserver/dup"})
        self.assertTrue(s.is_valid())
        s.save()
        self.assertEqual(Record.objects.filter(persistent_url="testserver/dup").count(), 1)
        self.assertEqual(Record.objects.get(persistent_url="testserver/dup").resource_url, "https://new.example.com")

    def test_update_does_not_change_persistent_url(self):
        record = make_record(persistent_url="testserver/immutable")
        s = RecordSerializer(record, data={"resource_url": "https://updated.example.com", "persistent_url": "testserver/ignored"})
        self.assertTrue(s.is_valid())
        s.save()
        record.refresh_from_db()
        self.assertEqual(record.persistent_url, "testserver/immutable")

    def test_invalid_resource_url_is_rejected(self):
        s = RecordSerializer(data={"resource_url": "not-a-url", "persistent_url": "testserver/bad"})
        self.assertFalse(s.is_valid())
        self.assertIn("resource_url", s.errors)

    def test_missing_persistent_url_is_rejected(self):
        s = RecordSerializer(data={"resource_url": "https://example.com"})
        self.assertFalse(s.is_valid())
        self.assertIn("persistent_url", s.errors)

    def test_status_field_is_read_only(self):
        """Client-supplied status must be silently ignored."""
        s = RecordSerializer(data={"resource_url": "https://example.com", "persistent_url": "testserver/ro", "status": "OFFLINE"})
        self.assertTrue(s.is_valid())
        record = s.save()
        self.assertEqual(record.status, "NOT_TESTED")

    def test_batch_create(self):
        data = [
            {"resource_url": "https://a.example.com", "persistent_url": "testserver/a"},
            {"resource_url": "https://b.example.com", "persistent_url": "testserver/b"},
        ]
        s = RecordSerializer(data=data, many=True)
        self.assertTrue(s.is_valid())
        records = s.save()
        self.assertEqual(len(records), 2)

    def test_enabled_defaults_to_true_when_omitted(self):
        s = RecordSerializer(data={"resource_url": "https://example.com", "persistent_url": "testserver/en"})
        self.assertTrue(s.is_valid())
        record = s.save()
        self.assertTrue(record.enabled)


# ---------------------------------------------------------------------------
# Views — auth
# ---------------------------------------------------------------------------

@patch("api.views.access_key", TEST_KEY)
class AuthTests(TestCase):
    def setUp(self):
        self.c = Client()

    def test_missing_key_returns_401(self):
        self.assertEqual(self.c.get("/api/info").status_code, 401)

    def test_wrong_key_returns_401(self):
        self.assertEqual(self.c.get("/api/info", HTTP_CULTURIZE_KEY="wrong").status_code, 401)

    def test_correct_key_accepted(self):
        self.assertEqual(self.c.get("/api/info", HTTP_CULTURIZE_KEY=TEST_KEY).status_code, 200)

    def test_login_valid_key(self):
        resp = self.c.post("/api/login", content_type="application/json", HTTP_CULTURIZE_KEY=TEST_KEY)
        self.assertEqual(resp.status_code, 200)

    def test_login_invalid_key(self):
        resp = self.c.post("/api/login", content_type="application/json", HTTP_CULTURIZE_KEY="bad")
        self.assertEqual(resp.status_code, 401)


# ---------------------------------------------------------------------------
# Views — /api/info
# ---------------------------------------------------------------------------

@patch("api.views.access_key", TEST_KEY)
class ServiceInfoTests(TestCase):
    H = {"HTTP_CULTURIZE_KEY": TEST_KEY}

    def test_record_and_enabled_counts(self):
        make_record(persistent_url="testserver/r1")
        make_record(persistent_url="testserver/r2", enabled=False)
        data = self.client.get("/api/info", **self.H).json()
        self.assertEqual(data["record_count"], 2)
        self.assertEqual(data["enabled_count"], 1)

    def test_click_count(self):
        r = make_record(persistent_url="testserver/r3")
        RequestLog.objects.create(record=r)
        RequestLog.objects.create(record=r)
        data = self.client.get("/api/info", **self.H).json()
        self.assertEqual(data["click_count"], 2)

    def test_no_exports_returns_empty_strings(self):
        data = self.client.get("/api/info", **self.H).json()
        self.assertEqual(data["last_record_export"], "")
        self.assertEqual(data["last_log_export"], "")

    def test_exports_returned_when_present(self):
        Export.objects.create(export_type="R", filename="records.zip")
        data = self.client.get("/api/info", **self.H).json()
        self.assertEqual(data["last_record_export_filename"], "records.zip")


# ---------------------------------------------------------------------------
# Views — /api/record (list)
# ---------------------------------------------------------------------------

@patch("api.views.access_key", TEST_KEY)
class RecordListTests(TestCase):
    H = {"HTTP_CULTURIZE_KEY": TEST_KEY}

    def test_empty_list(self):
        data = self.client.get("/api/record", **self.H).json()
        self.assertEqual(data["count"], 0)
        self.assertEqual(data["results"], [])

    def test_list_all_records(self):
        make_record(persistent_url="testserver/one")
        make_record(persistent_url="testserver/two")
        data = self.client.get("/api/record", **self.H).json()
        self.assertEqual(data["count"], 2)

    def test_search_filters_by_persistent_url(self):
        make_record(persistent_url="testserver/apple")
        make_record(persistent_url="testserver/orange")
        data = self.client.get("/api/record?search=apple", **self.H).json()
        self.assertEqual(data["count"], 1)
        self.assertEqual(data["results"][0]["persistent_url"], "testserver/apple")

    def test_search_is_case_insensitive(self):
        make_record(persistent_url="testserver/CaseSensitive")
        data = self.client.get("/api/record?search=casesensitive", **self.H).json()
        self.assertEqual(data["count"], 1)

    def test_empty_search_returns_all(self):
        make_record(persistent_url="testserver/x")
        make_record(persistent_url="testserver/y")
        data = self.client.get("/api/record?search=", **self.H).json()
        self.assertEqual(data["count"], 2)

    def test_post_creates_record(self):
        resp = self.client.post(
            "/api/record",
            {"resource_url": "https://example.com", "persistent_url": "testserver/new"},
            content_type="application/json",
            **self.H,
        )
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(Record.objects.filter(persistent_url="testserver/new").exists())

    def test_post_batch_creates_multiple_records(self):
        payload = [
            {"resource_url": "https://a.example.com", "persistent_url": "testserver/a"},
            {"resource_url": "https://b.example.com", "persistent_url": "testserver/b"},
        ]
        resp = self.client.post("/api/record", payload, content_type="application/json", **self.H)
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(Record.objects.count(), 2)

    def test_post_duplicate_upserts(self):
        make_record(persistent_url="testserver/dup", resource_url="https://old.example.com")
        resp = self.client.post(
            "/api/record",
            {"resource_url": "https://new.example.com", "persistent_url": "testserver/dup"},
            content_type="application/json",
            **self.H,
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(Record.objects.count(), 1)
        self.assertEqual(Record.objects.get(persistent_url="testserver/dup").resource_url, "https://new.example.com")

    def test_post_invalid_url_returns_400(self):
        resp = self.client.post(
            "/api/record",
            {"resource_url": "not-a-url", "persistent_url": "testserver/bad"},
            content_type="application/json",
            **self.H,
        )
        self.assertEqual(resp.status_code, 400)

    def test_put_updates_by_persistent_url(self):
        make_record(persistent_url="testserver/upd", resource_url="https://old.example.com")
        resp = self.client.put(
            "/api/record",
            {"resource_url": "https://updated.example.com", "persistent_url": "testserver/upd"},
            content_type="application/json",
            **self.H,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Record.objects.get(persistent_url="testserver/upd").resource_url, "https://updated.example.com")

    def test_put_nonexistent_returns_404(self):
        resp = self.client.put(
            "/api/record",
            {"resource_url": "https://example.com", "persistent_url": "testserver/missing"},
            content_type="application/json",
            **self.H,
        )
        self.assertEqual(resp.status_code, 404)


# ---------------------------------------------------------------------------
# Views — /api/record/<id>
# ---------------------------------------------------------------------------

@patch("api.views.access_key", TEST_KEY)
class RecordDetailTests(TestCase):
    H = {"HTTP_CULTURIZE_KEY": TEST_KEY}

    def test_get_by_id(self):
        r = make_record(persistent_url="testserver/detail")
        resp = self.client.get(f"/api/record/{r.id}", **self.H)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["persistent_url"], "testserver/detail")

    def test_get_nonexistent_returns_404(self):
        self.assertEqual(self.client.get("/api/record/99999", **self.H).status_code, 404)

    def test_put_updates_resource_url(self):
        r = make_record(persistent_url="testserver/put", resource_url="https://old.example.com")
        resp = self.client.put(
            f"/api/record/{r.id}",
            {"resource_url": "https://new.example.com", "persistent_url": r.persistent_url},
            content_type="application/json",
            **self.H,
        )
        self.assertEqual(resp.status_code, 200)
        r.refresh_from_db()
        self.assertEqual(r.resource_url, "https://new.example.com")

    def test_put_can_toggle_enabled(self):
        r = make_record(persistent_url="testserver/toggle", enabled=True)
        self.client.put(
            f"/api/record/{r.id}",
            {"resource_url": r.resource_url, "persistent_url": r.persistent_url, "enabled": False},
            content_type="application/json",
            **self.H,
        )
        r.refresh_from_db()
        self.assertFalse(r.enabled)

    def test_delete_removes_record(self):
        r = make_record(persistent_url="testserver/del")
        self.assertEqual(self.client.delete(f"/api/record/{r.id}", **self.H).status_code, 204)
        self.assertFalse(Record.objects.filter(pk=r.id).exists())

    def test_delete_nonexistent_returns_404(self):
        self.assertEqual(self.client.delete("/api/record/99999", **self.H).status_code, 404)


# ---------------------------------------------------------------------------
# Views — /api/logs
# ---------------------------------------------------------------------------

@patch("api.views.access_key", TEST_KEY)
class LogViewTests(TestCase):
    H = {"HTTP_CULTURIZE_KEY": TEST_KEY}

    def test_list_logs(self):
        r = make_record(persistent_url="testserver/logged")
        RequestLog.objects.create(record=r, referer="https://ref.example.com")
        data = self.client.get("/api/logs", **self.H).json()
        self.assertEqual(data["count"], 1)
        self.assertEqual(data["results"][0]["persistent_url"], "testserver/logged")

    def test_click_count_for_record(self):
        r = make_record(persistent_url="testserver/clicks")
        RequestLog.objects.create(record=r)
        RequestLog.objects.create(record=r)
        data = self.client.get(f"/api/logs/{r.id}", **self.H).json()
        self.assertEqual(data["click_count"], 2)

    def test_click_count_for_unknown_record_is_zero(self):
        data = self.client.get("/api/logs/99999", **self.H).json()
        self.assertEqual(data["click_count"], 0)


# ---------------------------------------------------------------------------
# Views — export / cleanup
# ---------------------------------------------------------------------------

@patch("api.views.access_key", TEST_KEY)
@patch("api.views.export_records")
@patch("api.views.export_logs")
@patch("api.views.cleanup")
class ExportViewTests(TestCase):
    H = {"HTTP_CULTURIZE_KEY": TEST_KEY}

    def test_record_export_returns_202(self, _cleanup, _logs, mock_records):
        self.assertEqual(self.client.get("/api/recordexport", **self.H).status_code, 202)
        mock_records.delay.assert_called_once()

    def test_log_export_returns_202(self, _cleanup, mock_logs, _records):
        self.assertEqual(self.client.get("/api/logexport", **self.H).status_code, 202)
        mock_logs.delay.assert_called_once()

    def test_cleanup_returns_202(self, mock_cleanup, _logs, _records):
        self.assertEqual(self.client.get("/api/cleanup", **self.H).status_code, 202)
        mock_cleanup.delay.assert_called_once()

    def test_export_requires_auth(self, _cleanup, _logs, _records):
        self.assertEqual(self.client.get("/api/recordexport").status_code, 401)


# ---------------------------------------------------------------------------
# Views — redirect
# ---------------------------------------------------------------------------

class RedirectViewTests(TestCase):
    def test_enabled_record_redirects_301(self):
        Record.objects.create(
            persistent_url="testserver/go",
            resource_url="https://dest.example.com",
            enabled=True,
        )
        resp = self.client.get("/go")
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], "https://dest.example.com")

    def test_redirect_creates_request_log(self):
        Record.objects.create(
            persistent_url="testserver/log",
            resource_url="https://dest.example.com",
            enabled=True,
        )
        self.client.get("/log", HTTP_REFERER="https://referrer.example.com")
        log = RequestLog.objects.get(record__persistent_url="testserver/log")
        self.assertEqual(log.referer, "https://referrer.example.com")

    def test_disabled_record_returns_404(self):
        Record.objects.create(
            persistent_url="testserver/off",
            resource_url="https://dest.example.com",
            enabled=False,
        )
        self.assertEqual(self.client.get("/off").status_code, 404)

    def test_disabled_record_does_not_log(self):
        Record.objects.create(
            persistent_url="testserver/nolog",
            resource_url="https://dest.example.com",
            enabled=False,
        )
        self.client.get("/nolog")
        self.assertEqual(RequestLog.objects.count(), 0)

    def test_unknown_path_returns_404(self):
        self.assertEqual(self.client.get("/nonexistent").status_code, 404)

    def test_log_referer_is_none_when_absent(self):
        Record.objects.create(
            persistent_url="testserver/noref",
            resource_url="https://dest.example.com",
            enabled=True,
        )
        self.client.get("/noref")
        log = RequestLog.objects.get(record__persistent_url="testserver/noref")
        self.assertIsNone(log.referer)


# ---------------------------------------------------------------------------
# URL Checker — _map_status
# ---------------------------------------------------------------------------

class MapStatusTests(TestCase):
    def test_200_online(self):
        self.assertEqual(_map_status(200), "ONLINE")

    def test_2xx_range_online(self):
        for code in (201, 204, 206, 299):
            with self.subTest(code=code):
                self.assertEqual(_map_status(code), "ONLINE")

    def test_404_offline(self):
        self.assertEqual(_map_status(404), "OFFLINE")

    def test_410_offline(self):
        self.assertEqual(_map_status(410), "OFFLINE")

    def test_401_restricted(self):
        self.assertEqual(_map_status(401), "RESTRICTED")

    def test_403_restricted(self):
        self.assertEqual(_map_status(403), "RESTRICTED")

    def test_5xx_error(self):
        for code in (500, 502, 503, 504):
            with self.subTest(code=code):
                self.assertEqual(_map_status(code), "ERROR")

    def test_405_error(self):
        self.assertEqual(_map_status(405), "ERROR")

    def test_301_not_followed_is_error(self):
        self.assertEqual(_map_status(301), "ERROR")


# ---------------------------------------------------------------------------
# URL Checker — _parse_retry_after
# ---------------------------------------------------------------------------

class ParseRetryAfterTests(TestCase):
    def setUp(self):
        # Instantiate without running __init__ to avoid creating httpx client.
        self.checker = RateLimitedChecker.__new__(RateLimitedChecker)

    def _resp(self, value):
        r = MagicMock()
        r.headers = {"Retry-After": value} if value is not None else {}
        return r

    def test_numeric_value(self):
        self.assertAlmostEqual(self.checker._parse_retry_after(self._resp("30")), 30.0)

    def test_missing_header_defaults_to_5(self):
        self.assertAlmostEqual(self.checker._parse_retry_after(self._resp(None)), 5.0)

    def test_invalid_string_defaults_to_5(self):
        self.assertAlmostEqual(self.checker._parse_retry_after(self._resp("garbage")), 5.0)

    def test_zero_is_accepted(self):
        self.assertAlmostEqual(self.checker._parse_retry_after(self._resp("0")), 0.0)


# ---------------------------------------------------------------------------
# URL Checker — _PendingCounter
# ---------------------------------------------------------------------------

class PendingCounterTests(IsolatedAsyncioTestCase):
    def test_starts_at_zero_and_is_settled(self):
        p = _PendingCounter()
        self.assertEqual(p._n, 0)
        self.assertTrue(p._zero.is_set())

    def test_inc_clears_zero_event(self):
        p = _PendingCounter()
        p.inc()
        self.assertFalse(p._zero.is_set())

    def test_dec_to_zero_sets_event(self):
        p = _PendingCounter()
        p.inc()
        p.dec()
        self.assertTrue(p._zero.is_set())

    def test_multiple_incs_require_matching_decs(self):
        p = _PendingCounter()
        for _ in range(3):
            p.inc()
        p.dec()
        p.dec()
        self.assertFalse(p._zero.is_set())
        p.dec()
        self.assertTrue(p._zero.is_set())

    async def test_join_returns_immediately_when_empty(self):
        p = _PendingCounter()
        await asyncio.wait_for(p.join(), timeout=0.1)

    async def test_join_blocks_until_dec(self):
        p = _PendingCounter()
        p.inc()

        async def release():
            await asyncio.sleep(0.05)
            p.dec()

        asyncio.create_task(release())
        await asyncio.wait_for(p.join(), timeout=1.0)


# ---------------------------------------------------------------------------
# URL Checker — _check_one
# ---------------------------------------------------------------------------

class CheckOneTests(IsolatedAsyncioTestCase):
    """Tests for _check_one. update_db and the httpx client are always mocked."""

    def _make_checker(self):
        return RateLimitedChecker(rps=1000, max_retries=2, max_concurrent=10)

    def _resp(self, status_code):
        r = MagicMock()
        r.status_code = status_code
        r.headers = {}
        return r

    def _stream_cm(self, status_code):
        cm = MagicMock()
        cm.__aenter__ = AsyncMock(return_value=self._resp(status_code))
        cm.__aexit__ = AsyncMock(return_value=False)
        return cm

    def _setup(self, checker):
        """Return (semaphore, retry_queue, redis_mock, pending) ready for _check_one."""
        semaphore = asyncio.Semaphore(10)
        retry_queue = asyncio.Queue()
        redis = AsyncMock()
        redis.ttl = AsyncMock(return_value=-2)  # no active backoff
        redis.set = AsyncMock()
        pending = _PendingCounter()
        checker.update_db = AsyncMock()
        return semaphore, retry_queue, redis, pending

    async def _run(self, checker, semaphore, retry_queue, redis, attempt, pending,
                   url="https://example.com", record_id=1, hostname="example.com"):
        await checker._check_one(record_id, url, hostname, semaphore, retry_queue, redis, attempt, pending)

    async def test_head_200_marks_online(self):
        c = self._make_checker()
        c.client = AsyncMock()
        c.client.head = AsyncMock(return_value=self._resp(200))
        sem, q, redis, pending = self._setup(c)
        await self._run(c, sem, q, redis, 0, pending)
        c.update_db.assert_called_once_with(1, "ONLINE")

    async def test_head_404_marks_offline(self):
        c = self._make_checker()
        c.client = AsyncMock()
        c.client.head = AsyncMock(return_value=self._resp(404))
        sem, q, redis, pending = self._setup(c)
        await self._run(c, sem, q, redis, 0, pending)
        c.update_db.assert_called_once_with(1, "OFFLINE")

    async def test_head_401_marks_restricted(self):
        c = self._make_checker()
        c.client = AsyncMock()
        c.client.head = AsyncMock(return_value=self._resp(401))
        sem, q, redis, pending = self._setup(c)
        await self._run(c, sem, q, redis, 0, pending)
        c.update_db.assert_called_once_with(1, "RESTRICTED")

    async def test_head_403_marks_restricted(self):
        c = self._make_checker()
        c.client = AsyncMock()
        c.client.head = AsyncMock(return_value=self._resp(403))
        sem, q, redis, pending = self._setup(c)
        await self._run(c, sem, q, redis, 0, pending)
        c.update_db.assert_called_once_with(1, "RESTRICTED")

    async def test_ambiguous_head_falls_back_to_get(self):
        """A 500 from HEAD is ambiguous; the checker must follow up with GET."""
        c = self._make_checker()
        c.client = AsyncMock()
        c.client.head = AsyncMock(return_value=self._resp(500))
        c.client.stream = MagicMock(return_value=self._stream_cm(200))
        sem, q, redis, pending = self._setup(c)
        await self._run(c, sem, q, redis, 0, pending)
        c.client.stream.assert_called_once()
        c.update_db.assert_called_once_with(1, "ONLINE")

    async def test_definitive_head_skips_get(self):
        """A 404 from HEAD is definitive; no GET should be issued."""
        c = self._make_checker()
        c.client = AsyncMock()
        c.client.head = AsyncMock(return_value=self._resp(404))
        c.client.stream = MagicMock()
        sem, q, redis, pending = self._setup(c)
        await self._run(c, sem, q, redis, 0, pending)
        c.client.stream.assert_not_called()

    async def test_transient_error_enqueues_retry(self):
        c = self._make_checker()
        c.client = AsyncMock()
        c.client.head = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
        sem, q, redis, pending = self._setup(c)
        await self._run(c, sem, q, redis, 0, pending)
        self.assertEqual(q.qsize(), 1)
        record_id, url, hostname, attempt, delay = q.get_nowait()
        self.assertEqual(record_id, 1)
        self.assertEqual(attempt, 1)
        self.assertGreater(delay, 0)
        c.update_db.assert_not_called()

    async def test_transient_error_at_max_retries_marks_error(self):
        c = self._make_checker()
        c.client = AsyncMock()
        c.client.head = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
        sem, q, redis, pending = self._setup(c)
        await self._run(c, sem, q, redis, 2, pending)  # attempt == max_retries
        self.assertTrue(q.empty())
        c.update_db.assert_called_once_with(1, "ERROR")

    async def test_connect_error_enqueues_retry(self):
        c = self._make_checker()
        c.client = AsyncMock()
        c.client.head = AsyncMock(side_effect=httpx.ConnectError("refused"))
        sem, q, redis, pending = self._setup(c)
        await self._run(c, sem, q, redis, 0, pending)
        self.assertEqual(q.qsize(), 1)

    async def test_connect_error_at_max_retries_marks_error(self):
        c = self._make_checker()
        c.client = AsyncMock()
        c.client.head = AsyncMock(side_effect=httpx.ConnectError("refused"))
        sem, q, redis, pending = self._setup(c)
        await self._run(c, sem, q, redis, 2, pending)
        self.assertTrue(q.empty())
        c.update_db.assert_called_once_with(1, "ERROR")

    async def test_429_sets_redis_key_and_enqueues_retry(self):
        c = self._make_checker()
        c.client = AsyncMock()
        c.client.head = AsyncMock(return_value=self._resp(429))
        sem, q, redis, pending = self._setup(c)
        await self._run(c, sem, q, redis, 0, pending)
        redis.set.assert_called_once()
        self.assertEqual(q.qsize(), 1)
        record_id, url, hostname, attempt, delay = q.get_nowait()
        self.assertEqual(attempt, 1)
        self.assertEqual(delay, 0)  # 429 retries gate via Redis, not a delay
        c.update_db.assert_not_called()

    async def test_429_at_max_retries_marks_error(self):
        c = RateLimitedChecker(rps=1000, max_retries=0, max_concurrent=10)
        c.client = AsyncMock()
        c.client.head = AsyncMock(return_value=self._resp(429))
        sem, q, redis, pending = self._setup(c)
        await self._run(c, sem, q, redis, 0, pending)
        self.assertTrue(q.empty())
        c.update_db.assert_called_once_with(1, "ERROR")

    async def test_unknown_exception_marks_error(self):
        c = self._make_checker()
        c.client = AsyncMock()
        c.client.head = AsyncMock(side_effect=RuntimeError("unexpected"))
        sem, q, redis, pending = self._setup(c)
        await self._run(c, sem, q, redis, 0, pending)
        c.update_db.assert_called_once_with(1, "ERROR")

    async def test_host_backoff_blocks_until_redis_key_expires(self):
        """_wait_for_host_backoff polls redis.ttl until it returns -2 (key gone)."""
        c = self._make_checker()
        c.client = AsyncMock()
        c.client.head = AsyncMock(return_value=self._resp(200))
        sem, q, redis, pending = self._setup(c)
        redis.ttl = AsyncMock(side_effect=[5, -2])
        with patch("asyncio.sleep", new_callable=AsyncMock):
            await self._run(c, sem, q, redis, 0, pending)
        self.assertEqual(redis.ttl.call_count, 2)

    async def test_semaphore_caps_concurrency(self):
        """Concurrent _check_one calls must not exceed the semaphore cap."""
        cap = 3
        sem = asyncio.Semaphore(cap)
        q = asyncio.Queue()
        redis = AsyncMock()
        redis.ttl = AsyncMock(return_value=-2)
        pending = _PendingCounter()

        c = RateLimitedChecker(rps=cap, max_retries=0, max_concurrent=cap)
        c.update_db = AsyncMock()

        active = 0
        peak = 0

        async def slow_head(*args, **kwargs):
            nonlocal active, peak
            active += 1
            peak = max(peak, active)
            await asyncio.sleep(0.01)
            active -= 1
            r = MagicMock()
            r.status_code = 200
            r.headers = {}
            return r

        c.client = AsyncMock()
        c.client.head = slow_head

        tasks = [
            asyncio.create_task(
                c._check_one(i, "https://example.com", "example.com", sem, q, redis, 0, pending)
            )
            for i in range(10)
        ]
        await asyncio.gather(*tasks)
        self.assertLessEqual(peak, cap)


# ---------------------------------------------------------------------------
# URL Checker — _retry_consumer
# ---------------------------------------------------------------------------

class RetryConsumerTests(IsolatedAsyncioTestCase):
    def _make_checker(self):
        return RateLimitedChecker(rps=10, max_retries=2, max_concurrent=10)

    async def test_none_sentinel_stops_consumer(self):
        c = self._make_checker()
        q = asyncio.Queue()
        await q.put(None)
        pending = _PendingCounter()
        await asyncio.wait_for(
            c._retry_consumer(q, {}, {}, AsyncMock(), pending),
            timeout=1.0,
        )

    async def test_queued_item_is_spawned(self):
        c = self._make_checker()
        spawn_calls = []

        def fake_spawn(*args, **kwargs):
            spawn_calls.append(kwargs or args)

        c._spawn = fake_spawn

        q = asyncio.Queue()
        pending = _PendingCounter()
        pending.inc()  # simulate item having been enqueued
        await q.put((1, "https://example.com", "example.com", 1, 0))
        await q.put(None)

        await c._retry_consumer(q, {}, {}, AsyncMock(), pending)
        self.assertEqual(len(spawn_calls), 1)

    async def test_positive_delay_causes_sleep(self):
        c = self._make_checker()
        c._spawn = MagicMock()

        q = asyncio.Queue()
        pending = _PendingCounter()
        pending.inc()
        await q.put((1, "https://example.com", "example.com", 1, 30))
        await q.put(None)

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await c._retry_consumer(q, {}, {}, AsyncMock(), pending)

        mock_sleep.assert_called_once_with(30)

    async def test_zero_delay_skips_sleep(self):
        c = self._make_checker()
        c._spawn = MagicMock()

        q = asyncio.Queue()
        pending = _PendingCounter()
        pending.inc()
        await q.put((1, "https://example.com", "example.com", 1, 0))
        await q.put(None)

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await c._retry_consumer(q, {}, {}, AsyncMock(), pending)

        mock_sleep.assert_not_called()


# ---------------------------------------------------------------------------
# Tasks — cleanup
# ---------------------------------------------------------------------------

class CleanupTaskTests(TestCase):
    def _make_exports(self, export_type, n):
        return [Export.objects.create(export_type=export_type, filename=f"{export_type}-{i}.zip") for i in range(n)]

    @patch("api.tasks.os.remove")
    def test_keeps_last_3_record_exports(self, mock_rm):
        from api.tasks import cleanup
        self._make_exports("R", 5)
        cleanup()
        self.assertEqual(Export.objects.filter(export_type="R").count(), 3)
        self.assertEqual(mock_rm.call_count, 2)

    @patch("api.tasks.os.remove")
    def test_keeps_last_3_log_exports(self, mock_rm):
        from api.tasks import cleanup
        self._make_exports("L", 5)
        cleanup()
        self.assertEqual(Export.objects.filter(export_type="L").count(), 3)

    @patch("api.tasks.os.remove")
    def test_under_3_exports_nothing_deleted(self, mock_rm):
        from api.tasks import cleanup
        self._make_exports("R", 2)
        cleanup()
        mock_rm.assert_not_called()
        self.assertEqual(Export.objects.filter(export_type="R").count(), 2)

    @patch("api.tasks.os.remove")
    def test_record_and_log_cleanup_are_independent(self, mock_rm):
        from api.tasks import cleanup
        self._make_exports("R", 5)
        self._make_exports("L", 2)
        cleanup()
        self.assertEqual(Export.objects.filter(export_type="R").count(), 3)
        self.assertEqual(Export.objects.filter(export_type="L").count(), 2)

    @patch("api.tasks.os.remove")
    def test_oldest_exports_are_deleted(self, mock_rm):
        from api.tasks import cleanup
        exports = self._make_exports("R", 5)
        cleanup()
        surviving_ids = set(Export.objects.filter(export_type="R").values_list("id", flat=True))
        # The two oldest (index 0 and 1) must be gone
        self.assertNotIn(exports[0].id, surviving_ids)
        self.assertNotIn(exports[1].id, surviving_ids)
        self.assertIn(exports[4].id, surviving_ids)
