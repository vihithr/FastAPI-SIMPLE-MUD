## 2024-05-18 - SQLAlchemy N+1 Query in Game Items
**Learning:** The project uses lazy loading by default for SQLAlchemy relationships. Fetching a list of Inventory or Equipment items and iterating over them to access their `.item` attribute triggers an N+1 query problem, which severely impacts performance for characters with many items or equipment.
**Action:** Use `.options(joinedload(Model.relationship))` like `.options(joinedload(Inventory.item))` to eagerly load related items whenever retrieving collections of `Inventory` or `Equipment` that require data from the related `Item` table.
