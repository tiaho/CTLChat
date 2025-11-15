"""Initialize and test the CTLChat database.

This script:
1. Creates the database tables
2. Optionally creates sample data for testing
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from database import Database
from config import settings
from loguru import logger


def init_database(create_sample_data: bool = False):
    """Initialize the database.

    Args:
        create_sample_data: Whether to create sample data for testing
    """
    logger.info("Initializing CTLChat database...")

    # Initialize database (this will create tables)
    db = Database(str(settings.db_path))

    logger.info(f"Database created at: {settings.db_path}")

    if create_sample_data:
        logger.info("Creating sample data...")

        # Create sample organization
        org_id = db.create_organization(
            org_name="Sample Organization",
            org_id="org_sample_001"
        )
        logger.info(f"Created organization: {org_id}")

        # Create sample users
        user1_id = db.create_user(
            org_id=org_id,
            username="johndoe",
            email="john.doe@example.com",
            full_name="John Doe",
            user_id="user_sample_001"
        )
        logger.info(f"Created user: {user1_id}")

        user2_id = db.create_user(
            org_id=org_id,
            username="janedoe",
            email="jane.doe@example.com",
            full_name="Jane Doe",
            user_id="user_sample_002"
        )
        logger.info(f"Created user: {user2_id}")

        # Test retrieval
        logger.info("\nTesting database retrieval...")

        org = db.get_organization(org_id)
        logger.info(f"Organization: {org}")

        user = db.get_user(user1_id)
        logger.info(f"User 1: {user}")

        user = db.get_user(user2_id)
        logger.info(f"User 2: {user}")

        logger.info("\nSample data created successfully!")

    logger.info("\nDatabase initialization complete!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Initialize CTLChat database")
    parser.add_argument(
        "--sample-data",
        action="store_true",
        help="Create sample data for testing"
    )

    args = parser.parse_args()

    init_database(create_sample_data=args.sample_data)
