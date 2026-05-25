import os
from app import create_app, db

app = create_app()

@app.cli.command("init-db")
def init_db():
    """Veritabanı tablolarını manuel oluşturmak için CLI komutu."""
    db.create_all()
    print("Veritabanı tabloları başarıyla oluşturuldu!")

if __name__ == '__main__':
    app.run(debug=True)
