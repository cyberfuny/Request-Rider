"""Django gateway views for the browser UI and Go execution engine."""

import json
import logging
import os
import time
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.http import HttpResponse, JsonResponse, StreamingHttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.csrf import ensure_csrf_cookie

from .models import IntruderAttack, TrafficRecord, TrafficSession
from .agent_services import AgentProviderError, generate_agent_chat

# The gateway talks to the engine over HTTP; Docker can override this address.
ENGINE_URL = os.environ.get("ENGINE_URL", "http://127.0.0.1:8081")
# The module logger records lifecycle metadata without request secrets.
logger = logging.getLogger(__name__)


# Django owns the browser-facing API; the Go engine owns outbound HTTP work.
@ensure_csrf_cookie
def index(request):
    """Render the single-page lab interface."""
    return render(request, "lab/index.html")


def history(request):
    """Return filtered and sorted durable History records."""
    # History is persisted in SQLite, unlike the in-memory passive Store.
    records = TrafficRecord.objects.filter(source__in=("repeater", "intruder")).order_by("-timestamp")
    query = request.GET.get("q", "").strip()
    if query:
        from django.db.models import Q
        records = records.filter(
            Q(url__icontains=query) | Q(request_body__icontains=query) |
            Q(response_body__icontains=query) | Q(host__icontains=query) |
            Q(notes__icontains=query) | Q(tags__icontains=query)
        )
    if request.GET.get("host"):
        records = records.filter(host__icontains=request.GET["host"].strip())
    if request.GET.get("path"):
        records = records.filter(url__icontains=request.GET["path"].strip())
    if request.GET.get("method"):
        records = records.filter(method__iexact=request.GET["method"].strip())
    if request.GET.get("status"):
        records = records.filter(status_code=request.GET["status"])
    if request.GET.get("mime"):
        records = records.filter(response_content_type__icontains=request.GET["mime"].strip())
    if request.GET.get("body"):
        records = records.filter(response_body__icontains=request.GET["body"])
    for parameter, field in (("size_min", "response_size__gte"), ("size_max", "response_size__lte"),
                             ("latency_min", "latency_ms__gte"), ("latency_max", "latency_ms__lte")):
        if request.GET.get(parameter):
            try:
                records = records.filter(**{field: int(request.GET[parameter])})
            except ValueError:
                return JsonResponse({"error": f"{parameter} must be numeric"}, status=400)
    sort = request.GET.get("sort", "-timestamp")
    if sort in {
        "timestamp", "-timestamp", "host", "-host", "method", "-method",
        "url", "-url", "status_code", "-status_code", "response_size",
        "-response_size",
    }:
        records = records.order_by(sort)
    # Keep the response bounded for the current table view.
    records = records[:200]
    return JsonResponse({"items": [history_item(item) for item in records]})


@csrf_exempt
def history_detail(request, record_id=None):
    """Delete one History record through the browser-facing API."""
    if request.method == "DELETE":
        TrafficRecord.objects.filter(id=record_id).delete()
        return JsonResponse({"ok": True})
    if request.method in {"PATCH", "PUT"}:
        try:
            payload = json.loads(request.body)
            record = TrafficRecord.objects.get(id=record_id)
            if "tags" in payload:
                if not isinstance(payload["tags"], list):
                    raise ValueError("tags must be a list")
                record.tags = [str(tag)[:80] for tag in payload["tags"]]
            if "notes" in payload:
                record.notes = str(payload["notes"])
            record.save(update_fields=["tags", "notes"])
            return JsonResponse(history_item(record))
        except TrafficRecord.DoesNotExist:
            return JsonResponse({"error": "history record not found"}, status=404)
        except (json.JSONDecodeError, TypeError, ValueError) as error:
            return JsonResponse({"error": f"invalid metadata: {error}"}, status=400)
    return JsonResponse({"error": "method not allowed"}, status=405)


def history_item(record):
    """Serialize a TrafficRecord into the stable UI/API representation."""
    return {
        "id": record.id,
        "timestamp": record.timestamp,
        "source": record.source,
        "host": record.host,
        "method": record.method,
        "url": record.url,
        "request_headers": record.request_headers,
        "request_body": record.request_body or "",
        "status": record.status_code,
        "time": record.latency_ms,
        "response_headers": record.response_headers,
        "response_body": record.response_body or "",
        "request_body_encoding": record.request_body_encoding,
        "request_body_base64": record.request_body_base64,
        "response_body_encoding": record.response_body_encoding,
        "response_body_base64": record.response_body_base64,
        "response_content_type": record.response_content_type,
        "response_size": record.response_size,
        "tags": record.tags,
        "notes": record.notes,
        "proxy_event_id": record.proxy_event_id,
        "proxy_session": record.proxy_session,
    }


