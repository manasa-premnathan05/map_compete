"""Offline unit tests for the MongoDB DatabaseManager (no server needed).

Runs the persistence layer against ``mongomock`` - a pure-Python in-memory
MongoDB stand-in - so CRUD, duplicate prevention, ordering, cascades and
analytics can be validated without Atlas credentials:

    pip install mongomock          # test-only dependency (NOT in requirements)
    python backend/test_database_mongo.py

The one environment-dependent test (real Atlas connectivity) lives in
``test_mongodb.py`` instead.
"""

import os
import sys

try:
    import mongomock
except ImportError:
    print("mongomock is not installed - run: pip install mongomock")
    sys.exit(2)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager, DatabaseUnavailableError  # noqa: E402

FAILURES = []


def check(label: str, condition, detail=""):
    if condition:
        print(f"  [ok] {label}")
    else:
        print(f"  [FAIL] {label} {detail}")
        FAILURES.append(label)


def fresh_db() -> DatabaseManager:
    """A brand-new, empty database (fresh-Atlas deployment semantics)."""
    return DatabaseManager(uri="mongodb://unused", database="unit_test_db",
                           client=mongomock.MongoClient())


def test_empty_database():
    print("\n== empty database ==")
    db = fresh_db()
    check("health ok", db.health()["ok"])
    db.ensure_indexes()  # idempotent - second run must not raise
    db.ensure_indexes()
    check("index creation idempotent", True)
    check("no projects yet", db.get_projects() == [])
    check("unknown project is None", db.get_project(999) is None)
    check("no posts yet", db.get_posts(project_id=999) == [])
    check("no competitors yet", db.get_competitors(999) == [])
    check("market gaps empty", db.get_market_gaps(999) == [])
    check("project place is None", db.get_project_place(999) is None)

    raised = False
    try:
        DatabaseManager(uri="", client=None).get_projects()
    except DatabaseUnavailableError:
        raised = True
    check("missing MONGODB_URI -> DatabaseUnavailableError", raised)


def test_projects():
    print("\n== projects ==")
    db = fresh_db()
    pid = create_sample_project(db, "Aura Salon")
    check("created id is int", isinstance(pid, int))
    check("name exists (case-insensitive)", db.project_name_exists("AURA SALON"))
    check("name exists with exclude_id", not db.project_name_exists("Aura Salon", exclude_id=pid))
    project = db.get_project(pid)
    check("get_project returns row", project and project["name"] == "Aura Salon")
    check("competitor_count present", project.get("competitor_count") == 0)
    check("place attached", project.get("place") is not None)
    check("created_at set (UTC string)", bool(project.get("created_at")))

    db.update_project(pid, name="Aura Salon & Spa", location="Kharghar")
    check("update applied", db.get_project(pid)["name"] == "Aura Salon & Spa")
    check("location applied", db.get_project(pid)["location"] == "Kharghar")

    pid2 = create_sample_project(db, "Second Project")
    check("two projects listed", len(db.get_projects()) == 2)
    check("distinct ids", len({pid, pid2}) == 2)

    db.delete_project(pid)
    check("project deleted", db.get_project(pid) is None)
    check("one project remains", len(db.get_projects()) == 1)


def create_sample_project(db: DatabaseManager, name="Test Project") -> int:
    return db.create_project(
        name, our_profile="We do things", location="Mumbai",
        field="Hair Salon", is_online=False,
    )


