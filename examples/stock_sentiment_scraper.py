import asyncio
import json
import os
from pathlib import Path

from twikit import Client


DEFAULT_QUERY = "TSLA OR Tesla"
DEFAULT_PROXY = "socks5://10.129.0.3:1086"

POSITIVE_WORDS = {
    "beat", "beats", "bull", "bullish", "buy", "growth", "moon", "profit",
    "profits", "rally", "strong", "surge", "upside", "upgrade", "win",
}
NEGATIVE_WORDS = {
    "bear", "bearish", "cut", "debt", "downgrade", "drop", "fraud", "lawsuit",
    "loss", "losses", "miss", "risk", "sell", "short", "slump", "weak",
}


def env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    return int(value)


def simple_sentiment(text: str) -> dict:
    words = set(text.lower().replace("$", " ").split())
    positive = len(words & POSITIVE_WORDS)
    negative = len(words & NEGATIVE_WORDS)
    score = positive - negative
    if score > 0:
        label = "positive"
    elif score < 0:
        label = "negative"
    else:
        label = "neutral"
    return {
        "label": label,
        "score": score,
        "positive_hits": positive,
        "negative_hits": negative,
    }


def load_cookies(client: Client) -> None:
    cookies_file = os.getenv("TWIKIT_COOKIES_FILE")
    if cookies_file:
        client.load_cookies(cookies_file)
        return

    auth_token = os.getenv("TWITTER_AUTH_TOKEN")
    ct0 = os.getenv("TWITTER_CT0")

    auth_token_file = Path(os.getenv("AUTH_TOKEN_FILE", "auth_token"))
    ct0_file = Path(os.getenv("CT0_FILE", "ct0"))
    if auth_token is None and auth_token_file.exists():
        auth_token = auth_token_file.read_text().strip()
    if ct0 is None and ct0_file.exists():
        ct0 = ct0_file.read_text().strip()

    if not auth_token or not ct0:
        raise RuntimeError(
            "Provide TWIKIT_COOKIES_FILE, or TWITTER_AUTH_TOKEN and TWITTER_CT0, "
            "or auth_token/ct0 files in the working directory."
        )

    client.set_cookies({"auth_token": auth_token, "ct0": ct0})


def tweet_to_record(tweet) -> dict:
    sentiment = simple_sentiment(tweet.full_text)
    return {
        "id": tweet.id,
        "created_at": tweet.created_at,
        "text": tweet.full_text,
        "lang": tweet.lang,
        "sentiment": sentiment,
        "metrics": {
            "views": tweet.view_count,
            "replies": tweet.reply_count,
            "likes": tweet.favorite_count,
            "retweets": tweet.retweet_count,
            "bookmarks": tweet.bookmark_count,
        },
        "user": {
            "id": tweet.user.id,
            "name": tweet.user.name,
            "screen_name": tweet.user.screen_name,
            "followers": tweet.user.followers_count,
            "verified": tweet.user.verified,
            "blue_verified": tweet.user.is_blue_verified,
        },
    }


async def main() -> None:
    query = os.getenv("STOCK_QUERY", DEFAULT_QUERY)
    product = os.getenv("SEARCH_PRODUCT", "Latest")
    proxy = os.getenv("TWITTER_PROXY", DEFAULT_PROXY)
    max_tweets = env_int("MAX_TWEETS", 100)
    min_view_count = env_int("MIN_VIEW_COUNT", 0)
    output = Path(os.getenv("OUTPUT", f"stock_tweets_{query.replace(' ', '_')}.jsonl"))

    client = Client("en-US", proxy=proxy)
    load_cookies(client)

    written = 0
    result = await client.search_tweet(query, product, count=min(100, max_tweets))
    with output.open("w", encoding="utf-8") as f:
        while result and written < max_tweets:
            for tweet in result:
                views = tweet.view_count or 0
                if views < min_view_count:
                    continue
                f.write(json.dumps(tweet_to_record(tweet), ensure_ascii=False) + "\n")
                written += 1
                if written >= max_tweets:
                    break
            result = await result.next() if written < max_tweets else None

    await client.http.aclose()
    print(f"Wrote {written} tweets to {output}")


if __name__ == "__main__":
    asyncio.run(main())
