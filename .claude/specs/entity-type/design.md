# Entity Type Feature - Design

## Overview
Add a `type` field to Company and Project entities throughout the stack using **enumerations** for type safety. The UI interprets the enum value as a visual color.

## Enum Definition

The type represents the **lifecycle stage** of a company or project.

| Enum Value | Display Name | Color | Hex |
|------------|--------------|-------|-----|
| `discovery` | Discovery | Ocean Blue | `#0077B6` |
| `potential` | Potential | Chrome Yellow | `#FFD60A` |
| `matured` | Matured | Ocean Green | `#2A9D8F` |
| `engaged` | Engaged | Moss Green | `#606C38` |
| `active` | Active | Coral Red | `#E63946` |
| `dormant` | Dormant | Grey | `#6C757D` |

**Note:** Colors are fixed and do not change with theme.

### Python (Core + Backend)
```python
# src/taskyn/db/enums.py (new file)
from enum import Enum

class EntityType(str, Enum):
    """Lifecycle stage for companies and projects."""
    DISCOVERY = "discovery"
    POTENTIAL = "potential"
    MATURED = "matured"
    ENGAGED = "engaged"
    ACTIVE = "active"
    DORMANT = "dormant"
```

Using `str, Enum` allows the enum to serialize as a string in JSON while providing type safety in Python.

### TypeScript (Frontend)
```typescript
// src/types/index.ts
export const ENTITY_TYPES = ['discovery', 'potential', 'matured', 'engaged', 'active', 'dormant'] as const;
export type EntityType = typeof ENTITY_TYPES[number];

// Fixed colors (theme-independent)
export const ENTITY_TYPE_COLORS: Record<EntityType, string> = {
  discovery: '#0077B6',  // Ocean Blue
  potential: '#FFD60A',  // Chrome Yellow
  matured: '#2A9D8F',    // Ocean Green
  engaged: '#606C38',    // Moss Green
  active: '#E63946',     // Coral Red
  dormant: '#6C757D',    // Grey
};
```

### SQLite (Database)
```sql
-- CHECK constraint enforces valid values
type TEXT DEFAULT 'discovery' CHECK (type IN ('discovery', 'potential', 'matured', 'engaged', 'active', 'dormant'))
```

## Architecture Impact

```
┌─────────────────────────────────────────────────────────────────────┐
│                           FRONTEND                                   │
│  types/index.ts: EntityType union type                              │
│  CompaniesPage.tsx: ENTITY_TYPE_TO_GRADIENT mapping                 │
│  - Reads company.type (EntityType)                                  │
│  - Maps EntityType → gradient for display                           │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        WEB BACKEND (FastAPI)                         │
│  schemas: Use EntityType enum in Pydantic models                    │
│  routes: Pass EntityType to MCP tools                               │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          MCP SERVER                                  │
│  Uses EntityType enum for type hints                                │
│  Validates type parameter against enum values                       │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                            CORE                                      │
│  db/enums.py: EntityType enum definition                            │
│  company.py, project.py: Use EntityType enum                        │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          DATABASE                                    │
│  CHECK constraint enforces enum values                              │
│  Stored as TEXT for readability                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## File Changes

### 1. Database Layer

**File: `src/taskyn/db/enums.py`** (NEW)
```python
from enum import Enum

class EntityType(str, Enum):
    """Lifecycle stage for companies and projects."""
    DISCOVERY = "discovery"
    POTENTIAL = "potential"
    MATURED = "matured"
    ENGAGED = "engaged"
    ACTIVE = "active"
    DORMANT = "dormant"
```

**File: `src/taskyn/db/schema.sql`**
```sql
-- companies table
type TEXT DEFAULT 'discovery' CHECK (type IN ('discovery', 'potential', 'matured', 'engaged', 'active', 'dormant'))

-- projects table
type TEXT DEFAULT 'discovery' CHECK (type IN ('discovery', 'potential', 'matured', 'engaged', 'active', 'dormant'))
```

**File: `src/taskyn/db/models.py`**
```python
from taskyn.db.enums import EntityType

class Company(BaseModel):
    # ... existing fields
    type: EntityType = EntityType.DISCOVERY

class Project(BaseModel):
    # ... existing fields
    type: EntityType = EntityType.DISCOVERY
```

### 2. Core Layer

**File: `src/taskyn/core/company.py`**
```python
from taskyn.db.enums import EntityType

