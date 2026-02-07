# Auto-Updating Data in Taskyn Web UI

## Research Summary

This document evaluates approaches for keeping the Taskyn Web UI automatically updated when underlying data changes. The current stack is React 19 + TanStack Query v5 + FastAPI (Python) acting as a REST bridge to an MCP server (source of truth).

**Date:** 2026-02-07

---

## Current Architecture Context

```
Browser (React + TanStack Query)
    |
    | HTTP REST (fetch)
    v
FastAPI Web Server (port 3020)
    |
    | FastMCP Client (HTTP)
    v
MCP Server (port 8000) — SQLite DB (source of truth)
```

**Key observations from current codebase:**
- `QueryClient` configured with `staleTime: 30_000` (30 seconds) and `retry: 1`
- No real-time mechanism currently exists; pages use manual `loadData()` calls via `useEffect`
- Some pages (e.g., `ProjectsPage`) bypass TanStack Query entirely, using raw `useState` + `useEffect` + API calls
- FastAPI backend is a stateless proxy to MCP tools via `call_mcp_tool()`
- The MCP server has no built-in change notification mechanism
- Single-user system (personal PM tool) — no multi-user sync requirements

---

## Approach 1: Polling (TanStack Query Built-in)

### How It Works

TanStack Query v5 provides several built-in mechanisms for auto-refreshing data:

| Option | Behavior |
|--------|----------|
| `refetchInterval` | Refetch every N milliseconds. Can be a function for dynamic intervals. |
| `refetchIntervalInBackground` | Continue polling even when tab is not focused. |
| `refetchOnWindowFocus` | Refetch when user returns to the tab (enabled by default if data is stale). |
| `refetchOnReconnect` | Refetch when network connection is restored. |
| `staleTime` | How long data is considered "fresh" before background refetch is allowed. |

**Example:**
```tsx
const { data } = useQuery({
  queryKey: ['nodes', { project_id: projectId }],
  queryFn: () => nodesApi.list({ project_id: projectId }),
  refetchInterval: 15_000,       // poll every 15 seconds
  refetchOnWindowFocus: true,    // refetch on tab focus
  staleTime: 10_000,             // data is fresh for 10 seconds
});
```

**Dynamic interval based on data:**
```tsx
const { data } = useQuery({
  queryKey: ['timer', 'active'],
  queryFn: () => timerApi.getActive(),
  refetchInterval: (query) => {
    // Poll faster when timer is running
    return query.state.data?.is_active ? 1_000 : 30_000;
  },
});
```

### Integration with TanStack Query

Native. Zero additional libraries required. This is how TanStack Query is designed to work.

### Complexity

| Aspect | Complexity |
|--------|------------|
| Frontend | **Very Low** — add options to existing `useQuery` calls |
| Backend | **None** — no changes needed, existing REST endpoints work |
| Infrastructure | **None** — standard HTTP |

### Fit with FastAPI-to-MCP Proxy Architecture

**Excellent.** Polling uses the same REST endpoints already built. The proxy architecture is completely transparent to this approach. No backend changes whatsoever.

### Performance Implications

- **Network overhead:** Each poll is a full HTTP request/response cycle. For 10 active queries polling every 15 seconds, that is ~40 requests/minute.
- **Server load:** Every poll hits FastAPI -> MCP -> SQLite. For a single-user system, this is negligible.
- **Latency:** Updates appear with average delay of `refetchInterval / 2`. A 15-second interval means updates appear 7.5 seconds late on average.
- **Battery/CPU:** Minimal if intervals are reasonable (>5 seconds). `refetchIntervalInBackground` should be used sparingly.
- **Unnecessary fetches:** Many polls will return identical data. HTTP 304 (Not Modified) is not supported by MCP calls, so every poll does real work.

### Browser Support

**Universal** — uses standard HTTP `fetch()`.

### Relevant Libraries

None needed beyond `@tanstack/react-query` (already installed, v5.62+).

### Verdict

Best starting point. Trivial to implement, zero backend changes, and perfectly adequate for a single-user personal tool.

---

## Approach 2: WebSockets

### How It Works

WebSockets establish a persistent bidirectional TCP connection between browser and server. The server can push messages to the client at any time without polling.

