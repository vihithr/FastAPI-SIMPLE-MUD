## 2024-05-24 - N+1 Query in Inventory and Equipment Loading
**Learning:** `get_character_inventory` and `get_character_equipment` load items via lazy relationships (e.g. `inv_item.item`), leading to O(N) queries where N is the number of inventory/equipment items. This happens because SQLAlchemy relationships like `Inventory.item` default to lazy loading.
**Action:** Use `.options(joinedload(Inventory.item))` and `.options(joinedload(Equipment.item))` in queries to eagerly load related items and eliminate the N+1 problem, reducing database load.
