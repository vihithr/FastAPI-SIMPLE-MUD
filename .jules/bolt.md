
## 2024-10-16 - Prevent N+1 queries in SQLAlchemy
**Learning:** This codebase defaults to lazy loading for all SQLAlchemy relationships. Fetching items for a character's inventory and equipment triggers an N+1 query issue since it loops over `inventory_items` and calls `.item` directly.
**Action:** Next time working with lists of database records which access relationships in a loop, actively look for and apply `.options(joinedload(...))` directly in the query.