**Integration pattern with TanStack Query (TkDodo's recommended approach):**
1. Use `useQuery` for initial data fetching via REST
2. Establish a single WebSocket connection at app level
3. When the server sends a change event, use `queryClient.invalidateQueries()` or `queryClient.setQueryData()` to update the cache
4. Set `staleTime: Infinity` so data only refreshes via explicit invalidation

**Two sub-patterns:**

**A) Invalidation-based (recommended by TkDodo):**
```tsx
// App-level WebSocket handler
useEffect(() => {
  const ws = new WebSocket('ws://localhost:3020/ws/events');
  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    // msg = { entity: ['nodes', 'list'], project_id: '...' }
    queryClient.invalidateQueries({ queryKey: msg.entity });
  };
  return () => ws.close();
}, [queryClient]);
```

**B) Direct cache update (for high-frequency updates):**
```tsx
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  // msg = { entity: 'node', id: '...', data: { ...updatedNode } }
  queryClient.setQueryData(['nodes', msg.id], msg.data);
};
```

### Integration with TanStack Query

No native integration. TanStack Query does not have built-in WebSocket support. You wire it manually via `queryClient.invalidateQueries()` or `queryClient.setQueryData()`. This is a well-documented and widely adopted pattern.

### Complexity

| Aspect | Complexity |
|--------|------------|
| Frontend | **Moderate** — WebSocket connection management, reconnection logic, message parsing, integration with QueryClient |
| Backend | **High** — FastAPI needs a WebSocket endpoint, connection manager, and a mechanism to detect changes from the MCP server to push events |
| Infrastructure | **Moderate** — WebSocket connections are stateful; proxies/load balancers need WebSocket upgrade support |

### Fit with FastAPI-to-MCP Proxy Architecture

**Poor.** This is the critical problem. The MCP server is the source of truth, but it has no change notification mechanism. FastAPI would need to:
1. Either poll the MCP server itself (defeating the purpose), or
2. Have direct access to the SQLite database to watch for changes, or
3. Hook into MCP tool calls and broadcast events after mutations — but this only catches changes made through the web UI, not through CLI or other MCP clients.

Option 3 is partially viable: FastAPI can emit WebSocket events after its own mutation endpoints succeed. But this only provides real-time updates for changes made through the web UI itself, not for changes from CLI or other sources.

### Performance Implications

- **Network:** Very efficient — small frames (2 bytes overhead) sent only when data changes
- **Server:** Maintains persistent connections; for a single user this is trivial
- **Latency:** Near-instantaneous (<100ms)
- **Battery/CPU:** Idle connections consume minimal resources

### Browser Support

**Universal.** WebSocket API is supported in all modern browsers (Chrome 16+, Firefox 11+, Safari 7+, Edge 12+).

### Relevant Libraries

| Library | Notes |
|---------|-------|
| `react-use-websocket` (v4.13.0) | React hooks for WebSocket. 77K weekly downloads. |
| `socket.io-client` | Feature-rich but heavy. Requires `python-socketio` on backend. |
| `fastapi-websocket-pubsub` | Pub/Sub over WebSocket for FastAPI. Good for topic-based events. |
| Native `WebSocket` API | No library needed; simple enough for this use case. |

### Verdict

Overkill for a single-user personal tool. The main blocker is that FastAPI cannot detect changes made outside the web UI (via CLI/MCP), so the server cannot push truly comprehensive change events. Bidirectional communication is unnecessary since the client already sends mutations via REST.

---

## Approach 3: Server-Sent Events (SSE)

### How It Works

SSE establishes a one-way HTTP streaming connection from server to client. The server sends events as text lines over a long-lived HTTP response. The browser's `EventSource` API handles reconnection automatically.

**FastAPI implementation with `sse-starlette`:**
```python
from sse_starlette.sse import EventSourceResponse
import asyncio

@app.get("/api/v1/events")
async def event_stream():
    async def generate():
        while True:
            # Check for changes somehow
            event = await get_next_event()
            yield {"event": "update", "data": json.dumps(event)}
    return EventSourceResponse(generate())
```

