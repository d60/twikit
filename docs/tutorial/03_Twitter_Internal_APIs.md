# Chapter 3: A Closer Look at Twitter's Internal APIs

In the previous chapter, we learned the general process of finding API requests using browser developer tools. Now, let's zoom in on the specific APIs that Twitter uses and that `twikit` is built to interact with. Twitter's backend is not a single, monolithic system; it's a combination of modern and legacy systems working in tandem. `twikit` needs to be ableto speak to both.

## The Modern Workhorse: The GraphQL API

Most of the new features and data you see on the Twitter website are powered by a **GraphQL API**.

#### What is GraphQL?

GraphQL is a modern query language for APIs, developed by Facebook and now open-source. Its main advantage is that it allows the client to ask for *exactly* the data it needs, no more and no less.

In a traditional REST API, the server defines a fixed data structure for each endpoint. For example, a `/user` endpoint might always return the user's name, birthday, and address. If you only need the user's name, you still get the other data (this is called **over-fetching**). If you need the user's name and their last three posts, you might have to make two separate requests (this is called **under-fetching**).

GraphQL solves this by letting the client specify the exact shape of the data it wants in a single request.

#### GraphQL in Action on Twitter

When `twikit` makes a request to a GraphQL endpoint, it's essentially sending a "query" that looks like a structured text document.

-   **Queries (Fetching Data)**: A query is used to *read* or *fetch* data. The `UserTweets` endpoint we found in the last chapter is a perfect example of a query. The actual query that the browser sends looks something like this:

    ```graphql
    query UserTweets($userId: ID!, $count: Int!) {
      user(id: $userId) {
        tweets(count: $count) {
          id
          text
          createdAt
          user {
            name
            screenName
          }
        }
      }
    }
    ```
    Notice how the query specifies the exact fields it wants ( `id`, `text`, etc.). To save bandwidth, Twitter's web app doesn't send this full text every time. Instead, it sends a pre-registered `queryId`, which is a hash of the full query text. `twikit` has a list of these known `queryId`s.

-   **Mutations (Modifying Data)**: A mutation is used to *change* data on the server (create, update, or delete). For example, to create a tweet, `twikit` would send a `CreateTweet` mutation. The structure is similar to a query, but it includes the data to be changed, such as the text of the new tweet.

The `twikit/client/gql.py` file is `twikit`'s library of GraphQL requests. It contains functions for many of Twitter's known queries and mutations. Each function knows the correct `queryId` and how to structure the `variables` (like `$userId` and `$count` in the example above) for the request payload.

## The Legacy System: The v1.1-like API

Before GraphQL became popular, Twitter, like most platforms, used a more traditional REST-style API. While much of Twitter has been migrated to GraphQL, remnants of this older system still exist and are used for certain features. `twikit` refers to this as the "v1.1" API because its structure is very similar to Twitter's old public v1.1 API.

This API is characterized by a more rigid, endpoint-per-resource structure. For example, you might see endpoints like:
-   `/1.1/friendships/create.json` (to follow a user)
-   `/1.1/direct_messages/new.json` (to send a DM)

These endpoints are less flexible than GraphQL and return a fixed block of data. The `twikit/client/v11.py` file is the client responsible for interacting with these older endpoints.

## The Tracking Header: `X-Client-Transaction-Id`

As you explore Twitter's network requests, you may notice a peculiar header being sent: `X-Client-Transaction-Id`.

-   **What is it?**: This is a custom HTTP header that Twitter's own web client sends with its requests. It's a long, seemingly random string.
-   **What is its Purpose?**: It's a unique identifier for a "transaction"—a sequence of related actions performed by a user. For example, the entire process of uploading a video and then attaching it to a tweet might be considered a single transaction. Twitter's engineers likely use this for internal analytics, debugging, and tracking how users flow through their application.
-   **Why `twikit` Replicates It**: To avoid being detected as a bot, a library like `twikit` must mimic the behavior of the official client as closely as possible. This includes generating and sending this obscure tracking header. The logic for generating these IDs is complex and was carefully reverse-engineered from Twitter's own obfuscated JavaScript code. The `twikit/x_client_transaction` directory is dedicated to this single purpose. This demonstrates the incredible level of detail required to build a robust scraping library.

---
By understanding these different API systems, you can now see how `twikit` acts as a comprehensive bridge, allowing you to interact with all parts of Twitter's backend. In the next chapter, we'll tackle the most complex part of the process: [**Chapter 4: Authentication in Depth**](./04_Authentication_in_Depth.md).
