from twikit import Client

###########################################

# Enter your account information
USERNAME = ...
EMAIL = ...
PASSWORD = ...

client = Client('en-US')
client.login(
    auth_info_1=USERNAME,
    auth_info_2=EMAIL,
    password=PASSWORD
)

###########################################

# Search Latest Tweets
tweets = client.search_tweet('query', 'Latest')
for tweet in tweets:
    print(tweet)
# Search more tweets
more_tweets = tweets.next()

###########################################

# Search users
users = client.search_user('query')
for user in users:
    print(user)
# Search more users
more_users = users.next()

###########################################

# Get user by screen name
USER_SCREEN_NAME = 'example_user'
user = client.get_user_by_screen_name(USER_SCREEN_NAME)

# Access user attributes
print(
    f'id: {user.id}',
    f'name: {user.name}',
    f'followers: {user.followers_count}',
    f'tweets count: {user.statuses_count}',
    sep='\n'
)

# Follow user
user.follow()
# Unfollow user
user.unfollow()

# Get user tweets
user_tweets = user.get_tweets('Tweets')
for tweet in user_tweets:
    print(tweet)
# Get more tweets
more_user_tweets = user_tweets.next()

###########################################

# Send dm to a user
media_id = client.upload_media('./image.png')
user.send_dm('dm text', media_id)

# Get dm history
messages = user.get_dm_history()
for message in messages:
    print(message)
# Get more messages
more_messages = messages.next()

###########################################

# Get tweet by ID
TWEET_ID = '0000000000'
tweet = client.get_tweet_by_id(TWEET_ID)

# Access tweet attributes
print(
    f'id: {tweet.id}',
    f'text {tweet.text}',
    f'favorite count: {tweet.favorite_count}',
    f'media: {tweet.media}',
    sep='\n'
)

# Favorite tweet
tweet.favorite()
# Unfavorite tweet
tweet.unfavorite()
# Retweet tweet
tweet.retweet()
# Delete retweet
tweet.delete_retweet()

# Reply to tweet
tweet.reply('tweet content')

###########################################

# Create tweet with media
TWEET_TEXT = 'tweet text'
MEDIA_IDS = [
    client.upload_media('./media1.png'),
    client.upload_media('./media2.png'),
    client.upload_media('./media3.png')
]

client.create_tweet(TWEET_TEXT, MEDIA_IDS)

# Create tweet with a poll
TWEET_TEXT = 'tweet text'
POLL_URI = client.create_poll(
    ['Option 1', 'Option 2', 'Option 3']
)

client.create_tweet(TWEET_TEXT, poll_uri=POLL_URI)

###########################################

# Get news trends
trends = client.get_trends('news')
for trend in trends:
    print(trend)

###########################################
