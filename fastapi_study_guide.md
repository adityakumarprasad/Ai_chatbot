# FastAPI Study Guide: From Node.js to Python Backend Development

This guide is designed for Node.js developers transitionary to Python's **FastAPI**. It maps familiar Node.js patterns (Express, TS/Zod, middlewares, `pg-pool`) to FastAPI, explaining core mechanics, best practices, and interview-essential concepts.

---

## 1. High-Level Concepts: FastAPI vs. Node.js

| Concept | Node.js (Express / NestJS) | FastAPI |
| :--- | :--- | :--- |
| **Runtime & Event Loop** | Single-threaded JavaScript event loop (V8 Engine) | Single-threaded Python Event Loop (via `asyncio` & `uvloop`) |
| **HTTP Gateway / Web Server** | Integrated `http` module / `Express` server | **Uvicorn** (ASGI Server) hosting **FastAPI** |
| **Type Validation** | TypeScript compilation + runtime libraries like **Zod** or **Joi** | **Pydantic** (Python type hinting enforced at runtime) |
| **Middlewares & Filters** | Express middleware chain `(req, res, next) => {}` | FastAPI Middlewares / **Dependency Injection (`Depends`)** |
| **Database Pool** | `pg.Pool` (via `pg` or `knex`/`Prisma`) | `psycopg.pool.AsyncConnectionPool` |

---

## 2. Event Loop & Concurrency Models

### Node.js Concurrency
Node.js runs on a single main thread using an event loop backed by `libuv` for asynchronous tasks (I/O, database, file system). When you execute non-blocking operations:
```javascript
// Node.js
async function getData(req, res) {
  const result = await db.query("SELECT * FROM users");
  res.json(result);
}
```
Under the hood, `libuv` delegates the db call to the system kernel or a worker thread pool, freeing the main thread to handle other incoming requests.

### FastAPI Concurrency (ASGI)
Historically, Python web frameworks (like Flask or Django) used **WSGI (Web Server Gateway Interface)**, which is synchronous and blocks the thread per request (meaning concurrency required spawning multiple threads or worker processes).

FastAPI is an **ASGI (Asynchronous Server Gateway Interface)** framework. It runs on `asyncio`.
When you define a route in FastAPI:
- If you use `async def`: FastAPI runs it on the main asyncio event loop (non-blocking, just like Node.js).
- If you use regular `def`: FastAPI automatically runs it in an external thread pool so it does not block the event loop!

```python
# FastAPI (Async - runs on asyncio loop)
@app.get("/users")
async def get_users():
    result = await db.fetch_users()  # Non-blocking async call
    return result

# FastAPI (Sync - runs in thread pool)
@app.get("/heavy-task")
def heavy_task():
    # Doing synchronous blocking computation here
    time.sleep(2) 
    return {"status": "done"}
```

> [!WARNING]
> **Blocking the Event Loop in Python**
> In Node.js, running blocking synchronous calculations blocks the event loop. Similarly in Python, using `time.sleep()` or blocking I/O calls (like synchronous `requests.get()`) *inside* an `async def` function will freeze the whole loop. 
> - For blocking code, use regular `def`.
> - For async non-blocking code, use `async def` with `await`.

---

## 3. Routing & Request Lifecycle

Routing in FastAPI is decorator-based, matching modern frameworks like NestJS or Spring Boot, but very intuitive if you are used to Express router declarations.

### Code Comparison

#### Express.js (Node.js)
```typescript
import express from 'express';
const router = express.Router();

router.get('/items/:id', (req, res) => {
  const itemId = req.params.id;
  const queryParam = req.query.search;
  res.status(200).json({ id: itemId, search: queryParam });
});
```

#### FastAPI (Python)
```python
from fastapi import APIRouter, Query

router = APIRouter()

@router.get("/items/{item_id}")
async def read_item(item_id: str, search: str | None = None):
    # Path parameter: item_id (declared in path)
    # Query parameter: search (not declared in path, default to None)
    return {"id": item_id, "search": search}
```

---

## 4. Request Validation: Pydantic vs. Zod

In Node.js, we write TypeScript interfaces for development compilation and use libraries like **Zod** to validate data at runtime.
In Python, **Pydantic** leverages Python's built-in type hints to do both simultaneously.

### Schema Validation Comparison

#### Zod Schema (Node.js)
```typescript
import { z } from 'zod';

export const CreateUserSchema = z.object({
  username: z.string().min(3),
  email: z.string().email(),
  age: z.number().int().positive().optional(),
});

type CreateUser = z.infer<typeof CreateUserSchema>;
```

#### Pydantic Model (FastAPI)
```python
from pydantic import BaseModel, EmailStr, Field

class CreateUser(BaseModel):
    username: str = Field(..., min_length=3)
    email: EmailStr
    age: int | None = Field(default=None, gt=0)
```
*Note: `EmailStr` automatically checks email syntax, similar to `z.string().email()`.*

When a client sends a request to FastAPI:
```python
@app.post("/users")
async def create_user(user: CreateUser):
    # FastAPI automatically parses body JSON, validates against CreateUser,
    # and exposes it as a strongly typed object.
    return {"message": f"Created user {user.username}"}
```
If validation fails, FastAPI automatically throws a structured `422 Unprocessable Entity` response, matching Zod's parsing errors.

