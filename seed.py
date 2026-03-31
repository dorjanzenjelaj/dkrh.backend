from app.core.db import SessionLocal
from app.seeds.run import (
    seed_permissions,
    seed_role_permissions,
    seed_roles,
    seed_super_admin,
)


def main() -> None:
    db = SessionLocal()
    try:
        seed_roles(db)
        seed_permissions(db)
        seed_role_permissions(db)
        seed_super_admin(
            db=db,
            username="admin",
            email="admin@dkrh.oshee.al",
            full_name="System Administrator",
            password="Admin123!!",
        )
        print("Seeding completed successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    main()