# DBBasic Glossary of Terms

## Core Concepts

### Model-Config Paradigm
The revolutionary approach where applications are defined entirely through configuration files instead of code. The model (data) and config (behavior) together create complete applications without traditional programming. Crucially, this config is:
- **Machine-parseable** - Software can execute it directly
- **AI-writable** - AI can generate and modify it
- **Human-readable** - Anyone can understand and edit it
- **Universal** - Not limited to web apps - can define games, IoT systems, enterprise software, anything

### Config-Driven Development (CDD)
A development methodology where features are added by modifying configuration files rather than writing code. Changes to config automatically update the running system.

### Human+AI+Software Framework
A framework designed to be simultaneously:
1. **Writable by humans** - Simple YAML anyone can understand
2. **Writable by AI** - AI can generate and modify configs
3. **Executable by software** - Regular programs parse and run the config
4. **Far beyond web frameworks** - Can build games, enterprise systems, anything

This triple compatibility means AI can write config that software executes, while humans can still understand and modify it.

## DBBasic Components

### Config File (.dbbasic)
A YAML file containing the complete specification of an application including data models, pages, forms, views, and business rules. Typically 50-200 lines replacing 50,000+ lines of traditional code.

### Data/Model Section
The part of config that defines data structures, relationships, and constraints. Generates database schema and CRUD operations automatically.
```yaml
data:
  users: [id, name, email]
  orders: [id, user_id, total]
```

### Pages Section
Defines web pages and their content. Each page is a route that serves HTML with specified data.
```yaml
pages:
  /dashboard: "User dashboard with recent activity"
```

### Views Section
SQL queries or data transformations that create read-only data views. Used for reports, analytics, and dashboards.
```yaml
views:
  top_customers: "SELECT * FROM customers ORDER BY revenue DESC LIMIT 10"
```

### Forms Section
Defines data input forms with validation rules. Can be auto-generated from data models or customized.
```yaml
forms:
  user_form: auto
  order_form:
    fields: [customer, products, quantity]
    validate: "quantity > 0"
```

### AI Services
Natural language descriptions that AI converts into executable code. Services handle complex business logic without human programming.
```yaml
ai_services:
  calculate_discount:
    description: "Apply tiered discounts based on customer loyalty and order size"
```

### Service Hooks
Connection points where AI services are triggered by system events (before_save, after_update, etc.).
```yaml
hooks:
  before_save: "ai://validate_inventory"
  after_order: "ai://send_confirmation_email"
```

### Specifications
Human-readable descriptions of features that bridge requirements and config. The middle layer between what users want and what the system does.

### Conformance Standards
Predefined patterns and rules that AI follows to ensure security, performance, and compliance (OWASP, PCI-DSS, WCAG, etc.).

## Performance Terms

### Polars
Rust-based DataFrame library that processes data 10-50x faster than Pandas. Core engine of DBBasic's data processing.

### DuckDB
In-process SQL database optimized for analytics. Provides SQL capabilities at 402 million rows/second.

### Parquet Files
Columnar storage format for efficient data storage and retrieval. Used for persistent data storage in DBBasic.

### 402M Rows/Sec
The benchmark processing speed achieved by DBBasic's Polars+DuckDB engine, making traditional caching obsolete.

## Development Lifecycle Terms

### 30-Minute Feature
The standard time to add a new feature in DBBasic (vs 2-4 weeks traditionally). Includes specification, config change, and deployment.

### Config Change
The act of modifying a DBBasic config file to add, remove, or modify features. Triggers automatic system updates.

### Auto-Deploy
The process where config changes automatically update the running system without traditional deployment pipelines.

### Instant Rollback
Ability to revert features by reverting git commits. Takes 3 seconds vs hours/days traditionally.

## Architecture Terms

### Single Source of Truth
The principle that all application logic lives in one config file, eliminating scattered code across hundreds of files.

### Progressive Disclosure
Config design pattern where simple declarations expand to detailed implementations as needed.
```yaml
# Simple
users: "manage users"

# Detailed (when needed)
users:
  fields: [id, email, name]
  validation: ...
  permissions: ...
```

### Declarative Over Imperative
Describing what you want rather than how to do it. Core principle of DBBasic config.
```yaml
# Declarative (DBBasic)
show: "user dashboard"

# Imperative (Traditional)
def show_dashboard():
  user = get_user()
  data = fetch_data(user)
  return render(template, data)
```

## Migration Terms

### Config Migration
Converting traditional applications (Rails, Django, etc.) to DBBasic config format. Typically takes hours vs months for rewrites.

### Universal Converter
AI-powered system that reads any codebase and generates equivalent DBBasic config.