def persist_intruder_history(attack_id, results, result_offset=0):
    """Persist each completed Intruder exchange once for durable History."""
    if not isinstance(results, list):
        return
    for index, result in enumerate(results, start=result_offset):
        if not isinstance(result, dict):
            continue
        request_data = result.get("request") or {}
        if not isinstance(request_data, dict) or not request_data.get("url"):
            continue
        if TrafficRecord.objects.filter(
            source="intruder",
            proxy_session=attack_id,
            proxy_event_id=index,
        ).exists():
            continue
        response_headers = result.get("headers") or {}
        response_body = result.get("body") or ""
        TrafficRecord.objects.create(
            source="intruder",
            host=urlsplit(request_data["url"]).netloc,
            proxy_event_id=index,
            proxy_session=attack_id,
            method=request_data.get("method", "GET"),
            url=request_data["url"],
            request_headers=request_data.get("headers") or {},
            request_body=request_data.get("body") or "",
            request_body_encoding=request_data.get("body_encoding", "utf8"),
            request_body_base64=request_data.get("body_base64", ""),
            response_headers=response_headers,
            response_body=response_body,
            response_body_encoding=result.get("body_encoding", "utf8"),
            response_body_base64=result.get("body_base64", ""),
            response_content_type=result.get("body_content_type", response_headers.get("Content-Type", "")),
            status_code=result.get("status"),
            latency_ms=result.get("time"),
            response_size=result.get("size"),
        )


def persist_proxy_history(events):
    """Persist completed passive proxy exchanges once for durable History."""
    if not isinstance(events, list):
        return
    for event in events:
        if not isinstance(event, dict) or not event.get("url"):
            continue
        if event.get("source") not in (None, "", "proxy"):
            continue
        if event.get("status") is None and not event.get("error"):
            continue
        event_id = event.get("id")
        session = event.get("session")
        if event_id is not None and TrafficRecord.objects.filter(
            source="proxy",
            proxy_session=session,
            proxy_event_id=event_id,
        ).exists():
            continue
        TrafficRecord.objects.create(
            source="proxy",
            host=event.get("host", ""),
            proxy_event_id=event_id,
            proxy_session=session,
            method=event.get("method", "GET"),
            url=event["url"],
            request_headers=event.get("request_headers") or {},
            request_body=event.get("request_body") or "",
            request_body_encoding=event.get("request_body_encoding", "utf8"),
            request_body_base64=event.get("request_body_base64", ""),
            response_headers=event.get("response_headers") or {},
            response_body=event.get("response_body") or "",
            response_body_encoding=event.get("response_body_encoding", "utf8"),
            response_body_base64=event.get("response_body_base64", ""),
            response_content_type=event.get("response_content_type", (event.get("response_headers") or {}).get("Content-Type", "")),
            status_code=event.get("status") or None,
            latency_ms=event.get("latency_ms") or None,
            response_size=event.get("response_size") or None,
            tags=event.get("tags") or [],
            notes=event.get("notes") or "",
        )


def history_export(request):
    """Download all History records as a portable JSON document."""
    if request.method != "GET":
        return JsonResponse({"error": "method not allowed"}, status=405)
    records = TrafficRecord.objects.filter(source__in=("repeater", "intruder")).order_by("timestamp", "id")
    ids = [value for value in request.GET.get("ids", "").split(",") if value.isdigit()]
    if ids:
        records = records.filter(id__in=ids)
    payload = {
        "format": "intruder-lab-history",
        "version": 1,
        "items": [history_item(record) for record in records],
    }
    response = HttpResponse(
        json.dumps(payload, ensure_ascii=False, default=str, indent=2),
        content_type="application/json",
    )
    response["Content-Disposition"] = 'attachment; filename="intruder-history.json"'
    return response


