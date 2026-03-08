## Feature: [name]

### What does it do?


### What needs to change?
- [ ] Database:
- [ ] Model:
- [ ] Route:
- [ ] Template:
- [ ] Tests: 

- [ ] is this a utility?: delete if not
### Edge cases


### What does done look like?


## REFERENCES
### 2xx — Success
#### everything works
200 OK — standard success
201 Created — resource was created
204 No Content — success but nothing to return

### 3xx — Redirection
#### things moved
--- 
301 Moved Permanently — URL changed forever
302 Found — temporary redirect
304 Not Modified — cached version is still valid

### 4xx — Client Errors
#### you did something wrong
--- You did something wrong.
400 Bad Request — malformed request
401 Unauthorized — not logged in
403 Forbidden — logged in but not allowed
404 Not Found — resource doesn't exist
405 Method Not Allowed — wrong HTTP method
409 Conflict — duplicate resource
422 Unprocessable Entity — valid request but bad data
429 Too Many Requests — rate limited

### 5xx — Server Errors
#### the server did something wrong
500 Internal Server Error — something crashed
502 Bad Gateway — upstream server failed
503 Service Unavailable — server is down or overloaded
504 Gateway Timeout — upstream server timed out