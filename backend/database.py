"""MongoDB persistence layer for MapCompete.

Replaces the former SQLite ``DatabaseManager`` while keeping the same
high-level method surface consumed by ``api.py``: callers never see raw
PyMongo operations.

* One reusable ``MongoClient`` per process (``MONGODB_URI``, Atlas SRV
  supported) with bounded timeouts so the API fails fast - and clearly -
  when MongoDB is unreachable (``DatabaseUnavailableError`` -> HTTP 503).
* Documents mirror the old relational rows (same field names), so API
  responses stay unchanged. Numeric application ids are preserved: MongoDB
  ``_id`` lives underneath while ids are allocated from an atomic
  ``counters`` collection (never count+1, never duplicates).
* Duplicate prevention is unchanged: posts dedupe on ``content_hash`` then
  ``post_url`` (shared posts are linked through ``post_competitors``),
  reviews on their content hash, competitors within a project on canonical
  place / business key, canonical places on unique ``place_key``.
* Indexes are created idempotently at startup. No seed/demo data: a fresh
  database starts empty.
"""

import collections
import hashlib
import json
import logging
import os
import re
from datetime import datetime
from typing import Dict, List, Optional

from pymongo import ASCENDING, DESCENDING, MongoClient, ReturnDocument
from pymongo.errors import DuplicateKeyError, PyMongoError

try:
    from place_identity import (
        extract_place_identity,
        is_strong_identity,
        maps_url_for_place,
        normalize_name,
        parse_place_id,
        place_id_from_hex,
        cid_from_hex,
    )
except ImportError:  # pragma: no cover - allow running from any cwd
    import sys as _sys

    _sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from place_identity import (
        extract_place_identity,
        is_strong_identity,
        maps_url_for_place,
        normalize_name,
        parse_place_id,
        place_id_from_hex,
        cid_from_hex,
    )

try:
    from topic_classifier import extract_products, infer_industry
except ImportError:  # pragma: no cover - allow running from any cwd
    import sys as _sys

    _sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from topic_classifier import extract_products, infer_industry

logger = logging.getLogger(__name__)

# Logical collections (the old SQLite tables).
COLLECTIONS = (
    "projects",
    "competitors",
    "places",
    "posts",
    "post_competitors",
    "reviews",
    "keywords",
    "generated_ideas",
    "scraping_logs",
)


class DatabaseUnavailableError(RuntimeError):
    """MongoDB not configured or unreachable. Message never holds credentials."""


def _safe_error(exc: BaseException) -> str:
    """Error text with any credentials stripped (never log the URI)."""
    return re.sub(r"//[^@\s]+@", "//***@", str(exc))


def _utc_ts() -> str:
    """SQLite CURRENT_TIMESTAMP equivalent (UTC, second precision)."""
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def _local_sec() -> str:
    """Local timestamp to the second (places.updated_at, as before)."""
    return datetime.now().isoformat(sep=" ", timespec="seconds")


def _local_full() -> str:
    """Local timestamp with microseconds (log start/end, as before)."""
    return str(datetime.now())