**Frontend integration with TanStack Query:**
```tsx
useEffect(() => {
  const source = new EventSource('/api/v1/events');
  source.addEventListener('update', (e) => {
    const msg = JSON.parse(e.data);
    queryClient.invalidateQueries({ queryKey: msg.entity });
  });
  return () => source.close();
}, [queryClient]);
```

### Integration with TanStack Query

No native integration, same as WebSockets. You manually wire `EventSource` events to `queryClient.invalidateQueries()`. TanStack Query's experimental `streamedQuery` API exists but is designed for streaming data within a single query, not for event-driven cache invalidation across queries.

**`experimental_streamedQuery`:**
- Designed for streaming responses (e.g., AI chat token-by-token), not for cross-query invalidation
- Data accumulates as an array of chunks within a single query
- Not suitable for our use case of "notify about changes to other queries"

### Complexity

| Aspect | Complexity |
|--------|------------|
| Frontend | **Low** — `EventSource` API is simpler than WebSocket (auto-reconnect, no ping/pong) |
| Backend | **Moderate-High** — same problem as WebSockets: FastAPI needs a way to detect changes from MCP. Requires `sse-starlette` library. |
| Infrastructure | **Low** — standard HTTP; works with all proxies, load balancers, CDNs |

### Fit with FastAPI-to-MCP Proxy Architecture

**Same limitation as WebSockets.** The MCP server provides no change notification mechanism. FastAPI can only push events for mutations it processes itself. External changes (CLI, other MCP clients) would not be detected.

However, SSE has one advantage over WebSockets here: if we fall back to a server-side polling pattern (FastAPI polls MCP and emits SSE events), the implementation is simpler because SSE is unidirectional.

### Performance Implications

- **Network:** Efficient for server-to-client. ~5 bytes overhead per message.
- **Connection limit:** Without HTTP/2, browsers limit to 6 concurrent SSE connections per domain. With HTTP/2, this increases to ~100. Taskyn uses HTTP/2 is not configured by default, but a single SSE connection is sufficient.
- **Latency:** Near-instantaneous when events are available
- **Battery/CPU:** Long-lived idle connections are efficient

### Browser Support

**Universal.** `EventSource` is supported in Chrome 6+, Firefox 6+, Safari 5+, Edge 79+. The only gap is IE (irrelevant in 2026).

### Relevant Libraries

| Library | Notes |
|---------|-------|
| `sse-starlette` (v3.2.0) | Production-ready SSE for FastAPI/Starlette. |
| `EventSource` (browser native) | No frontend library needed. |
| `eventsource` npm package | Polyfill/enhanced EventSource with header support. |
| `@microsoft/fetch-event-source` | EventSource using fetch() — supports POST, headers, retries. |

### Verdict

Simpler than WebSockets for the same use case. However, the fundamental problem remains: the FastAPI proxy cannot detect changes from external sources. For self-initiated changes only, SSE is cleaner than WebSockets since Taskyn only needs server-to-client push.

---

## Approach 4: Long Polling

### How It Works

The client sends an HTTP request; the server holds the connection open until new data is available (or a timeout occurs), then responds. The client immediately sends a new request after receiving a response.

```python
# Backend (FastAPI)
@app.get("/api/v1/poll")
async def long_poll(last_version: int = 0, timeout: int = 30):
    deadline = time.time() + timeout
    while time.time() < deadline:
        current = await get_version()
        if current > last_version:
            return {"version": current, "changes": await get_changes(last_version)}
        await asyncio.sleep(1)  # check every second
    return {"version": last_version, "changes": []}
```

### Integration with TanStack Query

Can be modeled as a regular query with long timeout:
```tsx
const { data } = useQuery({
  queryKey: ['changes', lastVersion],
  queryFn: () => fetch(`/api/v1/poll?last_version=${lastVersion}&timeout=30`),
  refetchInterval: 0,      // refetch immediately after receiving
  staleTime: 0,            // always stale, always refetch
  retry: true,
  retryDelay: 1000,
});
```

### Complexity

| Aspect | Complexity |
|--------|------------|
| Frontend | **Moderate** — timeout handling, reconnection, version tracking |
| Backend | **High** — holding connections open, version tracking, same MCP change detection problem |
| Infrastructure | **Moderate** — long-held connections consume server threads/workers |

