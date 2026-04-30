> ## Documentation Index
> Fetch the complete documentation index at: https://fal.ai/docs/llms.txt
> Use this file to discover all available pages before exploring further.

# Client Setup

> Install and configure the fal client library

The fal client is the easiest way to call models on fal. It handles [authentication](/documentation/model-apis/authentication), retries, and provides a clean API for all [inference methods](/documentation/model-apis/inference). Official clients are available for Python, JavaScript/TypeScript, Swift, Java, Kotlin, and Dart, and they all expose the same core methods (`subscribe`, `submit`, `run`, `stream`).

How you configure the client depends on where your code runs. In a server-side environment like a Python script, a Node.js backend, or a serverless function, you set your `FAL_KEY` as an environment variable and the client picks it up automatically. In a client-side environment like a React app running in the browser, you cannot use the API key directly because browser source code is visible to anyone. Instead, the fal client routes requests through a lightweight [proxy](/documentation/model-apis/inference/proxy-setup) on your server, which attaches the key before forwarding to fal. Both approaches are covered in the [Configuration](#configuration) section below.

## Installation

<CodeGroup>
  ```bash npm theme={null}
  npm install @fal-ai/client
  ```

  ```bash yarn theme={null}
  yarn add @fal-ai/client
  ```

  ```bash pnpm theme={null}
  pnpm add @fal-ai/client
  ```

  ```bash bun theme={null}
  bun add @fal-ai/client
  ```

  ```bash pip theme={null}
  pip install fal-client
  ```

  ```bash Flutter theme={null}
  flutter pub add fal_client
  ```

  ```swift Swift Package theme={null}
  .package(url: "https://github.com/fal-ai/fal-swift.git", from: "0.5.6")
  ```

  ```groovy Gradle (Java) theme={null}
  implementation 'ai.fal.client:fal-client:0.7.1'
  ```

  ```xml Maven (Java) theme={null}
  <dependency>
      <groupId>ai.fal.client</groupId>
      <artifactId>fal-client</artifactId>
      <version>0.7.1</version>
  </dependency>
  ```

  ```groovy Gradle (Kotlin) theme={null}
  implementation 'ai.fal.client:fal-client-kotlin:0.7.1'
  ```

  ```xml Maven (Kotlin) theme={null}
  <dependency>
      <groupId>ai.fal.client</groupId>
      <artifactId>fal-client-kotlin</artifactId>
      <version>0.7.1</version>
  </dependency>
  ```
</CodeGroup>

<Note>
  **Java Async Support** -- If your code relies on asynchronous operations via `CompletableFuture` or `Future`, use the `ai.fal.client:fal-client-async` artifact instead.
</Note>

***

## Configuration

### Server-side (Python, Node.js)

The simplest path. Set your API key as an environment variable and the client picks it up automatically:

```bash theme={null}
export FAL_KEY="your-api-key-here"
```

No additional configuration is needed. The client reads `FAL_KEY` from the environment on import:

<CodeGroup>
  ```python Python theme={null}
  import fal_client

  result = fal_client.run("fal-ai/flux/schnell", arguments={
      "prompt": "a sunset"
  })
  ```

  ```javascript JavaScript theme={null}
  import { fal } from "@fal-ai/client";

  const result = await fal.run("fal-ai/flux/schnell", {
    input: { prompt: "a sunset" }
  });
  ```
</CodeGroup>

In some environments (serverless functions, containers) you may not have access to shell environment variables. In those cases you can set credentials explicitly in code:

<CodeGroup>
  ```python Python theme={null}
  import os
  os.environ["FAL_KEY"] = "your-api-key-here"

  import fal_client
  ```

  ```javascript JavaScript theme={null}
  import { fal } from "@fal-ai/client";

  fal.config({
    credentials: "your-api-key-here"
  });
  ```
</CodeGroup>

### Client-side (Browser, React, Next.js)

When building web apps, your API key cannot live in browser code because browser source is visible to anyone. Instead, the fal client routes requests through a lightweight proxy on your server that attaches the key before forwarding to fal. Your API key stays on the server, and all client methods (`subscribe`, `submit`, `run`, `stream`) work transparently through the proxy.

The setup has two parts: create a proxy route on your server and point the client at it. Here is the quickest path using Next.js:

```bash theme={null}
npm install @fal-ai/server-proxy
```

Create `app/api/fal/proxy/route.ts` (App Router):

```typescript theme={null}
import { createRouteHandler } from "@fal-ai/server-proxy/nextjs";

export const { GET, POST, PUT } = createRouteHandler();
```

Then configure the client in your frontend code:

```typescript theme={null}
import { fal } from "@fal-ai/client";

fal.config({
  proxyUrl: "/api/fal/proxy"
});

const result = await fal.subscribe("fal-ai/flux/schnell", {
  input: { prompt: "a sunset" }
});
```

Make sure `FAL_KEY` is set as an environment variable on your server. The proxy reads it from the environment, just like the server-side setup above.

<Card title="Proxy Setup" icon="arrow-right" href="/documentation/model-apis/inference/proxy-setup">
  Pages Router, Vercel, Express, custom frameworks, and how the proxy works under the hood
</Card>

***

## Making Your First Call

Once configured, you can call any model:

<CodeGroup>
  ```python Python theme={null}
  import fal_client

  result = fal_client.subscribe("fal-ai/flux/schnell", arguments={
      "prompt": "a futuristic cityscape at sunset",
      "image_size": "landscape_16_9"
  })

  print(result["images"][0]["url"])
  ```

  ```python Python (async) theme={null}
  import asyncio
  import fal_client

  async def main():
      result = await fal_client.subscribe_async(
          "fal-ai/flux/schnell",
          arguments={
              "prompt": "a futuristic cityscape at sunset",
              "image_size": "landscape_16_9"
          },
      )
      print(result["images"][0]["url"])

  asyncio.run(main())
  ```

  ```javascript JavaScript theme={null}
  import { fal } from "@fal-ai/client";

  const result = await fal.subscribe("fal-ai/flux/schnell", {
    input: {
      prompt: "a futuristic cityscape at sunset",
      image_size: "landscape_16_9"
    }
  });

  console.log(result.data.images[0].url);
  ```

  ```swift Swift theme={null}
  import FalClient

  let result = try await fal.subscribe(
      to: "fal-ai/flux/schnell",
      input: [
          "prompt": "a futuristic cityscape at sunset",
          "image_size": "landscape_16_9"
      ],
      includeLogs: true
  ) { update in
      if case let .inProgress(logs) = update {
          print(logs)
      }
  }
  ```

  ```java Java theme={null}
  import ai.fal.client.*;
  import ai.fal.client.queue.*;

  var fal = FalClient.withEnvCredentials();

  var result = fal.subscribe("fal-ai/flux/schnell",
      SubscribeOptions.<JsonObject>builder()
          .input(Map.of(
              "prompt", "a futuristic cityscape at sunset",
              "image_size", "landscape_16_9"
          ))
          .logs(true)
          .resultType(JsonObject.class)
          .build()
  );
  ```

  ```kotlin Kotlin theme={null}
  import ai.fal.client.kt

  val fal = createFalClient()

  val result = fal.subscribe("fal-ai/flux/schnell",
      mapOf(
          "prompt" to "a futuristic cityscape at sunset",
          "image_size" to "landscape_16_9"
      ),
      options = SubscribeOptions(logs = true)
  ) { update ->
      if (update is QueueStatus.InProgress) {
          println(update.logs)
      }
  }
  ```

  ```dart Dart (Flutter) theme={null}
  import 'package:fal_client/fal_client.dart';

  final fal = FalClient.withCredentials("FAL_KEY");

  final output = await fal.subscribe("fal-ai/flux/schnell",
    input: {
      "prompt": "a futuristic cityscape at sunset",
      "image_size": "landscape_16_9"
    },
    logs: true,
    onQueueUpdate: (update) { print(update); }
  );

  print(output.data);
  ```
</CodeGroup>

***

## Client Methods

| Method        | How it works                              | Uses Queue |
| ------------- | ----------------------------------------- | ---------- |
| `run()`       | Direct synchronous call                   | No         |
| `subscribe()` | Blocks until result, polls automatically  | Yes        |
| `submit()`    | Returns immediately, poll or use webhooks | Yes        |
| `stream()`    | Progressive output via SSE                | No         |
| `realtime()`  | WebSocket connection                      | No         |

Every method in the Python SDK has an async counterpart with an `_async` suffix (e.g., `subscribe_async`, `submit_async`, `run_async`, `stream_async`, `realtime_async`). Use these when working with `asyncio`.

***

## API References and Support

<CardGroup cols={3}>
  <Card title="JavaScript / TypeScript" icon="js" href="https://fal-ai.github.io/fal-js/reference">
    API docs and [GitHub repo](https://github.com/fal-ai/fal-js)
  </Card>

  <Card title="Python" icon="python" href="https://fal-ai.github.io/fal/client">
    API docs and [GitHub repo](https://github.com/fal-ai/fal)
  </Card>

  <Card title="Swift (iOS)" icon="swift" href="https://swiftpackageindex.com/fal-ai/fal-swift/documentation/falclient">
    API docs and [GitHub repo](https://github.com/fal-ai/fal-swift)
  </Card>

  <Card title="Java / Kotlin" icon="java" href="https://fal-ai.github.io/fal-java/fal-client/index.html">
    API docs and [GitHub repo](https://github.com/fal-ai/fal-java)
  </Card>

  <Card title="Dart (Flutter)" icon="flutter" href="https://pub.dev/documentation/fal_client/latest">
    API docs and [GitHub repo](https://github.com/fal-ai/fal-dart)
  </Card>

  <Card title="Community" icon="discord" href="https://discord.gg/fal-ai">
    Get help on Discord
  </Card>
</CardGroup>
