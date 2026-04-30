> ## Documentation Index
> Fetch the complete documentation index at: https://fal.ai/docs/llms.txt
> Use this file to discover all available pages before exploring further.

# Asynchronous Inference

> The recommended way to call models on fal

Asynchronous inference is the recommended way to call models on fal. You submit a request to a persistent [queue](/documentation/model-apis/inference/reliability), then retrieve results later by polling for status or receiving them via [webhook](/documentation/model-apis/inference/webhooks). If you prefer a simpler blocking call that handles polling for you automatically, use [subscribe](/documentation/model-apis/inference/synchronous) instead.

The async approach gives you full control over the request lifecycle. You can submit many requests in parallel and process them as they complete, get real-time visibility into queue position and [runner](/documentation/deployment/runners) logs, and rely on [automatic retries](/documentation/serverless/reliability/retries) when failures occur. All of this works identically whether you are calling a pre-trained model from the gallery or your own app deployed on [Serverless](/documentation/serverless). This page covers the full queue API: submitting requests, checking status, streaming updates, retrieving results, cancelling, and configuring webhooks.

***

## How the Queue Works

When you submit a request to `queue.fal.run`, it enters a persistent, durable queue. The request moves through three states before completion:

### Request Lifecycle

| Status        | SDK Type (Python / JS)                     | What is happening                                                      |
| ------------- | ------------------------------------------ | ---------------------------------------------------------------------- |
| `IN_QUEUE`    | `Queued(position)` / `"IN_QUEUE"`          | Request is received and stored. Waiting for an available runner.       |
| `IN_PROGRESS` | `InProgress(logs)` / `"IN_PROGRESS"`       | fal's dispatcher has routed the request to a runner.                   |
| `COMPLETED`   | `Completed(logs, metrics)` / `"COMPLETED"` | Result is stored and available for retrieval, or sent to your webhook. |

