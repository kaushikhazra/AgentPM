# Authentication Flow

This document defines the authentication strategy for Taskyn's web interface.

---

## Strategy: JWT (JSON Web Tokens)

**Why JWT:**
- Stateless - no server-side session storage
- Works well with REST APIs
- Can include user claims (id, email, roles)
- Industry standard for SPAs

---

## Token Design

### Access Token
- **Lifetime**: 15 minutes (short-lived)
- **Storage**: Memory (React state)
- **Contains**: user_id, email, issued_at, expires_at

### Refresh Token
- **Lifetime**: 7 days
- **Storage**: HTTP-only cookie (secure, not accessible via JS)
- **Purpose**: Obtain new access tokens without re-login

---

## Auth Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Create new account |
| POST | `/auth/login` | Login, get tokens |
| POST | `/auth/logout` | Logout, clear refresh cookie |
| POST | `/auth/refresh` | Get new access token |
| GET | `/auth/me` | Get current user info |

---

## Flow Diagrams

### Login Flow

```
User                    React                   FastAPI
  │                       │                        │
  │── Enter credentials ──►│                        │
  │                       │── POST /auth/login ────►│
  │                       │                        │── Validate credentials
  │                       │                        │── Generate access token
  │                       │                        │── Generate refresh token
  │                       │◄─ { accessToken } ─────│
  │                       │   Set-Cookie: refresh  │
  │                       │                        │
  │                       │── Store in AuthContext │
  │◄── Redirect to app ───│                        │
```

### Token Refresh Flow

```
React                                    FastAPI
  │                                         │
  │── Access token expired ─────────────────│
  │                                         │
  │── POST /auth/refresh ──────────────────►│
  │   (refresh token in cookie)             │
  │                                         │── Validate refresh token
  │                                         │── Generate new access token
  │◄─ { accessToken } ─────────────────────│
  │                                         │
  │── Retry original request ───────────────►│
```

### Logout Flow

```
User                    React                   FastAPI
  │                       │                        │
  │── Click logout ───────►│                        │
  │                       │── POST /auth/logout ───►│
  │                       │                        │── Clear refresh cookie
  │                       │◄─ 200 OK ──────────────│
  │                       │                        │
  │                       │── Clear AuthContext ───│
  │◄── Redirect to login ─│                        │
```

---

## Backend Implementation

### User Model

```python
# models/user.py
from pydantic import BaseModel, EmailStr
from datetime import datetime

class User(BaseModel):
    id: str
    email: EmailStr
    name: str
    created_at: datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str
```

### Token Generation

```python
# auth/jwt.py
from datetime import datetime, timedelta
from jose import jwt

SECRET_KEY = "your-secret-key"  # Use env var in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_access_token(user_id: str, email: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "email": email,
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": user_id,
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
```

### Auth Routes

```python
# routes/auth.py
from fastapi import APIRouter, Response, HTTPException, Depends
from fastapi.security import HTTPBearer

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()

@router.post("/register")
async def register(data: UserCreate):
    # Check if email exists
    if get_user_by_email(data.email):
        raise HTTPException(409, "Email already registered")

    # Hash password and create user
    user = create_user(
        email=data.email,
        password_hash=hash_password(data.password),
        name=data.name,
    )

    return {"message": "Account created", "user_id": user.id}


@router.post("/login")
async def login(data: UserLogin, response: Response):
    # Validate credentials
    user = get_user_by_email(data.email)
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")

    # Generate tokens
    access_token = create_access_token(user.id, user.email)
    refresh_token = create_refresh_token(user.id)

    # Set refresh token as HTTP-only cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,       # HTTPS only in production
        samesite="strict",
        max_age=7 * 24 * 60 * 60,  # 7 days
    )

    return {"accessToken": access_token}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("refresh_token")
    return {"message": "Logged out"}


@router.post("/refresh")
async def refresh(request: Request, response: Response):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(401, "No refresh token")

    try:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(401, "Invalid token type")

        user_id = payload["sub"]
        user = get_user(user_id)
        if not user:
            raise HTTPException(401, "User not found")

        # Generate new access token
        access_token = create_access_token(user.id, user.email)
        return {"accessToken": access_token}

    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Refresh token expired")
    except jwt.JWTError:
        raise HTTPException(401, "Invalid refresh token")


@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user
```

### Auth Dependency

```python
# deps.py
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    token = credentials.credentials

    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise HTTPException(401, "Invalid token type")

        user_id = payload["sub"]
        user = get_user(user_id)
        if not user:
            raise HTTPException(401, "User not found")

        return user

    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.JWTError:
        raise HTTPException(401, "Invalid token")
```

---

## Frontend Implementation

### Auth Context