def create_company(
    name: str,
    description: str | None = None,
    type: EntityType = EntityType.DISCOVERY,  # NEW
    actor: str | None = None,
) -> Company:
    # Insert type.value into DB

def update_company(
    company_id: str,
    name: str | None = None,
    description: str | None = None,
    type: EntityType | None = None,  # NEW
    actor: str | None = None,
) -> Company | None:
    # Update type if provided
```

**File: `src/taskyn/core/project.py`**
- Same pattern as company.py

### 3. MCP Layer

**File: `src/taskyn/mcp/server.py`**
```python
from taskyn.db.enums import EntityType

@mcp.tool()
def pm_create_company(
    name: str,
    description: str | None = None,
    type: str = "discovery",  # String for MCP compatibility
) -> dict:
    entity_type = EntityType(type)  # Validate and convert
    company = create_company(name, description, type=entity_type, actor=get_actor())
    return company.model_dump()
```

### 4. Web Backend Layer

**File: `src/taskyn/web/backend/schemas/companies.py`**
```python
from taskyn.db.enums import EntityType

class CompanyCreate(BaseModel):
    name: str
    description: str | None = None
    type: EntityType = EntityType.DISCOVERY

class CompanyUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    type: EntityType | None = None

class CompanyResponse(BaseModel):
    # ... existing fields
    type: EntityType
```

**File: `src/taskyn/web/backend/routes/companies.py`**
- Pass `data.type.value` to MCP tool (string for JSON-RPC)

### 5. Frontend Layer

**File: `src/taskyn/web/frontend/src/types/index.ts`**
```typescript
// Entity type enum (lifecycle stages)
export const ENTITY_TYPES = ['discovery', 'potential', 'matured', 'engaged', 'active', 'dormant'] as const;
export type EntityType = typeof ENTITY_TYPES[number];

export interface Company {
  // ... existing fields
  type: EntityType;
}

export interface CompanyCreate {
  name: string;
  description?: string;
  type?: EntityType;
}
```

**File: `src/taskyn/web/frontend/src/pages/CompaniesPage.tsx`**
```typescript
import { ENTITY_TYPES, ENTITY_TYPE_COLORS, type EntityType } from '@/types';

// State: store the selected EntityType (not index)
const [createType, setCreateType] = useState<EntityType>('discovery');

// Color picker UI - iterate over ENTITY_TYPES, display their colors
<div className="color-picker">
  {ENTITY_TYPES.map((type) => (
    <div
      key={type}
      className={`color-option${createType === type ? ' selected' : ''}`}
      style={{ background: ENTITY_TYPE_COLORS[type] }}
      onClick={() => setCreateType(type)}
      title={type}  // Show type name on hover
    />
  ))}
</div>

// When creating company, send the type
await companiesApi.create({
  name: createName.trim(),
  description: createDesc.trim() || undefined,
  type: createType,  // EntityType string sent to API
});

// Display company icon with type color
const color = ENTITY_TYPE_COLORS[company.type];

// For gradient effect on icon backgrounds:
function getTypeGradient(type: EntityType): string {
  const color = ENTITY_TYPE_COLORS[type];
  return `linear-gradient(135deg, ${color}, ${color}dd)`;
}
```

**Mapping Flow:**
```
UI Color Picker           State                API Request
┌─────────────┐          ┌─────────────┐      ┌─────────────┐
│ Click blue  │ ──────►  │ 'discovery' │ ───► │ type:       │
│ swatch      │          │             │      │ "discovery" │
└─────────────┘          └─────────────┘      └─────────────┘

API Response             Display
┌─────────────┐          ┌─────────────┐
│ type:       │ ──────►  │ Show icon   │
│ "discovery" │          │ with #0077B6│
└─────────────┘          └─────────────┘
```

## Benefits of Enum Approach
1. **Type safety** - Invalid values caught at compile/runtime
2. **Self-documenting** - Clear what values are allowed
3. **IDE support** - Autocomplete and refactoring
4. **Database integrity** - CHECK constraint prevents invalid data
5. **Single source of truth** - Enum defined once, used everywhere

## Migration Strategy
- SQLite `DEFAULT 'discovery'` handles new rows
- Existing rows without type column will get `discovery` via migration
- The CHECK constraint only applies to new/updated rows

## Testing
- Unit tests: Verify enum validation in core functions
- API tests: Verify enum serialization/deserialization
- Frontend tests: Verify TypeScript type checking
