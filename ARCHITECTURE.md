# DBBasic Architecture Documentation

## Overview
DBBasic is a Config-Driven Development (CDD) framework that eliminates 99% of boilerplate code by replacing traditional programming with declarative YAML configurations.

## Core Philosophy: "41 Lines Replaces 50,000 Lines"
Instead of writing thousands of lines of CRUD code, define complete applications in simple YAML config files.

## Current System Status

### ✅ Implemented Components

#### 1. **CRUD Engine** (`dbbasic_crud_engine.py`)
**Complete CRUD Operations:**
- ✅ **CREATE** - `POST /api/{resource_name}`
- ✅ **READ/LIST** - `GET /api/{resource_name}`
- ✅ **READ/DISPLAY** - `GET /api/{resource_name}/{record_id}`
- ✅ **UPDATE** - `PUT /api/{resource_name}/{record_id}`
- ✅ **DELETE** - `DELETE /api/{resource_name}/{record_id}`

**Features:**
- Auto-generated database schemas from YAML
- Real-time WebSocket updates on all operations
- Hot config reloading with file watchers
- Complete HTML interface generation
- Hook system for business logic integration

#### 2. **AI Service Builder** (`dbbasic_ai_service_builder.py`)
- Generates missing hook services automatically
- Integrates with CRUD Engine for business logic
- Config-driven service generation

#### 3. **Real-time Monitor** (`realtime_monitor.py`)
- WebSocket-based live monitoring
- Receives all CRUD operation events
- Foundation for audit trail and history

### ❌ Missing Critical Components

#### **Magic Fields & Timestamps**
- **Current Status:** Config recognizes `auto_now`, `auto_now_add` but doesn't populate them
- **Missing:** Automatic timestamp setting on CREATE/UPDATE operations
- **Impact:** No audit trail timestamps

#### **Permissions & Security**
- **Current Status:** Config defines permissions but not enforced
- **Missing:** Authentication integration, role-based access control
- **Needed:** Field-level security (protected fields, encryption)

#### **Event Sourcing Architecture**
- **Current Status:** Sends full data snapshots via WebSocket
- **Missing:** True event sourcing with before/after states
- **Opportunity:** Enable reversible operations and complete audit trails

## Architectural Insights

### **Event-Driven Messaging System**
Currently implements a **snapshot-based** real-time system:

```python
# Every CRUD operation broadcasts updates
await self._broadcast_update(resource_name)

# Sends complete dataset after each change
{
  "type": "data_update",
  "records": [{"id": 1, "name": "Updated", "email": "new@email.com"}]
}
```

**Enhancement Opportunity:** True event sourcing would enable:
- Reversible operations
- Complete audit trails
- Config-driven business rules
- Automatic compliance logging

### **Config-Driven Security**
**Vision:** Field-level security through configuration:

```yaml
fields:
  password:
    type: password
    security:
      protected: true          # Never in API responses
      hash_algorithm: bcrypt   # Auto-hash on save

  email:
    type: email
    security:
      pii: true              # Mark as PII
      encrypt: true          # Encrypt at rest
      mask_in_logs: true     # Redact in audit logs
```

### **Event-Driven Business Logic**
**Future Vision:** Replace hook code with config rules:

```yaml
events:
  before_update:
    - rule: credit_limit_validation
      condition: "credit_limit > 50000"
      action: require_approval
      approver_role: manager
```

## System Integration

### **Service Architecture**
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   CRUD Engine   │    │ AI Service       │    │ Real-time       │
│   Port 8005     │◄──►│ Builder          │◄──►│ Monitor         │
│                 │    │ Port 8003        │    │ Port 8004       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Config Files    │    │ Generated        │    │ WebSocket       │
│ *_crud.yaml     │    │ Services         │    │ Event Stream    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### **WebSocket Event Flow**
```
CRUD Operation → Database → WebSocket Broadcast → Real-time Monitor
     ↓              ↓              ↓                    ↓
Config Rules → Auto Schema → Live Updates → Event History
```

## Testing Infrastructure

### ✅ **Implemented Tests**
- **API Tests** (`test_crud_engine_api.py`) - Complete CRUD validation
- **WebSocket Tests** (`test_websocket_realtime.py`) - Real-time functionality
- **Selenium Tests** (`test_selenium_web_interfaces.py`) - Browser automation
- **System Tests** (`test_comprehensive_system.py`) - End-to-end validation

### **Test Results**
- All CRUD operations working correctly
- WebSocket real-time updates functional
- Config hot-reload operational
- Cross-service integration verified

## Next Development Priorities

1. **Magic Fields Implementation**
   - Auto-populate `created_at`, `updated_at` timestamps
   - Add `created_by`, `updated_by` user tracking

2. **Event Sourcing Enhancement**
   - Capture before/after states in events
   - Enable reversible operations
   - Persistent audit trail in Real-time Monitor

3. **Security Implementation**
   - Field-level protection and encryption
   - Permission enforcement
   - Authentication integration

4. **Config-Driven Rules Engine**
   - Replace hook code with YAML business rules
   - Event-triggered workflows
   - Approval processes

## Performance Notes
- **DuckDB Backend:** Achieving 402M rows/sec performance
- **WebSocket Efficiency:** Real-time updates without polling
- **Config Hot-reload:** Zero-downtime configuration changes

---

*This document is updated as the system evolves. Last updated: 2025-09-19*