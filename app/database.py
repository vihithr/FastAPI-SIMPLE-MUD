from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# SQLite数据库路径
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./mud_game.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # SQLite需要这个参数
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库，创建所有表"""
    Base.metadata.create_all(bind=engine)
    # 运行迁移以添加新列
    migrate_db()


def migrate_db():
    """数据库迁移 - 添加新列和表"""
    from sqlalchemy import text, inspect
    
    inspector = inspect(engine)
    
    # 检查 rooms 表是否存在 special_properties 列
    if 'rooms' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('rooms')]
        if 'special_properties' not in columns:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE rooms ADD COLUMN special_properties JSON DEFAULT '{}'"))
                conn.commit()
                print("Added special_properties column to rooms table")
    
    # 检查 characters 表是否存在战斗状态列
    if 'characters' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('characters')]
        if 'in_combat_with' not in columns:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE characters ADD COLUMN in_combat_with INTEGER"))
                conn.commit()
                print("Added in_combat_with column to characters table")
        if 'combat_turn' not in columns:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE characters ADD COLUMN combat_turn INTEGER DEFAULT 0"))
                conn.commit()
                print("Added combat_turn column to characters table")
    
    # 确保所有新表都已创建
    Base.metadata.create_all(bind=engine)