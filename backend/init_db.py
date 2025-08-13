from database import engine, Base
from models import Hotel

print("Veritabanı tabloları oluşturuluyor...")
Base.metadata.create_all(bind=engine)
print("Tamamlandı.")
