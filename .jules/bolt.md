
## 2024-05-24 - Resolve N+1 query bottleneck in SQLAlchemy relation loops
**Learning:** In this project, SQLAlchemy relationships such as `Inventory.item` and `Equipment.item` default to lazy loading. Iterating over query results and accessing these relation properties (like checking `.item.name`) inside a loop results in an N+1 query performance bottleneck.
**Action:** Use `.options(joinedload(...))` on queries fetching collections when their relation properties will be accessed later in the logic, to load everything efficiently in a single query.