@csrf_exempt
def history_import(request):
    """Create new History records from an exported JSON document."""
    if request.method != "POST":
        return JsonResponse({"error": "method not allowed"}, status=405)
    try:
        # Accept both the documented object format and a raw list for compatibility.
        payload = json.loads(request.body)
        items = payload.get("items") if isinstance(payload, dict) else payload
        if not isinstance(items, list):
            raise ValueError("items must be a list")
        imported = 0
        # Import creates new IDs and timestamps rather than overwriting local rows.
        for item in items:
            if not isinstance(item, dict) or not item.get("url"):
                raise ValueError("each history item must contain a URL")
            TrafficRecord.objects.create(
                source=item.get("source", "repeater"),
                host=item.get("host", ""),
                proxy_event_id=item.get("proxy_event_id"),
                proxy_session=item.get("proxy_session"),
                method=item.get("method", "GET"),
                url=item["url"],
                request_headers=item.get("request_headers") or {},
                request_body=item.get("request_body") or "",
                request_body_encoding=item.get("request_body_encoding", "utf8"),
                request_body_base64=item.get("request_body_base64", ""),
                response_headers=item.get("response_headers") or {},
                response_body=item.get("response_body") or "",
                response_body_encoding=item.get("response_body_encoding", "utf8"),
                response_body_base64=item.get("response_body_base64", ""),
                response_content_type=item.get("response_content_type", ""),
                status_code=item.get("status"),
                latency_ms=item.get("time"),
                response_size=item.get("response_size"),
                tags=item.get("tags") or [],
                notes=item.get("notes") or "",
            )
            imported += 1
    except (json.JSONDecodeError, TypeError, ValueError) as error:
        return JsonResponse({"error": f"invalid history file: {error}"}, status=400)
    return JsonResponse({"ok": True, "imported": imported}, status=201)


def call_engine(path, payload):
    # Django is the browser-facing boundary; the Go engine owns outbound
    # network requests and returns the structured result to the UI.
    """POST JSON to Go and normalize transport errors into API responses."""
    # Keep engine communication in one gateway helper for consistent errors.
    started = time.monotonic()
    logger.info("engine_request_start path=%s method=%s", path, payload.get("method") or payload.get("base_request", {}).get("method", ""))
    # Serialize only the structured payload expected by the engine endpoint.
    request = Request(
        f"{ENGINE_URL}{path}",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request) as response:
            raw_result = response.read()
            try:
                result = json.loads(raw_result)
            except json.JSONDecodeError:
                logger.error("engine_request_invalid_json path=%s status=%s", path, response.status)
                return 502, {
                    "error": "engine returned an invalid response",
                    "reason": "ENGINE_INVALID_RESPONSE",
                    "status": response.status,
                    "raw_response": raw_result.decode(errors="replace")[:4000],
                }
            logger.info(
                "engine_request_complete path=%s status=%s duration_ms=%d",
                path,
                response.status,
                int((time.monotonic() - started) * 1000),
            )
            return response.status, result
    except HTTPError as error:
        logger.warning(
            "engine_request_http_error path=%s status=%s duration_ms=%d",
            path,
            error.code,
            int((time.monotonic() - started) * 1000),
        )
        raw_error = error.read()
        try:
            return error.code, json.loads(raw_error)
        except json.JSONDecodeError:
            return error.code, {
                "error": f"engine returned HTTP {error.code}",
                "reason": "ENGINE_HTTP_ERROR",
                "raw_response": raw_error.decode(errors="replace")[:4000],
            }
    except URLError as error:
        logger.error(
            "engine_request_unavailable path=%s duration_ms=%d reason=%s",
            path,
            int((time.monotonic() - started) * 1000),
            error.reason,
        )
        return 502, {"error": f"engine unavailable: {error.reason}", "reason": "ENGINE_UNAVAILABLE"}


# Snapshot and stream are separate so the UI can hydrate first, then stay live.
def call_engine_get(path):
    """GET a read-only engine endpoint such as the Traffic snapshot."""
    try:
        with urlopen(f"{ENGINE_URL}{path}") as response:
            raw_result = response.read()
            try:
                return response.status, json.loads(raw_result)
            except json.JSONDecodeError:
                return 502, {
                    "error": "engine returned an invalid response",
                    "reason": "ENGINE_INVALID_RESPONSE",
                    "status": response.status,
                    "raw_response": raw_result.decode(errors="replace")[:4000],
                }
    except HTTPError as error:
        raw_result = error.read()
        try:
            return error.code, json.loads(raw_result)
        except json.JSONDecodeError:
            return error.code, {
                "error": f"engine returned HTTP {error.code}",
                "reason": "ENGINE_HTTP_ERROR",
                "raw_response": raw_result.decode(errors="replace")[:4000],
            }
    except URLError as error:
        return 502, {"error": f"engine unavailable: {error.reason}", "reason": "ENGINE_UNAVAILABLE"}


def call_engine_delete(path):
    """DELETE an engine resource such as a running Intruder attack."""
    request = Request(f"{ENGINE_URL}{path}", method="DELETE")
    try:
        with urlopen(request) as response:
            raw_result = response.read()
            try:
                return response.status, json.loads(raw_result)
            except json.JSONDecodeError:
                return 502, {
                    "error": "engine returned an invalid response",
                    "reason": "ENGINE_INVALID_RESPONSE",
                    "status": response.status,
                    "raw_response": raw_result.decode(errors="replace")[:4000],
                }
    except HTTPError as error:
        raw_error = error.read()
        try:
            return error.code, json.loads(raw_error)
        except json.JSONDecodeError:
            return error.code, {
                "error": f"engine returned HTTP {error.code}",
                "reason": "ENGINE_HTTP_ERROR",
                "raw_response": raw_error.decode(errors="replace")[:4000],
            }
    except URLError as error:
        return 502, {"error": f"engine unavailable: {error.reason}", "reason": "ENGINE_UNAVAILABLE"}


