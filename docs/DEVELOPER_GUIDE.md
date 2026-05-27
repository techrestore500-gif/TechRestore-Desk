# Developer Guide

This guide helps developers set up, understand, and extend the Tech Restore Desk app.

## Prerequisites

- **Windows 10/11** (development tested on Windows; app design is Windows-first)
- **Python 3.8+** (tested with Python 3.14.3)
- **Node.js 18+** and npm 9+
- **Git** (optional, for version control)
- **PowerShell 5.1+** (for development scripts; not strictly required but convenient)

## Initial Setup

### 1. Clone or Extract Project

Extract `tech-restore-desk/` to your development machine. The project structure is:

```
tech-restore-desk/
  backend/
    app/
      main.py
      database.py
      models.py
      seed.py
      routes/
        __init__.py
        health.py
        customers.py
        tickets.py
        loaners.py
        dashboard.py
        pricing.py
    requirements.txt
    .venv/  (created by setup)
  frontend/
    src/
      api/
        tickets.ts
      components/
        AppShell.tsx
      pages/
        ...
      routes/
        ...
    public/
    vite.config.ts
    tsconfig.json
    package.json
    node_modules/  (created by setup)
  data/
    tech_restore_desk.sqlite  (created on first backend run)
  docs/
    README.md
    ARCHITECTURE.md
    API_REFERENCE.md
    DEVELOPER_GUIDE.md (this file)
    IMPLEMENTATION_STATUS.md
  README.md
```

### 2. Backend Setup

From PowerShell in the `tech-restore-desk/backend/` directory:

```powershell
# Create Python virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\Activate.ps1

# Install dependencies
python -m pip install -r requirements.txt

# Verify FastAPI and Uvicorn installed
pip list | grep -E "fastapi|uvicorn|pydantic"
```

**If activation fails**, ensure execution policy allows scripts:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.venv\Scripts\Activate.ps1
```

### 3. Frontend Setup

From PowerShell in the `tech-restore-desk/frontend/` directory:

```powershell
# Install dependencies
npm install

# Verify
npm list | head -20
```

### 4. Run Both Services

Open two PowerShell windows:

**Window 1 â€” Backend** (from `tech-restore-desk/backend`):
```powershell
.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 127.0.0.1 --port 8787
```

Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8787 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

**Window 2 â€” Frontend** (from `tech-restore-desk/frontend`):
```powershell
npm run dev -- --host 127.0.0.1
```

Expected output:
```
âžœ  Local:   http://127.0.0.1:5173/
```

### 5. Open in Browser

Navigate to `http://127.0.0.1:5173` in your browser. You should see the Tech Restore Desk dashboard.

## Development Workflow

### Adding a New API Endpoint

1. **Define the data model** in `app/models.py`:
   ```python
   class MyNewRequest(BaseModel):
       field: str
       amount: int

   class MyNewResponse(BaseModel):
       id: int
       field: str
       amount: int
       created_at: datetime
   ```

2. **Add database logic** in `app/database.py`:
   ```python
   def create_my_thing(conn, field: str, amount: int) -> dict:
       cursor = conn.cursor()
       cursor.execute(
           'INSERT INTO my_things (field, amount) VALUES (?, ?)',
           (field, amount)
       )
       conn.commit()
       return {"id": cursor.lastrowid, "field": field, "amount": amount, "created_at": datetime.now()}
   ```

3. **Create a route file** in `app/routes/my_things.py`:
   ```python
   from fastapi import APIRouter
   from app.models import MyNewRequest, MyNewResponse
   from app.database import get_db, create_my_thing

   router = APIRouter(prefix="/my-things", tags=["my-things"])

   @router.post("/", response_model=MyNewResponse, status_code=201)
   async def post_my_thing(req: MyNewRequest):
       conn = get_db()
       result = create_my_thing(conn, req.field, req.amount)
       return result
   ```

4. **Register the router** in `app/main.py`:
   ```python
   from app.routes import my_things

   app.include_router(my_things.router, prefix="/api")
   ```

5. **Add frontend types and fetch function** in `src/api/tickets.ts`:
   ```typescript
   export type MyNewThing = {
     id: number;
     field: string;
     amount: number;
     created_at: string;
   };

   export async function createMyThing(field: string, amount: number): Promise<MyNewThing> {
     const res = await fetch(`/api/my-things`, {
       method: 'POST',
       headers: { 'Content-Type': 'application/json' },
       body: JSON.stringify({ field, amount }),
     });
     if (!res.ok) throw new Error(`Failed to create: ${res.statusText}`);
     return res.json();
   }
   ```

