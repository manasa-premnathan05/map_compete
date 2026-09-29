"""MongoDB connection diagnostic for MapCompete.

Verifies the *live* MongoDB Atlas connection configured through the
environment (never hardcoded):

    MONGODB_URI=mongodb+srv://...     (required)
    MONGODB_DATABASE=competitor_intelligence  (optional)

Checks performed:
  1. configuration present
  2. connect + ping
  3. database/collection access
  4. insert one clearly-marked smoke-test document
  5. read it back
  6. delete it (NO junk is left behind - also removed from any previous run)

Usage:
    python backend/test_mongodb.py

This is the ONE test that requires real Atlas credentials. All other tests
run without a server (see test_database_mongo.py which uses mongomock).
Exit code 0 = success, 1 = failure.
"""

import os
import sys

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

try:
    from database import DatabaseManager
except ImportError:  # pragma: no cover - allow running from any cwd
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from database import DatabaseManager

SMOKE_ID = "mapcompete-smoke-test"
SMOKE_MARKER = {"_id": SMOKE_ID, "purpose": "connectivity check", "safe": True}


def main() -> int:
    if load_dotenv:
        load_dotenv()
        for candidate in (
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"),
        ):
            if os.path.exists(candidate):
                load_dotenv(candidate)

    if not os.environ.get("MONGODB_URI"):
        print("[FAIL] MONGODB_URI is not set.")
        print("       Copy .env.example to .env and fill in your Atlas SRV URI.")
        return 1

    print("[1/4] Connecting to MongoDB ...")
    db_manager = DatabaseManager()
    health = db_manager.health()
    if not health["ok"]:
        print(f"[FAIL] connection error: {health['error']}")
        return 1
    print("      connected")

    try:
        collection = db_manager._database()["smoke_test"]
        print("[2/4] Database/collection access OK "
              f"(database='{db_manager.database_name}')")

        print("[3/4] Insert / read back the smoke-test document ...")
        collection.delete_one({"_id": SMOKE_ID})  # clear leftovers, if any
        collection.insert_one(dict(SMOKE_MARKER))
        doc = collection.find_one({"_id": SMOKE_ID})
        if not doc or doc.get("purpose") != SMOKE_MARKER["purpose"]:
            print("[FAIL] document could not be read back")
            return 1
        print("      insert + read OK")

        print("[4/4] Removing the smoke-test document ...")
        collection.delete_one({"_id": SMOKE_ID})
        if collection.find_one({"_id": SMOKE_ID}):
            print("[FAIL] cleanup failed - document still present")
            return 1
        print("      cleaned up (no test data left behind)")
    except Exception as exc:  # noqa: BLE001 - report clearly
        print(f"[FAIL] {type(exc).__name__}: {exc}")
        return 1

    print("\nSUCCESS: MongoDB Atlas is configured correctly for MapCompete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
