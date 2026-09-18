import json
from unittest.mock import patch

from django.test import Client, TestCase

from .agent_services import AgentProviderError, OpenAICompatibleProvider, get_agent_provider
from .models import IntruderAttack, TrafficRecord, TrafficSession


class HistoryAndSettingsTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_history_returns_saved_records(self):
        record = TrafficRecord.objects.create(
            method="GET",
            url="http://localhost:3000",
            request_headers={"Accept": "application/json"},
            request_body="",
            response_headers={"Content-Type": "application/json"},
            response_body='{"ok":true}',
            status_code=200,
            latency_ms=12,
        )
        response = self.client.get("/api/history")
        self.assertEqual(response.status_code, 200)
        item = response.json()["items"][0]
        self.assertEqual(item["id"], record.id)
        self.assertEqual(item["request_headers"]["Accept"], "application/json")
        self.assertEqual(item["response_body"], '{"ok":true}')
        self.assertEqual(item["time"], 12)

    def test_history_can_be_cleared(self):
        TrafficRecord.objects.create(method="GET", url="http://example.test/one")
        TrafficRecord.objects.create(method="POST", url="http://example.test/two")
        TrafficRecord.objects.create(source="proxy", method="GET", url="http://example.test/traffic")

        response = self.client.post(
            "/api/history/bulk",
            data={"action": "clear"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["deleted"], 2)
        self.assertFalse(TrafficRecord.objects.filter(source__in=("repeater", "intruder")).exists())
        self.assertTrue(TrafficRecord.objects.filter(source="proxy").exists())

    def test_traffic_can_be_refreshed_without_csrf_cookie(self):
        response = self.client.delete("/api/traffic")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"ok": True})

    def test_history_excludes_proxy_records(self):
        TrafficRecord.objects.create(source="proxy", method="GET", url="http://example.test/traffic")
        TrafficRecord.objects.create(source="repeater", method="GET", url="http://example.test/repeater")
        response = self.client.get("/api/history")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["source"] for item in response.json()["items"]], ["repeater"])

    def test_proxy_traffic_can_be_saved_to_history(self):
        response = self.client.post(
            "/api/traffic/save",
            data={
                "id": 7,
                "session": 3,
                "method": "GET",
                "host": "localhost:3000",
                "url": "http://localhost:3000/health",
                "request_headers": {},
                "request_body": "",
                "status": 200,
                "response_headers": {},
                "response_body": "ok",
                "response_size": 2,
                "latency_ms": 1,
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        record = TrafficRecord.objects.get(source="proxy")
        self.assertEqual(record.host, "localhost:3000")

    @patch("lab.views.call_engine_get")
    def test_proxy_snapshot_is_persisted_to_history(self, call_engine_get):
        call_engine_get.return_value = (200, [{
            "id": 21,
            "session": 4,
            "timestamp": "2026-09-12T22:00:00Z",
            "method": "GET",
            "url": "http://target.test/health",
            "host": "target.test",
            "request_headers": {"Accept": "*/*"},
            "request_body": "",
            "status": 204,
            "response_headers": {"X-Test": "ok"},
            "response_body": "",
            "response_size": 0,
            "latency_ms": 7,
        }])

        first = self.client.get("/api/traffic")
        second = self.client.get("/api/traffic")

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(TrafficRecord.objects.filter(source="proxy").count(), 1)
        record = TrafficRecord.objects.get(source="proxy")
        self.assertEqual(record.request_headers["Accept"], "*/*")
        self.assertEqual(record.response_headers["X-Test"], "ok")


class AgentChatTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_legacy_agent_runtime_routes_are_removed(self):
        for path in ("/api/agent/context", "/api/agent/plan", "/api/agent/runs"):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 404, path)

    def test_agent_chat_requires_csrf_for_browser_requests(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post(
            "/api/agent/chat",
            data={"messages": [{"role": "user", "content": "hello"}]},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    @patch("lab.views.generate_agent_chat")
    def test_agent_chat_returns_provider_message_only(self, generate_chat):
        generate_chat.return_value = {"message": "evidence analyzed"}
        response = self.client.post(
            "/api/agent/chat",
            data={
                "provider": "ollama",
                "messages": [{"role": "user", "content": "Inspect the target"}],
                "context": {"attached_evidence": {"history": [{"url": "http://target.test/"}]}},
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"provider": "ollama", "message": "evidence analyzed"})
        self.assertEqual(
            generate_chat.call_args.kwargs["context"]["attached_evidence"]["history"][0]["url"],
            "http://target.test/",
        )

    def test_legacy_agent_tools_route_is_removed(self):
        response = self.client.get("/api/agent/tools")
        self.assertEqual(response.status_code, 404)

    @patch("lab.views.generate_agent_chat")
    def test_agent_chat_rejects_execution_payload(self, generate_chat):
        response = self.client.post(
            "/api/agent/chat",
            data={
                "messages": [{"role": "user", "content": "run it"}],
                "approved_tool_call": {"tool": "run_repeater", "arguments": {}},
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        generate_chat.assert_not_called()

    @patch("lab.views.generate_agent_chat")
    def test_agent_chat_drops_unattached_context(self, generate_chat):
        generate_chat.return_value = {"message": "chat only"}
        response = self.client.post(
            "/api/agent/chat",
            data={
                "messages": [{"role": "user", "content": "hello"}],
                "context": {"history": [{"url": "http://should-not-be-forwarded"}]},
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(generate_chat.call_args.kwargs["context"], {})

    @patch("lab.views.generate_agent_chat")
    def test_agent_chat_bounds_attached_context_and_messages(self, generate_chat):
        generate_chat.return_value = {"message": "bounded"}
        huge = "x" * 4000
        context = {"attached_evidence": {"history": [{"response_body": huge} for _ in range(30)]}}
        messages = [{"role": "user", "content": huge} for _ in range(40)]
        response = self.client.post(
            "/api/agent/chat",
            data={"messages": messages, "context": context, "provider": "ollama"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        sent_messages, = generate_chat.call_args.args
        sent_context = generate_chat.call_args.kwargs["context"]
        self.assertLessEqual(len(sent_messages), 24)
        self.assertLessEqual(len(sent_messages[-1]["content"]), 12000)
        self.assertLessEqual(len(json.dumps(sent_context, ensure_ascii=False)), 120000)

    def test_history_filters_binary_metadata_and_annotations(self):
        record = TrafficRecord.objects.create(
            method="GET",
            url="http://binary.test/image",
            host="binary.test",
            response_headers={"Content-Type": "image/png"},
            response_body_encoding="base64",
            response_body_base64="iVBORwD/",
            response_content_type="image/png",
            response_size=6,
            tags=["binary"],
            notes="fixture",
        )
        response = self.client.get("/api/history?mime=image/png&size_min=6&q=fixture")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["items"][0]["id"], record.id)
        annotated = self.client.patch(
            f"/api/history/{record.id}",
            data={"tags": ["image", "qa"], "notes": "updated"},
            content_type="application/json",
        )
        self.assertEqual(annotated.status_code, 200)
        self.assertEqual(annotated.json()["response_body_encoding"], "base64")
        self.assertEqual(annotated.json()["tags"], ["image", "qa"])

    def test_traffic_session_keeps_complete_exchanges_together(self):
        items = [
            {
                "id": 1,
                "method": "GET",
                "url": "http://example.test/a",
                "request_headers": {"X-Test": "one"},
                "request_body": "full request",
                "status": 200,
                "response_headers": {"Content-Type": "application/json"},
                "response_body": '{"complete":true,"value":"full"}',
                "response_size": 31,
            },
            {
                "id": 2,
                "method": "POST",
                "url": "http://example.test/b",
                "request_headers": {},
                "request_body": "payload",
                "status": 201,
                "response_headers": {},
                "response_body": "created",
            },
        ]
        saved = self.client.post(
            "/api/traffic/sessions",
            data={"name": "QA capture", "items": items},
            content_type="application/json",
        )
        self.assertEqual(saved.status_code, 201)
        session = TrafficSession.objects.get(id=saved.json()["id"])
        self.assertEqual(session.name, "QA capture")
        self.assertEqual(session.items, items)

        loaded = self.client.get(f"/api/traffic/sessions/{session.id}")
        self.assertEqual(loaded.status_code, 200)
        self.assertEqual(loaded.json()["items"], items)

    def test_history_can_be_exported_and_imported(self):
        TrafficRecord.objects.create(method="POST", url="http://example.test/api", request_body="{}")
        response = self.client.get("/api/history/export")
        self.assertEqual(response.status_code, 200)
        self.assertIn("intruder-history.json", response["Content-Disposition"])
        imported = self.client.post(
            "/api/history/import",
            data=response.content,
            content_type="application/json",
        )
        self.assertEqual(imported.status_code, 201)
        self.assertEqual(imported.json()["imported"], 1)

    @patch("lab.views.call_engine")
    def test_intruder_start_accepts_empty_result_snapshot(self, call_engine):
        call_engine.return_value = (
            202,
            {
                "attack_id": 7,
                "status": "running",
                "total": 2,
                "completed": 0,
                "failed": 0,
                "results": [],
            },
        )
        response = self.client.post(
            "/api/intruder",
            data={
                "base_request": {
                    "method": "GET",
                    "url": "http://example.test/?id=§id§",
                    "headers": {},
                    "body": "",
                },
                "mode": "batteringRam",
                "payloads": [["one", "two"]],
                "transformations": [],
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.json()["results"], [])

    @patch("lab.views.call_engine_delete")
    @patch("lab.views.call_engine_get")
    def test_intruder_status_and_cancel_forward_attack_id(self, call_engine_get, call_engine_delete):
        call_engine_get.return_value = (200, {"attack_id": 7, "status": "running", "results": []})
        call_engine_delete.return_value = (202, {"attack_id": 7, "status": "cancelled", "results": []})

        status = self.client.get("/api/intruder?attack_id=7")
        incremental = self.client.get("/api/intruder?attack_id=7&since=3")
        cancelled = self.client.delete("/api/intruder?attack_id=7")

        self.assertEqual(status.status_code, 200)
        self.assertEqual(incremental.status_code, 200)
        self.assertEqual(cancelled.status_code, 202)
        self.assertEqual(
            call_engine_get.call_args_list,
            [
                (( "/proxy/intruder/7",),),
                (( "/proxy/intruder/7?since=3",),),
            ],
        )
        call_engine_delete.assert_called_once_with("/proxy/intruder/7")

    @patch("lab.views.call_engine_action")
    def test_intruder_pause_and_resume_forward_action(self, call_engine_action):
        call_engine_action.return_value = (202, {"attack_id": 7, "status": "paused", "results": []})
        response = self.client.post("/api/intruder?attack_id=7&action=pause", data={"action": "pause"}, content_type="application/json")
        self.assertEqual(response.status_code, 202)
        call_engine_action.assert_called_once_with("/proxy/intruder/7", {"action": "pause"})

    @patch("lab.views.call_engine_get")
    def test_completed_intruder_results_are_saved_to_history_once(self, call_engine_get):
        result = {
            "attack_id": 8,
            "status": "completed",
            "results": [{
                "status": 201,
                "headers": {"Content-Type": "application/json"},
                "body": '{"created":true}',
                "time": 14,
                "size": 16,
                "payloads": ["alpha"],
                "request": {
                    "method": "POST",
                    "url": "http://target.test/api/items",
                    "headers": {"Content-Type": "application/json"},
                    "body": '{"name":"alpha"}',
                },
            }],
        }
        call_engine_get.return_value = (200, result)

        first = self.client.get("/api/intruder?attack_id=8")
        second = self.client.get("/api/intruder?attack_id=8")

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(TrafficRecord.objects.filter(source="intruder").count(), 1)
        record = TrafficRecord.objects.get(source="intruder")
        self.assertEqual(record.status_code, 201)
        self.assertEqual(record.request_body, '{"name":"alpha"}')
        self.assertEqual(record.response_body, '{"created":true}')

    @patch("lab.views.call_engine_get")
    def test_running_intruder_results_are_saved_to_history_live(self, call_engine_get):
        call_engine_get.return_value = (200, {
            "attack_id": 9,
            "status": "running",
            "result_offset": 4,
            "results": [{
                "status": 403,
                "headers": {"Content-Type": "text/plain"},
                "body": "blocked",
                "time": 8,
                "size": 7,
                "request": {
                    "method": "GET",
                    "url": "http://target.test/blocked",
                    "headers": {},
                    "body": "",
                },
            }],
        })

        response = self.client.get("/api/intruder?attack_id=9")

        self.assertEqual(response.status_code, 200)
        record = TrafficRecord.objects.get(source="intruder")
        self.assertEqual(record.proxy_event_id, 4)
        self.assertEqual(record.status_code, 403)
        self.assertEqual(record.response_body, "blocked")

    def test_intruder_attack_can_be_saved_and_listed(self):
        payload = {
            "name": "README IDs",
            "mode": "batteringRam",
            "base_request": {"method": "GET", "url": "http://example.test/?id=§id§", "headers": {}, "body": ""},
            "payloads": [["one", "two"]],
            "transformations": [],
        }
        created = self.client.post("/api/intruder/saved", data=payload, content_type="application/json")
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.json()["name"], "README IDs")
        self.assertEqual(IntruderAttack.objects.count(), 1)

        listed = self.client.get("/api/intruder/saved")
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(listed.json()["items"][0]["mode"], "batteringRam")

    @patch("lab.views.call_engine")
    def test_saved_intruder_attack_can_be_re_run(self, call_engine):
        attack = IntruderAttack.objects.create(
            name="Repeat me",
            attack_type="batteringRam",
            base_request={"method": "GET", "url": "http://example.test/?id=§id§", "headers": {}, "body": ""},
            payloads=[["one"]],
            transformations=[],
        )
        call_engine.return_value = (202, {"attack_id": 12, "status": "running", "results": []})

        response = self.client.post(f"/api/intruder/saved/{attack.id}/run")

        self.assertEqual(response.status_code, 202)
        call_engine.assert_called_once_with(
            "/proxy/intruder",
            {
                "base_request": attack.base_request,
                "mode": "batteringRam",
                "payloads": attack.payloads,
                "transformations": [],
                "delay_ms": attack.delay_ms,
                "concurrency": attack.concurrency,
            },
        )
        attack.refresh_from_db()
        self.assertEqual(attack.status, "running")


class AgentProviderTests(TestCase):
    def test_remote_provider_requires_secure_non_loopback_endpoint(self):
        with self.assertRaises(AgentProviderError):
            get_agent_provider(
                "openai_compatible",
                endpoint="http://collector.test/v1/chat/completions",
                model="test",
            )
        with self.assertRaises(AgentProviderError):
            get_agent_provider(
                "openai_compatible",
                endpoint="https://127.0.0.1/v1/chat/completions",
                model="test",
            )

    def test_openrouter_defaults_to_configured_deepseek_free_model(self):
        from .agent_services import PROVIDER_PRESETS

        self.assertEqual(
            PROVIDER_PRESETS["openrouter"][2],
            "deepseek/deepseek-v4-flash-0731:free",
        )

    @patch("lab.agent_services.urlopen")
    def test_chat_accepts_fenced_json_with_reasoning_prefix(self, urlopen):
        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                content = (
                    "I will inspect the evidence first.\n"
                    "```json\n"
                    '{"message":"I need to inspect History."}\n'
                    "```"
                )
                return json.dumps({"choices": [{"message": {"content": content}}]}).encode()

        urlopen.return_value = FakeResponse()
        provider = OpenAICompatibleProvider(
            endpoint="https://llm.test/v1/chat/completions",
            model="deepseek/deepseek-v4-flash-0731:free",
            api_key="secret-token",
        )
        self.assertEqual(
            provider.chat([{"role": "user", "content": "Inspect History"}]),
            {"message": "I need to inspect History."},
        )

    @patch("lab.agent_services.urlopen")
    def test_chat_accepts_plain_text_provider_response(self, urlopen):
        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return json.dumps({"choices": [{"message": {"content": "Plain answer"}}]}).encode()

        urlopen.return_value = FakeResponse()
        provider = OpenAICompatibleProvider(
            endpoint="https://llm.test/v1/chat/completions",
            model="local-model",
        )
        self.assertEqual(
            provider.chat([{"role": "user", "content": "Inspect evidence"}]),
            {"message": "Plain answer"},
        )

    @patch("lab.agent_services.urlopen")
    def test_openai_compatible_provider_sends_api_key_in_header_only(self, urlopen):
        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return json.dumps({"choices": [{"message": {"content": "ok"}}]}).encode()

        urlopen.return_value = FakeResponse()
        provider = OpenAICompatibleProvider(
            endpoint="https://llm.test/v1/chat/completions",
            model="local-model",
            api_key="secret-token",
        )
        provider.chat([{"role": "user", "content": "Inspect evidence"}])
        request = urlopen.call_args.args[0]
        self.assertEqual(request.headers["Authorization"], "Bearer secret-token")
        self.assertNotIn("secret-token", request.data.decode())

    @patch("lab.agent_services.urlopen")
    def test_chat_prompt_preserves_user_pentest_prompt(self, urlopen):
        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return json.dumps({"choices": [{"message": {"content": "ok"}}]}).encode()

        urlopen.return_value = FakeResponse()
        provider = OpenAICompatibleProvider(
            endpoint="https://llm.test/v1/chat/completions",
            model="local-model",
        )
        provider.chat([{"role": "user", "content": "Analyze attached response"}])
        request_body = json.loads(urlopen.call_args.args[0].data)
        self.assertIn("специализирующийся на Burp Suite Professional/Community", request_body["messages"][0]["content"])
        self.assertIn("Prioritized Test Plan", request_body["messages"][0]["content"])
        self.assertIn("Proxy и HTTP history", request_body["messages"][0]["content"])