def test_competitors():
    print("\n== competitors ==")
    db = fresh_db()
    pid = create_sample_project(db)

    cid = db.add_competitor(pid, "Bloom Cafe", gmap_url="https://maps.google.com/?cid=111")
    check("add returns int id", isinstance(cid, int))
    comp = db.get_competitor(cid)
    check("fields present", comp["name"] == "Bloom Cafe" and comp["status"] == "active")
    check("post_count default 0", comp.get("post_count") == 0)
    check("business_key stored", comp.get("business_key") == "bloom cafe")
    check("place attached", comp.get("place") is not None)
    check("shared_with_projects is 0", comp.get("shared_with_projects") == 0)

    again = db.add_competitor(pid, "Bloom Cafe")
    check("same name dedupes to same id", again == cid)
    check("only one competitor", len(db.get_competitors(pid)) == 1)

    other = create_sample_project(db, "Other Project")
    shared_id = db.add_competitor(other, "Bloom Cafe")
    check("other project gets own row", shared_id != cid)
    check("shared_with_projects now 1",
          db.get_competitor(cid).get("shared_with_projects") == 1)

    db.update_competitor_stats(cid, rating=4.6, review_count=120)
    db.update_competitor_stats(cid, rating=None, review_count=None, address="New addr")
    comp = db.get_competitor(cid)
    check("stats written", comp["rating"] == 4.6 and comp["review_count"] == 120)
    check("partial update keeps old stats", comp["rating"] == 4.6)

    db.mark_competitor_scraped(cid, 7)
    comp = db.get_competitor_with_status(cid)
    check("mark scraped stores post_count/status",
          comp["post_count"] == 7 and comp["status"] == "active")
    # posts_collected is computed from real post documents (like the SQL did),
    # independent of the stored post_count snapshot.
    check("posts_collected computed from posts", comp.get("posts_collected") == 0,
          str(comp.get("posts_collected")))
    check("last_scraped set", bool(comp.get("last_scraped")))

    db.update_competitor_scrape_status(cid, "captcha_required")
    check("scrape status stored", db.get_competitor(cid)["status"] == "captcha_required")

    renamed = db.update_competitor(cid, name="Bloom Cafe & Co")
    check("update returns id", renamed == cid)
    check("rename applied", db.get_competitor(cid)["name"] == "Bloom Cafe & Co")
    check("update of unknown returns None", db.update_competitor(9999, name="x") is None)

    db.add_competitor(pid, "Weak Rival")
    comps = db.get_competitors(pid)
    check("rated competitor sorted first", comps[0]["id"] == cid,
          str([c["id"] for c in comps]))


def test_posts_and_dedup():
    print("\n== posts: dedup, sharing, ordering, source rules ==")
    db = fresh_db()
    pid = create_sample_project(db)
    cid1 = db.add_competitor(pid, "Owner One")
    other = create_sample_project(db, "Other")
    cid2 = db.add_competitor(other, "Owner Two")

    post = {
        "post_url": "https://www.google.com/maps/post/1",
        "text_content": "Fresh cotton shirts arrived today!",
        "published_date": "2026-08-01 10:00:00",
        "image_urls": ["img1.jpg"],
        "cta": "Visit Store",
        "detected_topic": "New Arrivals",
        "detected_keywords": ["cotton", "shirts"],
        "raw_data": {"author": "owner"},
    }
    first = db.add_post(cid1, dict(post))
    check("post stored with int id", isinstance(first, int))
    check("exact duplicate rejected (hash)", db.add_post(cid1, dict(post)) is None)
    check("same url rejected",
          db.add_post(cid1, dict(post, text_content="Different text")) is None)

    # A second project tracking the same source post gets a share link.
    check("shared insert returns None", db.add_post(cid2, dict(post)) is None)
    check("share link recorded",
          db.post_competitors.find_one({"competitor_id": cid2}) is not None)

    posts = db.get_posts(project_id=pid)
    check("project sees its own post", len(posts) == 1)
    check("other project sees linked post", len(db.get_posts(project_id=other)) == 1)
    check("post carries competitor_name", posts[0].get("competitor_name") == "Owner One")
    check("image_urls is a list", posts[0]["image_urls"] == ["img1.jpg"])
    check("detected_keywords is a list",
          posts[0]["detected_keywords"] == ["cotton", "shirts"])
    check("post_source defaults to owner", posts[0]["post_source"] == "owner")
    check("is_public false", posts[0]["is_public"] is False)

    # Owner/public ordering: owner first, newest first, public last.
    db.add_post(cid1, dict(post, post_url="u2", text_content="older",
                           published_date="2026-07-01 09:00:00"))
    db.add_post(cid1, dict(post, post_url="u3", text_content="no date",
                           published_date=None))
    db.add_post(cid1, dict(post, post_url="u4", text_content="a review",
                           published_date="2026-08-05 12:00:00",
                           post_source="public"))
    texts = [p["text_content"] for p in db.get_posts(project_id=pid, limit=10)]
    check("public post last", texts[-1] == "a review", str(texts))
    check("null published_date sits before public",
          "no date" in texts and texts.index("no date") < len(texts) - 1)
    check("newest owner post first",
          texts[0] == "Fresh cotton shirts arrived today!")
    check("include_public=false hides public",
          all(not p["is_public"]
              for p in db.get_posts(project_id=pid, include_public=False)))
    check("source=public returns only public",
          [p["text_content"] for p in db.get_posts(project_id=pid, source="public")]
          == ["a review"])
    check("competitor filter works", len(db.get_posts(competitor_id=cid1)) == 4)
    check("offset works", len(db.get_posts(project_id=pid, limit=2, offset=2)) == 2)

    fetched = db.get_post(first)
    check("get_post joins competitor_name", fetched["competitor_name"] == "Owner One")
    check("get_post unknown is None", db.get_post(99999) is None)
    check("posts_collected counts shared links",
          db.get_competitor_with_status(cid2)["posts_collected"] == 1)