### Fit with FastAPI-to-MCP Proxy Architecture

**Same fundamental limitation.** Requires change detection from MCP server. Additionally, holding connections open in FastAPI while polling MCP for changes is wasteful.

### Performance Implications

- **Network:** More efficient than short polling (fewer empty responses), less efficient than SSE/WebSocket
- **Server:** Each held connection ties up an async task. For a single user, negligible.
- **Latency:** Typically 1-2 seconds (server-side check interval)
- **Overhead:** Full HTTP headers on every cycle (~hundreds of bytes)

### Browser Support

**Universal** — uses standard HTTP.

### Relevant Libraries

No specialized libraries needed. Standard `fetch()` with timeout support.

### Verdict

Strictly inferior to SSE for one-way push scenarios. More complex to implement, less efficient, and solves the same problem SSE solves more elegantly. Not recommended.

---

## Approach 5: WebTransport

### How It Works

WebTransport is a modern protocol built on HTTP/3 (QUIC) that provides multiplexed, bidirectional streams with lower latency than WebSockets. It supports both reliable and unreliable delivery.

### Browser Support

- Chrome 97+, Edge 98+, Firefox 115+
- **Safari: NOT SUPPORTED** (as of Feb 2026)
- Overall: ~75% browser coverage
- Production-ready adoption projected for 2027-2028

### Fit with FastAPI-to-MCP Proxy Architecture

**Not viable.** Requires HTTP/3 server infrastructure. FastAPI/uvicorn does not support WebTransport. No Python libraries for WebTransport servers are production-ready.

### Verdict

Not a practical option in 2026. The technology is too immature, browser support is incomplete (Safari), and no Python server-side support exists.

---

## Approach 6: HTTP/2 Server Push

### Status

**Deprecated and removed.** Chrome removed HTTP/2 Server Push support entirely. It was designed for pushing static assets (CSS, JS), not for real-time data. Not applicable.

---

## Approach 7: Mutation-Aware Invalidation (Recommended Practical Pattern)

### How It Works

This is not a new transport mechanism but a **pattern within TanStack Query** that eliminates the need for server-push entirely. After every mutation, the client proactively invalidates related queries.

```tsx
const createNodeMutation = useMutation({
  mutationFn: (data: NodeCreate) => nodesApi.create(data),
  onSuccess: () => {
    // Invalidate everything that might be affected
    queryClient.invalidateQueries({ queryKey: ['nodes'] });
    queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    queryClient.invalidateQueries({ queryKey: ['projects', projectId] });
  },
});
```

Combined with:
- `refetchOnWindowFocus: true` (catch external changes when user returns)
- Moderate `staleTime` (30-60 seconds)
- `refetchOnReconnect: true`

### Integration with TanStack Query

**Native and idiomatic.** This is the primary pattern TanStack Query was designed for. `useMutation` + `onSuccess` invalidation is the recommended approach in official documentation.

### Complexity

| Aspect | Complexity |
|--------|------------|
| Frontend | **Low-Moderate** — need to define invalidation rules per mutation, but this is standard TanStack Query usage |
| Backend | **None** — no changes needed |
| Infrastructure | **None** — standard HTTP |

### Fit with FastAPI-to-MCP Proxy Architecture

**Perfect.** No backend changes. The pattern works entirely within the frontend. When the user makes a change through the web UI, the mutation callback invalidates related queries. When the user returns to the tab, `refetchOnWindowFocus` catches any changes made elsewhere (CLI).

### Performance Implications

- Efficient: only refetches when mutations occur or when the user returns to the tab
- No unnecessary polling
- Immediate UI update after user's own mutations
- External changes (from CLI) are picked up within `staleTime` or on window focus

### Verdict

