"""
Initialize database with sample data for development
"""
from app.db.database import SessionLocal, init_db
from app.models import User
from app.core.security import get_password_hash


def create_sample_user():
    """Create a sample user for testing"""
    db = SessionLocal()

    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.id == 1).first()

        if not existing_user:
            # Create sample user
            sample_user = User(
                id=1,
                email="demo@lovable.dev",
                username="demo",
                hashed_password=get_password_hash("demo123"),
                is_active=True,
            )

            db.add(sample_user)
            db.commit()
            print("✅ Sample user created:")
            print(f"   Email: demo@lovable.dev")
            print(f"   Password: demo123")
        else:
            print("ℹ️  Sample user already exists")

    except Exception as e:
        print(f"❌ Error creating sample user: {e}")
        db.rollback()
    finally:
        db.close()


def main():
    """Initialize database and create sample data"""
    print("🚀 Initializing database...")

    # Create tables
    init_db()
    print("✅ Database tables created")

    # Create sample user
    create_sample_user()

    print("\n🎉 Database initialization complete!")
    print("\n📝 Next steps:")
    print("   1. Copy .env.example to .env")
    print("   2. Add your OPENAI_API_KEY to .env")
    print("   3. Run: python run.py")
    print("   4. Visit: http://localhost:8000/docs")


if __name__ == "__main__":
    main()
