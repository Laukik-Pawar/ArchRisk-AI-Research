# OpenTelemetry Astronomy Shop - service documentation (concatenated from repo READMEs)
## Welcome to the OpenTelemetry Astronomy Shop Demo

This repository contains the OpenTelemetry Astronomy Shop, a microservice-based
distributed system intended to illustrate the implementation of OpenTelemetry in
a near real-world environment.

Our goals are threefold:

- Provide a realistic example of a distributed system that can be used to
  demonstrate OpenTelemetry instrumentation and observability.
- Build a base for vendors, tooling authors, and others to extend and
  demonstrate their OpenTelemetry integrations.
- Create a living example for OpenTelemetry contributors to use for testing new
  versions of the API, SDK, and other components or enhancements.

We've already made [huge
progress](https://github.com/open-telemetry/opentelemetry-demo/blob/main/CHANGELOG.md),
and development is ongoing. We hope to represent the full feature set of
OpenTelemetry across its languages in the future.

If you'd like to help (**which we would love**), check out our [contributing
guidance](./CONTRIBUTING.md).

If you'd like to extend this demo or maintain a fork of it, read our
[fork guidance](https://opentelemetry.io/docs/demo/forking/).


<!-- source: src/accounting/README.md -->
# Accounting Service

This service consumes new orders from a Kafka topic.

## Local Build

To build the service binary, navigate to the root directory of the project and run:

```sh
make generate-protobuf
```

Navigate back to `src/accounting` and execute:

```sh
dotnet build
```

## Docker Build

From the root directory, run:

```sh
docker compose build accounting
```

## Bump dependencies

To bump all dependencies run in Package manager:

```sh
Update-Package -ProjectName Accounting
```

<!-- source: src/ad/README.md -->
# Ad Service

The Ad service provides advertisement based on context keys. If no context keys
are provided then it returns random ads.

## Building Locally

The Ad service requires at least JDK 21 to build and uses gradlew to
compile/install/distribute. Gradle wrapper is already part of the source code.
To build Ad Service, run:

```sh
./gradlew installDist
```

It will create an executable script
`src/ad/build/install/oteldemo/bin/Ad`.

To run the Ad Service:

```sh
export AD_PORT=8080
export FEATURE_FLAG_GRPC_SERVICE_ADDR=featureflagservice:50053
./build/install/opentelemetry-demo-ad/bin/Ad
```

### Upgrading Gradle

If you need to upgrade the version of gradle then run

```sh
./gradlew wrapper --gradle-version <new-version>
```

## Building Docker

From the root of `opentelemetry-demo`, run:

```sh
docker build --file ./src/ad/Dockerfile ./
```

## Custom metrics: bridging Prometheus to OpenTelemetry

The Ad service intentionally emits custom metrics in **two different ways**:

1. **OpenTelemetry SDK** (recommended): `adRequestsCounter`
   (`demo.ad.requests`) is created via `GlobalOpenTelemetry.getMeter(...)`
   and exported to the OTel Collector over OTLP.
2. **Prometheus client library**: `adsServedCounter`
   (`demo_ad_served_total{category}`) is created with the
   `io.prometheus:prometheus-metrics-core` library and exposed on a separate
   HTTP endpoint (`AD_PROMETHEUS_PORT`, default `9465`). The OTel Collector's
   `prometheus/ad` receiver scrapes this endpoint and forwards the metric
   into the same metrics pipeline.

The Prometheus-client path is included to demonstrate a **common pattern
during OpenTelemetry adoption**: organizations frequently already own a
significant amount of Prometheus instrumentation (in libraries, third-party
exporters, or legacy services) and want to ingest those metrics into an
OpenTelemetry-native pipeline without rewriting everything up front. The
Collector's `prometheus` receiver is the bridge that makes this possible.

**Recommendation**: this is a *transitional* pattern. Prefer the
OpenTelemetry SDK for new custom metrics, and migrate existing
Prometheus-client metrics to it - incremental migration as you touch
the surrounding code has proven successful in practice, but a focused
refactor works too; what matters is that the migration happens.

<!-- source: src/cart/README.md -->
# Cart Service

This service stores user shopping carts in Valkey.

## Local Build

Run `dotnet restore` and `dotnet build`.

## Docker Build

From the root directory of this repository, run:

```sh
docker compose build cart
```

## Metric cardinality overflow

Enable `cartMetricCardinalityOverflow` in the feature flag UI to deliberately add
`Activity.Current.TraceId` as `demo.cart.trace_id` on the get-cart latency metric.
After enough distinct traces exceed the SDK limit (2,000 by default), view the
**Metric cardinality overflow** section of the **Self-Observability** dashboard.
This simulates an incorrect attempt to correlate metrics with traces; use exemplars
instead (the cart service already enables them). The flag is off by default.

Turning the flag off stops adding trace IDs, but cumulative overflow can remain
visible. Restart cart with the flag off to reset SDK state; historical overflow
remains visible in dashboard time ranges that include it.

<!-- source: src/checkout/README.md -->
# Checkout Service

This service provides checkout services for the application.

## Local Build

To build the service binary, run:

```sh
go build -o /go/bin/checkout/
```

## Docker Build

From the root directory, run:

```sh
docker compose build checkout
```

## Regenerate protos

To build the protos, run from the root directory:

```sh
make docker-generate-protobuf
```

## Generate feature flag types

To regenerate the typed feature flag accessors from `flags.json`, run from the
service directory:

```sh
go generate ./...
```

This uses the [OpenFeature CLI](https://github.com/open-feature/cli) to
produce `flags/flags_gen.go`.

## Bump dependencies

To bump all dependencies run:

```sh
go get -u -t ./...
go mod tidy
```

<!-- source: src/currency/README.md -->
# Currency Service

The Currency Service does the conversion from one currency to another.
It is a C++ based service.

## Building docker image

To build the currency service, run the following from root directory
of opentelemetry-demo

```sh
docker compose build currency
```

## Run the service

Execute the below command to run the service.

```sh
docker compose up currency
```

## Run the client

currencyclient is a sample client which sends some request to currency
service. To run the client, execute the below command.

```sh
docker exec -it <container_name> currencyclient 7000
```

`7000` is port where currency listens to.

<!-- source: src/email/README.md -->
# Email Service

The Email service "sends" an email to the customer with their order details by
rendering it as a log message. It expects a JSON payload like:

```json
{
  "email": "some.address@website.com",
  "order": "<serialized order protobuf>"
}
```

## Local Build

We use `bundler` to manage dependencies. To get started, simply `bundle install`.

## Running locally

You may run this service locally with `bundle exec ruby email_server.rb`.

## Docker Build

From `src/email`, run `docker build .`

<!-- source: src/fraud-detection/README.md -->
# Fraud Detection Service

This service receives new orders by a Kafka topic and returns cases which are
suspected of fraud.

## Local Build

To build the protos and the service binary, run from the repo root:

```sh
cp -r ../../pb/ src/main/proto/
./gradlew shadowJar
```

## Docker Build

To build using Docker run from the repo root:

```sh
docker build -f ./src/fraud-detection/Dockerfile .
```

<!-- source: src/frontend/README.md -->
# Frontend service

The frontend is a [Next.js](https://nextjs.org/) application that is composed
by two layers.

1. Client side application. Which renders the components for the OTEL webstore.
2. API layer. Connects the client to the backend services by exposing REST endpoints.

## Build Locally

By running `docker compose up` at the root of the project you'll have access to
the frontend client by going to <http://localhost:8080/>.

## Local development

Currently, the easiest way to run the frontend for local development is to execute

```shell
docker compose run --service-ports -e NODE_ENV=development --volume $(pwd)/src/frontend:/app --volume $(pwd)/pb:/app/pb --user node --entrypoint sh frontend
```

from the root folder.

It will start all of the required backend services
and within the container simply run `npm run dev`.
After that the app should be available at <http://localhost:8080/>.

<!-- source: src/frontend-proxy/README.md -->
# Frontend Proxy Service

This service acts as a reverse proxy for the various user-facing web interfaces.

## Modifying the Envoy Configuration

The envoy configuration is generated from the `envoy.tmpl.yaml` file in this
directory. Environment variables are substituted at deploy-time.

<!-- source: src/kafka/README.md -->
# Kafka

This is used as a message queue service to connect the checkout service with
the accounting and fraud detection services.

Kafka is run in KRaft mode. Environment variables are substituted at
deploy-time.

<!-- source: src/load-generator/README.md -->
# Load Generator

The load generator creates simulated traffic to the demo.

## Accessing the Load Generator

You can access the web interface to Locust at `http://localhost:8080/loadgen/`.

## Modifying the Load Generator

Please see the [Locust
documentation](https://docs.locust.io/en/stable/writing-a-locustfile.html) to
learn more about modifying the locustfile.

## Configuration

* `LOCUST_BROWSER_TRAFFIC_ENABLED`: when `true`, spawns `WebsiteBrowserUser`
  virtual users that drive a real headless Chromium session against the
  frontend. Each one keeps its browser process alive for its whole lifetime,
  so raising the ratio of these users increases memory usage.
* `LOCUST_HTTP_USER_WEIGHT` / `LOCUST_BROWSER_USER_WEIGHT`: relative [Locust
  weights](https://docs.locust.io/en/stable/writing-a-locustfile.html#weight-of-tasks)
  for `WebsiteUser` (plain HTTP) vs `WebsiteBrowserUser` (real browser),
  defaulting to `9` and `1`. Raise `LOCUST_BROWSER_USER_WEIGHT` for more
  browser/frontend traffic, at the cost of more concurrent Chromium
  processes.

<!-- source: src/payment/README.md -->
# Payment Service

This service is responsible for processing and validating payments through the
application.

## Local Build

Copy the `demo.proto` file to this directory and run `npm ci`

## Docker Build

From the root directory, run:

```sh
docker compose build payment
```

<!-- source: src/product-catalog/README.md -->
# Product Catalog Service

When this service is run the output should be similar to the following

```json
{"message":"successfully parsed product catalog json","severity":"info","timestamp":"2022-06-02T23:54:10.191283363Z"}
{"message":"starting grpc server at :3550","severity":"info","timestamp":"2022-06-02T23:54:10.191849078Z"}
```

## Local Build

To build the service binary, run:

```sh
go build -o /go/bin/product-catalog/
```

## Docker Build

From the root directory, run:

```sh
docker compose build product-catalog
```

Database Calls Instrumentation

PostgreSQL queries are instrumented with
[otelsql](https://pkg.go.dev/github.com/XSAM/otelsql), with SQLCommenter enabled
to append trace context to SQL statements (for example, `traceparent` key-value
pairs in query comments).

The option is configured in `main.go` when opening the database connection:

```go
db, err = otelsql.Open("postgres", connStr,
    dbAttrs,
    otelsql.WithSQLCommenter(true),
    otelsql.WithSpanOptions(...),
)
```

Queries must use context-aware methods such as `QueryContext` and
`QueryRowContext` so the active trace context is available when SQL comments
are injected.

## Regenerate protos

To build the protos, run from the root directory:

```sh
make docker-generate-protobuf
```

## Generate feature flag types

To regenerate the typed feature flag accessors from `flags.json`, run from the
service directory:

```sh
go generate ./...
```

This uses the [OpenFeature CLI](https://github.com/open-feature/cli) to
produce `flags/flags_gen.go`.

## Bump dependencies

To bump all dependencies run:

```sh
go get -u -t ./...
go mod tidy
```

<!-- source: src/quote/README.md -->
# Quote Service

The Quote Service calculates the shipping costs,
based on the number of items to be shipped.

It is a PHP based service, using a combination of automatic and manual instrumentation.

## Docker Build

To build the quote service, run the following from root directory
of opentelemetry-demo

```sh
docker compose build quote
```

## Run the service

Execute the below command to run the service.

```sh
docker compose up quote
```

In order to get traffic into the service you have to deploy
the whole opentelemetry-demo.

Please follow the root README to do so.

## Development

To build and run the quote service locally:

```sh
docker build src/quote --target base -t quote
cd src/quote
docker run --rm -it -v $(pwd):/var/www -e QUOTE_PORT=8999 -p "8999:8999" quote
```

Then, send some curl requests:

```sh
curl --location 'http://localhost:8999/getquote' \
--header 'Content-Type: application/json' \
--data '{"numberOfItems":3}'
```

<!-- source: src/recommendation/README.md -->
# Recommendation Service

This service provides recommendations for other products based on the currently
selected product.

> [!NOTE]
> This service uses the OpenTelemetry Spring Boot starter so the demo shows a
> second way to instrument Java. It is not the default recommendation. The
> default choice for Spring Boot applications is the OpenTelemetry Java agent,
> which the [ad service](../ad/README.md) uses. The
> [Spring Boot starter](https://opentelemetry.io/docs/zero-code/java/spring-boot-starter/)
> page explains when the starter is the better fit.

It is a Spring Boot 4 application. The gRPC API is served with Spring gRPC, and
the telemetry comes from the OpenTelemetry Spring Boot starter plus the
OpenTelemetry gRPC instrumentation library, so no Java agent is involved.

Catalog calls have a two-second deadline, so a catalog that stops responding
does not hold recommendation requests open indefinitely. Set
`RECOMMENDATION_CATALOG_TIMEOUT_MS` to change this timeout in milliseconds.

## Local Build

Requires JDK 21 or newer. The protobuf classes are generated from
`../../pb/demo.proto` as part of the Gradle build:

```sh
./gradlew build
```

## Docker Build

From the root directory, run:

```sh
docker compose build recommendation
```

<!-- source: src/shipping/README.md -->
# Shipping Service

The Shipping service queries `quote` for price quote, provides tracking IDs,
and the impression of order fulfillment & shipping processes.

## Local

This repo assumes you have rust 1.82 installed. You may use docker, or
[install rust](https://www.rust-lang.org/tools/install).

## Build

From `../../`, run:

```sh
docker compose build shipping
```

## Test

```sh
cargo test
```

## Feature Flags

* `intlShippingSlowdown`: integer flag (default 0). When non-zero, non-US
  shipping requests are delayed by the flag's value in seconds to simulate
  overseas shipping latency. US addresses are never affected.

## Environment Variables

| Variable           | Default | Description                   |
|--------------------|---------|-------------------------------|
| `FLAGD_HOST`       | `flagd` | Hostname of the flagd service |
| `FLAGD_OFREP_PORT` | `8016`  | Port for the flagd OFREP API  |
