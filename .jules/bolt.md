## 2026-10-15 - Resolve N+1 query bottleneck in items system
**Learning:** SQLAlchemy relationships like `Inventory.item` or `Equipment.item` default to lazy loading, which creates N+1 query performance bottlenecks in iteration loops within `app/game/items.py`.
**Action:** Always use `.options(joinedload(...))` when querying these collections to ensure eager loading.
