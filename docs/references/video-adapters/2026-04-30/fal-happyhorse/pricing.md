> ## Documentation Index
> Fetch the complete documentation index at: https://fal.ai/docs/llms.txt
> Use this file to discover all available pages before exploring further.

# Pricing

> How billing works for fal Model APIs.

When you call a pre-trained model through fal's Model APIs, you are billed based on the output you generate. Each model on fal has its own pricing and billing unit, visible on the model's page in the [gallery](https://fal.ai/models) and at [fal.ai/pricing](https://fal.ai/pricing). You pay only for successful outputs, and you are never charged for server errors or time spent waiting in the queue.

fal uses a prepaid credit model. You purchase credits in advance and they are drawn down as you use the platform. Credits fund both Model API usage and your [concurrency limit](/documentation/model-apis/concurrency-limits), which scales with your purchase history. If you deploy your own applications on [Serverless](/documentation/serverless), billing works differently and is covered on the [Serverless pricing](/documentation/serverless/pricing) page.

## Per-Model Pricing

The billing unit varies by model type. Image generation models typically charge per image or per megapixel of output, where higher resolutions cost proportionally more. Video generation models charge per second of generated video or a flat rate per video. Other models, such as LLMs or audio models, charge per request or per output unit specific to the model.

Models that do not have a fixed per-output price fall back to per-second billing based on the GPU [machine type](/documentation/deployment/machine-types) used to run the request. This fallback applies to some less common models and to your own Serverless endpoints.

| Model type       | Billing unit                   | How it works                                              |
| ---------------- | ------------------------------ | --------------------------------------------------------- |
| Image generation | Per image or per megapixel     | Flat rate per image, or proportional to output resolution |
| Video generation | Per second or per video        | Per second of generated video, or flat rate per video     |
| Other models     | Per request or compute seconds | Flat rate per request, or per-second billing by GPU type  |

<Note>
  Prices vary by model and may change. Check the model's page or the [pricing page](https://fal.ai/pricing) for current rates. You can also query prices programmatically through the [Platform APIs](/api-reference/platform-apis/for-models).
</Note>

## What You Pay For

You are billed for successfully generated outputs. The billing unit (image, megapixel, video second, etc.) is defined per model. When a model does not have a fixed output price, billing falls back to per-second pricing based on the GPU machine type that processed your request.

## What You Are Not Charged For

Server errors are never billed. If a request fails with an HTTP 500 or higher status code, no charge is incurred. Time spent waiting in the [queue](/documentation/model-apis/inference/queue) before a runner starts processing your request is also free. Only the actual inference work counts toward your bill.

## Checking Prices Programmatically

You can retrieve pricing information for any model endpoint through the [Platform APIs](/api-reference/platform-apis/for-models). This is useful for building cost estimation into your application or comparing rates across models.

```bash theme={null}
curl "https://api.fal.ai/v1/models/pricing?endpoint_id=fal-ai/flux/dev" \
  -H "Authorization: Key $FAL_KEY"
```

The response includes the billing unit and unit price for each endpoint:

```json theme={null}
{
  "prices": [
    {
      "endpoint_id": "fal-ai/flux/dev",
      "unit_price": 0.025,
      "unit": "image",
      "currency": "USD"
    }
  ],
  "next_cursor": null,
  "has_more": false
}
```

You can also estimate costs before running a request, query usage line items with unit quantities and prices, and access time-bucketed analytics for spend tracking.

<Card title="Platform APIs for Models" icon="arrow-right" href="/api-reference/platform-apis/for-models">
  Full reference for pricing, usage, and analytics APIs
</Card>

## Enterprise Pricing

Enterprise customers can receive custom per-endpoint pricing and volume discounts. These are configured per account and apply automatically to all requests. Contact the [sales team](https://fal.ai/enterprise#contact-sales) for details.

## Monitoring Your Usage

The billing dashboard shows your overall spend, invoices, and payment history. For per-model cost breakdowns and request-level detail, use the usage and analytics Platform APIs, or check the billing reports available in the dashboard.

<CardGroup cols={2}>
  <Card title="Dashboard Billing" icon="chart-line" href="https://fal.ai/dashboard/billing">
    View your overall spend, invoices, and payment methods
  </Card>

  <Card title="Concurrency Limits" icon="gauge" href="/documentation/model-apis/concurrency-limits">
    Understand how credit purchases affect your concurrency limit
  </Card>
</CardGroup>