6. **Use in a React component** (e.g., `src/pages/MyThingsPage.tsx`):
   ```typescript
   import { createMyThing, MyNewThing } from '../api/tickets';

   export function MyThingsPage() {
     const [things, setThings] = useState<MyNewThing[]>([]);

     const handleCreate = async (field: string, amount: number) => {
       const newThing = await createMyThing(field, amount);
       setThings([...things, newThing]);
     };

     return (
       <div>
         <h2>My Things</h2>
         <button onClick={() => handleCreate('test', 100)}>Add</button>
         <ul>
           {things.map(t => <li key={t.id}>{t.field}: ${t.amount}</li>)}
         </ul>
       </div>
     );
   }
   ```

7. **Test**: Send a request via PowerShell or Postman:
   ```powershell
   Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8787/api/my-things `
     -ContentType 'application/json' `
     -Body (@{ field = "test"; amount = 100 } | ConvertTo-Json)
   ```

### Modifying the Database Schema

1. **Update `app/database.py`**: Add new table creation in `initialize_database()` or alter existing tables.
2. **Delete** `tech-restore-desk/data/tech_restore_desk.sqlite` to trigger re-initialization.
3. **Restart backend**: The app will recreate the schema on next startup.

âš ï¸ **Warning**: This destroys all local data. For production, implement migrations (Alembic).

### Debugging

**Backend**:
- Check terminal output for FastAPI logs.
- Add `print()` statements in Python functions; output appears in backend terminal.
- Use `ipdb` for interactive debugging (install with `pip install ipdb`, then `import ipdb; ipdb.set_trace()`).

**Frontend**:
- Open browser DevTools (F12).
- Check Network tab for API responses.
- Check Console tab for JavaScript errors.
- Use `console.log()` in React components.

**Database**:
- Inspect SQLite directly using `sqlite3` CLI or a GUI like **DB Browser for SQLite**.
  ```powershell
  cd tech-restore-desk/data
  sqlite3 tech_restore_desk.sqlite
  sqlite> .tables
  sqlite> SELECT * FROM tickets LIMIT 5;
  sqlite> .quit
  ```

## Testing

### Manual Smoke Test

Run the validation script in PowerShell to test core flows:

```powershell
# Backend must be running on port 8787

# Create customer
$customer = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8787/api/customers `
  -ContentType 'application/json' `
  -Body (@{ full_name = 'Test User'; primary_phone = '7325551234' } | ConvertTo-Json)
Write-Output "Created customer $($customer.id)"

# Create ticket
$ticket = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8787/api/tickets `
  -ContentType 'application/json' `
  -Body (@{ customer_id = $customer.id; device_model_id = 1; issue_category = 'Test'; customer_approval_limit = 50; intake_staff = 'Test' } | ConvertTo-Json)
Write-Output "Created ticket $($ticket.id)"

# List tickets
$tickets = Invoke-RestMethod -Method Get -Uri http://127.0.0.1:8787/api/tickets
Write-Output "Total tickets: $($tickets.Count)"
```

### Frontend Build Test

From `tech-restore-desk/frontend`:

```powershell
npm run build
```

Should output:
```
âœ“ 44 modules transformed.
dist/index.html    0.37 kB â”‚ gzip:  0.28 kB
...
âœ“ built in 6.64s
```

If there are TypeScript errors, the build will fail.

## Code Style and Conventions

### Python (Backend)

- **Style**: Follow PEP 8 with 4-space indentation.
- **Type hints**: Use for function arguments and returns (seen in `database.py`).
- **Imports**: Group as (1) stdlib, (2) third-party, (3) local.
- **Naming**: `snake_case` for functions/variables, `PascalCase` for classes.

Example:
```python
from datetime import datetime
from typing import Optional
from fastapi import APIRouter
from app.models import TicketResponse

def get_ticket_by_id(conn, ticket_id: int) -> Optional[dict]:
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tickets WHERE id = ?', (ticket_id,))
    return cursor.fetchone()
```

### TypeScript (Frontend)

