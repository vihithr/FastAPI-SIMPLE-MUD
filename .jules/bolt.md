## 2024-05-18 - SQLAlchemy N+1 Lazy Loading
**Learning:** Default lazy loading on relationships like `Inventory.item` and `Equipment.item` causes N+1 query bottlenecks when iterating over collections.
**Action:** Always use `.options(joinedload(...))` on relationship attributes accessed in loops or immediately after querying.