def call_engine_action(path, payload):
    """POST an action to an existing engine resource."""
    request = Request(
        f"{ENGINE_URL}{path}",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request) as response:
            return response.status, json.loads(response.read())
    except HTTPError as error:
        try:
            return error.code, json.loads(error.read())
        except json.JSONDecodeError:
            return error.code, {"error": error.reason}
    except URLError as error:
        return 502, {"error": f"engine unavailable: {error.reason}", "reason": "ENGINE_UNAVAILABLE"}


@csrf_exempt
def traffic(request):
    """Return the current in-memory passive Traffic snapshot."""
    if request.method == "DELETE":
        status, result = call_engine_delete("/events")
        return JsonResponse(result, status=status)
    if request.method != "GET":
        return JsonResponse({"error": "method not allowed"}, status=405)
    status, result = call_engine_get("/events")
    if status == 200:
        persist_proxy_history(result)
    return JsonResponse(result, status=status, safe=isinstance(result, dict))


def traffic_stream(request):
    """Proxy the engine SSE stream without buffering individual lines."""
    if request.method != "GET":
        return JsonResponse({"error": "method not allowed"}, status=405)
    try:
        cursor = request.headers.get("Last-Event-ID") or request.GET.get("last_event_id", "")
        stream_url = f"{ENGINE_URL}/events/stream"
        if cursor:
            stream_url += f"?last_event_id={cursor}"
        upstream = Request(stream_url, headers={"Last-Event-ID": cursor})
        response = urlopen(upstream)
    except URLError as error:
        return JsonResponse({"error": f"engine unavailable: {error.reason}", "reason": "ENGINE_UNAVAILABLE"}, status=502)

    def stream():
        # Read one SSE line at a time so small events reach the browser immediately.
        try:
            while True:
                chunk = response.readline()
                if not chunk:
                    break
                yield chunk
        finally:
            response.close()

    result = StreamingHttpResponse(stream(), content_type="text/event-stream")
    result["Cache-Control"] = "no-cache"
    result["X-Accel-Buffering"] = "no"
    return result


@csrf_exempt
def save_traffic(request):
    """Persist one selected passive event into durable History."""
    if request.method != "POST":
        return JsonResponse({"error": "method not allowed"}, status=405)
    try:
        payload = json.loads(request.body)
        events = payload.get("items") if isinstance(payload, dict) and isinstance(payload.get("items"), list) else [payload]
        persist_proxy_history(events)
        event = events[0] if events else {}
        record = TrafficRecord.objects.filter(
            source="proxy",
            proxy_event_id=event.get("id"),
            proxy_session=event.get("session"),
        ).order_by("-id").first()
        if record is None:
            return JsonResponse({"error": "traffic event must contain a URL"}, status=400)
    except (json.JSONDecodeError, TypeError, ValueError):
        return JsonResponse({"error": "invalid traffic event"}, status=400)
    records = TrafficRecord.objects.filter(source="proxy", proxy_event_id__in=[
        item.get("id") for item in events if isinstance(item, dict) and item.get("id") is not None
    ])
    return JsonResponse({"ok": True, "id": record.id, "ids": list(records.values_list("id", flat=True))}, status=201)


@csrf_exempt
def annotate_traffic(request):
    if request.method != "POST":
        return JsonResponse({"error": "method not allowed"}, status=405)
    try:
        payload = json.loads(request.body)
        if not isinstance(payload.get("tags", []), list):
            raise ValueError("tags must be a list")
        status, result = call_engine_action("/events/annotate", payload)
        return JsonResponse(result, status=status)
    except (json.JSONDecodeError, TypeError, ValueError) as error:
        return JsonResponse({"error": str(error)}, status=400)


@csrf_exempt
def history_bulk(request):
    if request.method != "POST":
        return JsonResponse({"error": "method not allowed"}, status=405)
    try:
        payload = json.loads(request.body)
        action = payload.get("action")
        if action == "clear":
            count, _ = TrafficRecord.objects.filter(source__in=("repeater", "intruder")).delete()
            return JsonResponse({"ok": True, "deleted": count})
        ids = [int(value) for value in payload.get("ids", [])]
        if not ids or action not in {"delete", "metadata"}:
            raise ValueError("ids and action are required")
        records = TrafficRecord.objects.filter(id__in=ids)
        if action == "delete":
            count, _ = records.delete()
            return JsonResponse({"ok": True, "deleted": count})
        tags = payload.get("tags", [])
        notes = payload.get("notes", "")
        records.update(tags=tags, notes=str(notes))
        return JsonResponse({"ok": True, "updated": records.count()})
    except (json.JSONDecodeError, TypeError, ValueError) as error:
        return JsonResponse({"error": str(error)}, status=400)