```tsx
// providers/AuthProvider.tsx
interface AuthState {
  user: User | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

interface AuthContextValue extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  register: (email: string, password: string, name: string) => Promise<void>;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    accessToken: null,
    isAuthenticated: false,
    isLoading: true,
  });

  // On mount, try to refresh token
  useEffect(() => {
    refreshToken()
      .then((token) => {
        if (token) {
          setState(s => ({ ...s, accessToken: token, isAuthenticated: true }));
          fetchCurrentUser(token);
        }
      })
      .finally(() => {
        setState(s => ({ ...s, isLoading: false }));
      });
  }, []);

  const login = async (email: string, password: string) => {
    const { accessToken } = await api.post<{ accessToken: string }>('/auth/login', {
      email,
      password,
    });

    setState(s => ({ ...s, accessToken, isAuthenticated: true }));
    await fetchCurrentUser(accessToken);
  };

  const logout = async () => {
    await api.post('/auth/logout', {});
    setState({
      user: null,
      accessToken: null,
      isAuthenticated: false,
      isLoading: false,
    });
  };

  const fetchCurrentUser = async (token: string) => {
    const user = await api.get<User>('/auth/me');
    setState(s => ({ ...s, user }));
  };

  return (
    <AuthContext.Provider value={{ ...state, login, logout, register }}>
      {children}
    </AuthContext.Provider>
  );
}
```

### Token Refresh Logic

```tsx
// api/client.ts
let accessToken: string | null = null;
let refreshPromise: Promise<string | null> | null = null;

export function setAccessToken(token: string | null) {
  accessToken = token;
}

async function refreshToken(): Promise<string | null> {
  // Prevent multiple simultaneous refresh requests
  if (refreshPromise) return refreshPromise;

  refreshPromise = fetch(`${API_BASE}/auth/refresh`, {
    method: 'POST',
    credentials: 'include', // Include cookies
  })
    .then(res => {
      if (!res.ok) return null;
      return res.json().then(data => data.accessToken);
    })
    .catch(() => null)
    .finally(() => {
      refreshPromise = null;
    });

  return refreshPromise;
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    credentials: 'include', // Include cookies for refresh
    headers: {
      'Content-Type': 'application/json',
      ...(accessToken && { Authorization: `Bearer ${accessToken}` }),
      ...options.headers,
    },
  });

  // If 401, try to refresh and retry
  if (res.status === 401) {
    const newToken = await refreshToken();
    if (newToken) {
      setAccessToken(newToken);
      // Retry original request with new token
      return request(endpoint, options);
    }
    // Refresh failed - redirect to login
    window.location.href = '/login';
    throw new Error('Session expired');
  }

  if (!res.ok) {
    const error = await res.json();
    throw new ApiError(error.error, error.detail, error.code, res.status);
  }

  if (res.status === 204) return null as T;
  return res.json();
}
```

---

## Security Considerations

### Password Hashing

```python
# auth/password.py
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
```

### Token Storage Summary

| Token | Storage | Why |
|-------|---------|-----|
| Access Token | React state (memory) | Short-lived, needs to be in JS for API calls |
| Refresh Token | HTTP-only cookie | Long-lived, protected from XSS |

### Cookie Settings (Production)

```python
response.set_cookie(
    key="refresh_token",
    value=refresh_token,
    httponly=True,      # Not accessible via JavaScript
    secure=True,        # HTTPS only
    samesite="strict",  # CSRF protection
    path="/api/v1/auth/refresh",  # Only sent to refresh endpoint
)
```

---

## User Storage

For v1, store users in SQLite alongside other Taskyn data:

```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Decisions

- [x] **JWT-based auth** - Stateless, works well with REST
- [x] **Short-lived access tokens** - 15 minutes, stored in memory
- [x] **Refresh token in HTTP-only cookie** - Protected from XSS
- [x] **Automatic token refresh** - Seamless UX, retry failed requests
- [x] **bcrypt for passwords** - Industry standard hashing
- [x] **SQLite user storage** - Simple, no extra dependencies for v1

---

## Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                        Authentication Flow                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Login:                                                         │
│    1. User submits email/password                               │
│    2. Server validates, returns access token                    │
│    3. Server sets refresh token in HTTP-only cookie             │
│    4. React stores access token in memory                       │
│                                                                 │
│  API Request:                                                   │
│    1. React sends access token in Authorization header          │
│    2. If 401, automatically try refresh                         │
│    3. If refresh succeeds, retry request                        │
│    4. If refresh fails, redirect to login                       │
│                                                                 │
│  Logout:                                                        │
│    1. Call /auth/logout to clear cookie                         │
│    2. Clear React state                                         │
│    3. Redirect to login                                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

