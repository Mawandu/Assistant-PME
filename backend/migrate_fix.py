
from database import engine
from sqlalchemy import text

def add_column():
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE products ADD COLUMN data_source_id UUID REFERENCES data_sources(id) ON DELETE CASCADE;"))
            conn.commit()
            print("Successfully added columns.")
        except Exception as e:
            print(f"Error (maybe already exists): {e}")

if __name__ == "__main__":
    add_column()