- **Style**: Follow ESLint config (Vite default).
- **Type hints**: Export types for all API data structures.
- **Naming**: `camelCase` for variables/functions, `PascalCase` for components/types.
- **Async**: Use `async/await` over `.then()`.

Example:
```typescript
export type Ticket = {
  id: number;
  status: string;
  created_at: string;
};

export async function getTicket(id: number): Promise<Ticket> {
  const res = await fetch(`/api/tickets/${id}`);
  if (!res.ok) throw new Error(`Ticket ${id} not found`);
  return res.json();
}
```

### SQL

- **Indentation**: 2-space for readability.
- **Naming**: Lowercase table names, snake_case columns.
- **Syntax**: Use parameterized queries (`?` placeholders) to prevent SQL injection.

Example:
```python
cursor.execute(
  'INSERT INTO tickets (customer_id, status, created_at) VALUES (?, ?, ?)',
  (customer_id, 'New Intake', datetime.now())
)
```

## File Organization Rules

- **Backend route files**: One responsibility per file (e.g., `routes/tickets.py` handles ticket endpoints only).
- **Frontend page files**: Each page is a separate React component (e.g., `pages/TicketDetailPage.tsx`).
- **API types**: All API types live in `src/api/tickets.ts` (centralized for consistency).
- **Database logic**: All SQL queries and business rules go in `app/database.py` (single source of truth).

## Common Tasks

### Restarting Services

If you see stale data or 404 errors after code changes:

1. **Kill backend**: Ctrl+C in the backend terminal.
2. **Kill frontend**: Ctrl+C in the frontend terminal (or Ctrl+K to close Vite HMR).
3. **Restart backend**: `uvicorn app.main:app --reload --host 127.0.0.1 --port 8787`
4. **Restart frontend**: `npm run dev -- --host 127.0.0.1`
5. **Refresh browser**: F5 or Ctrl+Shift+R (hard refresh).

### Adding a New Page

1. Create `src/pages/MyNewPage.tsx`:
   ```typescript
   export function MyNewPage() {
     return <div><h2>My New Page</h2></div>;
   }
   ```

2. Add route in `src/routes/`:
   ```typescript
   import { MyNewPage } from '../pages/MyNewPage';
   // In your router config:
   { path: '/my-new-page', element: <MyNewPage /> }
   ```

3. Add nav link in `src/components/AppShell.tsx`:
   ```typescript
   <a href="/my-new-page">My New Page</a>
   ```

### Installing Dependencies

**Backend** (from `backend/`):
```powershell
.venv\Scripts\Activate.ps1
pip install <package-name>
pip freeze > requirements.txt  # Update requirements.txt
```

**Frontend** (from `frontend/`):
```powershell
npm install <package-name>
npm install --save-dev <dev-package>  # For dev dependencies
```

## Troubleshooting

### Backend won't start: `Address already in use`
Port 8787 is already in use. Either:
- Kill the existing process: `Get-Process | Where-Object { $_.Handles -gt 100 } | Stop-Process`
- Use a different port: `uvicorn app.main:app --port 8888`

### Frontend shows `Cannot GET /`
Vite dev server is not running or crashed. Check the frontend terminal for errors. Restart it.

### API returns `404 Not Found` after adding a route
The backend needs to be restarted to pick up new route registrations. Kill and restart the backend.

### TypeScript errors in build: `Property 'X' does not exist`
Ensure the TypeScript type matches the backend response. Add missing fields to the type in `src/api/tickets.ts`.

### SQLite `database is locked` error
Multiple processes are writing to the database simultaneously, or a transaction is stuck. Restart the backend.

## Deployment Checklist (Future)

- [ ] No `console.log()` in production code.
- [ ] No hardcoded API URLs (use config).
- [ ] All error handling has user-facing messages.
- [ ] Database has automated backup script.
- [ ] Frontend build passes without warnings.
- [ ] Backend runs without errors at startup.
- [ ] All smoke tests pass.

## Further Reading

- [ARCHITECTURE.md](ARCHITECTURE.md) â€” System design and trade-offs.
- [API_REFERENCE.md](API_REFERENCE.md) â€” Complete API endpoint documentation.
- [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) â€” What's done, what's planned.
- FastAPI docs: https://fastapi.tiangolo.com
- React docs: https://react.dev
- TypeScript docs: https://www.typescriptlang.org