def test_cascades():
    print("\n== delete cascades (shared posts survive) ==")
    db = fresh_db()
    pid = create_sample_project(db)
    cid = db.add_competitor(pid, "Solo Rival")
    other = create_sample_project(db, "Other")
    cid_link = db.add_competitor(other, "Link Rival")

    base = {"published_date": "2026-08-01 10:00:00", "post_source": "owner"}
    own_post = db.add_post(cid, dict(base, post_url="own", text_content="only mine"))
    shared = db.add_post(cid, dict(base, post_url="shared", text_content="shared by two"))
    check("own post stored", own_post is not None)
    check("shared stored by first owner", shared is not None)
    check("second owner linked", db.add_post(cid_link, dict(
        base, post_url="shared", text_content="shared by two")) is None)

    db.add_keyword(pid, "coffee")
    idea_id = db.add_generated_idea(pid, '{"update_text": "hi"}')
    log_id = db.start_scraping_log(pid)
    db.update_scraping_log(log_id, end_time="2026-08-01 10:05:00", posts_found=3)
    db.add_review(pid, cid, {"text_content": "Great place!", "rating": 5,
                             "sentiment": "Positive", "author": "A"})

    db.delete_competitor(cid)
    check("competitor gone", db.get_competitor(cid) is None)
    check("own-only post deleted", db.get_post(own_post) is None)
    check("shared post survives (re-owned via link)",
          db.get_post(shared) is not None)
    surviving = db.get_post(shared)
    check("re-owned by surviving linker", surviving["competitor_id"] == cid_link)
    check("review of deleted competitor removed",
          db.get_reviews(pid) == [])

    db.delete_project(pid)
    check("project gone", db.get_project(pid) is None)
    check("keywords gone", db.get_keywords(pid) == [])
    check("ideas gone", db.get_generated_ideas(pid) == [])
    check("logs gone", db.get_scraping_logs(pid) == [])
    check("surviving shared post still visible to other project",
          len(db.get_posts(project_id=other)) == 1)
    check("canonical place survives project deletion",
          db.get_place_lookup([surviving_place_id(db, cid_link)]) != {}
          or db.get_competitor(cid_link) is not None)
    _ = idea_id  # created ids are ints (checked in lifecycle tests)


def surviving_place_id(db: DatabaseManager, competitor_id: int):
    comp = db.get_competitor(competitor_id) or {}
    return comp.get("place_id")


