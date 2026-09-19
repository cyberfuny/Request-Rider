"""Database models for durable HTTP history and future Intruder metadata."""

from django.db import models

# Durable History combines completed Repeater requests and explicitly saved
# passive proxy events in one table so both workflows can be replayed together.
class TrafficRecord(models.Model):
    """One request/response exchange shown in the History tab."""

    # The source distinguishes active Repeater traffic from saved proxy traffic.
    SOURCE_CHOICES = [
        ("repeater", "Repeater"),
        ("intruder", "Intruder"),
        ("proxy", "Proxy"),
        ("route-check", "Route check"),
    ]
    # Creation time is assigned by Django and used by History sorting.
    timestamp = models.DateTimeField(auto_now_add=True)
    # Origin of the record in the UI workflow.
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default="repeater")
    # Original HTTP request metadata.
    method = models.CharField(max_length=10)
    url = models.URLField(max_length=2048)
    # Passive proxy metadata, empty for ordinary Repeater records.
    host = models.CharField(max_length=255, blank=True, default="")
    source_ip = models.GenericIPAddressField(null=True, blank=True)
    proxy_event_id = models.PositiveBigIntegerField(null=True, blank=True)
    proxy_session = models.BigIntegerField(null=True, blank=True)
    # Request data is stored as JSON headers plus text body.
    request_headers = models.JSONField(default=dict)
    request_body = models.TextField(null=True, blank=True)
    request_body_encoding = models.CharField(max_length=16, default="utf8")
    request_body_base64 = models.TextField(blank=True, default="")
    # Response data mirrors the request representation.
    response_headers = models.JSONField(default=dict)
    response_body = models.TextField(null=True, blank=True)
    response_body_encoding = models.CharField(max_length=16, default="utf8")
    response_body_base64 = models.TextField(blank=True, default="")
    response_content_type = models.CharField(max_length=255, blank=True, default="")
    # Measurement fields are nullable because pending proxy events may lack
    # a response when they are first observed.
    status_code = models.IntegerField(null=True, blank=True)
    latency_ms = models.IntegerField(null=True, blank=True)
    response_size = models.IntegerField(null=True, blank=True)
    tags = models.JSONField(default=list)
    notes = models.TextField(blank=True, default="")


class TrafficSession(models.Model):
    """One imported/exported Traffic capture containing complete exchanges."""

    name = models.CharField(max_length=160, default="Traffic session")
    items = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)


class IntruderAttack(models.Model):
    """Saved Intruder configuration that can be run again."""

    # These values match the Go generator and UI mode names.
    TYPE_CHOICES = [
        ('sniper', 'Sniper'),
        ('batteringRam', 'Battering Ram'),
        ('pitchfork', 'Pitchfork'),
        ('clusterBomb', 'Cluster Bomb'),
    ]
    # Human-readable label shown in the saved attack list.
    name = models.CharField(max_length=120, default="Intruder attack")
    # Selected generation algorithm for the attack.
    attack_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    # Base request before marker replacement.
    base_request = models.JSONField()
    # Original dictionaries/payload lists submitted by the user.
    payloads = models.JSONField()
    # Ordered transformation chain applied by the engine.
    transformations = models.JSONField(default=list)
    # Delay between sequential Intruder requests in milliseconds.
    delay_ms = models.PositiveIntegerField(default=150)
    # Number of concurrent Intruder workers.
    concurrency = models.PositiveIntegerField(default=1)
    # Lifecycle state reserved for future persisted attack jobs.
    status = models.CharField(max_length=20, default='pending')
    # Creation time used for future attack history sorting.
    created_at = models.DateTimeField(auto_now_add=True)