See the [Python SDK reference](/api-reference/client-libraries/python/fal_client#status) or [JavaScript SDK reference](/api-reference/client-libraries/javascript/types.common) for the full type definitions.

### Key Guarantees

Requests in the queue are never dropped. If no runners are available, your request waits while fal [scales up new runners](/documentation/deployment/scale-your-application) automatically. There is no queue size limit. If a runner fails during processing (503, 504, or a connection error), the request is automatically re-queued and [retried](/documentation/model-apis/inference/reliability) up to 10 times. As demand grows, runners scale up to match. When demand drops, they scale back down, so you only pay for compute you use.

***

## Submit a Request

Use `submit` to send a request to the queue and return immediately. In Python, `submit()` returns a `SyncRequestHandle` object with methods for status, result, and cancel (`submit_async()` returns an `AsyncRequestHandle`). In JavaScript, `submit()` returns an object with the `request_id`, and you use separate `fal.queue.*` functions. In the REST API, the response includes URLs for each operation.

<CodeGroup>
  ```python Python theme={null}
  import fal_client

  handler = fal_client.submit("fal-ai/flux/schnell", arguments={
      "prompt": "a sunset over mountains"
  })

  print(handler.request_id)
  ```

  ```python Python (async) theme={null}
  import asyncio
  import fal_client

  async def main():
      handler = await fal_client.submit_async("fal-ai/flux/schnell", arguments={
          "prompt": "a sunset over mountains"
      })
      print(handler.request_id)

  asyncio.run(main())
  ```

  ```javascript JavaScript theme={null}
  import { fal } from "@fal-ai/client";

  const { request_id } = await fal.queue.submit("fal-ai/flux/schnell", {
    input: { prompt: "a sunset over mountains" },
  });

  console.log(request_id);
  ```

  ```bash cURL theme={null}
  curl -X POST https://queue.fal.run/fal-ai/flux/schnell \
    -H "Authorization: Key $FAL_KEY" \
    -H "Content-Type: application/json" \
    -d '{"prompt": "a sunset over mountains"}'
  ```
</CodeGroup>

The submit response includes the `request_id` and convenience URLs for tracking the request:

```json theme={null}
{
  "request_id": "764cabcf-b745-4b3e-ae38-1200304cf45b",
  "response_url": "https://queue.fal.run/fal-ai/flux/schnell/requests/764cabcf.../response",
  "status_url": "https://queue.fal.run/fal-ai/flux/schnell/requests/764cabcf.../status",
  "cancel_url": "https://queue.fal.run/fal-ai/flux/schnell/requests/764cabcf.../cancel",
  "queue_position": 0
}
```

Store the `request_id` if you need to check status or retrieve results later, even from a different process.

***

## Check Status

Poll for the current state of the request. Pass `with_logs=True` (Python) or `logs: true` (JS) or `?logs=1` (REST) to include runner log output.

<CodeGroup>
  ```python Python theme={null}
  status = handler.status(with_logs=True)
  if isinstance(status, fal_client.Queued):
      print(f"Position: {status.position}")
  elif isinstance(status, fal_client.InProgress):
      for log in status.logs:
          print(log["message"])
  ```

  ```python Python (async) theme={null}
  status = await handler.status(with_logs=True)
  if isinstance(status, fal_client.Queued):
      print(f"Position: {status.position}")
  elif isinstance(status, fal_client.InProgress):
      for log in status.logs:
          print(log["message"])
  ```

  ```javascript JavaScript theme={null}
  const status = await fal.queue.status("fal-ai/flux/schnell", {
    requestId: request_id,
    logs: true,
  });
  if (status.status === "IN_QUEUE") {
    console.log(`Position: ${status.queue_position}`);
  } else if (status.status === "IN_PROGRESS") {
    status.logs?.forEach(log => console.log(log.message));
  }
  ```

  ```bash cURL theme={null}
  curl "https://queue.fal.run/fal-ai/flux/schnell/requests/{request_id}/status?logs=1" \
    -H "Authorization: Key $FAL_KEY"
  ```
</CodeGroup>

The response shape depends on the current status:

**IN\_QUEUE** -- waiting for an available runner:

```json theme={null}
{
  "status": "IN_QUEUE",
  "request_id": "764cabcf-...",
  "queue_position": 2,
  "response_url": "https://queue.fal.run/.../response"
}
```

**IN\_PROGRESS** -- a runner is processing the request:

```json theme={null}
{
  "status": "IN_PROGRESS",
  "request_id": "764cabcf-...",
  "response_url": "https://queue.fal.run/.../response",
  "logs": [
    {"message": "Loading model weights...", "timestamp": "2026-02-17T10:30:01.123Z"},
    {"message": "Generating image...", "timestamp": "2026-02-17T10:30:02.456Z"}
  ]
}
```

**COMPLETED** -- the result is ready to retrieve:

```json theme={null}
{
  "status": "COMPLETED",
  "request_id": "764cabcf-...",
  "response_url": "https://queue.fal.run/.../response",
  "logs": [
    {"message": "Done.", "timestamp": "2026-02-17T10:30:05.789Z"}
  ],
  "metrics": {"inference_time": 3.42}
}
```

| Field                    | Description                                                                                                                                                                |
| ------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `queue_position`         | Number of requests ahead of yours (only when `IN_QUEUE`)                                                                                                                   |
| `logs`                   | Array of log messages from the runner (when logs are enabled)                                                                                                              |
| `metrics.inference_time` | Seconds the runner spent processing (only when `COMPLETED`)                                                                                                                |
| `error`                  | A human-readable error message, present only if the request failed (only when `COMPLETED`)                                                                                 |
| `error_type`             | A machine-readable error type string, present only if the request failed. See [Request Error Types](/documentation/model-apis/request-errors) for the full list of values. |

***

## Stream Status Updates

Instead of polling manually, you can stream status updates continuously until the request completes. In Python, `iter_events()` polls and yields each status. In JavaScript, `streamStatus()` opens an SSE connection.

<CodeGroup>
  ```python Python theme={null}
  for event in handler.iter_events(with_logs=True):
      if isinstance(event, fal_client.InProgress):
          for log in event.logs:
              print(log["message"])

  result = handler.get()
  ```

  ```python Python (async) theme={null}
  async for event in handler.iter_events(with_logs=True):
      if isinstance(event, fal_client.InProgress):
          for log in event.logs:
              print(log["message"])

  result = await handler.get()
  ```

  ```javascript JavaScript theme={null}
  const stream = await fal.queue.streamStatus("fal-ai/flux/schnell", {
    requestId: request_id,
    logs: true,
  });

  for await (const status of stream) {
    if (status.status === "IN_PROGRESS") {
      status.logs?.forEach(log => console.log(log.message));
    } else if (status.status === "COMPLETED") {
      console.log(`Done in ${status.metrics?.inference_time}s`);
    }
  }
  ```

  ```bash cURL theme={null}
  curl "https://queue.fal.run/fal-ai/flux/schnell/requests/{request_id}/status/stream?logs=1" \
    -H "Authorization: Key $FAL_KEY"
  ```
</CodeGroup>

The REST streaming endpoint returns `text/event-stream` with SSE events. Each event is a JSON status object in the same format as the polling endpoint. The connection stays open until the status reaches `COMPLETED`.

***

## Get the Result

Retrieve the final output once the request is complete. In Python, `get()` polls internally until `Completed` then fetches the response. In JavaScript, call `fal.queue.result()` after the status is `COMPLETED`.

<CodeGroup>
  ```python Python theme={null}
  result = handler.get()
  print(result["images"][0]["url"])
  ```

  ```python Python (async) theme={null}
  result = await handler.get()
  print(result["images"][0]["url"])
  ```

  ```javascript JavaScript theme={null}
  const result = await fal.queue.result("fal-ai/flux/schnell", {
    requestId: request_id,
  });
  console.log(result.data.images[0].url);
  ```

  ```bash cURL theme={null}
  curl https://queue.fal.run/fal-ai/flux/schnell/requests/{request_id} \
    -H "Authorization: Key $FAL_KEY"
  ```
</CodeGroup>

The result structure is **model-specific**. For example, an image model returns:

```json theme={null}
{
  "images": [
    {
      "url": "https://v3.fal.media/files/rabbit/abc123.png",
      "width": 1024,
      "height": 1024,
      "content_type": "image/png"
    }
  ],
  "prompt": "a sunset over mountains",
  "seed": 42,
  "has_nsfw_concepts": [false]
}
```

Video generation models return a `video` object, and audio/speech models return an `audio_url` or `audio` object. Check the model's API page (e.g., [FLUX.1 schnell API](https://fal.ai/models/fal-ai/flux/schnell/api)) for the exact output schema.

<Note>
  All media URLs in responses (`https://v3.fal.media/...`) are publicly accessible and subject to your [media expiration settings](/documentation/model-apis/media-expiration). Download files you need to keep before they expire.
</Note>

***

## Cancel a Request

Cancel a request. What happens depends on the request's state:

* **Still in the queue (IN\_QUEUE):** The request is removed immediately and is never processed.
* **Already being processed (IN\_PROGRESS):** fal sends a cancellation signal to the runner. The request may still complete if the app does not handle cancellation. Whether the running code actually stops depends on whether the app has implemented a cancel endpoint.

If you are deploying your own serverless app and want in-progress requests to stop cleanly when cancelled, see [Handle Cancellations](/documentation/development/handle-cancellations) for how to implement a cancel endpoint.

<CodeGroup>
  ```python Python theme={null}
  handler.cancel()
  ```

  ```python Python (async) theme={null}
  await handler.cancel()
  ```

  ```javascript JavaScript theme={null}
  await fal.queue.cancel("fal-ai/flux/schnell", {
    requestId: request_id,
  });
  ```

  ```bash cURL theme={null}
  curl -X PUT https://queue.fal.run/fal-ai/flux/schnell/requests/{request_id}/cancel \
    -H "Authorization: Key $FAL_KEY"
  ```
</CodeGroup>

The response includes both an HTTP status code and a JSON body:

| HTTP Status       | JSON Body                              | Meaning                                                                           |
| ----------------- | -------------------------------------- | --------------------------------------------------------------------------------- |
| `202 Accepted`    | `{"status": "CANCELLATION_REQUESTED"}` | Cancel accepted. The request may still complete if it was already mid-processing. |
| `400 Bad Request` | `{"status": "ALREADY_COMPLETED"}`      | The request already finished before the cancel arrived.                           |
| `404 Not Found`   | `{"status": "NOT_FOUND"}`              | No request exists with that ID.                                                   |

When using the SDK, `handler.cancel()` succeeds silently on `202` and raises an exception on `400` or `404`.

***

## Webhooks

Instead of polling, configure fal to POST results directly to your server when a request completes.

<CodeGroup>
  ```python Python theme={null}
  import fal_client

  handler = fal_client.submit("fal-ai/flux/schnell",
      arguments={"prompt": "a sunset over mountains"},
      webhook_url="https://your-server.com/webhook",
  )

  print(f"Request submitted: {handler.request_id}")
  ```

  ```python Python (async) theme={null}
  import fal_client

  handler = await fal_client.submit_async("fal-ai/flux/schnell",
      arguments={"prompt": "a sunset over mountains"},
      webhook_url="https://your-server.com/webhook",
  )

  print(f"Request submitted: {handler.request_id}")
  ```

  ```javascript JavaScript theme={null}
  const { request_id } = await fal.queue.submit("fal-ai/flux/schnell", {
    input: { prompt: "a sunset over mountains" },
    webhookUrl: "https://your-server.com/webhook",
  });
  ```

  ```bash cURL theme={null}
  curl -X POST "https://queue.fal.run/fal-ai/flux/schnell?fal_webhook=https://your-server.com/webhook" \
    -H "Authorization: Key $FAL_KEY" \
    -H "Content-Type: application/json" \
    -d '{"prompt": "a sunset over mountains"}'
  ```
</CodeGroup>

When complete, fal sends a POST to your webhook URL:

```json theme={null}
{
  "request_id": "abc123",
  "gateway_request_id": "abc123",
  "status": "OK",
  "payload": {
    "images": [
      {"url": "https://fal.media/files/...", "width": 1024, "height": 1024}
    ]
  }
}
```

The webhook `status` is `"OK"` for successful responses (HTTP 200) or `"ERROR"` for failures -- this is different from the queue status values (`IN_QUEUE`, `IN_PROGRESS`, `COMPLETED`). Return 200 quickly to acknowledge the webhook. fal may retry failed deliveries, so use `request_id` for idempotency. See [Webhooks](/documentation/model-apis/inference/webhooks) for full details on payload format, retries, and signature verification.

***

## `submit()` Parameters

### `path`

Endpoint path appended to the model ID. Most models expose a single root endpoint, so you can leave this empty. Use it when a model or your own app defines additional endpoints at sub-paths.

<CodeGroup>
  ```python Python theme={null}
  handler = fal_client.submit("fal-ai/nano-banana-2", arguments={...}, path="/custom-endpoint")
  ```

  ```javascript JavaScript theme={null}
  const { request_id } = await fal.queue.submit("fal-ai/nano-banana-2/custom-endpoint", {
    input: {...},
  });
  ```
</CodeGroup>

In JavaScript, append the path directly to the endpoint string.

### `start_timeout`

Server-side deadline in seconds, sent as the `X-Fal-Request-Timeout` header. This sets an absolute wall-clock deadline, computed once when the request is submitted. The server checks this deadline before processing begins. If the deadline has passed, the server returns a 504 without processing the request.

If a runner picks up the request but **fails** (e.g., returns 503 or crashes), the request goes back to the queue for a retry. Because the deadline is a fixed timestamp, all elapsed time -- including time spent on the failed attempt -- counts against the same original deadline. If the deadline is reached before any runner successfully starts processing, the server returns `504 Gateway Timeout` with the header `X-Fal-Request-Timeout-Type: user` and no further retries occur.

<Note>
  This timeout does not limit how long inference takes. Once a runner starts processing, the deadline is not enforced and the request runs to completion. This is different from `request_timeout`, which limits each individual processing attempt and actively kills the runner if exceeded. The maximum inference time is controlled by the app's `request_timeout` setting (default 3600s), which is configured by the app developer, not the caller. If you need a total client-side deadline that includes processing time, use [`client_timeout`](#client_timeout-subscribe-only) on `subscribe()`.
</Note>

For a full comparison of timeout mechanisms, see [Timeouts and Retries](/documentation/serverless/reliability/retries#timeouts-and-retries).

<CodeGroup>
  ```python Python theme={null}
  handler = fal_client.submit("fal-ai/nano-banana-2", arguments={...}, start_timeout=30)
  ```

  ```javascript JavaScript theme={null}
  const { request_id } = await fal.queue.submit("fal-ai/nano-banana-2", {
    input: {...},
    startTimeout: 30,
  });
  ```
</CodeGroup>

### `hint`

Routing hint sent as the `X-Fal-Runner-Hint` header. When you pass a hint string, fal tries to route the request to the same runner that handled a previous request with the same hint. This is useful for session affinity -- for example, keeping requests pinned to a runner that already has a specific model or adapter loaded in memory. For serverless apps that serve multiple models, your app can implement `provide_hints()` on the server side to tell fal what each runner is specialized for. See [Optimize Routing Behavior](/documentation/serverless/optimizations/optimize-routing-behavior) for the full pattern.

<CodeGroup>
  ```python Python theme={null}
  handler = fal_client.submit("fal-ai/nano-banana-2", arguments={...}, hint="user-session-abc")
  ```

  ```javascript JavaScript theme={null}
  const { request_id } = await fal.queue.submit("fal-ai/nano-banana-2", {
    input: {...},
    hint: "user-session-abc",
  });
  ```
</CodeGroup>

### `priority`

Queue priority for the request, sent as the `X-Fal-Queue-Priority` header. Accepts `"normal"` (default) or `"low"`.

Priority applies to the **per-endpoint queue** -- every request to the same endpoint shares one queue, regardless of who sent it. A low-priority request sits behind all normal-priority requests in that queue and is only processed once no normal requests are waiting. This means setting `priority="low"` on a shared model API (like `fal-ai/flux/dev`) deprioritizes your request relative to **all other users** of that model.

Low priority is most useful for your own deployed serverless apps where you control all traffic. For example, you might submit user-facing requests at normal priority and background batch jobs at low priority so interactive requests are always served first.

<CodeGroup>
  ```python Python theme={null}
  handler = fal_client.submit("your-username/your-app", arguments={...}, priority="low")
  ```

  ```javascript JavaScript theme={null}
  const { request_id } = await fal.queue.submit("your-username/your-app", {
    input: {...},
    priority: "low",
  });
  ```
</CodeGroup>

### `webhook_url`

URL where fal sends a POST request with the result when processing completes. When set, you don't need to poll for status -- the result arrives at your server automatically. The webhook payload includes the `request_id`, `status`, and the full model output. See [Webhooks](/documentation/model-apis/inference/webhooks) for payload format, retries, and signature verification.

<CodeGroup>
  ```python Python theme={null}
  handler = fal_client.submit(
      "fal-ai/nano-banana-2",
      arguments={"prompt": "a sunset"},
      webhook_url="https://your-server.com/api/fal/webhook",
  )
  ```

  ```javascript JavaScript theme={null}
  const { request_id } = await fal.queue.submit("fal-ai/nano-banana-2", {
    input: { prompt: "a sunset" },
    webhookUrl: "https://your-server.com/api/fal/webhook",
  });
  ```
</CodeGroup>

### `headers`

Additional HTTP headers passed with the request. Use this to set [platform-level headers](/documentation/model-apis/common-parameters) like `X-Fal-Store-IO` (disable payload storage), `X-Fal-No-Retry` (disable retries), or `X-Fal-Object-Lifecycle-Preference` (control media expiration).

<CodeGroup>
  ```python Python theme={null}
  handler = fal_client.submit("fal-ai/nano-banana-2", arguments={...}, headers={"X-Fal-No-Retry": "1"})
  ```

  ```javascript JavaScript theme={null}
  const { request_id } = await fal.queue.submit("fal-ai/nano-banana-2", {
    input: {...},
    headers: { "X-Fal-No-Retry": "1" },
  });
  ```
</CodeGroup>

***

## `subscribe()` Parameters

`subscribe()` accepts all of the `submit()` parameters above (`path`, `start_timeout`, `hint`, `priority`, `headers`), plus the following. In JavaScript, `fal.subscribe()` supports `priority`, `headers`, and `webhookUrl` as named options; for `hint`, use [`fal.queue.submit()`](#hint) directly.

### `client_timeout` / `timeout`

Client-side deadline that limits the total time the client waits for the result, including queue wait and processing. When exceeded, the client stops polling and raises an error. The request may still be processing on the server. In Python the parameter is called `client_timeout` and accepts seconds. In JavaScript the parameter is called `timeout` and accepts milliseconds.

<CodeGroup>
  ```python Python theme={null}
  result = fal_client.subscribe(
      "fal-ai/flux/dev",
      arguments={"prompt": "a cat"},
      client_timeout=60,  # client gives up after 60 seconds
  )
  ```

  ```javascript JavaScript theme={null}
  const result = await fal.subscribe("fal-ai/flux/dev", {
    input: { prompt: "a cat" },
    timeout: 60000,  // client gives up after 60000 milliseconds
  });
  ```
</CodeGroup>

**Interaction with `start_timeout` (Python):** If you set `client_timeout` without setting `start_timeout`, the SDK automatically sets `start_timeout = client_timeout` so the server also respects your deadline. If you explicitly set `start_timeout` to a value larger than `client_timeout`, the SDK emits a warning because the server-side timeout would never be reached before the client gives up.

| Timeout                                    | Enforced by   | Scope                                                                       | Affects server                     | Use when                                                   |
| ------------------------------------------ | ------------- | --------------------------------------------------------------------------- | ---------------------------------- | ---------------------------------------------------------- |
| `start_timeout` / `X-Fal-Request-Timeout`  | Server        | Absolute deadline across entire lifecycle (enforced before processing only) | Yes (returns 504, stops retries)   | You want the server to cancel the request before it starts |
| `client_timeout` (Python) / `timeout` (JS) | Client        | Total wall-clock time including processing                                  | No (request may continue)          | You want a local deadline without affecting the server     |
| `request_timeout`                          | App developer | Per-attempt processing limit (resets on each retry)                         | Yes (kills runner, triggers retry) | Set by the app to cap individual inference time            |

***

## Disabling Retries

By default, fal [automatically retries](/documentation/serverless/reliability/retries) queue requests that fail due to server errors, timeouts, or rate limits. If you need to disable retries for a specific request, pass the `X-Fal-No-Retry` header when submitting:

```bash theme={null}
curl -X POST "https://queue.fal.run/fal-ai/flux/dev" \
  -H "Authorization: Key $FAL_KEY" \
  -H "Content-Type: application/json" \
  -H "X-Fal-No-Retry: 1" \
  -d '{"prompt": "a cat"}'
```

When this header is set to `1`, `true`, or `yes`, fal will not retry the request even if it fails due to a retryable error.
