package passive

import (
	"io"
	"net/http"
	"strings"
	"testing"
)

func TestReadAndRestorePreservesBody(t *testing.T) {
	body := io.NopCloser(strings.NewReader("0123456789"))
	captured, err := readAndRestore(&body)
	if err != nil {
		t.Fatalf("readAndRestore() error = %v", err)
	}
	if string(captured) != "0123456789" {
		t.Fatalf("captured body = %q, want original body", captured)
	}
	restored, err := io.ReadAll(body)
	if err != nil {
		t.Fatalf("reading restored body: %v", err)
	}
	if string(restored) != "0123456789" {
		t.Fatalf("restored body = %q, want original body", restored)
	}
}

func TestStoreKeepsMostRecentEvents(t *testing.T) {
	store := NewStore()
	for index := int64(1); index <= 3; index++ {
		store.Add(Event{Session: index})
	}

	events := store.List()
	if len(events) != 3 || events[0].Session != 1 || events[2].Session != 3 {
		t.Fatalf("stored events = %#v, want all sessions", events)
	}
}

func TestStoreClearRemovesSnapshotAndReplay(t *testing.T) {
	store := NewStore()
	store.Add(Event{Method: "GET"})
	store.Clear()
	if events := store.List(); len(events) != 0 {
		t.Fatalf("snapshot after clear = %#v", events)
	}
	if events := store.ListSince(0); len(events) != 0 {
		t.Fatalf("replay after clear = %#v", events)
	}
}

func TestStorePublishesRequestAndResponseUpdates(t *testing.T) {
	store := NewStore()
	events, unsubscribe := store.Subscribe()
	defer unsubscribe()

	id := store.Add(Event{Method: "GET", URL: "https://example.test/path"})
	requestEvent := <-events
	if requestEvent.ID != id || requestEvent.URL == "" || requestEvent.Status != 0 {
		t.Fatalf("request event = %#v", requestEvent)
	}

	store.Update(id, func(event *Event) {
		event.Status = http.StatusNoContent
		event.Latency = 12
	})
	responseEvent := <-events
	if responseEvent.ID != id || responseEvent.Status != http.StatusNoContent || responseEvent.Latency != 12 {
		t.Fatalf("response event = %#v", responseEvent)
	}

}

func TestStoreReplaysUpdatesAfterCursor(t *testing.T) {
	store := NewStore()
	id := store.Add(Event{Method: "GET"})
	initial := store.ListSince(0)
	if len(initial) != 1 || initial[0].ID != id {
		t.Fatalf("initial replay = %#v", initial)
	}

	store.Update(id, func(event *Event) { event.Status = http.StatusOK })
	replayed := store.ListSince(initial[0].Cursor)
	if len(replayed) != 1 || replayed[0].ID != id || replayed[0].Status != http.StatusOK {
		t.Fatalf("updated replay = %#v", replayed)
	}

}

func TestStoreResetsCursorAfterEngineRestartEpoch(t *testing.T) {
	store := NewStore()
	store.Add(Event{Method: "GET"})
	events := store.ListSince(100)
	if len(events) != 1 {
		t.Fatalf("restart reconciliation = %#v, want current snapshot", events)
	}
}

func TestFlattenHeaders(t *testing.T) {
	headers := flattenHeaders(http.Header{"X-Test": {"one", "two"}})
	if headers["X-Test"] != "one, two" {
		t.Fatalf("flattened header = %q", headers["X-Test"])
	}
}