@csrf_exempt
def traffic_sessions(request, session_id=None):
    """Save, list, export, or import complete Traffic sessions as one bundle."""
    if request.method == "GET" and session_id is None:
        items = [{"id": item.id, "name": item.name, "count": len(item.items), "created_at": item.created_at} for item in TrafficSession.objects.order_by("-created_at")]
        return JsonResponse({"items": items})
    if request.method == "GET" and session_id is not None:
        try:
            session = TrafficSession.objects.get(id=session_id)
        except TrafficSession.DoesNotExist:
            return JsonResponse({"error": "traffic session not found"}, status=404)
        return JsonResponse({"id": session.id, "name": session.name, "items": session.items, "created_at": session.created_at})
    if request.method != "POST":
        return JsonResponse({"error": "method not allowed"}, status=405)
    try:
        payload = json.loads(request.body)
        items = payload.get("items") if isinstance(payload, dict) else payload
        name = payload.get("name", "Traffic session") if isinstance(payload, dict) else "Traffic session"
        if not isinstance(items, list):
            raise ValueError("items must be a list")
        if not all(isinstance(item, dict) and item.get("url") for item in items):
            raise ValueError("every session item must contain a URL")
        session = TrafficSession.objects.create(name=str(name)[:160], items=items)
    except (json.JSONDecodeError, TypeError, ValueError) as error:
        return JsonResponse({"error": f"invalid traffic session: {error}"}, status=400)
    return JsonResponse({"id": session.id, "name": session.name, "count": len(session.items)}, status=201)


"""Merge UI query/cookie editors into the engine request shape."""
# Convert the UI's structured query/cookie editors into one engine request.
def normalize_payload(payload):
    payload = dict(payload)
    split = urlsplit(payload.get("url", ""))
    query = payload.pop("query", None)
    # Preserve existing URL query values, then apply editor values over them.
    if isinstance(query, dict):
        merged = dict(parse_qsl(split.query, keep_blank_values=True))
        merged.update({str(key): str(value) for key, value in query.items()})
        payload["url"] = urlunsplit((split.scheme, split.netloc, split.path, urlencode(merged), split.fragment))
    cookies = payload.pop("cookies", None)
    # Represent cookie editor values as one standard Cookie request header.
    if isinstance(cookies, dict):
        headers = dict(payload.get("headers") or {})
        headers["Cookie"] = "; ".join(f"{key}={value}" for key, value in cookies.items())
        payload["headers"] = headers
    return payload


@csrf_exempt
def execute(request):
    """Forward one Repeater request and persist successful responses."""
    if request.method != "POST":
        return JsonResponse({"error": "method not allowed"}, status=405)
    try:
        payload = normalize_payload(json.loads(request.body))
        status, result = call_engine("/proxy/request", payload)
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({"error": "invalid JSON"}, status=400)
    # Persist every completed target HTTP response, including 4xx/5xx results.
    if status == 200 and isinstance(result, dict) and result.get("status") is not None:
        TrafficRecord.objects.create(
            source="repeater",
            method=payload.get("method", "GET"),
            url=payload.get("url", ""),
            request_headers=payload.get("headers", {}),
            request_body=payload.get("body", ""),
            response_headers=result.get("headers", {}),
            response_body=result.get("body", ""),
            response_body_encoding=result.get("body_encoding", "utf8"),
            response_body_base64=result.get("body_base64", ""),
            response_content_type=result.get("body_content_type", (result.get("headers") or {}).get("Content-Type", "")),
            status_code=result.get("status"),
            latency_ms=result.get("time"),
            response_size=result.get("size"),
        )
    return JsonResponse(result, status=status)