### Meta-Migration
The process of converting entire frameworks and their patterns to DBBasic equivalents.

## Scaling Terms

### Config Scaling
Scaling applications by changing config values rather than re-architecting.
```yaml
scaling:
  type: single_server  # Change to: distributed
  regions: [us-east]   # Change to: [us-east, eu-west, asia]
```

### Predictive Scaling
Automatic scaling based on growth patterns without manual intervention.

### Zero-Downtime Updates
Ability to update applications instantly through config changes without service interruption.

## Comparison Terms

### Traditional Development
- **MVC/MVT**: Model-View-Controller/Template patterns used by Rails, Django
- **Microservices**: Distributed architecture DBBasic replaces with config
- **Boilerplate**: Repetitive code DBBasic eliminates
- **Sprint**: 2-week development cycle DBBasic compresses to 30 minutes

### No-Code vs Low-Code vs Beyond-Code vs DBBasic
- **No-Code**: Limited, template-based platforms with restricted capabilities
- **Low-Code**: Still requires some programming for complex features
- **Beyond-Code**: AI writes all code from descriptions
- **DBBasic**: Config that both AI and software can read/write/execute - not limited to web apps, can build anything from games to enterprise systems to embedded software

## Business Terms

### Time to Value
Time from idea to working feature. DBBasic: 30 minutes. Traditional: 2-4 weeks.

### Total Cost of Ownership (TCO)
Complete cost including development, maintenance, and operations. DBBasic reduces by 90%+.

### Developer Productivity
40x improvement in feature delivery speed with DBBasic vs traditional development.

## File Structure Terms

### Three-File Architecture
DBBasic apps consist of only:
1. `config.dbbasic` - Application specification
2. `data/store.parquet` - Data storage  
3. `services/` - AI-generated services

vs traditional apps with 50,000+ files.

## Command Terms

### dbbasic CLI
Command-line interface for DBBasic operations:
- `dbbasic server` - Start API server
- `dbbasic repl` - Interactive interface
- `dbbasic benchmark` - Performance testing
- `dbbasic routes` - Display all routes

## Revolutionary Concepts

### Post-Code Era
The period starting ~2025 where AI generates all code from human specifications, making traditional programming obsolete.

### Config as Code
The principle that configuration files are the new source code, version-controlled and deployed like traditional code but without complexity.

### AI-First Development
Development approach where AI is the primary code generator, not an assistant.

### Zero-Bug Architecture
Since humans don't write code and AI follows standards, bugs become nearly impossible.

## Standard Abbreviations

- **CDD**: Config-Driven Development
- **MCP**: Model-Config Paradigm  
- **TCO**: Total Cost of Ownership
- **CRUD**: Create, Read, Update, Delete
- **API**: Application Programming Interface
- **SQL**: Structured Query Language
- **YAML**: Yet Another Markup Language (config format)
- **JWT**: JSON Web Tokens (authentication)
- **OWASP**: Open Web Application Security Project
- **WCAG**: Web Content Accessibility Guidelines
- **PCI-DSS**: Payment Card Industry Data Security Standard
- **GDPR**: General Data Protection Regulation
- **HIPAA**: Health Insurance Portability and Accountability Act
- **SOC2**: Service Organization Control 2

## Usage Examples in Context

### Correct Usage
- "Update the **config** to add user avatars" ✓
- "The **AI service** handles payment processing" ✓
- "Deploy through **config change**" ✓
- "Use **progressive disclosure** for complex features" ✓

### Avoid These Terms
- "Write code for..." ✗ (Use: "Configure...")
- "Program the feature..." ✗ (Use: "Specify the feature...")
- "Debug the application..." ✗ (Use: "Adjust the config...")
- "Develop the module..." ✗ (Use: "Define in config...")

## Key Principles to Remember

1. **Config replaces code** - Everything is configuration
2. **Triple compatibility** - Humans write it, AI writes it, software executes it
3. **Universal application** - Not just web apps - games, IoT, enterprise, anything
4. **AI generates implementation** - From config or natural language descriptions
5. **Standards ensure quality** - Conformance standards guarantee best practices
6. **Speed is default** - 402M rows/sec is baseline performance
7. **Simplicity over complexity** - 50 lines > 50,000 lines
8. **Instant everything** - Deploy, rollback, scale in seconds
9. **No bugs possible** - Config can't have logic errors
10. **Version control native** - Git-first, every change tracked
11. **Beyond frameworks** - More powerful than Rails, Django, Spring combined
12. **Post-code era** - We don't develop software, we configure systems

---

*This glossary is a living document. As DBBasic evolves and new patterns emerge, terms will be added and refined.*