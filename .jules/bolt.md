## 2023-11-20 - Fix N+1 Queries in SQLAlchemy ORM
**Learning:** By default, SQLAlchemy relationships (like `Inventory.item` or `Equipment.item`) are lazily loaded. In loops over items like getting inventory or equipment for a character, this causes an N+1 query problem, creating a performance bottleneck when a player has many items.
**Action:** Use `.options(joinedload(...))` when querying collections where related models will be accessed within a loop, to fetch all required data in a single SQL query.