@csrf_exempt
def intruder(request):
    """Start or inspect an asynchronous Intruder attack."""
    if request.method == "GET":
        attack_id = request.GET.get("attack_id", "").strip()
        if not attack_id.isdigit():
            return JsonResponse({"error": "attack_id must be numeric"}, status=400)
        since = request.GET.get("since", "").strip()
        limit = request.GET.get("limit", "").strip()
        if limit:
            try:
                limit_value = int(limit)
            except ValueError:
                return JsonResponse({"error": "limit must be numeric"}, status=400)
            if limit_value <= 0:
                return JsonResponse({"error": "limit must be positive"}, status=400)
        if since:
            try:
                since_value = int(since)
            except ValueError:
                return JsonResponse({"error": "since must be numeric"}, status=400)
            if since_value < 0:
                return JsonResponse({"error": "since must not be negative"}, status=400)
            engine_path = f"/proxy/intruder/{attack_id}?since={since_value}"
        else:
            engine_path = f"/proxy/intruder/{attack_id}"
        if limit:
            engine_path += f"{'&' if '?' in engine_path else '?'}limit={limit_value}"
        status, result = call_engine_get(engine_path)
        if status == 200 and isinstance(result, dict):
            persist_intruder_history(
                int(attack_id),
                result.get("results"),
                result.get("result_offset", 0),
            )
        return JsonResponse(result, status=status)


    if request.method == "DELETE":
        attack_id = request.GET.get("attack_id", "").strip()
        if not attack_id.isdigit():
            return JsonResponse({"error": "attack_id must be numeric"}, status=400)
        status, result = call_engine_delete(f"/proxy/intruder/{attack_id}")
        return JsonResponse(result, status=status)


    if request.method == "POST" and request.GET.get("attack_id"):
        attack_id = request.GET.get("attack_id", "").strip()
        if not attack_id.isdigit():
            return JsonResponse({"error": "attack_id must be numeric"}, status=400)
        action = request.GET.get("action", "").strip().lower()
        if action not in {"pause", "resume"}:
            return JsonResponse({"error": "action must be pause or resume"}, status=400)
        status, result = call_engine_action(
            f"/proxy/intruder/{attack_id}",
            {"action": action},
        )
        return JsonResponse(result, status=status)
    if request.method != "POST":
        return JsonResponse({"error": "method not allowed"}, status=405)
    try:
        payload = json.loads(request.body)
        payload["base_request"] = normalize_payload(payload.get("base_request", {}))
        logger.info(
            "intruder_start mode=%s payload_sets=%d transformations=%d",
            payload.get("mode", ""),
            len(payload.get("payloads") or payload.get("dictionaries") or []),
            len(payload.get("transformations") or []),
        )
        status, result = call_engine("/proxy/intruder", payload)
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({"error": "invalid JSON"}, status=400)
    logger.info(
        "intruder_complete status=%s results=%d",
        status,
        len((result.get("results") or [])) if isinstance(result, dict) else 0,
    )
    return JsonResponse(result, status=status)


@csrf_exempt
def target_map(request):
    # Target jobs run asynchronously in Go so the browser can poll progress
    # and cancel a crawl without blocking the Django request worker.
    """Start or inspect an asynchronous same-origin site map crawl."""
    if request.method == "GET":
        map_id = request.GET.get("map_id", "").strip()
        if not map_id.isdigit():
            return JsonResponse({"error": "map_id must be numeric"}, status=400)
        status, result = call_engine_get(f"/proxy/target-map/{map_id}")
        return JsonResponse(result, status=status)
    if request.method == "DELETE":
        map_id = request.GET.get("map_id", "").strip()
        if not map_id.isdigit():
            return JsonResponse({"error": "map_id must be numeric"}, status=400)
        status, result = call_engine_delete(f"/proxy/target-map/{map_id}")
        return JsonResponse(result, status=status)
    if request.method != "POST":
        return JsonResponse({"error": "method not allowed"}, status=405)
    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({"error": "invalid JSON"}, status=400)
    status, result = call_engine("/proxy/target-map", payload)
    return JsonResponse(result, status=status)


@csrf_exempt
def osint(request):
    # Keep validation and error formatting consistent with the other gateway
    # endpoints while preserving partial OSINT results from the engine.
    """Run the built-in passive OSINT and WAF fingerprint checks."""
    if request.method != "POST":
        return JsonResponse({"error": "method not allowed"}, status=405)
    try:
        payload = json.loads(request.body)
        if not isinstance(payload, dict) or not str(payload.get("url", "")).strip():
            raise ValueError("url is required")
    except (json.JSONDecodeError, TypeError, ValueError) as error:
        return JsonResponse({"error": f"invalid OSINT request: {error}"}, status=400)
    status, result = call_engine("/proxy/osint", {
        "url": str(payload["url"]).strip(),
        "waf_check": bool(payload.get("waf_check", False)),
    })
    return JsonResponse(result, status=status)


@csrf_exempt
def scanner(request):
    """Run a read-only reconnaissance scan with security findings and verifyable evidence."""
    if request.method != "POST":
        return JsonResponse({"error": "method not allowed"}, status=405)
    try:
        payload = json.loads(request.body)
        if not isinstance(payload, dict) or not str(payload.get("url", "")).strip():
            raise ValueError("url is required")
    except (json.JSONDecodeError, TypeError, ValueError) as error:
        return JsonResponse({"error": f"invalid scanner request: {error}"}, status=400)
    status, result = call_engine("/proxy/scanner", {
        "url": str(payload["url"]).strip(),
    })
    return JsonResponse(result, status=status)




