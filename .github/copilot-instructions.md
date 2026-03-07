## Route conventions
- Follow/unfollow: POST /profile/<username>/follow (toggle)
- Feed: /?feed=following or /?feed=all
- Posts: /posts/<id>
- Topics: /t/<topic_name>
- Profile: /profile/<username>

## Test conventions
- Always pass `app` fixture when creating a second test client
- Use `use_cookies=True` on all test clients
- Register users before interacting with their profile