def _as_str(value) -> Optional[str]:
    """Store timestamps the way SQLite returned them: strings."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return str(value)
    return str(value)


def _json_loads(value, default):
    """Parse a JSON string; pass lists/dicts through unchanged."""
    if value is None:
        return default
    if isinstance(value, (list, dict)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (TypeError, ValueError):
            return default
    return default


def _public(doc) -> Dict:
    """Document -> API dict without the MongoDB ``_id``."""
    if doc is None:
        return None
    return {key: value for key, value in doc.items() if key != "_id"}


class DatabaseManager:
    """Application-facing persistence API backed by MongoDB."""

    def __init__(self, uri: Optional[str] = None, database: Optional[str] = None,
                 client=None):
        # ``client`` is an injection hook for tests (e.g. mongomock); the
        # application never passes it.
        self.uri = (uri if uri is not None else os.environ.get("MONGODB_URI") or "").strip()
        self.database_name = (
            database or os.environ.get("MONGODB_DATABASE") or "competitor_intelligence"
        ).strip()
        self._client = None
        self._db = None
        self._last_error: Optional[str] = None

        if client is not None:
            self._client = client
            self.uri = self.uri or "mongodb://test-injected-client"
            self._db = self._client[self.database_name]
            self.ensure_indexes()
            return

        if not self.uri:
            self._last_error = (
                "MONGODB_URI is not configured. Set MONGODB_URI "
                "(mongodb+srv://...) in the environment or .env file."
            )
            logger.error("MongoDB configuration error: %s", self._last_error)
            return

        try:
            self._client = MongoClient(
                self.uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                appname="mapcompete",
            )
            # Verify early so boot logs show a clear connection status.
            self._client.admin.command("ping")
            self._db = self._client[self.database_name]
            self._last_error = None
            logger.info("Connected to MongoDB database '%s'", self.database_name)
            self.ensure_indexes()
        except Exception as exc:  # noqa: BLE001 - report clearly, never crash boot
            self._last_error = f"MongoDB is unreachable: {_safe_error(exc)}"
            logger.error("MongoDB connection failed: %s", self._last_error)

    # ------------------------------------------------------------------
    # Connection / infrastructure helpers
    # ------------------------------------------------------------------
    def _database(self):
        if self._db is None:
            raise DatabaseUnavailableError(
                self._last_error or "MongoDB is not available."
            )
        return self._db

    @property
    def projects(self):
        return self._database()["projects"]

    @property
    def competitors(self):
        return self._database()["competitors"]

    @property
    def places(self):
        return self._database()["places"]

    @property
    def posts(self):
        return self._database()["posts"]

    @property
    def post_competitors(self):
        return self._database()["post_competitors"]

    @property
    def reviews(self):
        return self._database()["reviews"]

    @property
    def keywords(self):
        return self._database()["keywords"]

    @property
    def generated_ideas(self):
        return self._database()["generated_ideas"]

    @property
    def scraping_logs(self):
        return self._database()["scraping_logs"]

    @property
    def counters(self):
        return self._database()["counters"]

    def available(self) -> bool:
        """True when the client is configured and the first ping succeeded."""
        return self._db is not None

    def health(self) -> Dict:
        """Small, credential-free connectivity report for /api/health."""
        if not self.uri:
            return {"ok": False, "error": self._last_error or "MONGODB_URI is not configured"}
        if self._db is None:
            # Client exists but the first ping failed: retry now (max 5s).
            try:
                self._client.admin.command("ping")
                self._db = self._client[self.database_name]
                self._last_error = None
                self.ensure_indexes()
            except Exception as exc:  # noqa: BLE001
                self._last_error = f"MongoDB is unreachable: {_safe_error(exc)}"
                return {"ok": False, "error": self._last_error}
        try:
            self._db.command("ping")
            return {"ok": True, "error": None}
        except Exception as exc:  # noqa: BLE001
            self._last_error = f"MongoDB is unreachable: {_safe_error(exc)}"
            return {"ok": False, "error": self._last_error}

    def ensure_indexes(self) -> None:
        """Create every index the application relies on (idempotent)."""
        if self._db is None:
            return
        try:
            # Every API route resolves documents by the small integer ``id``
            # allocated from the counters collection, so those lookups have to
            # be indexed - without this each one is a collection scan.
            for collection in (self.places, self.competitors, self.posts,
                               self.post_competitors, self.reviews, self.keywords,
                               self.generated_ideas, self.scraping_logs):
                collection.create_index([("id", ASCENDING)])

            self.places.create_index([("place_key", ASCENDING)], unique=True)
            self.places.create_index([("google_place_id", ASCENDING)])
            self.places.create_index([("hex_id", ASCENDING)])
            self.places.create_index([("cid", ASCENDING)])
            self.places.create_index([("kgmid", ASCENDING)])
            self.places.create_index([("name", ASCENDING)])

            self.competitors.create_index([("project_id", ASCENDING)])
            self.competitors.create_index([("place_id", ASCENDING)])
            self.competitors.create_index([("business_key", ASCENDING)])
            self.competitors.create_index(
                [("project_id", ASCENDING), ("place_id", ASCENDING)]
            )
            # Reverse order: used to count how many projects track a place.
            self.competitors.create_index(
                [("place_id", ASCENDING), ("project_id", ASCENDING)]
            )

            # Duplicate prevention: one document per source post / review.
            self.posts.create_index([("content_hash", ASCENDING)], unique=True)
            self.posts.create_index([("post_url", ASCENDING)])
            self.posts.create_index([("competitor_id", ASCENDING)])
            self.posts.create_index([("scrape_date", ASCENDING)])
            self.posts.create_index([("published_date", ASCENDING)])
            self.posts.create_index([("canonical_post_id", ASCENDING)])

            self.post_competitors.create_index(
                [("post_id", ASCENDING), ("competitor_id", ASCENDING)], unique=True
            )
            self.post_competitors.create_index([("competitor_id", ASCENDING)])
            self.post_competitors.create_index([("post_id", ASCENDING)])
            self.post_competitors.create_index(
                [("competitor_id", ASCENDING), ("post_id", ASCENDING)]
            )

            self.reviews.create_index([("content_hash", ASCENDING)], unique=True)
            self.reviews.create_index([("project_id", ASCENDING)])
            self.reviews.create_index([("competitor_id", ASCENDING)])

            self.keywords.create_index([("project_id", ASCENDING)])
            self.generated_ideas.create_index([("project_id", ASCENDING)])
            self.scraping_logs.create_index([("project_id", ASCENDING)])
            # Used by the "last scrape status" lookup on every project read.
            self.scraping_logs.create_index(
                [("project_id", ASCENDING), ("start_time", DESCENDING)]
            )

            self._seed_counters()
        except PyMongoError as exc:
            logger.error("Failed to ensure MongoDB indexes: %s", _safe_error(exc))

    def _seed_counters(self) -> None:
        """Anchor each numeric-id counter at the highest existing id.

        ``$max`` means concurrent workers can never rewind a counter and a
        second run is a no-op (idempotent).
        """
        for name in COLLECTIONS:
            coll = self._database()[name]
            max_id = 0
            for doc in coll.find({}, {"id": 1}).sort("id", DESCENDING).limit(1):
                try:
                    max_id = int(doc.get("id") or 0)
                except (TypeError, ValueError):
                    max_id = 0
            if max_id > 0:
                self.counters.update_one(
                    {"_id": name}, {"$max": {"seq": max_id}}, upsert=True
                )
            else:
                self.counters.update_one(
                    {"_id": name}, {"$setOnInsert": {"seq": 0}}, upsert=True
                )

    def _next_id(self, collection: str) -> int:
        """Atomically allocate the next application-level numeric id."""
        doc = self.counters.find_one_and_update(
            {"_id": collection},
            {"$inc": {"seq": 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return int(doc["seq"])

    # ------------------------------------------------------------------
    # Pure helpers (behaviour identical to the SQLite implementation)
    # ------------------------------------------------------------------
    @staticmethod
    def _normalize_business_key(name: str) -> str:
        return re.sub(r"[^a-z0-9]+", " ", (name or "").strip().lower()).strip()

    @staticmethod
    def _duration_seconds(start_time, end_time) -> Optional[int]:
        """Seconds between a run's start and end timestamps (None when open)."""
        def _parse(value):
            if not value:
                return None
            if isinstance(value, datetime):
                return value
            text = str(value).strip().replace("T", " ")
            if "." in text:
                text = text.split(".")[0]
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
                try:
                    return datetime.strptime(text[:19], fmt)
                except ValueError:
                    continue
            return None

        start = _parse(start_time)
        end = _parse(end_time)
        if not start or not end:
            return None
        return max(0, int((end - start).total_seconds()))

    @staticmethod
    def _decorate_scraping_log(log: Dict) -> Dict:
        """Normalize a raw scraping log document for the API/dashboard."""
        for json_field in ("competitor_names", "details"):
            raw = log.get(json_field)
            if isinstance(raw, str) and raw.strip():
                try:
                    log[json_field] = json.loads(raw)
                except (TypeError, ValueError):
                    log[json_field] = []
            elif not isinstance(raw, list):
                log[json_field] = []

        for numeric_field in ("competitors_processed", "posts_found", "new_posts",
                              "duplicates_skipped", "failures", "images_downloaded"):
            log[numeric_field] = log.get(numeric_field) or 0

        log["captcha_encountered"] = int(bool(log.get("captcha_encountered")))
        log["has_captcha_issue"] = bool(log["captcha_encountered"])
        log["has_errors"] = bool(log.get("error_info")) or bool(log["failures"])
        log["status"] = log.get("status") or ("failed" if log["failures"] else "completed")
        log["duration_seconds"] = DatabaseManager._duration_seconds(
            log.get("start_time"), log.get("end_time")
        )
        if not log["competitor_names"]:
            log["competitor_names"] = [
                detail.get("competitor") or detail.get("name")
                for detail in log["details"]
                if isinstance(detail, dict) and (detail.get("competitor") or detail.get("name"))
            ]
        return log

    def generate_content_hash(self, post_url: str, text_content: str) -> str:
        """Generate a hash for duplicate detection."""
        content = f"{post_url or ''}{text_content or ''}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _is_richer_name(self, candidate: str, current: str) -> bool:
        """True when `candidate` is a strictly more descriptive name."""
        candidate_tokens = normalize_name(candidate, aggressive=True).split()
        current_tokens = normalize_name(current, aggressive=True).split()
        if not candidate_tokens or not current_tokens:
            return False
        return (
            len(candidate_tokens) > len(current_tokens)
            and set(current_tokens) <= set(candidate_tokens)
        )

    def resolve_place_identity(self, name: str = None, gmap_url: str = None,
                               address: str = None, place_key: str = None,
                               google_place_id: str = None, cid: str = None,
                               hex_id: str = None, kgmid: str = None,
                               latitude=None, longitude=None) -> Dict:
        """Pure helper: canonical identity for any mix of hints (no DB write)."""
        return extract_place_identity(
            gmap_url=gmap_url,
            name=name,
            address=address,
            place_key=place_key,
            google_place_id=google_place_id,
            cid=cid,
            hex_id=hex_id,
            kgmid=kgmid,
            latitude=latitude,
            longitude=longitude,
        )

    # ------------------------------------------------------------------
    # Canonical places
    # ------------------------------------------------------------------
    def _find_place_row(self, identity: Dict) -> Optional[Dict]:
        """Find the canonical place document an identity belongs to, if any.

        Strong signals (hex pair / place id / CID / kgmid) are tried first and
        the stored text keys last, so a hand-typed business name links upwards
        to the real Google Maps listing instead of creating a rival row.
        """
        candidates = list(identity.get("lookup_keys") or [])
        candidates += [key for key in (identity.get("text_keys") or []) if key not in candidates]
        for key in candidates:
            row = self.places.find_one({"place_key": key})
            if row:
                return row
        for column in ("google_place_id", "hex_id", "cid", "kgmid"):
            value = identity.get(column)
            if not value:
                continue
            row = self.places.find_one(
                {column: value}, sort=[("confidence", DESCENDING), ("id", ASCENDING)]
            )
            if row:
                return row

        # A hand-typed business (no Google id of its own) belongs to the real
        # listing of the same name when one is already known.
        core_name = identity.get("core_name")
        if core_name and not is_strong_identity(identity):
            first_token = core_name.split(" ")[0]
            cursor = self.places.find(
                {"confidence": {"$gte": 2},
                 "name": {"$regex": re.escape(first_token), "$options": "i"}},
                sort=[("confidence", DESCENDING), ("id", ASCENDING)],
            )
            for candidate in cursor:
                if normalize_name(candidate.get("name"), aggressive=True) == core_name:
                    return candidate
        return None

    def _merge_places(self, keep_id: int, drop_id: int) -> int:
        """Fold a duplicate place document into the canonical one."""
        if not keep_id or not drop_id or keep_id == drop_id:
            return keep_id or drop_id
        self.competitors.update_many({"place_id": drop_id}, {"$set": {"place_id": keep_id}})
        self.projects.update_many({"place_id": drop_id}, {"$set": {"place_id": keep_id}})
        self.places.delete_one({"id": drop_id})
        return keep_id

    def _fold_weak_name_duplicates(self, place_id: int, identity: Dict) -> int:
        """Merge *weak* (hand-typed) place documents for the same name.

        Rows carrying a Google identity of their own are never folded: two
        different listings that share a name are real, separate businesses.
        """
        core_name = identity.get("core_name")
        if not core_name or not place_id:
            return 0
        folded = 0
        for other in self.places.find(
            {"id": {"$ne": place_id}}, {"id": 1, "name": 1, "confidence": 1}
        ):
            if (other.get("confidence") or 0) >= 2:
                continue
            if normalize_name(other.get("name"), aggressive=True) == core_name:
                self._merge_places(place_id, other["id"])
                folded += 1
        return folded

    def _upsert_place(self, identity: Dict, name: str = None, address: str = None,
                      category: str = None) -> Optional[int]:
        """Return the canonical ``places.id`` for an identity, creating it once."""
        key = (identity.get("place_key") or "").strip()
        if not key:
            return None

        display_name = (name or "").strip() or identity.get("name")
        display_address = (address or "").strip() or identity.get("address")
        confidence = int(identity.get("confidence") or 0)
        source = identity.get("identity_source") or "unknown"
        now = _local_sec()

        row = self._find_place_row(identity)
        if row is not None:
            place_id = row["id"]
            updates = {}
            if confidence > (row.get("confidence") or 0) and row.get("place_key") != key:
                updates["place_key"] = key
                updates["identity_source"] = source
                updates["confidence"] = confidence
            for column in ("google_place_id", "hex_id", "cid", "kgmid"):
                value = identity.get(column)
                if value and not row.get(column):
                    updates[column] = value
            if display_name:
                if not row.get("name") or self._is_richer_name(display_name, row["name"]):
                    updates["name"] = display_name
            if display_address and not row.get("address"):
                updates["address"] = display_address
            if category and not row.get("category"):
                updates["category"] = category
            if identity.get("latitude") is not None and row.get("latitude") is None:
                updates["latitude"] = identity["latitude"]
            if identity.get("longitude") is not None and row.get("longitude") is None:
                updates["longitude"] = identity["longitude"]

            if updates:
                updates["updated_at"] = now
                try:
                    self.places.update_one({"id": place_id}, {"$set": updates})
                except DuplicateKeyError:
                    # Another document already owns the upgraded key: merge.
                    owner = self.places.find_one({"place_key": key})
                    if owner and owner["id"] != place_id:
                        place_id = self._merge_places(owner["id"], place_id)
            # A hand-typed row for the same business is superseded by this
            # real listing, even when the listing already existed.
            self._fold_weak_name_duplicates(place_id, identity)
            return place_id

        doc = {
            "id": self._next_id("places"),
            "place_key": key,
            "identity_source": source,
            "confidence": confidence,
            "google_place_id": identity.get("google_place_id"),
            "hex_id": identity.get("hex_id"),
            "cid": identity.get("cid"),
            "kgmid": identity.get("kgmid"),
            "name": display_name,
            "address": display_address,
            "category": category,
            "latitude": identity.get("latitude"),
            "longitude": identity.get("longitude"),
            "created_at": _utc_ts(),
            "updated_at": now,
            "rating": None,
            "review_count": None,
        }
        place_id = doc["id"]
        try:
            self.places.insert_one(doc)
        except DuplicateKeyError:
            owner = self.places.find_one({"place_key": key})
            if owner:
                # Same key won the race: keep the existing canonical row.
                self._fold_weak_name_duplicates(owner["id"], identity)
                return owner["id"]

        # Fold only *weak* (name-only) duplicates created earlier from a plain
        # name; listings with their own Google identity are never merged.
        self._fold_weak_name_duplicates(place_id, identity)
        return place_id

    def _place_dict(self, place: Optional[Dict]) -> Optional[Dict]:
        """Place document -> API dict, enriched with links and usage counts."""
        if not place:
            return None
        place = _public(place)
        place["place_url"] = maps_url_for_place(place)
        place["identity_label"] = (
            place.get("google_place_id") or place.get("hex_id")
            or ("cid:" + place["cid"] if place.get("cid") else None)
            or place.get("kgmid") or place.get("place_key")
        )
        place["project_count"] = len(self.competitors.distinct(
            "project_id", {"place_id": place["id"]}
        ))
        place["competitor_count"] = self.competitors.count_documents(
            {"place_id": place["id"]}
        )
        return place

    def _attach_place_info(self, rows: List[Dict]) -> List[Dict]:
        """Attach the canonical place (and its key) to project/competitor rows."""
        ids = sorted({row.get("place_id") for row in rows if row.get("place_id")})
        places: Dict[int, Dict] = {}
        if ids:
            for place_row in self.places.find({"id": {"$in": ids}}):
                place = _public(place_row)
                place["place_url"] = maps_url_for_place(place)
                place["identity_label"] = (
                    place.get("google_place_id") or place.get("hex_id")
                    or ("cid:" + place["cid"] if place.get("cid") else None)
                    or place.get("kgmid") or place.get("place_key")
                )
                places[place_row["id"]] = place
        for row in rows:
            place = places.get(row.get("place_id"))
            row["place"] = place
            row["place_key"] = (place or {}).get("place_key")
            row["place_url"] = (place or {}).get("place_url")
        return rows

    def ensure_place(self, name: str = None, gmap_url: str = None, address: str = None,
                     category: str = None, place_key: str = None,
                     google_place_id: str = None, cid: str = None, hex_id: str = None,
                     kgmid: str = None, latitude=None, longitude=None) -> Optional[Dict]:
        """Upsert the canonical place for any mix of hints and return it."""
        identity = self.resolve_place_identity(
            name=name, gmap_url=gmap_url, address=address, place_key=place_key,
            google_place_id=google_place_id, cid=cid, hex_id=hex_id, kgmid=kgmid,
            latitude=latitude, longitude=longitude,
        )
        if not identity.get("place_key"):
            return None
        place_id = self._upsert_place(identity, name=name, address=address, category=category)
        return self._place_dict(self.places.find_one({"id": place_id}))

    def get_place(self, place_id: int) -> Optional[Dict]:
        return self._place_dict(self.places.find_one({"id": place_id}))

    def get_places(self, query: str = None, limit: int = 500) -> List[Dict]:
        """All canonical businesses, optionally filtered by name/address/id."""
        mongo_filter = {}
        if query:
            term = re.escape(query.strip())
            like = {"$regex": term, "$options": "i"}
            mongo_filter = {"$or": [
                {"name": like}, {"address": like}, {"place_key": like},
                {"google_place_id": like}, {"cid": like},
            ]}
        rows = self.places.find(mongo_filter).sort(
            [("confidence", DESCENDING), ("id", ASCENDING)]
        ).limit(int(limit))
        return [self._place_dict(row) for row in rows]

    def get_place_projects(self, place_id: int) -> List[Dict]:
        """Every project that tracks this canonical business (with counts)."""
        if not place_id:
            return []
        project_ids = self.competitors.distinct("project_id", {"place_id": place_id})
        results = []
        for project in self.projects.find({"id": {"$in": project_ids}}).sort("id", ASCENDING):
            results.append({
                "id": project["id"],
                "name": project.get("name"),
                "location": project.get("location"),
                "field": project.get("field"),
                "is_online": project.get("is_online"),
                "is_tracked": self.competitors.count_documents(
                    {"project_id": project["id"], "place_id": place_id}
                ),
            })
        return results

    def get_place_competitors(self, place_id: int) -> List[Dict]:
        rows = []
        for comp in self.competitors.find({"place_id": place_id}).sort("id", ASCENDING):
            doc = _public(comp)
            project = self.projects.find_one({"id": comp.get("project_id")}, {"name": 1})
            doc["project_name"] = (project or {}).get("name")
            rows.append(doc)
        return rows

    def get_place_by_key(self, place_key: str) -> Optional[Dict]:
        """Look up a canonical place by its canonical key."""
        if not place_key:
            return None
        return self._place_dict(self.places.find_one({"place_key": str(place_key).strip()}))

    def get_project_places(self, project_id: int) -> List[Dict]:
        """Canonical places linked to this project through its competitors."""
        place_ids = self.competitors.distinct("place_id", {
            "project_id": project_id, "place_id": {"$ne": None}
        })
        return [
            self._place_dict(row)
            for row in self.places.find({"id": {"$in": place_ids}}).sort("id", ASCENDING)
        ]

    def get_project_place(self, project_id: int) -> Optional[Dict]:
        """The project's own business as a canonical place (may be None)."""
        project = self.projects.find_one({"id": project_id})
        if not project or not project.get("place_id"):
            return None
        return self._place_dict(self.places.find_one({"id": project["place_id"]}))

    def get_competitor_place(self, competitor_id: int) -> Optional[Dict]:
        comp = self.competitors.find_one({"id": competitor_id})
        if not comp or not comp.get("place_id"):
            return None
        return self._place_dict(self.places.find_one({"id": comp["place_id"]}))

    def get_place_lookup(self, place_ids: List[int]) -> Dict[int, Dict]:
        """Batch place lookup for list endpoints, keyed by place id."""
        ids = sorted({int(pid) for pid in (place_ids or []) if pid})
        if not ids:
            return {}
        return {
            row["id"]: self._place_dict(row)
            for row in self.places.find({"id": {"$in": ids}})
        }

    def link_project_place(self, project_id: int, name: str = None, gmap_url: str = None,
                           address: str = None, place_key: str = None,
                           google_place_id: str = None, cid: str = None,
                           hex_id: str = None) -> Optional[Dict]:
        """Attach the project's own business to its canonical place row."""
        identity = self.resolve_place_identity(
            name=name, gmap_url=gmap_url, address=address, place_key=place_key,
            google_place_id=google_place_id, cid=cid, hex_id=hex_id,
        )
        if not identity.get("place_key"):
            return None
        if gmap_url:
            self.projects.update_one({"id": project_id}, {"$set": {"gmap_url": gmap_url}})
        place_id = self._upsert_place(identity, name=name, address=address)
        if place_id:
            self.projects.update_one({"id": project_id}, {"$set": {"place_id": place_id}})
        return self._place_dict(self.places.find_one({"id": place_id}))

    # ------------------------------------------------------------------
    # Projects
    # ------------------------------------------------------------------
    def project_name_exists(self, name: str, exclude_id: int = None) -> bool:
        """True when another project already uses this business name."""
        clean_name = (name or "").strip()
        if not clean_name:
            return False
        query: Dict = {"name": {"$regex": f"^{re.escape(clean_name)}$", "$options": "i"}}
        if exclude_id is not None:
            query["id"] = {"$ne": exclude_id}
        return self.projects.find_one(query, {"id": 1}) is not None

    def create_project(self, name: str, our_profile: str = None, location: str = None,
                       field: str = None, is_online: bool = False,
                       gmap_url: str = None) -> int:
        """Create a new project. Every creation makes a NEW project row.

        The project's own business is registered in the canonical ``places``
        collection so it can be recognised later (e.g. when a discovery run
        returns the project's own listing).
        """
        clean_name = (name or "").strip()
        if not clean_name:
            raise ValueError("Project name is required")
        clean_url = (gmap_url or "").strip() or None

        doc = {
            "id": self._next_id("projects"),
            "name": clean_name,
            "our_profile": our_profile,
            "created_at": _utc_ts(),
            "location": location,
            "field": field,
            "is_online": int(bool(is_online)),
            "gmap_url": clean_url,
            "place_id": None,
        }
        project_id = doc["id"]
        self.projects.insert_one(doc)

        identity = self.resolve_place_identity(
            name=clean_name, gmap_url=clean_url,
            address=location or our_profile,
        )
        place_id = self._upsert_place(identity, name=clean_name, address=location or our_profile)
        if place_id:
            self.projects.update_one({"id": project_id}, {"$set": {"place_id": place_id}})
        return project_id

    def get_projects(self) -> List[Dict]:
        projects = [_public(doc) for doc in self.projects.find().sort("created_at", DESCENDING)]
        return self._attach_place_info(projects)

    def get_project(self, project_id: int) -> Optional[Dict]:
        doc = self.projects.find_one({"id": project_id})
        if not doc:
            return None
        project = self._attach_place_info([_public(doc)])[0]
        place = project.get("place")
        project["competitor_count"] = self.competitors.count_documents(
            {"project_id": project_id}
        )
        project["own_place_id"] = place["id"] if place else None
        return project

    def update_project(self, project_id: int, name: str = None, our_profile: str = None,
                       location: str = None, field: str = None, is_online: bool = None,
                       gmap_url: str = None):
        updates: Dict = {}
        if name is not None:
            updates["name"] = name
        if our_profile is not None:
            updates["our_profile"] = our_profile
        if location is not None:
            updates["location"] = location
        if field is not None:
            updates["field"] = field
        if is_online is not None:
            updates["is_online"] = int(bool(is_online))
        if gmap_url is not None:
            updates["gmap_url"] = gmap_url or None
        if updates:
            self.projects.update_one({"id": project_id}, {"$set": updates})

        # Keep the project's canonical business in sync with its new name,
        # location or Google Maps URL.
        if name is not None or location is not None or gmap_url is not None:
            current = self.projects.find_one({"id": project_id})
            if current:
                resolved_name = name if name is not None else current.get("name")
                resolved_address = (
                    location if location is not None else current.get("location")
                ) or current.get("our_profile")
                identity = self.resolve_place_identity(
                    name=resolved_name,
                    gmap_url=gmap_url if gmap_url is not None else current.get("gmap_url"),
                    address=resolved_address,
                )
                place_id = self._upsert_place(
                    identity, name=resolved_name, address=resolved_address
                )
                if place_id and place_id != current.get("place_id"):
                    self.projects.update_one(
                        {"id": project_id}, {"$set": {"place_id": place_id}}
                    )

    def delete_project(self, project_id: int):
        """Delete a project together with every record it owns.

        Keywords, generated ideas, scraping logs, reviews and competitors
        belong to the project and are always removed. Posts shared with a
        competitor of another project survive through ``post_competitors``
        (exactly like the old SQL cascade); canonical ``places`` documents
        deliberately survive - they describe a real-world business, not this
        project's tracking of it.
        """
        competitor_ids = [
            doc["id"] for doc in self.competitors.find(
                {"project_id": project_id}, {"id": 1}
            )
        ]
        self._delete_competitor_records(competitor_ids)

        self.reviews.delete_many({"project_id": project_id})
        self.competitors.delete_many({"project_id": project_id})
        self.keywords.delete_many({"project_id": project_id})
        self.generated_ideas.delete_many({"project_id": project_id})
        self.scraping_logs.delete_many({"project_id": project_id})
        self.projects.delete_one({"id": project_id})

    # ------------------------------------------------------------------
    # Competitors
    # ------------------------------------------------------------------
    def _find_project_competitor(self, project_id: int, name: str,
                                 business_key: str, place_id: int = None):
        """The competitor in this project that already represents the same business."""
        if place_id:
            row = self.competitors.find_one(
                {"project_id": project_id, "place_id": place_id},
                sort=[("id", ASCENDING)],
            )
            if row:
                return row
        # LOWER(name) = LOWER(?) OR business_key = ?
        return self.competitors.find_one(
            {"project_id": project_id,
             "$or": [
                 {"name": {"$regex": f"^{re.escape(name)}$", "$options": "i"}},
                 {"business_key": business_key},
             ]},
            sort=[("id", ASCENDING)],
        )

    def add_competitor(self, project_id: int, name: str, gmap_url: str = None,
                       address: str = None, category: str = None,
                       place_key: str = None, google_place_id: str = None,
                       cid: str = None, hex_id: str = None) -> int:
        """Add a competitor to a project and link it to its canonical business.

        Order of operations (unchanged from the SQL implementation):
        1. the canonical ``places`` document is upserted first, so the same
           real business always resolves to one row however it was entered;
        2. when this project already tracks that place - or a competitor with
           the same normalised name - the existing row is enriched and reused
           instead of creating a duplicate.
        """
        clean_name = (name or "").strip()
        if not clean_name:
            raise ValueError("Competitor name is required")
        clean_url = (gmap_url or "").strip() or None
        clean_address = (address or "").strip() or None
        clean_category = (category or "").strip() or None
        business_key = self._normalize_business_key(clean_name)

        identity = self.resolve_place_identity(
            name=clean_name, gmap_url=clean_url, address=clean_address,
            place_key=place_key, google_place_id=google_place_id,
            cid=cid, hex_id=hex_id,
        )

        place_id = self._upsert_place(
            identity, name=clean_name, address=clean_address, category=clean_category
        )
        # Only a real Google identity is safe to de-duplicate on across
        # different names; a name-only identity already matches by name.
        existing = self._find_project_competitor(
            project_id, clean_name, business_key,
            place_id if is_strong_identity(identity) else None,
        )
        if existing:
            updates: Dict = {}
            for field, value in (("gmap_url", clean_url),
                                 ("address", clean_address),
                                 ("category", clean_category)):
                if value and not existing.get(field):
                    updates[field] = value
            if place_id and existing.get("place_id") != place_id:
                updates["place_id"] = place_id
            if not existing.get("business_key"):
                updates["business_key"] = business_key
            if updates:
                self.competitors.update_one({"id": existing["id"]}, {"$set": updates})
            return existing["id"]

        doc = {
            "id": self._next_id("competitors"),
            "project_id": project_id,
            "name": clean_name,
            "gmap_url": clean_url,
            "added_at": _utc_ts(),
            "business_key": business_key,
            "last_scraped": None,
            "post_count": 0,
            "status": "active",
            "place_id": place_id,
            "address": clean_address,
            "category": clean_category,
            "rating": None,
            "review_count": None,
            "rating_distribution": None,
        }
        self.competitors.insert_one(doc)
        return doc["id"]

    def _delete_competitor_records(self, competitor_ids: List[int]):
        """Remove the records that hang off the given competitors.

        Shared "danger zone" of ``delete_competitor`` and ``delete_project``.
        Deduplicated posts are shared between projects through
        ``post_competitors``, so a post another (surviving) competitor still
        links to is kept: its links of the removed competitors are dropped, it
        is re-owned by the smallest surviving competitor that links to it, and
        only posts nothing links to any more are deleted. Links pointing at a
        competitor row that no longer exists (a scrape that finished after its
        competitor was deleted) are dropped too - a post is never reassigned
        through a dead link.
        """
        if not competitor_ids:
            return
        batch = list(competitor_ids)

        # 1. This batch's share-links go away first (as in the SQL version).
        self.post_competitors.delete_many({"competitor_id": {"$in": batch}})

        # Competitor rows still exist at this point (delete_project /
        # delete_competitor remove them right after this call).
        live = set(self.competitors.distinct("id"))

        # 2. Dead links left behind by a scrape-vs-delete race.
        dead_links = list(self.post_competitors.find(
            {"competitor_id": {"$nin": list(live)}}, {"_id": 1}
        ))
        if dead_links:
            self.post_competitors.delete_many(
                {"_id": {"$in": [link["_id"] for link in dead_links]}}
            )

        # Surviving links grouped by post.
        links_by_post = collections.defaultdict(list)
        for link in self.post_competitors.find({}, {"post_id": 1, "competitor_id": 1}):
            links_by_post[link["post_id"]].append(link["competitor_id"])

        # 3. Posts owned by the removed competitors (or by a competitor that
        #    no longer exists at all): re-own through a surviving link or drop.
        candidates = self.posts.find({"$or": [
            {"competitor_id": {"$in": batch}},
            {"competitor_id": {"$nin": list(live)}},
        ]})
        for post in candidates:
            survivors = sorted(c for c in links_by_post.get(post["id"], []) if c in live)
            if survivors:
                self.posts.update_one(
                    {"_id": post["_id"]}, {"$set": {"competitor_id": survivors[0]}}
                )
            else:
                self.posts.delete_one({"_id": post["_id"]})

        # 4. Link rows whose post is gone, then link-less leftovers are already
        #    handled above; sweep any still-orphaned links defensively.
        post_ids = set(self.posts.distinct("id"))
        if post_ids:
            self.post_competitors.delete_many({"post_id": {"$nin": list(post_ids)}})
        else:
            self.post_competitors.delete_many({})

        # 5. Reviews owned by removed or vanished competitors.
        self.reviews.delete_many({"$or": [
            {"competitor_id": {"$in": batch}},
            {"competitor_id": {"$nin": list(live)}},
        ]})

    def _merge_competitors(self, keep_id: int, drop_id: int) -> int:
        """Fold a duplicate competitor into the kept one (posts included)."""
        if not keep_id or not drop_id or keep_id == drop_id:
            return keep_id or drop_id
        self.posts.update_many(
            {"competitor_id": drop_id}, {"$set": {"competitor_id": keep_id}}
        )
        for link in list(self.post_competitors.find({"competitor_id": drop_id})):
            conflict = self.post_competitors.find_one(
                {"post_id": link["post_id"], "competitor_id": keep_id}
            )
            if conflict:
                self.post_competitors.delete_one({"_id": link["_id"]})
            else:
                self.post_competitors.update_one(
                    {"_id": link["_id"]}, {"$set": {"competitor_id": keep_id}}
                )
        self.competitors.delete_one({"id": drop_id})
        return keep_id

    def delete_competitor(self, competitor_id: int):
        """Delete a competitor and the records that only it owned.

        Posts deduplicated against another project's competitor stay (their
        ``post_competitors`` link is what keeps them alive), but posts,
        reviews and link rows that existed only for this competitor go with it.
        """
        self._delete_competitor_records([competitor_id])
        self.competitors.delete_one({"id": competitor_id})

    @staticmethod
    def _shape_competitor(doc: Dict) -> Dict:
        """Competitor document -> API dict (rating_distribution stays a JSON
        string exactly like the SQLite column did)."""
        doc = _public(doc)
        if isinstance(doc.get("rating_distribution"), (dict, list)):
            doc["rating_distribution"] = json.dumps(doc["rating_distribution"])
        return doc

    def posts_collected_counts(self, competitor_ids: List[int]) -> Dict[int, int]:
        """Posts collected per competitor, in a fixed number of queries.

        A competitor owns the posts stored under its own id plus the posts it
        shares with another project (linked through ``post_competitors``).
        Computing this per competitor issued one count query per competitor and
        one lookup per shared link, which is what made the competitors endpoint
        slow once a project had a real amount of content. Both parts are now
        fetched in bulk and grouped in memory.
        """
        ids = [int(cid) for cid in competitor_ids if cid is not None]
        counts: Dict[int, int] = {cid: 0 for cid in ids}
        if not ids:
            return counts

        # 1. Posts stored against the competitor itself.
        for row in self.posts.find({"competitor_id": {"$in": ids}},
                                   {"competitor_id": 1}):
            cid = row.get("competitor_id")
            if cid in counts:
                counts[cid] += 1

        # 2. Posts another project links to this competitor. The links are read
        #    in one query and the owning competitor of each linked post in a
        #    second, so the cost does not grow with the number of links.
        links = [
            (row.get("competitor_id"), row.get("post_id"))
            for row in self.post_competitors.find(
                {"competitor_id": {"$in": ids}}, {"competitor_id": 1, "post_id": 1}
            )
        ]
        if links:
            post_ids = sorted({post_id for _, post_id in links if post_id is not None})
            owners = {
                row["id"]: row.get("competitor_id")
                for row in self.posts.find({"id": {"$in": post_ids}},
                                           {"id": 1, "competitor_id": 1})
            }
            for competitor_id, post_id in links:
                if owners.get(post_id) != competitor_id:
                    counts[competitor_id] = counts.get(competitor_id, 0) + 1
        return counts

    def _posts_collected(self, competitor_id: int) -> int:
        """Own posts + shared posts another project links to this competitor."""
        return self.posts_collected_counts([competitor_id]).get(competitor_id, 0)

    def _last_scrape_status(self, project_id: int):
        """MAX(start_time) of the project's scraping logs (None when no run)."""
        row = self.scraping_logs.find_one(
            {"project_id": project_id}, sort=[("start_time", DESCENDING)]
        )
        return row.get("start_time") if row else None

    @staticmethod
    def _competitor_sort_key(comp: Dict):
        """The exact ORDER BY used by the old SQL (best-ranked rivals first)."""
        rating = comp.get("rating") or 0
        review_count = comp.get("review_count") or 0
        post_count = comp.get("post_count") or 0
        ranked = 1 if (rating > 0 and (review_count > 0 or post_count > 0)) else 0
        raw_rating = comp.get("rating")
        # COALESCE(rating, 1.0): only NULL (None) falls back, 0 stays 0.
        score = review_count * (raw_rating if raw_rating is not None else 1.0)
        return (-ranked, -score, -post_count, comp.get("id") or 0)

    def get_competitors(self, project_id: int) -> List[Dict]:
        competitors = [
            self._shape_competitor(doc)
            for doc in self.competitors.find({"project_id": project_id})
        ]

        # Shared counts: how many *projects* track each canonical place. One
        # pass over the competitors holding those places replaces a distinct()
        # call per place; that pattern issued one round trip per place and was
        # the main reason this endpoint took seconds on a small instance.
        place_ids = sorted({c.get("place_id") for c in competitors if c.get("place_id")})
        places: Dict[int, Dict] = {}
        shared: Dict[int, int] = {}
        if place_ids:
            for place_row in self.places.find({"id": {"$in": place_ids}}):
                places[place_row["id"]] = self._place_dict(place_row)
            project_sets: Dict[int, set] = {pid: set() for pid in place_ids}
            for row in self.competitors.find(
                {"place_id": {"$in": place_ids}}, {"place_id": 1, "project_id": 1}
            ):
                bucket = project_sets.get(row.get("place_id"))
                if bucket is not None:
                    bucket.add(row.get("project_id"))
            shared = {pid: len(bucket) for pid, bucket in project_sets.items()}

        last_scrape = self._last_scrape_status(project_id)
        # Batched: one pass instead of a posts count (plus one lookup per shared
        # link) for every competitor.
        post_counts = self.posts_collected_counts([c["id"] for c in competitors])
        for competitor in competitors:
            cid = competitor["id"]
            competitor["posts_collected"] = post_counts.get(cid, 0)
            competitor["last_scrape_status"] = last_scrape
            place = places.get(competitor.get("place_id"))
            competitor["place"] = place
            competitor["place_key"] = (place or {}).get("place_key")
            competitor["identity_source"] = (place or {}).get("identity_source")
            competitor["shared_with_projects"] = max(
                0, (shared.get(competitor.get("place_id")) or 0) - 1
            )

        competitors.sort(key=self._competitor_sort_key)
        return competitors

    def get_competitor(self, competitor_id: int) -> Optional[Dict]:
        doc = self.competitors.find_one({"id": competitor_id})
        if not doc:
            return None
        competitor = self._shape_competitor(doc)
        self._attach_place_info([competitor])
        place = competitor.get("place")
        competitor["identity_source"] = (place or {}).get("identity_source")
        competitor["shared_with_projects"] = (
            max(0, len(self.competitors.distinct(
                "project_id", {"place_id": competitor.get("place_id")}
            )) - 1)
            if competitor.get("place_id") else 0
        )
        return competitor

    def get_competitor_with_status(self, competitor_id: int) -> Optional[Dict]:
        """Single competitor plus posts-collected count and last scrape status."""
        competitor = self.get_competitor(competitor_id)
        if not competitor:
            return None
        competitor["posts_collected"] = self._posts_collected(competitor_id)
        competitor["last_scrape_status"] = self._last_scrape_status(
            competitor.get("project_id")
        )
        return competitor

    def update_competitor(self, competitor_id: int, name: str = None, gmap_url: str = None,
                          address: str = None, category: str = None,
                          place_key: str = None, google_place_id: str = None,
                          cid: str = None, hex_id: str = None):
        """Edit a tracked competitor and re-resolve its canonical business.

        Editing the name or the Google Maps URL re-runs identity resolution,
        so a competitor that was only a typed name can be promoted to the real
        Google Maps listing (and merge with any duplicate for that business).
        Returns the (possibly merged) competitor id, or None when missing.
        """
        current = self.competitors.find_one({"id": competitor_id})
        if current is None:
            return None

        updates: Dict = {}
        new_name = current.get("name")
        if name is not None:
            clean_name = name.strip()
            if not clean_name:
                raise ValueError("Competitor name is required")
            new_name = clean_name
            updates["name"] = clean_name
            updates["business_key"] = self._normalize_business_key(clean_name)
        if gmap_url is not None:
            updates["gmap_url"] = gmap_url or None
        if address is not None:
            updates["address"] = address or None
        if category is not None:
            updates["category"] = category or None

        changed_identity = any(
            value is not None and value != current.get(field)
            for field, value in (("name", name), ("gmap_url", gmap_url),
                                 ("address", address))
        )
        if changed_identity or place_key or google_place_id or cid or hex_id:
            identity = self.resolve_place_identity(
                name=new_name,
                gmap_url=gmap_url if gmap_url is not None else current.get("gmap_url"),
                address=address if address is not None else current.get("address"),
                place_key=place_key, google_place_id=google_place_id,
                cid=cid, hex_id=hex_id,
            )
            place_id = self._upsert_place(
                identity, name=new_name,
                address=address if address is not None else current.get("address"),
                category=category if category is not None else current.get("category"),
            )
            if place_id and place_id != current.get("place_id"):
                updates["place_id"] = place_id
                # Re-check for an in-project duplicate of the same business.
                duplicate = self._find_project_competitor(
                    current.get("project_id"), new_name,
                    self._normalize_business_key(new_name),
                    place_id if is_strong_identity(identity) else None,
                )
                if duplicate and duplicate["id"] != competitor_id:
                    return self._merge_competitors(duplicate["id"], competitor_id)

        if updates:
            self.competitors.update_one({"id": competitor_id}, {"$set": updates})
        return competitor_id

    def update_competitor_stats(self, competitor_id: int, rating=None, review_count=None,
                                address: str = None, category: str = None,
                                rating_distribution=None, last_scraped=None) -> bool:
        """Persist the Google Maps profile statistics captured while scraping.

        Only non-``None`` values are written so a partial read never erases
        earlier good data (unchanged from the SQL version).
        """
        updates: Dict = {}
        if rating is not None:
            updates["rating"] = float(rating)
        if review_count is not None:
            updates["review_count"] = int(review_count)
        if address:
            updates["address"] = address
        if category:
            updates["category"] = category
        if rating_distribution:
            updates["rating_distribution"] = _json_loads(
                rating_distribution, rating_distribution
            )
        if last_scraped is not None:
            updates["last_scraped"] = _as_str(last_scraped)

        if not updates:
            return False
        result = self.competitors.update_one({"id": competitor_id}, {"$set": updates})
        return result.matched_count > 0

    def mark_competitor_scraped(self, competitor_id: int, posts_collected: int):
        """Record a (re-)scrape: last-scraped timestamp, status, and count."""
        self.competitors.update_one(
            {"id": competitor_id},
            {"$set": {
                "last_scraped": _utc_ts(),
                "post_count": int(posts_collected or 0),
                "status": "active",
            }},
        )

    def update_competitor_scrape_status(self, competitor_id: int, status: str):
        """Record the outcome status of a scrape run on the competitor row."""
        self.competitors.update_one(
            {"id": competitor_id},
            {"$set": {"last_scraped": _utc_ts(), "status": status or "active"}},
        )

    # ------------------------------------------------------------------
    # Keywords
    # ------------------------------------------------------------------
    def add_keyword(self, project_id: int, keyword: str) -> int:
        doc = {
            "id": self._next_id("keywords"),
            "project_id": project_id,
            "keyword": keyword,
            "added_at": _utc_ts(),
        }
        self.keywords.insert_one(doc)
        return doc["id"]

    def get_keywords(self, project_id: int) -> List[Dict]:
        return [
            _public(doc)
            for doc in self.keywords.find({"project_id": project_id})
            .sort("added_at", DESCENDING)
        ]

    def delete_keyword(self, keyword_id: int):
        self.keywords.delete_one({"id": keyword_id})

    # ------------------------------------------------------------------
    # Posts
    # ------------------------------------------------------------------
    def _link_shared_post(self, post_id: int, competitor_id: int):
        """Track that another project's competitor also links this source post."""
        try:
            self.post_competitors.insert_one(
                {"post_id": post_id, "competitor_id": competitor_id}
            )
        except DuplicateKeyError:
            pass  # already linked

    def add_post(self, competitor_id: int, post_data: Dict) -> Optional[int]:
        """Store one scraped post; None when it was already collected anywhere.

        Duplicate detection is unchanged: exact source posts hash the same
        (``content_hash``) and the same ``post_url`` is also treated as a
        duplicate - both keep a share link so other projects still see it.
        """
        content_hash = self.generate_content_hash(
            post_data.get("post_url", ""), post_data.get("text_content", "")
        )
        existing = self.posts.find_one({"content_hash": content_hash}, {"id": 1})
        if existing:
            self._link_shared_post(existing["id"], competitor_id)
            return None  # Duplicate source post - already collected

        post_url = (post_data.get("post_url") or "").strip() or None
        if post_url:
            existing = self.posts.find_one({"post_url": post_url}, {"id": 1})
            if existing:
                self._link_shared_post(existing["id"], competitor_id)
                return None  # Duplicate source post - already collected

        raw_data = post_data.get("raw_data") or {}
        if isinstance(raw_data, str):
            raw_data = _json_loads(raw_data, {})
        if not isinstance(raw_data, dict):
            raw_data = {}
        raw_source = post_data.get("post_source")
        if not raw_source:
            raw_source = raw_data.get("post_source")
        # Owner updates are the default; anything explicitly flagged as
        # user-generated content is stored as a public post.
        post_source = "public" if str(raw_source or "").strip().lower() == "public" else "owner"
        raw_data = {**raw_data, "post_source": post_source}

        doc = {
            "id": self._next_id("posts"),
            "competitor_id": competitor_id,
            "post_url": post_data.get("post_url"),
            "text_content": post_data.get("text_content"),
            "published_date": post_data.get("published_date"),
            "scrape_date": _utc_ts(),
            "image_urls": _json_loads(post_data.get("image_urls"), []),
            "cta": post_data.get("cta"),
            "detected_topic": post_data.get("detected_topic"),
            "detected_keywords": _json_loads(post_data.get("detected_keywords"), []),
            "raw_data": raw_data,
            "content_hash": content_hash,
            "canonical_post_id": None,
            "post_source": post_source,
        }
        try:
            self.posts.insert_one(doc)
            return doc["id"]
        except DuplicateKeyError:
            # A concurrent scrape stored the same source post first.
            existing = self.posts.find_one({"content_hash": content_hash}, {"id": 1})
            if existing:
                self._link_shared_post(existing["id"], competitor_id)
            return None

    def get_posts(self, project_id: int = None, competitor_id: int = None,
                  limit: int = 100, offset: int = 0,
                  source: Optional[str] = None,
                  include_public: bool = True) -> List[Dict]:
        """Posts for a project and/or competitor with the original ordering.

        * project scope = posts owned by the project's competitors UNION posts
          linked through ``post_competitors`` (deduplicated by id).
        * owner posts first, then newest publications; public posts last.
        * public posts stay hidden unless explicitly requested.
        """
        mongo_filter: Dict = {}

        proj_competitor_ids: Optional[set] = None
        if project_id is not None:
            proj_competitor_ids = set(
                self.competitors.distinct("id", {"project_id": project_id})
            )
            if not proj_competitor_ids:
                return []
        cid_linked_ids: Optional[set] = None
        if competitor_id is not None:
            # SQL: (p.competitor_id = ? OR EXISTS link for this competitor)
            cid_linked_ids = set(self.post_competitors.distinct(
                "post_id", {"competitor_id": competitor_id}
            ))
            mongo_filter["$or"] = [
                {"competitor_id": competitor_id},
                {"id": {"$in": list(cid_linked_ids) if cid_linked_ids else [-1]}},
            ]

        docs: List[Dict] = list(self.posts.find(mongo_filter)) if mongo_filter else \
            list(self.posts.find())

        # Project scope: posts owned by the project's competitors UNION posts
        # linked through post_competitors (deduplicated by id).
        if proj_competitor_ids is not None:
            linked_from_project = set(self.post_competitors.distinct(
                "post_id", {"competitor_id": {"$in": list(proj_competitor_ids)}}
            ))
            docs = [
                post for post in docs
                if post["competitor_id"] in proj_competitor_ids
                or post["id"] in linked_from_project
            ]


        # Source visibility rules (COALESCE(post_source,'owner')).
        def _source_of(post):
            return post.get("post_source") or "owner"

        if source in ("owner", "public"):
            docs = [post for post in docs if _source_of(post) == source]
        elif not include_public:
            docs = [post for post in docs if _source_of(post) != "public"]

        # Owner updates first, then newest publications; public posts last.
        # Stable sorts from least to most significant key (SQL ORDER BY).
        docs.sort(key=lambda post: post.get("scrape_date") or "", reverse=True)
        docs.sort(key=lambda post: post.get("published_date") or "", reverse=True)
        docs.sort(key=lambda post: 0 if post.get("published_date") else 1)
        docs.sort(key=lambda post: 1 if _source_of(post) == "public" else 0)

        docs = docs[int(offset):int(offset) + int(limit)]

        # The project's own listing lets callers flag posts that belong to the
        # owner's own Google Maps profile.
        own_place_id = None
        competitor_places: Dict[int, Optional[int]] = {}
        if project_id is not None:
            project_row = self.projects.find_one({"id": project_id}, {"place_id": 1})
            if project_row is not None:
                own_place_id = project_row.get("place_id")
            for comp_row in self.competitors.find(
                {"project_id": project_id}, {"id": 1, "place_id": 1}
            ):
                competitor_places[comp_row["id"]] = comp_row.get("place_id")

        owner_ids = sorted({post["competitor_id"] for post in docs})
        owners = {}
        if owner_ids:
            owners = {
                comp["id"]: comp
                for comp in self.competitors.find({"id": {"$in": owner_ids}})
            }

        posts = []
        for post in docs:
            owner = owners.get(post.get("competitor_id"))
            if owner is None:
                continue  # inner JOIN semantics of the old SQL
            item = _public(post)
            item["image_urls"] = _json_loads(post.get("image_urls"), [])
            item["detected_keywords"] = _json_loads(post.get("detected_keywords"), [])
            item["raw_data"] = _json_loads(post.get("raw_data"), {})
            item["post_source"] = _source_of(post)
            item["is_public"] = item["post_source"] == "public"
            item["competitor_name"] = owner.get("name")
            item["competitor_gmap_url"] = owner.get("gmap_url")
            item["is_own_profile"] = bool(
                own_place_id
                and competitor_places.get(post.get("competitor_id")) == own_place_id
            )
            posts.append(item)
        return posts

    def get_post(self, post_id: int) -> Optional[Dict]:
        post = self.posts.find_one({"id": post_id})
        if not post:
            return None
        owner = self.competitors.find_one({"id": post.get("competitor_id")})
        if owner is None:
            return None  # inner JOIN semantics of the old SQL
        item = _public(post)
        item["image_urls"] = _json_loads(post.get("image_urls"), [])
        item["detected_keywords"] = _json_loads(post.get("detected_keywords"), [])
        item["raw_data"] = _json_loads(post.get("raw_data"), {})
        item["competitor_name"] = owner.get("name")
        item["competitor_gmap_url"] = owner.get("gmap_url")
        return item

    # ------------------------------------------------------------------
    # Generated ideas
    # ------------------------------------------------------------------
    def add_generated_idea(self, project_id: int, idea_text: str) -> int:
        doc = {
            "id": self._next_id("generated_ideas"),
            "project_id": project_id,
            "idea_text": idea_text,
            "generated_at": _utc_ts(),
            "used_flag": 0,
        }
        self.generated_ideas.insert_one(doc)
        return doc["id"]

    def get_generated_ideas(self, project_id: int, limit: int = 50) -> List[Dict]:
        return [
            _public(doc)
            for doc in self.generated_ideas.find({"project_id": project_id})
            .sort("generated_at", DESCENDING)
            .limit(int(limit))
        ]

    def mark_idea_used(self, idea_id: int):
        self.generated_ideas.update_one({"id": idea_id}, {"$set": {"used_flag": 1}})

    # ------------------------------------------------------------------
    # Scraping logs
    # ------------------------------------------------------------------
    def start_scraping_log(self, project_id: int) -> int:
        doc = {
            "id": self._next_id("scraping_logs"),
            "project_id": project_id,
            "start_time": _local_full(),
            "end_time": None,
            "competitors_processed": 0,
            "posts_found": 0,
            "new_posts": 0,
            "duplicates_skipped": 0,
            "failures": 0,
            "captcha_encountered": 0,
            "error_info": None,
            "images_downloaded": 0,
            "competitor_names": None,
            "details": None,
            "status": "completed",
        }
        self.scraping_logs.insert_one(doc)
        return doc["id"]

    def update_scraping_log(self, log_id: int, **kwargs):
        updates: Dict = {}
        for key, value in kwargs.items():
            if value is not None:
                updates[key] = _as_str(value) if isinstance(value, datetime) else value
        if updates:
            self.scraping_logs.update_one({"id": log_id}, {"$set": updates})

    def get_scraping_logs(self, project_id: int, limit: int = 10) -> List[Dict]:
        """Persistent per-run scraping logs (requirement 21)."""
        return [
            self._decorate_scraping_log(_public(doc))
            for doc in self.scraping_logs.find({"project_id": project_id})
            .sort("start_time", DESCENDING)
            .limit(int(limit))
        ]

    # ------------------------------------------------------------------
    # Reviews
    # ------------------------------------------------------------------
    def add_review(self, project_id: int, competitor_id: int,
                   review_data: Dict) -> Optional[int]:
        """Persist one scraped Google Maps review.

        Duplicate reviews (same competitor + author + text prefix) are skipped
        via a SHA-256 content hash so repeated runs never double the review
        analytics. Returns the new id, or ``None`` for a duplicate.
        """
        text = (review_data.get("text_content") or "").strip()
        if not text:
            return None

        author = (review_data.get("author") or "").strip() or None
        review_date = review_data.get("review_date") or review_data.get("published_date")
        content_hash = hashlib.sha256(
            f"{competitor_id}|{(author or '').lower()}|{(text or '')[:400]}".encode("utf-8")
        ).hexdigest()[:40]

        if self.reviews.find_one({"content_hash": content_hash}, {"id": 1}):
            return None

        keywords = review_data.get("detected_keywords") or []
        if isinstance(keywords, str):
            keywords = _json_loads(keywords, [])

        doc = {
            "id": self._next_id("reviews"),
            "project_id": project_id,
            "competitor_id": competitor_id,
            "author": author,
            "rating": review_data.get("rating"),
            "relative_date": review_data.get("relative_date"),
            "review_date": review_date,
            "text_content": text[:5000],
            "sentiment": review_data.get("sentiment"),
            "sentiment_score": review_data.get("sentiment_score"),
            "detected_topic": review_data.get("detected_topic"),
            "detected_keywords": keywords,
            "source_url": review_data.get("source_url"),
            "created_at": _utc_ts(),
            "content_hash": content_hash,
        }
        try:
            self.reviews.insert_one(doc)
            return doc["id"]
        except DuplicateKeyError:
            return None

    def get_reviews(self, project_id: int, competitor_id: Optional[int] = None,
                    sentiment: Optional[str] = None, topic: Optional[str] = None,
                    rating: Optional[int] = None, limit: int = 100,
                    offset: int = 0) -> List[Dict]:
        query: Dict = {"project_id": project_id}
        if competitor_id:
            query["competitor_id"] = competitor_id
        if sentiment and sentiment.lower() != "all":
            query["sentiment"] = {"$regex": f"^{re.escape(sentiment)}$", "$options": "i"}
        if topic and topic.lower() != "all":
            query["detected_topic"] = {"$regex": f"^{re.escape(topic)}$", "$options": "i"}
        if rating:
            query["rating"] = rating

        owner_ids = None
        reviews = []
        for doc in self.reviews.find(query).sort("id", DESCENDING).skip(int(offset)).limit(int(limit)):
            rev = _public(doc)
            rev["detected_keywords"] = _json_loads(rev.get("detected_keywords"), [])
            reviews.append(rev)
        owner_ids = sorted({rev.get("competitor_id") for rev in reviews if rev.get("competitor_id")})
        owners = {}
        if owner_ids:
            owners = {
                comp["id"]: comp
                for comp in self.competitors.find({"id": {"$in": owner_ids}})
            }
        for rev in reviews:
            owner = owners.get(rev.get("competitor_id"))
            rev["competitor_name"] = (owner or {}).get("name")
            rev["competitor_gmap_url"] = (owner or {}).get("gmap_url")
        return reviews

    # ------------------------------------------------------------------
    # Analytics (aggregations ported 1:1 from the SQL versions)
    # ------------------------------------------------------------------
    @staticmethod
    def _days_ago(days: int) -> str:
        from datetime import timedelta
        return (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")

    def get_topic_frequency(self, project_id: int) -> List[Dict]:
        total_competitors = self.competitors.count_documents({"project_id": project_id})
        if total_competitors <= 0:
            total_competitors = 1

        proj_comps = self.competitors.distinct("id", {"project_id": project_id})
        counts = collections.Counter()
        users: Dict[str, set] = collections.defaultdict(set)
        if proj_comps:
            for post in self.posts.find(
                {"competitor_id": {"$in": proj_comps},
                 "detected_topic": {"$nin": [None, ""]},
                 "post_source": {"$ne": "public"}},
                {"detected_topic": 1, "competitor_id": 1},
            ):
                topic = post["detected_topic"]
                counts[topic] += 1
                users[topic].add(post["competitor_id"])

        topics = []
        for topic, count in counts.most_common():
            competitor_count = len(users[topic])
            item = {
                "detected_topic": topic,
                "count": count,
                "competitor_count": competitor_count,
            }
            item["competitors_using"] = f"{competitor_count} of {total_competitors}"
            item["occurrence_percentage"] = round(
                (competitor_count / total_competitors) * 100, 1
            )
            item["total_competitors"] = total_competitors
            topics.append(item)
        return topics

    def get_keyword_frequency(self, project_id: int) -> List[Dict]:
        proj_comps = self.competitors.distinct("id", {"project_id": project_id})
        counts = collections.Counter()
        if proj_comps:
            for post in self.posts.find(
                {"competitor_id": {"$in": proj_comps}, "post_source": {"$ne": "public"}},
                {"detected_keywords": 1},
            ):
                for keyword in _json_loads(post.get("detected_keywords"), []):
                    counts[keyword] += 1
        return [
            {"keyword": keyword, "count": count}
            for keyword, count in counts.most_common()
        ]

    def get_scraping_stats(self, project_id: int) -> Dict:
        """Aggregated dashboard statistics (requirement 20).

        Everything the dashboard needs is derived from the persistent
        repository so it survives refreshes and restarts.
        """
        competitors_count = self.competitors.count_documents({"project_id": project_id})
        unique_businesses = len(set(self.competitors.distinct(
            "place_id", {"project_id": project_id, "place_id": {"$ne": None}}
        ))) or competitors_count

        proj_comps = self.competitors.distinct("id", {"project_id": project_id})
        scope: Dict[int, Dict] = {}
        # Stats need neither review text nor raw HTML/media. Fetching complete
        # post documents multiplied memory usage during concurrent dashboards.
        stats_fields = {"id": 1, "post_source": 1, "scrape_date": 1, "_id": 0}
        if proj_comps:
            for post in self.posts.find({"competitor_id": {"$in": proj_comps}}, stats_fields):
                scope[post["id"]] = post
            linked_ids = self.post_competitors.distinct(
                "post_id", {"competitor_id": {"$in": proj_comps}}
            )
            for post in self.posts.find({"id": {"$in": linked_ids}}, stats_fields):
                scope[post["id"]] = post

        total_posts = len(scope)
        public_posts = sum(
            1 for post in scope.values()
            if (post.get("post_source") or "owner") == "public"
        )
        seven_days_ago = self._days_ago(7)
        posts_last_7_days = sum(
            1 for post in scope.values()
            if (post.get("scrape_date") or "") >= seven_days_ago
        )

        logs = self.get_scraping_logs(project_id, 50)
        runs_with_failures = sum(1 for log in logs if log["failures"])
        totals = {
            "total_runs": len(logs),
            "successful_runs": len(logs) - runs_with_failures,
            "failed_attempts": sum(log["failures"] for log in logs),
            "captcha_interventions": sum(1 for log in logs if log["has_captcha_issue"]),
            "images_downloaded": sum(log["images_downloaded"] for log in logs),
            "posts_found": sum(log["posts_found"] for log in logs),
            "new_posts": sum(log["new_posts"] for log in logs),
            "duplicates_skipped": sum(log["duplicates_skipped"] for log in logs),
            "competitors_processed": sum(log["competitors_processed"] for log in logs),
        }
        totals["success_rate"] = (
            round((totals["successful_runs"] / totals["total_runs"]) * 100, 1)
            if totals["total_runs"] else 100.0
        )

        generated_content_count = self.generated_ideas.count_documents(
            {"project_id": project_id}
        )
        generated_content_used = self.generated_ideas.count_documents(
            {"project_id": project_id, "used_flag": 1}
        )
        latest_run = logs[0] if logs else None
        topics = self.get_topic_frequency(project_id)
        keywords = self.get_keyword_frequency(project_id)

        return {
            "project_id": project_id,
            "competitors_count": competitors_count,
            "unique_businesses": unique_businesses,
            "total_posts": total_posts,
            "owner_posts": max(0, total_posts - public_posts),
            "public_posts": public_posts,
            "posts_last_7_days": posts_last_7_days,
            "latest_run": latest_run,
            "new_posts_latest_run": latest_run["new_posts"] if latest_run else 0,
            "duplicates_skipped_latest_run": (
                latest_run["duplicates_skipped"] if latest_run else 0
            ),
            "images_downloaded_latest_run": (
                latest_run["images_downloaded"] if latest_run else 0
            ),
            "failures_latest_run": latest_run["failures"] if latest_run else 0,
            "captcha_latest_run": bool(latest_run and latest_run["has_captcha_issue"]),
            "last_scrape_at": latest_run.get("start_time") if latest_run else None,
            "last_scrape_status": latest_run.get("status") if latest_run else None,
            "totals": totals,
            "generated_content_count": generated_content_count,
            "generated_content_used": generated_content_used,
            "top_topics": [
                {"topic": t.get("detected_topic") or t.get("topic"),
                 "count": t.get("count") or 0}
                for t in topics[:5]
            ],
            "top_keywords": [
                {"keyword": k.get("keyword"), "count": k.get("count") or 0}
                for k in keywords[:8] if k.get("keyword")
            ],
        }

    def get_market_overview(self, project_id: int) -> Dict:
        """Real scraped market overview for the dashboard/analytics header."""
        # 1. Competitor profile stats (real scraped Google Maps values only).
        comp_docs = list(self.competitors.find({"project_id": project_id}))
        ratings = [c.get("rating") for c in comp_docs if c.get("rating") is not None]
        avg_rating = (sum(ratings) / len(ratings)) if ratings else None
        review_totals = [c.get("review_count") for c in comp_docs
                         if c.get("review_count") is not None]
        total_reviews_meta = sum(review_totals) if review_totals else None

        # 2. Real post count (posts owned by this project's competitors).
        proj_ids = [c["id"] for c in comp_docs]
        actual_posts = self.posts.count_documents(
            {"competitor_id": {"$in": proj_ids}}
        ) if proj_ids else 0

        # 3. Sentiment breakdown from captured reviews. No review rows yet =>
        #    no percentages (the UI shows an honest empty state).
        sentiment_counts: Dict[str, int] = collections.Counter()
        for review in self.reviews.find({"project_id": project_id}, {"sentiment": 1}):
            sentiment_counts[review.get("sentiment")] += 1
        total_rev_sampled = sum(sentiment_counts.values())

        pos_pct = neg_pct = neu_pct = None
        if total_rev_sampled > 0:
            pos_pct = round((sentiment_counts.get("Positive", 0) / total_rev_sampled) * 100, 1)
            neg_pct = round((sentiment_counts.get("Negative", 0) / total_rev_sampled) * 100, 1)
            neu_pct = round((sentiment_counts.get("Neutral", 0) / total_rev_sampled) * 100, 1)

        # 4. Total reviews: real listing volumes first, then captured reviews.
        total_reviews = total_reviews_meta
        if not total_reviews:
            total_reviews = total_rev_sampled or 0

        # 5/6. Top discussion topic and top negative topic (from reviews).
        def _top_topic(match: Dict):
            counts: Dict[str, int] = collections.Counter()
            for review in self.reviews.find(
                {**match, "project_id": project_id,
                 "detected_topic": {"$nin": [None, ""]}},
                {"detected_topic": 1},
            ):
                counts[review["detected_topic"]] += 1
            return counts.most_common(1)[0][0] if counts else None

        top_discussion_topic = _top_topic({})
        top_negative_topic = _top_topic({"sentiment": "Negative"})

        # 7. Competitor details with place coords for scatter & map.
        captured_by_comp: Dict[int, int] = collections.Counter()
        for review in self.reviews.find({"project_id": project_id}, {"competitor_id": 1}):
            captured_by_comp[review.get("competitor_id")] += 1
        place_ids = {c.get("place_id") for c in comp_docs if c.get("place_id")}
        places = {
            place["id"]: place
            for place in self.places.find({"id": {"$in": list(place_ids)}})
        } if place_ids else {}

        competitors = []
        for comp in comp_docs:
            captured = captured_by_comp.get(comp["id"], 0)
            review_count = comp.get("review_count")
            effective = review_count if review_count is not None else (captured or 0)
            place = places.get(comp.get("place_id")) or {}
            competitors.append({
                "id": comp["id"],
                "name": comp.get("name"),
                "rating": comp.get("rating"),
                "review_count": review_count,
                "post_count": comp.get("post_count"),
                "address": comp.get("address"),
                "gmap_url": comp.get("gmap_url"),
                "latitude": place.get("latitude"),
                "longitude": place.get("longitude"),
                "google_place_id": place.get("google_place_id"),
                "effective_review_count": effective,
                "captured_reviews": captured,
            })

        def _overview_sort_key(competitor: Dict):
            rating = competitor.get("rating") or 0
            review_count = competitor.get("review_count")
            effective = (review_count if review_count is not None
                         else (competitor.get("captured_reviews") or 0))
            post_count = competitor.get("post_count") or 0
            ranked = 1 if (rating > 0 and (effective > 0 or post_count > 0)) else 0
            raw_rating = competitor.get("rating")
            score = effective * (raw_rating if raw_rating is not None else 1.0)
            return (-ranked, -score, -post_count, competitor.get("id") or 0)

        competitors.sort(key=_overview_sort_key)
        for competitor in competitors:
            # The charts read `review_count`; expose the effective (scraped)
            # number while keeping the raw listing metadata fields intact.
            if not competitor.get("review_count"):
                competitor["review_count"] = competitor.get("captured_reviews") or 0

        return {
            "market_avg_rating": round(avg_rating, 2) if avg_rating is not None else None,
            "total_reviews": total_reviews,
            "total_posts": actual_posts,
            "competitor_count": len(comp_docs) or len(competitors),
            "positive_sentiment_pct": pos_pct,
            "negative_sentiment_pct": neg_pct,
            "neutral_sentiment_pct": neu_pct,
            "top_discussion_topic": top_discussion_topic,
            "top_negative_topic": top_negative_topic,
            "competitors": competitors,
        }

    def get_review_analytics(self, project_id: int) -> Dict:
        """Sentiment / rating / topic analytics over captured reviews."""
        # 1. Sentiment counts.
        sentiment_dist: Dict = collections.Counter()
        for review in self.reviews.find({"project_id": project_id}, {"sentiment": 1}):
            sentiment_dist[review.get("sentiment")] += 1

        # 2. Rating distribution (1..5 stars), highest first.
        rating_counts: Dict[int, int] = collections.Counter()
        for review in self.reviews.find({"project_id": project_id}, {"rating": 1}):
            rating_counts[review.get("rating")] += 1
        rating_dist = {
            str(star): rating_counts[star]
            for star in sorted(rating_counts.keys(),
                               key=lambda value: (value is not None, value),
                               reverse=True)
        }

        # No individual reviews stored yet: fall back to the real star
        # breakdown scraped from each listing (aggregate counts only).
        if not rating_dist:
            aggregate: Dict[str, int] = {}
            for comp in self.competitors.find(
                {"project_id": project_id, "rating_distribution": {"$nin": [None, ""]}},
                {"rating_distribution": 1},
            ):
                distribution = _json_loads(comp.get("rating_distribution"), {})
                if not isinstance(distribution, dict):
                    continue
                for star, count in distribution.items():
                    try:
                        aggregate[str(int(star))] = aggregate.get(str(int(star)), 0) + int(count)
                    except (TypeError, ValueError):
                        continue
            rating_dist = aggregate

        # 3/4. Topic ranking (and negative-only ranking) with competitor names.
        def _topic_ranking(match: Dict) -> List[Dict]:
            grouped: Dict[str, Dict] = {}
            order: List[str] = []
            rows = []
            for review in self.reviews.find(
                {**match, "project_id": project_id,
                 "detected_topic": {"$nin": [None, ""]}},
                {"detected_topic": 1, "competitor_id": 1},
            ):
                rows.append(review)
            counts: Dict = collections.defaultdict(collections.Counter)
            for review in rows:
                counts[review["detected_topic"]][review.get("competitor_id")] += 1
            for topic, per_comp in counts.items():
                grouped[topic] = {"topic": topic, "count": 0, "competitors": {}}
                for comp_id, mentions in per_comp.items():
                    grouped[topic]["count"] += mentions
                    owner = self.competitors.find_one({"id": comp_id}, {"name": 1})
                    name = (owner or {}).get("name") or str(comp_id)
                    grouped[topic]["competitors"][name] = mentions
                order.append(topic)
            result = [grouped[topic] for topic in order]
            result.sort(key=lambda item: item["count"], reverse=True)
            return result

        topics_list = _topic_ranking({})
        neg_list = _topic_ranking({"sentiment": "Negative"})

        return {
            "sentiment_distribution": dict(sentiment_dist),
            "rating_distribution": rating_dist,
            "topics": topics_list,
            "negative_topics": neg_list,
        }

    def get_market_gaps(self, project_id: int) -> List[Dict]:
        """Synthesize market gaps from **real scraped data only**.

        Every card is derived from captured Google Maps values (ratings,
        review counts, scraped reviews and posts). If a project has no data
        for a signal, that card is omitted.
        """
        overview = self.get_market_overview(project_id)
        analytics = self.get_review_analytics(project_id)
        competitors = overview.get("competitors", []) or []
        gaps: List[Dict] = []

        if not competitors and not (analytics.get("topics") or []):
            return gaps

        # ---------- 1. Real negative-review friction (only when captured) ----
        negative_topics = analytics.get("negative_topics", []) or []
        if negative_topics:
            top_complaint = negative_topics[0]
            topic = top_complaint.get("topic") or "Negative feedback"
            affected = list((top_complaint.get("competitors") or {}).keys())
            complaint_count = top_complaint.get("count") or 0

            quote = ""
            for review in self.get_reviews(project_id, sentiment="Negative", limit=1):
                text = (review.get("text_content") or "").strip().replace("\n", " ")
                if text:
                    quote = text[:160]
                    break

            weakness = (
                f"{complaint_count} captured negative review(s) mention "
                f"'{topic}'"
                + (f" — main sources: {', '.join(affected[:3])}." if affected else ".")
            )
            if quote:
                weakness += f' Example: "{quote}"'

            gaps.append({
                "id": "gap-policy-friction",
                "title": f"Customer Friction & Complaints in {topic}",
                "category": "Customer Sentiment Deficit",
                "icon_type": "shield-alert",
                "badge": "Critical Opportunity",
                "badge_color": "terracotta",
                "competitor_weakness": weakness,
                "actionable_strategy": (
                    f"Address the '{topic}' complaints head-on in your Google Maps "
                    "posts and profile: publish the guarantee, policy or service "
                    "change that removes that exact friction for customers."
                ),
                "expected_impact": "Convert dissatisfied rival customers into first-time visitors",
                "affected_competitors": affected[:3],
            })

        # ---------- 2. Publishing cadence (real captured post counts) --------
        low_publishers = [
            c["name"] for c in competitors if int(c.get("post_count") or 0) < 3
        ]
        if competitors and low_publishers:
            leader_posts = max(
                (int(c.get("post_count") or 0) for c in competitors), default=0
            )
            top_publishers = sorted(
                competitors, key=lambda c: int(c.get("post_count") or 0), reverse=True
            )[:2]
            top_names = ", ".join(
                f"{c['name']} ({int(c.get('post_count') or 0)} posts)" for c in top_publishers
            )
            gaps.append({
                "id": "gap-content-cadence",
                "title": "Google Maps Content Publishing Vacuum",
                "category": "Organic Visibility Void",
                "icon_type": "flame",
                "badge": "High Impact",
                "badge_color": "amber",
                "competitor_weakness": (
                    f"{len(low_publishers)} of {len(competitors)} tracked competitors "
                    f"have fewer than 3 captured Google Maps updates "
                    f"({', '.join(low_publishers[:3])}"
                    + ("…)" if len(low_publishers) > 3 else ")")
                    + f". Most active so far: {top_names}."
                ),
                "actionable_strategy": (
                    "Publish consistently (e.g. 2x weekly) with offers and updates; "
                    f"out-posting the busiest rival ({leader_posts} captured posts) "
                    "puts your profile in front of local searchers first."
                ),
                "expected_impact": (
                    f"Out-publish {len(low_publishers)} less active rival(s) "
                    "on the Google Maps feed"
                ),
                "affected_competitors": low_publishers[:4],
            })

        # ---------- 3. Rating quality gap (real scraped ratings) -------------
        rated = [c for c in competitors if c.get("rating") is not None]
        if len(rated) >= 2:
            weakest = min(rated, key=lambda c: float(c["rating"]))
            strongest = max(rated, key=lambda c: float(c["rating"]))
            market_avg = overview.get("market_avg_rating")
            gaps.append({
                "id": "gap-rating-quality",
                "title": f"Rating Quality Gap vs {weakest['name']}",
                "category": "Local Trust Deficit",
                "icon_type": "trending-up",
                "badge": "Competitive Edge",
                "badge_color": "sage",
                "competitor_weakness": (
                    f"{weakest['name']} sits at {float(weakest['rating']):.1f}★ "
                    f"({int(weakest.get('review_count') or 0):,} reviews) against a "
                    f"tracked-market average of "
                    f"{market_avg if market_avg is not None else 'n/a'}★"
                    + (
                        f", while {strongest['name']} leads at "
                        f"{float(strongest['rating']):.1f}★."
                        if strongest["id"] != weakest["id"] else "."
                    )
                ),
                "actionable_strategy": (
                    f"Lift visible trust above {float(weakest['rating']):.1f}★: showcase "
                    "five-star service stories, refresh photos, and answer every review "
                    "so your profile reads better than the weakest tracked rival."
                ),
                "expected_impact": (
                    f"Out-rank {weakest['name']} ({float(weakest['rating']):.1f}★) "
                    "on local trust signals"
                ),
                "affected_competitors": [weakest["name"]],
            })

        # ---------- 4. Review evidence coverage (real captured review rows) --
        captured: Dict[int, int] = collections.Counter()
        for review in self.reviews.find({"project_id": project_id}, {"competitor_id": 1}):
            captured[review.get("competitor_id")] += 1
        review_rows = [
            {"name": c["name"], "captured_reviews": captured.get(c["id"], 0)}
            for c in competitors
        ]
        missing_reviews = [r["name"] for r in review_rows if not r["captured_reviews"]]
        total_reviews = sum(int(r["captured_reviews"] or 0) for r in review_rows)
        competitors_with_reviews = len(review_rows) - len(missing_reviews)

        if review_rows and missing_reviews:
            gaps.append({
                "id": "gap-review-evidence",
                "title": "Review Evidence Coverage Gap",
                "category": "Data Coverage",
                "icon_type": "clock",
                "badge": "Quick Win",
                "badge_color": "sage",
                "competitor_weakness": (
                    f"{total_reviews} review(s) captured for {competitors_with_reviews} "
                    f"of {len(review_rows)} competitors; no reviews captured yet for "
                    f"{len(missing_reviews)} ({', '.join(missing_reviews[:3])}"
                    + ("…)" if len(missing_reviews) > 3 else ")")
                    + "."
                ),
                "actionable_strategy": (
                    "Re-scrape the competitors without captured reviews so sentiment, "
                    "rating distribution and complaint analysis cover the whole market "
                    "before deciding the next campaign."
                ),
                "expected_impact": "Complete review intelligence across every tracked competitor",
                "affected_competitors": missing_reviews[:4],
            })

        return gaps

    def _product_trends_for_project(self, project_id: int) -> Dict:
        """Which EXACT products are mentioned over time (posts + reviews).

        Products are extracted with the project's industry vocabulary, so a
        cafe project gets espresso/frappe/cold brew while a fashion project
        gets shirts/jeans/blazers. Works from both captured posts and reviews.
        """

        def month_label(value):
            if not value:
                return None
            try:
                return datetime.fromisoformat(str(value)[:10]).strftime("%b %Y")
            except Exception:
                return None

        project_row = self.get_project(project_id) or {}
        industry = infer_industry(
            project_row.get("field"), project_row.get("our_profile")
        )

        proj_comps = self.competitors.distinct("id", {"project_id": project_id})
        comp_names = {}
        if proj_comps:
            for comp in self.competitors.find({"id": {"$in": proj_comps}},
                                              {"id": 1, "name": 1}):
                comp_names[comp["id"]] = comp.get("name")

        sources = []
        if proj_comps:
            # Posts first, then reviews (SQL UNION ALL order matters for
            # first-seen month ordering before the chronological sort).
            for post in self.posts.find(
                {"competitor_id": {"$in": proj_comps}},
                {"competitor_id": 1, "published_date": 1, "text_content": 1},
            ):
                label = month_label(post.get("published_date"))
                if label and post.get("text_content"):
                    sources.append((comp_names.get(post["competitor_id"]), label,
                                    post["text_content"]))
            for review in self.reviews.find(
                {"project_id": project_id},
                {"competitor_id": 1, "review_date": 1, "text_content": 1},
            ):
                label = month_label(review.get("review_date"))
                if label and review.get("text_content"):
                    sources.append((comp_names.get(review["competitor_id"]), label,
                                    review["text_content"]))

        month_order = []
        seen_months = set()
        for _, label, _ in sources:
            if label not in seen_months:
                seen_months.add(label)
                month_order.append(label)
        month_order.sort(key=lambda m: datetime.strptime(m, "%b %Y"))

        product_months = collections.defaultdict(collections.Counter)
        product_group = {}
        product_competitors = collections.defaultdict(set)
        for comp_name, label, text in sources:
            for group, product in extract_products(text, industry):
                product_months[product][label] += 1
                product_group.setdefault(product, group)
                product_competitors[product].add(comp_name)

        trends = []
        for product, months_counter in product_months.items():
            data = [months_counter.get(month, 0) for month in month_order]
            half = len(data) // 2
            first_half = sum(data[:half]) if half > 0 else 0
            second_half = sum(data[half:])
            if first_half == 0 and second_half > 0:
                direction = "rising"
            elif second_half > first_half * 1.2:
                direction = "rising"
            elif first_half > second_half * 1.2:
                direction = "falling"
            else:
                direction = "stable"

            active_months = [
                month_order[index] for index, value in enumerate(data) if value
            ]
            trends.append({
                "product": product,
                "group": product_group.get(product, "Other"),
                "occurrence": sum(data),
                "competitors_using": len(product_competitors[product]),
                "data": data,
                "first_month": active_months[0] if active_months else None,
                "last_month": active_months[-1] if active_months else None,
                "trend_direction": direction,
            })

        trends.sort(
            key=lambda item: (item["occurrence"], item["competitors_using"]),
            reverse=True,
        )
        return {
            "product_trends": trends[:30],
            "product_groups": sorted({product_group[p] for p in product_months}),
            "product_months": month_order,
        }

    def get_trend_analysis(self, project_id: int) -> Dict:
        """Analyse topic and keyword trends across competitor posts.

        Returns topic table, keyword table, monthly frequency data, and trend
        direction per topic (same payload shape as the SQL implementation).
        """
        # All posts for this project with competitor info and date.
        proj_comps = self.competitors.distinct("id", {"project_id": project_id})
        comp_names: Dict[int, str] = {}
        if proj_comps:
            for comp in self.competitors.find({"id": {"$in": proj_comps}},
                                              {"id": 1, "name": 1}):
                comp_names[comp["id"]] = comp.get("name")
            rows = [
                (comp_names.get(post["competitor_id"]), post["competitor_id"],
                 post.get("detected_topic"), post.get("detected_keywords"),
                 post.get("published_date"), post.get("text_content"))
                for post in self.posts.find(
                    {"competitor_id": {"$in": proj_comps}},
                    {"competitor_id": 1, "detected_topic": 1, "detected_keywords": 1,
                     "published_date": 1, "text_content": 1},
                )
            ]
        else:
            rows = []
        rows.sort(key=lambda row: (row[4] or ""))

        if not rows:
            # No owner posts at all: charts have nothing to show, but products
            # can still be tracked from captured reviews.
            empty_payload = {
                "topic_trends": [],
                "keyword_trends": [],
                "monthly_volume": {},
                "months": [],
                "competitor_monthly": [],
                "topic_competitor_monthly": [],
                "product_trends": [],
                "product_groups": [],
                "product_months": [],
                "total_posts": 0,
                "total_competitors": 0,
            }
            empty_payload.update(self._product_trends_for_project(project_id))
            return empty_payload

        # --- Brand word blocklist (competitor names -> not keywords) --------
        brand_blocklist = set()
        for comp in self.competitors.find({"project_id": project_id}, {"name": 1}):
            cname = comp.get("name")
            if not cname:
                continue
            brand_blocklist.add(cname.lower())
            for word in cname.lower().split():
                if len(word) > 3:
                    brand_blocklist.add(word)

        common_fashion_words = {
            "collection", "style", "fashion", "wear", "clothes", "clothing", "dress",
            "shirt", "fabric", "premium", "quality", "casual", "formal", "comfort",
            "design", "trend", "summer", "winter", "spring", "season", "store",
            "visit", "offer", "sale", "movement", "wedding", "celebration",
            "trousers", "chinos", "jackets",
        }

        # Capitalized proprietary collection names in post text -> blocklist.
        for _, _, _, _, _, text_body in rows:
            if text_body:
                for word in re.findall(r"\b[A-Z][a-z]{3,}\b", text_body):
                    wl = word.lower()
                    if wl not in common_fashion_words and len(wl) > 4:
                        brand_blocklist.add(wl)

        common_stops = {
            "want", "through", "where", "bring", "press", "fomo", "ways", "grand",
            "their", "with", "your", "that", "this", "from", "have", "will", "more",
            "into", "also", "what", "when", "just", "make", "than", "been", "some",
            "they", "know", "over",
        }

        all_comp_names = set(row[0] for row in rows)
        total_posts = len(rows)
        total_competitors = len(all_comp_names)

        topic_comp_map: Dict[str, set] = collections.defaultdict(set)
        topic_count: "collections.Counter" = collections.Counter()
        topic_months: Dict[str, Dict[str, int]] = collections.defaultdict(
            lambda: collections.defaultdict(int)
        )
        kw_comp_map: Dict[str, set] = collections.defaultdict(set)
        kw_count: "collections.Counter" = collections.Counter()

        for comp_name, comp_id, topic, kws_raw, date_str, text in rows:
            month_key = "Unknown"
            if date_str:
                try:
                    month_key = datetime.fromisoformat(str(date_str)[:10]).strftime("%b %Y")
                except Exception:
                    pass

            if topic and topic.strip():
                topic_comp_map[topic].add(comp_name)
                topic_count[topic] += 1
                topic_months[topic][month_key] += 1

            kws = _json_loads(kws_raw, [])
            if not isinstance(kws, list):
                kws = []
            for kw in kws:
                if not kw or len(str(kw)) < 3:
                    continue
                kwl = str(kw).lower().strip()
                if kwl in brand_blocklist or kwl in common_stops:
                    continue
                if any(bw == kwl or bw in kwl for bw in brand_blocklist):
                    continue
                kw_comp_map[kw].add(comp_name)
                kw_count[kw] += 1

        # --- topic_trends table --------------------------------------------
        topic_trends = []
        for topic, count in topic_count.most_common():
            comps_using = len(topic_comp_map[topic])
            months_data = topic_months[topic]
            sorted_months = sorted(months_data.keys())
            mid = len(sorted_months) // 2
            first_half = sum(months_data[m] for m in sorted_months[:mid]) if mid > 0 else 0
            second_half = sum(months_data[m] for m in sorted_months[mid:])
            if first_half == 0 and second_half > 0:
                direction = "rising"
            elif second_half > first_half * 1.2:
                direction = "rising"
            elif first_half > second_half * 1.2:
                direction = "falling"
            else:
                direction = "stable"

            topic_trends.append({
                "topic": topic,
                "occurrence": count,
                "occurrence_pct": round(count / total_posts * 100, 1),
                "competitors_using": comps_using,
                "competitor_pct": round(comps_using / max(total_competitors, 1) * 100, 1),
                "total_competitors": total_competitors,
                "trend_direction": direction,
                "monthly_breakdown": dict(months_data),
            })

        # --- keyword_trends table (top 25) ---------------------------------
        keyword_trends = []
        for kw, count in kw_count.most_common(25):
            keyword_trends.append({
                "keyword": kw,
                "occurrence": count,
                "occurrence_pct": round(count / total_posts * 100, 1),
                "competitors_using": len(kw_comp_map[kw]),
                "total_competitors": total_competitors,
            })

        # --- Monthly total volume ------------------------------------------
        monthly_volume: "collections.Counter" = collections.Counter()
        for _, _, _, _, date_str, _ in rows:
            if date_str:
                try:
                    monthly_volume[datetime.fromisoformat(str(date_str)[:10]).strftime("%b %Y")] += 1
                except Exception:
                    pass

        # --- Per-competitor monthly series (one line per competitor) --------
        # Posts without a parsed date cannot be placed on a timeline.
        monthly_by_competitor: "collections.OrderedDict" = collections.OrderedDict()
        topic_competitor_months = collections.defaultdict(
            lambda: collections.defaultdict(collections.Counter)
        )
        ordered_months: List[str] = []
        seen_months = set()

        def _month_label(raw_date):
            try:
                return datetime.fromisoformat(str(raw_date)[:10]).strftime("%b %Y")
            except Exception:
                return None

        dated_rows = []
        for row in rows:
            date_str = row[4]
            label = _month_label(date_str) if date_str else None
            if not label:
                continue
            dated_rows.append((row, label))
        dated_rows.sort(key=lambda item: (datetime.fromisoformat(str(item[0][4])[:10]),
                                          item[0][0] or ""))

        for row, label in dated_rows:
            comp_name = row[0]
            topic = row[2] or "General Update"
            monthly_by_competitor.setdefault(comp_name, collections.Counter())[label] += 1
            topic_competitor_months[topic][comp_name][label] += 1
            if label not in seen_months:
                seen_months.add(label)
                ordered_months.append(label)

        # --- Product-level demand over time --------------------------------
        product_payload = self._product_trends_for_project(project_id)

        series = []
        for comp_name, months_counter in monthly_by_competitor.items():
            series.append({
                "competitor": comp_name,
                "total": sum(months_counter.values()),
                "data": [months_counter.get(month, 0) for month in ordered_months],
            })
        series.sort(key=lambda item: item["total"], reverse=True)

        topic_series = []
        for topic, comp_months in sorted(
            topic_competitor_months.items(),
            key=lambda item: -sum(sum(counter.values()) for counter in item[1].values())
        ):
            entries = []
            for comp_name, months_counter in comp_months.items():
                entries.append({
                    "competitor": comp_name,
                    "total": sum(months_counter.values()),
                    "data": [months_counter.get(month, 0) for month in ordered_months],
                })
            entries.sort(key=lambda item: item["total"], reverse=True)
            topic_series.append({"topic": topic, "series": entries})

        return {
            "topic_trends": topic_trends,
            "keyword_trends": keyword_trends,
            "monthly_volume": dict(monthly_volume),
            "months": ordered_months,
            "competitor_monthly": series,
            "topic_competitor_monthly": topic_series,
            **product_payload,
            "total_posts": total_posts,
            "total_competitors": total_competitors,
        }




























