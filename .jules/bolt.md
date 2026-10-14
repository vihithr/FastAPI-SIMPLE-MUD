## 2026-10-14 - N+1 Query in ORM Relations
**Learning:** Found an N+1 query performance bottleneck in `app/game/items.py` when iterating through `Inventory` or `Equipment` objects and accessing their related `item` object. Because the `item` relationship is lazy-loaded by default, iterating and accessing it triggers a new query for every single item, degrading performance exponentially for players with large inventories.
**Action:** Use SQLAlchemy's `.options(joinedload(Model.relation))` to eagerly load related objects when fetching collections that will be iterated over.
