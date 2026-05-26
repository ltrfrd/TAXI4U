# MIGRATIONS — Database Migration Guide

Database migrations are one of the most dangerous categories of code change. A bad migration can lose data, break production for hours, or make rollback impossible. This document defines how migrations are written, reviewed, and applied for this project.

---

## Tool

We use **Alembic** for all schema changes. No raw SQL on the production database. No manual schema edits. Ever.

---

## The Migration Chain

Migrations live in `migrations/versions/`. Each file has a sequential ID and a parent reference. Together they form a chain:

```
0000_initial.py
  → 0001_core_models.py
    → 0002_add_audit_fields.py
      → 0003_add_special_routes.py
        → ...
```

The chain is sacred. Once a migration is applied to any environment beyond local development, it is **never modified**. Corrections happen in new migrations.

---

## Naming Convention

Migration files follow this format:

```
{4-digit-number}_{snake_case_description}.py
```

Examples:
```
0001_core_models.py
0007_add_special_routes.py
0014_index_trips_status.py
```

The 4-digit number is sequential and matches the order they were created. Use the next available number.

---

## Creating a New Migration

### Step 1 — Make your model change
Edit the SQLAlchemy model in `app/models/`.

### Step 2 — Auto-generate the migration
```bash
alembic revision --autogenerate -m "add_some_field_to_trips"
```

This creates a new file in `migrations/versions/`.

### Step 3 — Review the generated migration
**Never trust autogenerate blindly.** Always read every line. Common issues:
- It may miss enum changes
- It may drop a column you didn't intend to drop
- It may reorder operations incorrectly
- It may not pick up index changes

### Step 4 — Test it locally
```bash
alembic upgrade head        # apply it
alembic downgrade -1        # roll it back
alembic upgrade head        # apply again
```

If the migration can't be safely rolled back, that's a red flag — see "Irreversible Migrations" below.

### Step 5 — Commit
The migration file goes into the same PR as the model change.

---

## Rules for Safe Migrations

### Rule 1 — One Concern Per Migration
A migration does one thing. Don't combine an unrelated schema change with a data backfill.

```
✓ 0007_add_zone_is_active_field.py
✓ 0008_backfill_zone_is_active.py

✗ 0007_add_zone_is_active_and_seed_data_and_fix_index.py
```

### Rule 2 — Always Write Both `upgrade()` and `downgrade()`
Every migration must be reversible. If you can't write a sensible downgrade, you probably need to redesign the migration.

### Rule 3 — Never Edit an Applied Migration
Once a migration runs on staging or production, it is frozen. To correct it:
1. Create a new migration that fixes the issue
2. Document why in the migration's docstring

### Rule 4 — Be Careful with Defaults
Adding a `NOT NULL` column without a default on a large table will lock the table during migration. Always provide a default, then drop the default in a follow-up migration if you want.

```python
# Step 1 — add nullable column with default
op.add_column('trips', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))

# Step 2 (later) — drop the default
op.alter_column('trips', 'is_active', server_default=None)
```

### Rule 5 — Indexes on Large Tables
Adding an index can lock a table. On large tables, use PostgreSQL's `CREATE INDEX CONCURRENTLY`:

```python
op.execute('CREATE INDEX CONCURRENTLY idx_trips_status ON trips(status)')
```

Note: `CONCURRENTLY` cannot run inside a transaction, so the migration must opt out.

### Rule 6 — Backfill Data in Separate Migrations
Don't combine schema and data changes. Schema change first, then data backfill in the next migration.

---

## Enum Changes

PostgreSQL enums are particularly tricky. Adding a value is fine. Removing or renaming requires care.

### Adding a Value
```python
op.execute("ALTER TYPE tripstatus ADD VALUE 'NEW_VALUE'")
```

Cannot be done inside a transaction in older PostgreSQL versions — opt out if needed.

### Removing a Value
Cannot be done directly. You have to:
1. Create a new enum type without the value
2. Migrate the column to use the new type
3. Drop the old type

This is painful — prefer to leave unused enum values in place.

---

## Applying Migrations

### Local Development
```bash
alembic upgrade head
```

### Staging
Applied automatically by the deployment pipeline.

### Production

**Before any production migration:**
1. Database is backed up
2. Migration is tested on a staging environment with production-like data
3. Migration is reviewed by at least one other engineer
4. Maintenance window is scheduled if the migration may lock tables

**Applying:**
```bash
alembic upgrade head
```

**If something goes wrong:**
1. Stop the application
2. Restore from backup if data was corrupted
3. Otherwise: `alembic downgrade -1` and investigate

---

## Irreversible Migrations

Some migrations cannot be safely reversed (data deletion, irreversible transformations). For these:
1. The migration's `downgrade()` should `raise NotImplementedError` with a clear message
2. The migration file must contain a comment explaining why
3. Extra care in review — irreversible migrations need a second pair of eyes

```python
def downgrade():
    raise NotImplementedError(
        "This migration deletes archived trip data and cannot be reversed. "
        "Restore from backup if needed."
    )
```

---

## Common Migration Patterns

### Adding a Soft Delete Field
```python
def upgrade():
    op.add_column('zones', sa.Column('is_active', sa.Boolean(), 
        nullable=False, server_default='true'))

def downgrade():
    op.drop_column('zones', 'is_active')
```

### Adding Audit Fields
```python
def upgrade():
    op.add_column('vehicles', sa.Column('created_by_user_id', sa.Integer(),
        sa.ForeignKey('users.id'), nullable=True))
    op.add_column('vehicles', sa.Column('updated_by_user_id', sa.Integer(),
        sa.ForeignKey('users.id'), nullable=True))

def downgrade():
    op.drop_column('vehicles', 'updated_by_user_id')
    op.drop_column('vehicles', 'created_by_user_id')
```

Note: nullable at first because existing records have no creator. Make non-nullable later via backfill + alter.

### Renaming a Column
```python
def upgrade():
    op.alter_column('trips', 'old_name', new_column_name='new_name')

def downgrade():
    op.alter_column('trips', 'new_name', new_column_name='old_name')
```

Application code must be updated in the same release.

---

## Reviewing a Migration

When reviewing a migration PR, ask:

- [ ] Is the migration file numbered correctly (next in sequence)?
- [ ] Does it do only one thing?
- [ ] Is `downgrade()` actually correct, or just a placeholder?
- [ ] Will it lock any large table?
- [ ] Are defaults handled safely?
- [ ] Are indexes added concurrently where appropriate?
- [ ] Is there a test that exercises the new schema?
- [ ] Has the corresponding model change been reviewed?

---

## Disaster Recovery

If a migration corrupts production data:
1. **Stop the application immediately** — don't let more bad data accumulate
2. **Assess the damage** — what tables, what rows, what fields?
3. **Restore from backup** — pre-migration backup is your safety net
4. **Forensic** — figure out what went wrong before re-running anything
5. **Post-mortem** — write up what happened, add to this document as a new section

Backups are taken before every production migration. No exceptions.