def _agent_error(message, reason, status=400):
    return JsonResponse({"error": message, "reason": reason}, status=status)








CHAT_CONTEXT_HISTORY_LIMIT = 20
CHAT_CONTEXT_TRAFFIC_LIMIT = 40
CHAT_CONTEXT_BODY_LIMIT = 4000
CHAT_MESSAGE_LIMIT = 12000
CHAT_MESSAGES_LIMIT = 24
CHAT_TOTAL_CONTEXT_LIMIT = 120000
CHAT_REQUEST_LIMIT = 1_000_000


def _truncate_chat_text(value, limit=CHAT_CONTEXT_BODY_LIMIT):
    text = str(value or "")
    if len(text) <= limit:
        return text
    suffix = f"\n[truncated; original_length={len(text)}]"
    return text[: max(0, limit - len(suffix))] + suffix


def _compact_chat_value(value, key=""):
    if isinstance(value, str):
        limit = CHAT_CONTEXT_BODY_LIMIT if any(
            marker in key.lower()
            for marker in ("body", "content", "request", "response", "message")
        ) else 2000
        return _truncate_chat_text(value, limit)
    if isinstance(value, list):
        return [_compact_chat_value(item, key) for item in value[:50]]
    if isinstance(value, dict):
        return {
            str(item_key): _compact_chat_value(item_value, str(item_key))
            for item_key, item_value in list(value.items())[:80]
        }
    return value


