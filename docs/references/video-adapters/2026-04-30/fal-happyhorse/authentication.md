> ## Documentation Index
> Fetch the complete documentation index at: https://fal.ai/docs/llms.txt
> Use this file to discover all available pages before exploring further.

# Get Your API Key

> Create an API key to authenticate your requests to fal

Most requests to fal require authentication. You need an API key to call any model on the [Model APIs](/documentation/model-apis/overview), deploy your own with [Serverless](/documentation/serverless), or access any private or shared endpoint. The only exception is endpoints deployed with `app_auth = "public"`, which accept unauthenticated requests.

API keys are tied to accounts, not people. If you are working under a [team](/documentation/setting-up/teams), the key belongs to that team and all members share it. The [fal client libraries](/documentation/model-apis/inference/client-setup) read your key automatically from the `FAL_KEY` environment variable, so once it is set, every SDK call and CLI command authenticates without extra configuration.

## Create Your API Key

<Steps>
  <Step title="Go to the Dashboard">
    Navigate to [fal.ai/dashboard/keys](https://fal.ai/dashboard/keys)
  </Step>

  <Step title="Generate a Key">
    Click **Create Key** and give it a name you'll remember
  </Step>

  <Step title="Copy Your Key">
    Copy the key immediately. You will not be able to see it again
  </Step>
</Steps>

## Set Your API Key

Set your key as an environment variable:

<CodeGroup>
  ```bash macOS/Linux theme={null}
  export FAL_KEY="your-api-key-here"
  ```

  ```bash Windows (PowerShell) theme={null}
  $env:FAL_KEY="your-api-key-here"
  ```

  ```bash .env file theme={null}
  FAL_KEY=your-api-key-here
  ```
</CodeGroup>

Or configure it directly in code:

<CodeGroup>
  ```python Python theme={null}
  import fal_client

  # The client automatically reads FAL_KEY from environment
  # Or you can set it explicitly:
  import os
  os.environ["FAL_KEY"] = "your-api-key-here"
  ```

  ```javascript JavaScript theme={null}
  import { fal } from "@fal-ai/client";

  fal.config({
    credentials: "your-api-key-here",
  });
  ```
</CodeGroup>

<Tip>
  **Best practice**: Use environment variables instead of hardcoding keys in your code. This keeps your keys secure and makes it easy to use different keys for development and production.
</Tip>

## Key Scopes

When creating a key, you'll choose a scope that controls what the key can access:

| Scope     | Use Case                                                                                                                                                                                                                           |
| --------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **API**   | Calling any model on fal, including Model APIs and your own deployed endpoints. Also grants access to API-scoped [Platform APIs](/api-reference/platform-apis/index).                                                              |
| **ADMIN** | Everything in API, plus CLI operations (`fal deploy`, `fal run`), managing apps, and accessing admin-scoped [Platform APIs](/api-reference/platform-apis/index). Use this for [Serverless](/documentation/serverless) deployments. |

<Note>
  If you're not sure which to choose, start with **API** scope. You can always create an additional **ADMIN** key later if you need to deploy models.
</Note>

## Test Your Key

Verify your key works by making a simple API call:

```bash theme={null}
curl -X POST "https://fal.run/fal-ai/flux/schnell" \
  -H "Authorization: Key $FAL_KEY" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a cute cat"}'
```

If you see a response with an image URL, your key is working correctly.

## Team Keys

If you're part of a team, make sure to select your team in the top-left corner of the dashboard before creating a key. Keys are scoped to the account (personal or team) that created them.