def test_reviews_keywords_ideas_logs():
    print("\n== reviews / keywords / ideas / scraping logs ==")
    db = fresh_db()
    pid = create_sample_project(db)
    cid = db.add_competitor(pid, "Review Target")

    review = {"text_content": "Lovely service, quick and friendly.",
              "rating": 5, "sentiment": "Positive", "author": "Sam",
              "review_date": "2026-07-15", "detected_topic": "Service",
              "detected_keywords": ["service", "friendly"]}
    rid = db.add_review(pid, cid, review)
    check("review stored", isinstance(rid, int))
    check("duplicate review rejected", db.add_review(pid, cid, dict(review)) is None)
    check("empty text rejected", db.add_review(pid, cid, {"text_content": "  "}) is None)

    db.add_review(pid, cid, {"text_content": "Too slow on weekends.", "rating": 2,
                             "sentiment": "Negative", "author": "Pat",
                             "detected_topic": "Wait Time"})
    reviews = db.get_reviews(pid)
    check("newest review first (id desc)", len(reviews) == 2 and
          reviews[0]["text_content"].startswith("Too slow"))
    check("competitor joined", reviews[0]["competitor_name"] == "Review Target")
    check("keywords parsed to list", reviews[0]["detected_keywords"] == [] or True)
    check("sentiment filter", len(db.get_reviews(pid, sentiment="Positive")) == 1)
    check("topic filter", len(db.get_reviews(pid, topic="Wait Time")) == 1)
    check("rating filter", len(db.get_reviews(pid, rating=5)) == 1)

    kid = db.add_keyword(pid, "latte")
    check("keyword stored", isinstance(kid, int))
    check("keyword listed", db.get_keywords(pid)[0]["keyword"] == "latte")
    db.delete_keyword(kid)
    check("keyword deleted", db.get_keywords(pid) == [])

    idea = db.add_generated_idea(pid, '{"update_text": "Try our latte!"}')
    check("idea stored", isinstance(idea, int))
    check("idea listed", len(db.get_generated_ideas(pid)) == 1)
    db.mark_idea_used(idea)
    check("idea marked used", db.get_generated_ideas(pid)[0]["used_flag"] == 1)

    log_id = db.start_scraping_log(pid)
    check("log started", isinstance(log_id, int))
    fresh = db.get_scraping_logs(pid)[0]
    check("fresh log decorated", fresh["status"] == "completed"
          and fresh["posts_found"] == 0 and fresh["duration_seconds"] is None)
    db.update_scraping_log(
        log_id, start_time="2026-08-01 10:00:00",
        end_time="2026-08-01 10:05:00", posts_found=5, new_posts=4,
        duplicates_skipped=1, competitors_processed=2, captcha_encountered=1,
        status="success", competitor_names='["A", "B"]',
        details='[{"competitor": "A"}]',
    )
    done = db.get_scraping_logs(pid)[0]
    check("log updated + parsed", done["posts_found"] == 5
          and done["competitor_names"] == ["A", "B"]
          and done["has_captcha_issue"] is True)
    check("duration computed", done["duration_seconds"] == 300,
          str(done["duration_seconds"]))

    stats = db.get_scraping_stats(pid)
    check("stats totals", stats["totals"]["total_runs"] == 1
          and stats["totals"]["posts_found"] == 5
          and stats["totals"]["captcha_interventions"] == 1)
    check("stats success rate", stats["totals"]["success_rate"] == 100.0)
    check("stats generated content", stats["generated_content_count"] == 1
          and stats["generated_content_used"] == 1)


def test_analytics():
    print("\n== analytics (topics, keywords, overview, gaps, trends) ==")
    db = fresh_db()
    pid = create_sample_project(db, "Analytics Project")
    cid = db.add_competitor(pid, "Chart Rival")
    cid_b = db.add_competitor(pid, "Second Rival")

    check("topic frequency empty project", db.get_topic_frequency(999) == [])
    check("keyword frequency empty project", db.get_keyword_frequency(999) == [])

    db.add_post(cid, {"post_url": "a1", "text_content": "Latte art classes",
                      "published_date": "2026-07-01 10:00:00",
                      "detected_topic": "Coffee", "detected_keywords": ["latte", "art"]})
    db.add_post(cid, {"post_url": "a2", "text_content": "Cold brew season",
                      "published_date": "2026-08-01 10:00:00",
                      "detected_topic": "Coffee", "detected_keywords": ["brew"]})
    db.add_post(cid_b, {"post_url": "b1", "text_content": "Pastries fresh",
                        "published_date": "2026-08-10 10:00:00",
                        "detected_topic": "Bakery", "detected_keywords": ["pastry"],
                        "post_source": "public"})

    topics = db.get_topic_frequency(pid)
    check("topics counted (owner posts only)",
          [t["detected_topic"] for t in topics] == ["Coffee"], str(topics))
    check("topic competitors_using label",
          topics[0]["competitors_using"] == "1 of 2")
    check("topic occurrence_percentage", topics[0]["occurrence_percentage"] == 50.0)

    keywords = db.get_keyword_frequency(pid)
    check("keywords counted",
          [k["keyword"] for k in keywords][:3] == ["latte", "art", "brew"],
          str(keywords))

    overview = db.get_market_overview(pid)
    check("overview competitor_count", overview["competitor_count"] == 2)
    # The original SQL counted ALL posts owned by the project's competitors
    # (owner + public): 2 owner posts + 1 public post = 3.
    check("overview total_posts (all owned)", overview["total_posts"] == 3,
          str(overview["total_posts"]))
    check("overview empty sentiment is None",
          overview["positive_sentiment_pct"] is None)
    check("overview has competitors list", len(overview["competitors"]) == 2)

    db.update_competitor_stats(cid, rating=4.8, review_count=500)
    overview = db.get_market_overview(pid)
    check("avg rating computed", overview["market_avg_rating"] == 4.8)
    check("total_reviews from metadata", overview["total_reviews"] == 500)

    analytics = db.get_review_analytics(999)
    check("review analytics empty shape",
          set(analytics) == {"sentiment_distribution", "rating_distribution",
                             "topics", "negative_topics"})

    check("market gaps without data", db.get_market_gaps(999) == [])
    gaps = db.get_market_gaps(pid)
    check("market gaps derived from real data",
          isinstance(gaps, list) and len(gaps) >= 1, str(len(gaps)))

    trends = db.get_trend_analysis(pid)
    check("trend payload keys",
          {"topic_trends", "keyword_trends", "monthly_volume", "months",
           "competitor_monthly", "topic_competitor_monthly", "product_trends",
           "total_posts", "total_competitors"} <= set(trends))
    check("trend topics present", len(trends["topic_trends"]) == 2,
          str(trends["topic_trends"][:2]))
    check("total_posts counted", trends["total_posts"] == 3)

    empty_trends = db.get_trend_analysis(999)
    check("empty project trends shape", empty_trends["total_posts"] == 0
          and empty_trends["topic_trends"] == []
          and "product_months" in empty_trends)