---

## 5. Middleware vs. Dependency Injection

Express relies on **middlewares** chained sequentially (`req, res, next`). You pass data between middlewares by attaching properties to the request object (e.g., `req.user = user`).

FastAPI has middleware support, but advocates for **Dependency Injection (DI)** using `Depends`. DI is cleaner, supports asynchronous operations, allows type hints on injected values, and is much easier to mock in tests.

### Authentication Pattern Comparison

#### Node.js / Express Middleware
```javascript
// Middleware
const authenticate = async (req, res, next) => {
  const token = req.headers['authorization'];
  if (!token) return res.status(401).send("Unauthorized");
  
  const user = await db.getUserFromToken(token);
  req.user = user;
  next();
};

// Route usage
app.get('/me', authenticate, (req, res) => {
  res.json(user: req.user);
});
```

#### FastAPI Dependency Injection
```python
from fastapi import Header, HTTPException, Depends, status

# Injected function
async def get_current_user(authorization: str | None = Header(default=None)):
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Missing Authorization Header"
        )
    user = await db.get_user_from_token(authorization)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid Token"
        )
    return user  # Can return any object

# Route usage
@app.get("/me")
async def read_current_user(current_user: User = Depends(get_current_user)):
    # current_user is fully typed and injected directly!
    return {"user": current_user}
```

---

## 6. Server-Sent Events (SSE) & Streaming

In our LLM project, we stream text tokens from our LangGraph execution to the frontend.

### Node.js SSE (Express)
In Express, you manually configure headers and write chunks to the response stream.
```javascript
app.get('/stream', (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');

  res.write('data: hello\n\n');
  res.write('data: world\n\n');
  res.end();
});
```

### FastAPI SSE (StreamingResponse)
FastAPI provides a standard `StreamingResponse` which takes an async generator yielding string chunks.
```python
from fastapi.responses import StreamingResponse
import asyncio

async def token_generator():
    tokens = ["hello", " ", "world", " ", "from", " ", "fastapi"]
    for token in tokens:
        # SSE format: "data: <content>\n\n"
        yield f"data: {token}\n\n"
        await asyncio.sleep(0.5)

@app.get("/stream")
async def stream_tokens():
    return StreamingResponse(token_generator(), media_type="text/event-stream")
```

---

## 7. Lifespan Events (Startup & Shutdown hooks)

In Node.js, code that runs when starting or stopping the application is managed procedurally:
```javascript
const server = app.listen(port, () => {
  console.log("Database and server online.");
});

process.on('SIGTERM', () => {
  db.close();
  server.close();
});
```

FastAPI handles this with a **Lifespan Context Manager**, wrapping the server lifecycle. We use this to boot up database connection pools and shut them down cleanly.

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from psycopg_pool import AsyncConnectionPool

db_pool = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP HOOK ---
    global db_pool
    # Initialize connection pool
    db_pool = AsyncConnectionPool(conninfo="postgresql://user:pass@localhost/db", max_size=10)
    print("PostgreSQL connection pool initialized")
    
    yield  # FastAPI app runs here, waiting for requests
    
    # --- SHUTDOWN HOOK ---
    await db_pool.close()
    print("PostgreSQL connection pool closed")

app = FastAPI(lifespan=lifespan)
```

---

## 8. Interview Q&A Preparation for Web Developers

Here are essential interview questions concerning FastAPI, Python concurrency, and microservices architecture.

### Q1: What is ASGI, and how does it differ from WSGI?
- **Answer**: 
  - **WSGI** (Web Server Gateway Interface) is a synchronous specification designed for older Python frameworks (like Flask). It operates in a request-per-thread model, blocking the thread during I/O operations.
  - **ASGI** (Asynchronous Server Gateway Interface) is built for async applications, supporting HTTP/2, WebSockets, and long-polling. FastAPI uses ASGI (running on Uvicorn), enabling the event loop to manage thousands of concurrent connections efficiently, similar to Node.js.

### Q2: What is the purpose of Pydantic in FastAPI?
- **Answer**: Pydantic handles parsing, serialization, and type validation. It verifies that incoming request bodies match custom Pydantic schemas (throwing automatic 422 errors if invalid). It also manages serialization (converting internal Python model instances into JSON format when returning responses).

### Q3: How does FastAPI's dependency injection (`Depends`) improve application design?
- **Answer**: It separates logic from routing. You can declare dependencies (like authenticated users, database connections, or configuration settings) and inject them directly into route parameters. This promotes modularity, keeps controller routes lean, and allows easy mocking during unit tests (by rewriting the dependency override dictionary `app.dependency_overrides`).

### Q4: If Python is single-threaded due to the Global Interpreter Lock (GIL), how does FastAPI achieve high performance?
- **Answer**: While the GIL prevents multiple threads from executing Python code *in parallel* on multiple CPU cores, FastAPI's performance comes from **concurrency during I/O-bound tasks**. When an async route awaits database or network operations, the event loop switches to process another request. For CPU-bound tasks, we bypass the event loop bottleneck by spinning off tasks to multi-process pools or Celery background workers.
