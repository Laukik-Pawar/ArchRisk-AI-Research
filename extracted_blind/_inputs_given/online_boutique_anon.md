**System X** is a cloud-first microservices demo application.  The application is a
web-based e-commerce app where users can browse items, add them to the cart, and purchase them.




## Architecture

**System X** is composed of 11 microservices written in different
languages that talk to each other over gRPC.


Find **Protocol Buffers Descriptions** at the [`./protos` directory](/protos).

| Service                                              | Language      | Description                                                                                                                       |
| ---------------------------------------------------- | ------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| svc-08                           | Go            | Exposes an HTTP server to serve the website. Does not require signup/login and generates session IDs for all users automatically. |
| svc-01                     | C#            | Stores the items in the user's shopping cart in Redis and retrieves it.                                                           |
| svc-10 | Go            | Provides the list of products from a JSON file and ability to search products and get individual products.                        |
| svc-03             | Node.js       | Converts one money amount to another currency. Uses real values fetched from European Central Bank. It's the highest QPS service. |
| svc-06               | Node.js       | Charges the given credit card info (mock) with the given amount and returns a transaction ID.                                     |
| svc-11             | Go            | Gives shipping cost estimates based on the shopping cart. Ships items to the given address (mock)                                 |
| svc-09                   | Python        | Sends users an order confirmation email (mock).                                                                                   |
| svc-07             | Go            | Retrieves user cart, prepares order and orchestrates the payment, shipping and the email notification.                            |
| svc-05 | Python        | Recommends other products based on what's given in the cart.                                                                      |
| svc-04                         | Java          | Provides text ads based on given context words.                                                                                   |
| svc-02                 | Python/Locust | Continuously sends requests imitating realistic user shopping flows to the svc-08.                                              |