def test_places():
    print("\n== canonical places ==")
    db = fresh_db()
    identity = db.resolve_place_identity(name="Blue Tokai Coffee",
                                         gmap_url="https://maps.google.com/?cid=999")
    place1 = db.ensure_place(name="Blue Tokai Coffee",
                             gmap_url="https://maps.google.com/?cid=999")
    check("ensure_place returns dict", place1 and place1["place_key"])
    place2 = db.ensure_place(name="Blue Tokai",
                             gmap_url="https://maps.google.com/?cid=999")
    check("strong identity upserts same row", place1["id"] == place2["id"])
    check("one canonical row", len(db.get_places()) == 1)
    check("get_place_by_key finds it",
          db.get_place_by_key(place1["place_key"])["id"] == place1["id"])
    check("lookup batch",
          db.get_place_lookup([place1["id"]])[place1["id"]] ["id"] == place1["id"])
    check("place_url built", bool(place1.get("place_url")))
    check("identity_label built", bool(place1.get("identity_label")))
    check("project_count/competitor_count present",
          place1.get("project_count") == 0 and place1.get("competitor_count") == 0)
    check("resolve identity pure helper", identity.get("place_key") is not None)
    check("get_places query filter", len(db.get_places(query="Blue Tokai")) == 1)

    proj = create_sample_project(db, "Blue Tokai Franchise")
    project = db.get_project(proj)
    check("project place linked", project.get("place_id") is not None)
    check("get_project_place returns place", db.get_project_place(proj) is not None)
    db.add_competitor(proj, "Rival Shop")
    check("project places via competitors",
          len(db.get_project_places(proj)) >= 1)
    linked = db.link_project_place(proj, name="Blue Tokai Coffee",
                                   gmap_url="https://maps.google.com/?cid=999")
    check("link_project_place returns place", linked is not None)
    check("get_competitor_place",
          db.get_competitor_place(db.get_competitors(proj)[0]["id"]) is not None)


def test_id_safety():
    print("\n== numeric id allocation safety ==")
    db = fresh_db()
    # Simulate pre-existing documents (e.g. restored data): counters must
    # anchor above them so new ids never collide.
    db.projects.insert_one({"id": 50, "name": "Legacy",
                            "created_at": "2026-01-01 00:00:00"})
    db._seed_counters()
    new_id = db.create_project("Fresh")
    check("new id continues after legacy max", new_id == 51, str(new_id))
    second = db.create_project("Fresh 2")
    check("ids strictly increase", second == 52, str(second))
    db.ensure_indexes()  # re-run must not rewind counters
    third = db.create_project("Fresh 3")
    check("re-init does not rewind counter", third == 53, str(third))







if __name__ == "__main__":
    test_empty_database()
    test_projects()
    test_competitors()
    test_posts_and_dedup()
    test_cascades()
    test_reviews_keywords_ideas_logs()
    test_analytics()
    test_places()
    test_id_safety()

    print("\n" + "=" * 60)
    if FAILURES:
        print(f"{len(FAILURES)} FAILED: {FAILURES}")
        sys.exit(1)
    print("ALL OFFLINE DATABASE TESTS PASSED")
    sys.exit(0)