def _compact_chat_context(context):
    if not isinstance(context, dict):
        return {}
    if not context.get("attached_evidence"):
        return {}
    compact = dict(context)
    compact["history"] = [
        _compact_chat_value(item)
        for item in (context.get("history") or [])[:CHAT_CONTEXT_HISTORY_LIMIT]
        if isinstance(item, dict)
    ]
    compact["traffic"] = [
        _compact_chat_value(item)
        for item in (context.get("traffic") or [])[:CHAT_CONTEXT_TRAFFIC_LIMIT]
        if isinstance(item, dict)
    ]
    compact["saved_intruder"] = [
        _compact_chat_value(item)
        for item in (context.get("saved_intruder") or [])[:20]
        if isinstance(item, dict)
    ]
    compact = _compact_chat_value(compact)
    encoded = json.dumps(compact, ensure_ascii=False)
    while len(encoded) > CHAT_TOTAL_CONTEXT_LIMIT and (
        compact.get("traffic")
        or compact.get("history")
        or compact.get("saved_intruder")
        or compact.get("attached_evidence")
    ):
        if compact.get("traffic"):
            compact["traffic"] = compact["traffic"][: max(1, len(compact["traffic"]) // 2)]
        elif compact.get("history"):
            compact["history"] = compact["history"][: max(1, len(compact["history"]) // 2)]
        elif compact.get("saved_intruder"):
            compact["saved_intruder"] = compact["saved_intruder"][: max(1, len(compact["saved_intruder"]) // 2)]
        else:
            reduced = False
            for key, value in compact.get("attached_evidence", {}).items():
                if isinstance(value, list) and len(value) > 1:
                    compact["attached_evidence"][key] = value[: max(1, len(value) // 2)]
                    reduced = True
                    break
            if not reduced:
                compact["attached_evidence"] = {
                    "summary": "Attached evidence exceeded the chat context limit."
                }
        encoded = json.dumps(compact, ensure_ascii=False)
    if len(encoded) > CHAT_TOTAL_CONTEXT_LIMIT:
        compact["compaction"] = {
            "applied": True,
            "reason": "chat_context_size_limit",
            "max_chars": CHAT_TOTAL_CONTEXT_LIMIT,
        }
    return compact


def _compact_chat_messages(messages):
    compact = []
    for message in messages[-CHAT_MESSAGES_LIMIT:]:
        if not isinstance(message, dict):
            continue
        item = {
            "role": str(message.get("role", "user")),
            "content": _truncate_chat_text(
                message.get("content", ""),
                CHAT_MESSAGE_LIMIT,
            ),
        }
        if message.get("name"):
            item["name"] = str(message["name"])[:80]
        compact.append(item)
    return compact
















@csrf_protect
def agent_chat(request):
    """Analyze only evidence explicitly attached by the operator."""
    if request.method != "POST":
        return _agent_error("method not allowed", "METHOD_NOT_ALLOWED", 405)
    try:
        if len(request.body) > CHAT_REQUEST_LIMIT:
            raise ValueError("chat request is too large")
        payload = json.loads(request.body)
        if not isinstance(payload, dict):
            raise ValueError("request must be an object")
        messages = payload.get("messages")
        if not isinstance(messages, list) or not messages:
            raise ValueError("messages must be a non-empty list")
        if "approved_tool_call" in payload or "execution_profile" in payload:
            raise ValueError("agent execution tools are not supported; use the UI evidence attachment buttons")
        supplied_context = payload.get("context")
        if supplied_context is None:
            supplied_context = {}
        if not isinstance(supplied_context, dict):
            raise ValueError("context must be an object")
        attached_evidence = supplied_context.get("attached_evidence", {})
        if not isinstance(attached_evidence, dict):
            raise ValueError("attached_evidence must be an object")
        context = {
            "kind": "request_rider_selected_evidence",
            "attached_evidence": attached_evidence,
        } if attached_evidence else {}
        messages = _compact_chat_messages(messages)
        context = _compact_chat_context(context)
        provider = str(payload.get("provider", "ollama"))
        config = {
            "endpoint": payload.get("endpoint"),
            "model": payload.get("model"),
            "api_key": payload.get("api_key"),
        }
        result = generate_agent_chat(messages, provider=provider, context=context, **config)
        return JsonResponse({"provider": provider, "message": result["message"]})
    except (json.JSONDecodeError, TypeError, ValueError, RuntimeError, AgentProviderError) as error:
        return _agent_error(f"invalid agent chat: {error}", "INVALID_AGENT_CHAT")


def intruder_saved_item(attack):
        """Serialize a saved Intruder definition for the browser."""
        return {
            "id": attack.id,
            "name": attack.name,
            "mode": attack.attack_type,
            "base_request": attack.base_request,
            "payloads": attack.payloads,
            "transformations": attack.transformations,
            "delay_ms": attack.delay_ms,
            "concurrency": attack.concurrency,
            "status": attack.status,
            "created_at": attack.created_at,
        }


@csrf_exempt
def intruder_saved(request, attack_id=None):
        """List, save, or re-run persisted Intruder configurations."""
        if request.method == "GET" and attack_id is None:
            return JsonResponse({"items": [intruder_saved_item(item) for item in IntruderAttack.objects.order_by("-created_at")]})
        if attack_id is not None:
            try:
                attack = IntruderAttack.objects.get(id=attack_id)
            except IntruderAttack.DoesNotExist:
                return JsonResponse({"error": "saved attack not found"}, status=404)
            if request.method == "GET":
                return JsonResponse(intruder_saved_item(attack))
            if request.method == "POST":
                engine_payload = {
                    "base_request": attack.base_request,
                    "mode": attack.attack_type,
                    "payloads": attack.payloads,
                    "transformations": attack.transformations,
                }
                if attack.delay_ms:
                    engine_payload["delay_ms"] = attack.delay_ms
                if attack.concurrency:
                    engine_payload["concurrency"] = attack.concurrency
                status, result = call_engine("/proxy/intruder", engine_payload)
                if status in {200, 202}:
                    attack.status = result.get("status", "running")
                    attack.save(update_fields=["status"])
                return JsonResponse(result, status=status)
            return JsonResponse({"error": "method not allowed"}, status=405)
        if request.method != "POST":
            return JsonResponse({"error": "method not allowed"}, status=405)
        try:
            payload = json.loads(request.body)
            mode = payload.get("mode")
            base_request = payload.get("base_request")
            payloads = payload.get("payloads")
            transformations = payload.get("transformations") or []
            delay_ms = payload.get("delay_ms", 150)
            concurrency = payload.get("concurrency", 1)
            if mode not in dict(IntruderAttack.TYPE_CHOICES):
                raise ValueError("unsupported attack mode")
            if not isinstance(base_request, dict) or not isinstance(payloads, list) or not isinstance(transformations, list):
                raise ValueError("base_request, payloads, and transformations must be JSON values of the expected type")
            if isinstance(delay_ms, bool) or not isinstance(delay_ms, int) or delay_ms < 0:
                raise ValueError("delay_ms must be a non-negative integer")
            if isinstance(concurrency, bool) or not isinstance(concurrency, int) or concurrency < 1:
                raise ValueError("concurrency must be a positive integer")
            attack = IntruderAttack.objects.create(
                name=str(payload.get("name") or "Intruder attack")[:120],
                attack_type=mode,
                base_request=base_request,
                payloads=payloads,
                transformations=transformations,
                delay_ms=delay_ms,
                concurrency=concurrency,
            )
        except (json.JSONDecodeError, TypeError, ValueError) as error:
            return JsonResponse({"error": f"invalid saved attack: {error}"}, status=400)
        return JsonResponse(intruder_saved_item(attack), status=201)