This is the pragmatic sweet spot for Taskyn. It handles the most common case (user's own changes) instantly, and handles the edge case (CLI changes) via window focus refetch.

---

## TanStack Query v5 Feature Summary

### Built-in Auto-Refresh Features

| Feature | Status | Use Case |
|---------|--------|----------|
| `refetchInterval` | Stable | Periodic polling |
| `refetchOnWindowFocus` | Stable | Catch changes on tab return |
| `refetchOnReconnect` | Stable | Catch changes after network loss |
| `refetchIntervalInBackground` | Stable | Background polling |
| `focusManager` | Stable | Custom focus event handling |
| `onlineManager` | Stable | Custom online/offline detection |
| `invalidateQueries` | Stable | Manual cache invalidation |
| `setQueryData` | Stable | Direct cache update |
| `setQueriesData` | Stable | Bulk cache update |
| `experimental_streamedQuery` | Experimental | Streaming data within a single query |

### WebSocket/SSE Plugins

**There are no official TanStack Query plugins for WebSocket or SSE integration.** The recommended approach is to use `queryClient.invalidateQueries()` or `queryClient.setQueryData()` manually when events arrive. This is a deliberate design choice — TanStack Query handles caching and synchronization, while the transport layer is left to the developer.

### Key Configuration Options for Real-Time

```tsx
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,           // data fresh for 30 seconds
      refetchOnWindowFocus: true,   // refetch on tab focus (default: true)
      refetchOnReconnect: true,     // refetch on network reconnect (default: true)
      retry: 1,
    },
  },
});
```

---

## FastAPI Native Support

### WebSockets

FastAPI has **first-class WebSocket support** via Starlette:
```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Echo: {data}")
```

Connection management (tracking connected clients, broadcasting) must be implemented manually or via libraries like `fastapi-websocket-pubsub`.

### Server-Sent Events

FastAPI supports SSE via the `sse-starlette` library (v3.2.0):
```python
from sse_starlette.sse import EventSourceResponse

@app.get("/events")
async def events():
    async def generate():
        while True:
            yield {"event": "ping", "data": "alive"}
            await asyncio.sleep(10)
    return EventSourceResponse(generate())
```

No built-in SSE support in FastAPI core; `sse-starlette` is the standard choice.

---

## Comparison Table

| Criterion | Polling | WebSocket | SSE | Long Polling | Mutation Invalidation |
|-----------|---------|-----------|-----|-------------|----------------------|
| **Frontend complexity** | Very Low | Moderate | Low | Moderate | Low |
| **Backend complexity** | None | High | Moderate-High | High | None |
| **New dependencies** | None | react-use-websocket (optional) | sse-starlette | None | None |
| **Latency** | interval/2 avg | <100ms | <100ms | 1-2s | Instant (own changes) |
| **Detects CLI changes** | Yes | Partial* | Partial* | Partial* | On window focus |
| **Works with MCP proxy** | Excellent | Poor | Poor | Poor | Excellent |
| **Browser support** | Universal | Universal | Universal (except IE) | Universal | Universal |
| **Server overhead** | O(polls/sec) | O(connections) | O(connections) | O(connections) | None |
| **Scalability concern** | Wasted requests | State management | Connection limits (HTTP/1.1) | Thread holding | None |
| **Implementation time** | 1-2 hours | 2-3 days | 1-2 days | 1-2 days | 2-4 hours |

*Partial: Can only detect changes the FastAPI server itself makes, not changes from CLI or other MCP clients, unless FastAPI polls the MCP server.

---

## Recommendation

### Phase 1 (Immediate): Mutation-Aware Invalidation + Smart Polling

This is the right approach for Taskyn given its architecture and single-user nature.

**Actions:**
1. **Migrate pages to TanStack Query hooks** — Replace raw `useState`/`useEffect` patterns (e.g., in `ProjectsPage`) with proper `useQuery` and `useMutation` hooks.
2. **Define invalidation rules** — After each mutation, invalidate related query keys:
   - Creating a node invalidates `['nodes']`, `['dashboard']`, and the parent project stats
   - Updating a project invalidates `['projects']` and `['projects', id]`
   - Starting/completing a node invalidates `['nodes']`, `['dashboard']`, related rollups
3. **Configure smart defaults:**
   ```tsx
   const queryClient = new QueryClient({
     defaultOptions: {
       queries: {
         staleTime: 30_000,              // 30 seconds
         refetchOnWindowFocus: true,     // catch CLI changes on tab return
         refetchOnReconnect: true,       // catch changes after disconnect
         retry: 1,
       },
     },
   });
   ```
4. **Use `refetchInterval` selectively** for data that benefits from live updates:
   - Active timer widget: `refetchInterval: 1_000` (1 second)
   - Dashboard stats: `refetchInterval: 60_000` (1 minute)
   - Regular entity lists: no polling (rely on mutation invalidation + window focus)

**Why this is sufficient:**
- Taskyn is a single-user personal tool. The user making changes through the web UI is the most common scenario.
- CLI changes are the edge case, caught by `refetchOnWindowFocus` when the user returns to the browser.
- Zero backend changes required.
- Immediate UI response to the user's own actions.

### Phase 2 (Future, if needed): SSE for Cross-Client Sync

If Taskyn evolves to need real-time sync between CLI and web UI (e.g., both open simultaneously), SSE is the recommended upgrade path.

**Why SSE over WebSockets:**
- Unidirectional (server-to-client) is all Taskyn needs — mutations go through REST
- Simpler to implement (auto-reconnect, standard HTTP)
- Works with all proxies and infrastructure
- `sse-starlette` is mature and well-supported

**Implementation approach:**
- FastAPI watches its own mutation endpoints and emits SSE events after successful operations
- For CLI changes: FastAPI could periodically poll the MCP server's activity log and emit events for new entries
- Frontend listens to SSE and calls `queryClient.invalidateQueries()` with the affected entity keys

**This phase should only be pursued if:**
- Users find `refetchOnWindowFocus` insufficient for catching CLI changes
- The tool becomes multi-user
- Real-time collaboration features are added

---

## Sources

- [TanStack Query Auto-Refetching Documentation](https://tanstack.com/query/v5/docs/framework/react/examples/auto-refetching)
- [TanStack Query Window Focus Refetching](https://tanstack.com/query/v5/docs/react/guides/window-focus-refetching)
- [TanStack Query Query Invalidation Guide](https://tanstack.com/query/v5/docs/framework/react/guides/query-invalidation)
- [TanStack Query streamedQuery Reference](https://tanstack.com/query/latest/docs/reference/streamedQuery)
- [TkDodo: Using WebSockets with React Query](https://tkdodo.eu/blog/using-web-sockets-with-react-query)
- [React Query and Server Side Events (Fragmented Thought)](https://fragmentedthought.com/blog/2025/react-query-caching-with-server-side-events)
- [TanStack Query WebSocket Discussion #1519](https://github.com/TanStack/query/discussions/1519)
- [TanStack Query SSE Discussion #418](https://github.com/TanStack/query/discussions/418)
- [TanStack Query streamedQuery Discussion #9065](https://github.com/TanStack/query/discussions/9065)
- [TanStack Query and WebSockets (LogRocket)](https://blog.logrocket.com/tanstack-query-websockets-real-time-react-data-fetching/)
- [sse-starlette on PyPI](https://pypi.org/project/sse-starlette/)
- [sse-starlette on GitHub](https://github.com/sysid/sse-starlette)
- [FastAPI WebSockets Documentation](https://fastapi.tiangolo.com/advanced/websockets/)
- [react-use-websocket on npm](https://www.npmjs.com/package/react-use-websocket)
- [fastapi-websocket-pubsub on GitHub](https://github.com/permitio/fastapi_websocket_pubsub)
- [SSE vs WebSockets Comparison (SoftwareMill)](https://softwaremill.com/sse-vs-websockets-comparing-real-time-communication-protocols/)
- [Polling vs Long Polling vs SSE vs WebSockets (AlgoMaster)](https://blog.algomaster.io/p/polling-vs-long-polling-vs-sse-vs-websockets-webhooks)
- [WebSockets vs SSE vs Polling vs WebRTC vs WebTransport (RxDB)](https://rxdb.info/articles/websockets-sse-polling-webrtc-webtransport.html)
- [Chrome Removing HTTP/2 Push](https://developer.chrome.com/blog/removing-push)
- [WebTransport Browser Support (Can I Use)](https://caniuse.com/webtransport)
- [EventSource Browser Support (Can I Use)](https://caniuse.com/eventsource)
- [EventSource MDN Documentation](https://developer.mozilla.org/en-US/docs/Web/API/EventSource)
