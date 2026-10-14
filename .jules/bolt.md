## 2024-10-15 - FastAPI SQLAlchemy N+1 Queries
**Learning:** Found N+1 query vulnerability when iterating over fetched characters' inventory/equipment relationships in `app/game/items.py` due to lazy loading missing `joinedload`.
**Action:** Use `.options(joinedload(Model.relation))` to eager load related models and eliminate unnecessary database round trips in SQLAlchemy queries.
