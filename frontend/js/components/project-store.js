// Local persistence and seed store for instant project loading
// Enables zero-second initial paint and offline/cold-start resilience.

export const SEED_PROJECTS = [
  {
    "id": 11,
    "name": "ZARA ,NEXUS SEAWOODS",
    "field": "fashion,clothing",
    "location": "nexus seawoods",
    "our_profile": "",
    "is_online": 0,
    "competitor_count": 11,
    "place": {
      "address": "nexus seawoods",
      "category": null,
      "cid": null,
      "confidence": 1,
      "created_at": "2026-10-04 15:30:38",
      "google_place_id": null,
      "hex_id": null,
      "id": 59,
      "identity_label": "addr:zara nexus seawoods|nexus seawoods",
      "identity_source": "name_address",
      "kgmid": null,
      "latitude": null,
      "longitude": null,
      "name": "ZARA ,NEXUS SEAWOODS",
      "place_key": "addr:zara nexus seawoods|nexus seawoods",
      "place_url": "https://www.google.com/maps/search/?api=1&query=ZARA%20%2CNEXUS%20SEAWOODS%20nexus%20seawoods",
      "rating": null,
      "review_count": null,
      "updated_at": "2026-10-04 15:30:37"
    },
    "gmap_url": null
  },
  {
    "id": 7,
    "name": "Brew and Bold Cafe Bandra",
    "field": "cafe ,food ,cofee ,mocha ,macha",
    "location": "bandra",
    "our_profile": "cafe ,stylish ,cozy",
    "is_online": 0,
    "competitor_count": 17,
    "place": {
      "address": "bandra",
      "category": null,
      "cid": null,
      "confidence": 1,
      "created_at": "2026-10-04 15:29:25",
      "google_place_id": null,
      "hex_id": null,
      "id": 58,
      "identity_label": "addr:brew and bold cafe bandra|bandra",
      "identity_source": "name_address",
      "kgmid": null,
      "latitude": null,
      "longitude": null,
      "name": "Brew and Bold Cafe Bandra",
      "place_key": "addr:brew and bold cafe bandra|bandra",
      "place_url": "https://www.google.com/maps/search/?api=1&query=Brew%20and%20Bold%20Cafe%20Bandra%20bandra",
      "rating": null,
      "review_count": null,
      "updated_at": "2026-10-04 15:29:25"
    },
    "gmap_url": null
  }
];

export const SEED_DATA = {
  "11": {
    "project": {
      "competitor_count": 11,
      "created_at": "2026-10-01 17:38:17",
      "field": "fashion,clothing",
      "gmap_url": null,
      "id": 11,
      "is_online": 0,
      "location": "nexus seawoods",
      "name": "ZARA ,NEXUS SEAWOODS",
      "our_profile": "",
      "own_place_id": 59,
      "place": {
        "address": "nexus seawoods",
        "category": null,
        "cid": null,
        "confidence": 1,
        "created_at": "2026-10-04 15:30:38",
        "google_place_id": null,
        "hex_id": null,
        "id": 59,
        "identity_label": "addr:zara nexus seawoods|nexus seawoods",
        "identity_source": "name_address",
        "kgmid": null,
        "latitude": null,
        "longitude": null,
        "name": "ZARA ,NEXUS SEAWOODS",
        "place_key": "addr:zara nexus seawoods|nexus seawoods",
        "place_url": "https://www.google.com/maps/search/?api=1&query=ZARA%20%2CNEXUS%20SEAWOODS%20nexus%20seawoods",
        "rating": null,
        "review_count": null,
        "updated_at": "2026-10-04 15:30:37"
      },
      "place_id": 59,
      "place_key": "addr:zara nexus seawoods|nexus seawoods",
      "place_url": "https://www.google.com/maps/search/?api=1&query=ZARA%20%2CNEXUS%20SEAWOODS%20nexus%20seawoods"
    },
    "competitors": [
      {
        "added_at": "2026-10-04 15:03:57",
        "address": "Grand Central Mall, Sector 40, Seawoods, Navi Mumbai, Maharashtra 400706, India",
        "business_key": "trends",
        "category": null,
        "gmap_url": "https://maps.app.goo.gl/TqVEmxxQJYKnVSLc8",
        "id": 46,
        "identity_source": "hex_id",
        "last_scrape_status": "2026-10-04 15:04:24.679199",
        "last_scraped": "2026-10-04 15:06:39",
        "name": "TRENDS",
        "place": {
          "address": null,
          "category": null,
          "cid": "6463393496138288600",
          "competitor_count": 1,
          "confidence": 3,
          "created_at": "2026-10-04 15:03:56",
          "google_place_id": "ChIJv6IYKRTD5zsR2I3k5COWslk",
          "hex_id": "0x3be7c3142918a2bf:0x59b29623e4e48dd8",
          "id": 55,
          "identity_label": "ChIJv6IYKRTD5zsR2I3k5COWslk",
          "identity_source": "hex_id",
          "kgmid": null,
          "latitude": null,
          "longitude": null,
          "name": "TRENDS",
          "place_key": "place:0x3be7c3142918a2bf:0x59b29623e4e48dd8",
          "place_url": "https://www.google.com/maps/place/?q=place_id:ChIJv6IYKRTD5zsR2I3k5COWslk",
          "project_count": 1,
          "rating": null,
          "review_count": null,
          "updated_at": "2026-10-04 15:03:56"
        },
        "place_id": 55,
        "place_key": "place:0x3be7c3142918a2bf:0x59b29623e4e48dd8",
        "post_count": 8,
        "posts_collected": 8,
        "project_id": 11,
        "rating": 4.1,
        "rating_distribution": "{\"5\": 1412, \"4\": 1164, \"3\": 514, \"2\": 122, \"1\": 152}",
        "review_count": 3364,
        "shared_with_projects": 0,
        "status": "active"
      },
      {
        "added_at": "2026-10-01 17:40:43",
        "address": "First Floor, Nexus Seawoods, No. 11, Seawoods Station Rd, near Railway Station, Nerul East, Sector 40, Nerul, Mumbai, Navi Mumbai, Maharashtra 400706, India",
        "business_key": "pantaloons",
        "category": "Clothing store",
        "gmap_url": "https://www.google.com/maps/place/Pantaloons/data=!4m7!3m6!1s0x3be7c3bd9be46b9d:0xfb1de664b3b92329!8m2!3d19.0224547!4d73.017665!16s%2Fg%2F11g6xq928d!19sChIJnWvkm73D5zsRKSO5s2TmHfs?authuser=0&hl=en&g_ep=EgoyMDI2MDkyOC4wIJJjKgBIAVAD&rclk=1",
        "id": 38,
        "identity_source": "hex_id",
        "last_scrape_status": "2026-10-04 15:04:24.679199",
        "last_scraped": "2026-10-04 13:01:11",
        "name": "Pantaloons",
        "place": {
          "address": "First Floor, Nexus Seawoods, No. 11, Seawoods Station Rd, near Railway Station",
          "category": "Clothing store",
          "cid": "18094872198030893865",
          "competitor_count": 1,
          "confidence": 3,
          "created_at": "2026-10-01 17:40:43",
          "google_place_id": "ChIJnWvkm73D5zsRKSO5s2TmHfs",
          "hex_id": "0x3be7c3bd9be46b9d:0xfb1de664b3b92329",
          "id": 47,
          "identity_label": "ChIJnWvkm73D5zsRKSO5s2TmHfs",
          "identity_source": "hex_id",
          "kgmid": "/g/11g6xq928d",
          "latitude": 19.0224547,
          "longitude": 73.017665,
          "name": "Pantaloons",
          "place_key": "place:0x3be7c3bd9be46b9d:0xfb1de664b3b92329",
          "place_url": "https://www.google.com/maps/place/?q=place_id:ChIJnWvkm73D5zsRKSO5s2TmHfs",
          "project_count": 1,
          "rating": null,
          "review_count": null,
          "updated_at": "2026-10-01 17:40:42"
        },
        "place_id": 47,
        "place_key": "place:0x3be7c3bd9be46b9d:0xfb1de664b3b92329",
        "post_count": 13,
        "posts_collected": 13,
        "project_id": 11,
        "rating": 4.1,
        "rating_distribution": "{\"5\": 1355, \"4\": 1105, \"3\": 422, \"2\": 93, \"1\": 127}",
        "review_count": 3102,
        "shared_with_projects": 0,
        "status": "active"
      },
      {
        "added_at": "2026-10-01 17:40:39",
        "address": "Unit 68, 1, Seawoods Station Rd, Nerul East, Sector 40, Nerul, Navi Mumbai, Maharashtra 400706, India",
        "business_key": "and nexus seawoods mall",
        "category": "Western apparel store",
        "gmap_url": "https://www.google.com/maps/place/AND+-+Nexus+Seawoods+Mall/data=!4m7!3m6!1s0x3be7c3bd87e26ef7:0xf000aa052dafb82b!8m2!3d19.0213252!4d73.0187137!16s%2Fg%2F11dxkbd1sx!19sChIJ927ih73D5zsRK7ivLQWqAPA?authuser=0&hl=en&g_ep=EgoyMDI2MDkyOC4wIJJjKgBIAVAD&rclk=1",
        "id": 36,
        "identity_source": "hex_id",
        "last_scrape_status": "2026-10-04 15:04:24.679199",
        "last_scraped": "2026-10-04 14:25:41",
        "name": "AND - Nexus Seawoods Mall",
        "place": {
          "address": "Unit 68, 1, Seawoods Station Rd",
          "category": "Western apparel store",
          "cid": "17294009508320753707",
          "competitor_count": 1,
          "confidence": 3,
          "created_at": "2026-10-01 17:40:39",
          "google_place_id": "ChIJ927ih73D5zsRK7ivLQWqAPA",
          "hex_id": "0x3be7c3bd87e26ef7:0xf000aa052dafb82b",
          "id": 45,
          "identity_label": "ChIJ927ih73D5zsRK7ivLQWqAPA",
          "identity_source": "hex_id",
          "kgmid": "/g/11dxkbd1sx",
          "latitude": 19.0213252,
          "longitude": 73.0187137,
          "name": "AND - Nexus Seawoods Mall",
          "place_key": "place:0x3be7c3bd87e26ef7:0xf000aa052dafb82b",
          "place_url": "https://www.google.com/maps/place/?q=place_id:ChIJ927ih73D5zsRK7ivLQWqAPA",
          "project_count": 1,
          "rating": null,
          "review_count": null,
          "updated_at": "2026-10-01 17:40:38"
        },
        "place_id": 45,
        "place_key": "place:0x3be7c3bd87e26ef7:0xf000aa052dafb82b",
        "post_count": 3,
        "posts_collected": 3,
        "project_id": 11,
        "rating": 4.5,
        "rating_distribution": "{\"5\": 86, \"4\": 29, \"3\": 9, \"2\": 1, \"1\": 5}",
        "review_count": 130,
        "shared_with_projects": 0,
        "status": "active"
      },
      {
        "added_at": "2026-10-01 17:40:40",
        "address": "Unit SF 60 & 61, Second Floor, Seawoods Grand Central, Seawoods Station Rd, Nerul East, Sector 40, Nerul, Navi Mumbai, Maharashtra 400706, India",
        "business_key": "w nexus seawoods mumbai",
        "category": "Clothing store",
        "gmap_url": "https://www.google.com/maps/place/W+Nexus+Seawoods,+Mumbai/data=!4m7!3m6!1s0x3be7c32beda0a495:0xf25247ee3f0d040c!8m2!3d19.0219517!4d73.0187191!16s%2Fg%2F11khrk2_7p!19sChIJlaSg7SvD5zsRDAQNP-5HUvI?authuser=0&hl=en&g_ep=EgoyMDI2MDkyOC4wIJJjKgBIAVAD&rclk=1",
        "id": 37,
        "identity_source": "hex_id",
        "last_scrape_status": "2026-10-04 15:04:24.679199",
        "last_scraped": "2026-10-04 14:21:50",
        "name": "W Nexus Seawoods, Mumbai",
        "place": {
          "address": "Unit SF 60 & 61, Second Floor, Seawoods Grand Central, Seawoods Station Rd",
          "category": "Clothing store",
          "cid": "17461097793854440460",
          "competitor_count": 1,
          "confidence": 3,
          "created_at": "2026-10-01 17:40:40",
          "google_place_id": "ChIJlaSg7SvD5zsRDAQNP-5HUvI",
          "hex_id": "0x3be7c32beda0a495:0xf25247ee3f0d040c",
          "id": 46,
          "identity_label": "ChIJlaSg7SvD5zsRDAQNP-5HUvI",
          "identity_source": "hex_id",
          "kgmid": "/g/11khrk2_7p",
          "latitude": 19.0219517,
          "longitude": 73.0187191,
          "name": "W Nexus Seawoods, Mumbai",
          "place_key": "place:0x3be7c32beda0a495:0xf25247ee3f0d040c",
          "place_url": "https://www.google.com/maps/place/?q=place_id:ChIJlaSg7SvD5zsRDAQNP-5HUvI",
          "project_count": 1,
          "rating": null,
          "review_count": null,
          "updated_at": "2026-10-01 17:40:39"
        },
        "place_id": 46,
        "place_key": "place:0x3be7c32beda0a495:0xf25247ee3f0d040c",
        "post_count": 0,
        "posts_collected": 0,
        "project_id": 11,
        "rating": 3.7,
        "rating_distribution": "{\"5\": 2, \"4\": 0, \"3\": 0, \"2\": 0, \"1\": 1}",
        "review_count": 130,
        "shared_with_projects": 0,
        "status": "active"
      },
      {
        "added_at": "2026-10-01 17:40:49",
        "address": "2nd Flr, Seawoods, Grand Central Mall, Nerul East, Sector 28, Nerul, Navi Mumbai, Maharashtra 400706, India",
        "business_key": "max fashion nexus seawoods",
        "category": "Casual Wear & Footwear",
        "gmap_url": "https://www.google.com/maps/search/?api=1&query=Max+Fashion+Nexus+Seawoods",
        "id": 40,
        "identity_source": "name_address",
        "last_scrape_status": "2026-10-04 15:04:24.679199",
        "last_scraped": "2026-10-02 13:41:53",
        "name": "Max Fashion - Nexus Seawoods",
        "place": {
          "address": "Nexus Mall, Sector 15, Kharghar, Navi Mumbai, Maharashtra 400703",
          "category": "Casual Wear & Footwear",
          "cid": null,
          "competitor_count": 1,
          "confidence": 1,
          "created_at": "2026-10-01 17:40:48",
          "google_place_id": null,
          "hex_id": null,
          "id": 49,
          "identity_label": "addr:max fashion nexus seawoods|nexus mall sector 15 kharghar navi mumbai maharashtra",
          "identity_source": "name_address",
          "kgmid": null,
          "latitude": null,
          "longitude": null,
          "name": "Max Fashion - Nexus Seawoods",
          "place_key": "addr:max fashion nexus seawoods|nexus mall sector 15 kharghar navi mumbai maharashtra",
          "place_url": "https://www.google.com/maps/search/?api=1&query=Max%20Fashion%20-%20Nexus%20Seawoods%20Nexus%20Mall%2C%20Sector%2015%2C%20Kharghar%2C%20Navi%20Mumbai%2C%20Maharashtra%20400703",
          "project_count": 1,
          "rating": null,
          "review_count": null,
          "updated_at": "2026-10-01 17:40:48"
        },
        "place_id": 49,
        "place_key": "addr:max fashion nexus seawoods|nexus mall sector 15 kharghar navi mumbai maharashtra",
        "post_count": 2,
        "posts_collected": 2,
        "project_id": 11,
        "rating": 4.1,
        "rating_distribution": null,
        "review_count": null,
        "shared_with_projects": 0,
        "status": "active"
      },
      {
        "added_at": "2026-10-01 17:40:46",
        "address": "Shop 34, above Mahavir Vihar, Nerul East, Sector 40, Nerul, Navi Mumbai, Maharashtra 400706, India",
        "business_key": "westside nexus seawoods",
        "category": "Western Wear & Fashion",
        "gmap_url": "https://www.google.com/maps/search/?api=1&query=Westside+Nexus+Seawoods",
        "id": 39,
        "identity_source": "name_address",
        "last_scrape_status": "2026-10-04 15:04:24.679199",
        "last_scraped": "2026-10-04 13:02:52",
        "name": "Westside - Nexus Seawoods",
        "place": {
          "address": "Nexus Mall, Plot No. 1, Sector 15, Navi Mumbai, Maharashtra 400703",
          "category": "Western Wear & Fashion",
          "cid": null,
          "competitor_count": 1,
          "confidence": 1,
          "created_at": "2026-10-01 17:40:46",
          "google_place_id": null,
          "hex_id": null,
          "id": 48,
          "identity_label": "addr:westside nexus seawoods|nexus mall plot no 1 sector 15 navi mumbai maharashtra",
          "identity_source": "name_address",
          "kgmid": null,
          "latitude": null,
          "longitude": null,
          "name": "Westside - Nexus Seawoods",
          "place_key": "addr:westside nexus seawoods|nexus mall plot no 1 sector 15 navi mumbai maharashtra",
          "place_url": "https://www.google.com/maps/search/?api=1&query=Westside%20-%20Nexus%20Seawoods%20Nexus%20Mall%2C%20Plot%20No.%201%2C%20Sector%2015%2C%20Navi%20Mumbai%2C%20Maharashtra%20400703",
          "project_count": 1,
          "rating": null,
          "review_count": null,
          "updated_at": "2026-10-01 17:40:45"
        },
        "place_id": 48,
        "place_key": "addr:westside nexus seawoods|nexus mall plot no 1 sector 15 navi mumbai maharashtra",
        "post_count": 0,
        "posts_collected": 0,
        "project_id": 11,
        "rating": 4.2,
        "rating_distribution": null,
        "review_count": null,
        "shared_with_projects": 0,
        "status": "active"
      },
      {
        "added_at": "2026-10-01 17:40:50",
        "address": "Nexus Mall, Sector 15, Kharghar, Navi Mumbai, Maharashtra 400703",
        "business_key": "levi s nexus seawoods",
        "category": "Denim & Casual Apparel",
        "gmap_url": "https://www.google.com/maps/search/?api=1&query=Levi%27s+Nexus+Seawoods",
        "id": 41,
        "identity_source": "name_address",
        "last_scrape_status": "2026-10-04 15:04:24.679199",
        "last_scraped": "2026-10-04 14:17:23",
        "name": "Levi's - Nexus Seawoods",
        "place": {
          "address": "Nexus Mall, Sector 15, Kharghar, Navi Mumbai, Maharashtra 400703",
          "category": "Denim & Casual Apparel",
          "cid": null,
          "competitor_count": 1,
          "confidence": 1,
          "created_at": "2026-10-01 17:40:50",
          "google_place_id": null,
          "hex_id": null,
          "id": 50,
          "identity_label": "addr:levi s nexus seawoods|nexus mall sector 15 kharghar navi mumbai maharashtra",
          "identity_source": "name_address",
          "kgmid": null,
          "latitude": null,
          "longitude": null,
          "name": "Levi's - Nexus Seawoods",
          "place_key": "addr:levi s nexus seawoods|nexus mall sector 15 kharghar navi mumbai maharashtra",
          "place_url": "https://www.google.com/maps/search/?api=1&query=Levi%27s%20-%20Nexus%20Seawoods%20Nexus%20Mall%2C%20Sector%2015%2C%20Kharghar%2C%20Navi%20Mumbai%2C%20Maharashtra%20400703",
          "project_count": 1,
          "rating": null,
          "review_count": null,
          "updated_at": "2026-10-01 17:40:49"
        },
        "place_id": 50,
        "place_key": "addr:levi s nexus seawoods|nexus mall sector 15 kharghar navi mumbai maharashtra",
        "post_count": 0,
        "posts_collected": 0,
        "project_id": 11,
        "rating": null,
        "rating_distribution": null,
        "review_count": null,
        "shared_with_projects": 0,
        "status": "business_mismatch"
      },
      {
        "added_at": "2026-10-01 17:40:53",
        "address": "Nexus Mall, Sector 15, Kharghar, Navi Mumbai, Maharashtra 400703",
        "business_key": "zudio nexus seawoods",
        "category": "Affordable Fashion",
        "gmap_url": "https://www.google.com/maps/search/?api=1&query=Zudio+Nexus+Seawoods",
        "id": 42,
        "identity_source": "name_address",
        "last_scrape_status": "2026-10-04 15:04:24.679199",
        "last_scraped": "2026-10-04 14:19:56",
        "name": "Zudio - Nexus Seawoods",
        "place": {
          "address": "Nexus Mall, Sector 15, Kharghar, Navi Mumbai, Maharashtra 400703",
          "category": "Affordable Fashion",
          "cid": null,
          "competitor_count": 1,
          "confidence": 1,
          "created_at": "2026-10-01 17:40:53",
          "google_place_id": null,
          "hex_id": null,
          "id": 51,
          "identity_label": "addr:zudio nexus seawoods|nexus mall sector 15 kharghar navi mumbai maharashtra",
          "identity_source": "name_address",
          "kgmid": null,
          "latitude": null,
          "longitude": null,
          "name": "Zudio - Nexus Seawoods",
          "place_key": "addr:zudio nexus seawoods|nexus mall sector 15 kharghar navi mumbai maharashtra",
          "place_url": "https://www.google.com/maps/search/?api=1&query=Zudio%20-%20Nexus%20Seawoods%20Nexus%20Mall%2C%20Sector%2015%2C%20Kharghar%2C%20Navi%20Mumbai%2C%20Maharashtra%20400703",
          "project_count": 1,
          "rating": null,
          "review_count": null,
          "updated_at": "2026-10-01 17:40:52"
        },
        "place_id": 51,
        "place_key": "addr:zudio nexus seawoods|nexus mall sector 15 kharghar navi mumbai maharashtra",
        "post_count": 0,
        "posts_collected": 0,
        "project_id": 11,
        "rating": null,
        "rating_distribution": null,
        "review_count": null,
        "shared_with_projects": 0,
        "status": "business_mismatch"
      },
      {
        "added_at": "2026-10-01 17:40:54",
        "address": "Nexus Mall, Sector 15, Kharghar, Navi Mumbai, Maharashtra 400703",
        "business_key": "shoppers stop nexus seawoods",
        "category": "Department Store & Fashion",
        "gmap_url": "https://www.google.com/maps/search/?api=1&query=Shoppers+Stop+Nexus+Seawoods",
        "id": 43,
        "identity_source": "name_address",
        "last_scrape_status": "2026-10-04 15:04:24.679199",
        "last_scraped": null,
        "name": "Shoppers Stop - Nexus Seawoods",
        "place": {
          "address": "Nexus Mall, Sector 15, Kharghar, Navi Mumbai, Maharashtra 400703",
          "category": "Department Store & Fashion",
          "cid": null,
          "competitor_count": 1,
          "confidence": 1,
          "created_at": "2026-10-01 17:40:54",
          "google_place_id": null,
          "hex_id": null,
          "id": 52,
          "identity_label": "addr:shoppers stop nexus seawoods|nexus mall sector 15 kharghar navi mumbai maharashtra",
          "identity_source": "name_address",
          "kgmid": null,
          "latitude": null,
          "longitude": null,
          "name": "Shoppers Stop - Nexus Seawoods",
          "place_key": "addr:shoppers stop nexus seawoods|nexus mall sector 15 kharghar navi mumbai maharashtra",
          "place_url": "https://www.google.com/maps/search/?api=1&query=Shoppers%20Stop%20-%20Nexus%20Seawoods%20Nexus%20Mall%2C%20Sector%2015%2C%20Kharghar%2C%20Navi%20Mumbai%2C%20Maharashtra%20400703",
          "project_count": 1,
          "rating": null,
          "review_count": null,
          "updated_at": "2026-10-01 17:40:54"
        },
        "place_id": 52,
        "place_key": "addr:shoppers stop nexus seawoods|nexus mall sector 15 kharghar navi mumbai maharashtra",
        "post_count": 0,
        "posts_collected": 0,
        "project_id": 11,
        "rating": null,
        "rating_distribution": null,
        "review_count": null,
        "shared_with_projects": 0,
        "status": "active"
      },
      {
        "added_at": "2026-10-01 17:40:56",
        "address": "One World Center, Sector 15, Kharghar, Navi Mumbai, Maharashtra 400703",
        "business_key": "h m one world center",
        "category": "Fast Fashion",
        "gmap_url": "https://www.google.com/maps/search/?api=1&query=H%26M+One+World+Center",
        "id": 44,
        "identity_source": "name_address",
        "last_scrape_status": "2026-10-04 15:04:24.679199",
        "last_scraped": null,
        "name": "H&M - One World Center",
        "place": {
          "address": "One World Center, Sector 15, Kharghar, Navi Mumbai, Maharashtra 400703",
          "category": "Fast Fashion",
          "cid": null,
          "competitor_count": 1,
          "confidence": 1,
          "created_at": "2026-10-01 17:40:56",
          "google_place_id": null,
          "hex_id": null,
          "id": 53,
          "identity_label": "addr:h m one world center|one world center sector 15 kharghar navi mumbai maharashtra",
          "identity_source": "name_address",
          "kgmid": null,
          "latitude": null,
          "longitude": null,
          "name": "H&M - One World Center",
          "place_key": "addr:h m one world center|one world center sector 15 kharghar navi mumbai maharashtra",
          "place_url": "https://www.google.com/maps/search/?api=1&query=H%26M%20-%20One%20World%20Center%20One%20World%20Center%2C%20Sector%2015%2C%20Kharghar%2C%20Navi%20Mumbai%2C%20Maharashtra%20400703",
          "project_count": 1,
          "rating": null,
          "review_count": null,
          "updated_at": "2026-10-01 17:40:56"
        },
        "place_id": 53,
        "place_key": "addr:h m one world center|one world center sector 15 kharghar navi mumbai maharashtra",
        "post_count": 0,
        "posts_collected": 0,
        "project_id": 11,
        "rating": null,
        "rating_distribution": null,
        "review_count": null,
        "shared_with_projects": 0,
        "status": "active"
      },
      {
        "added_at": "2026-10-02 13:06:58",
        "address": null,
        "business_key": "h m",
        "category": null,
        "gmap_url": "https://www.google.com/maps/place/H%26M/@19.0217777,73.0186023,17z/data=!3m1!4b1!4m6!3m5!1s0x3be7c331e711650d:0xaeaf9b1c2c1f67ae!8m2!3d19.0217777!4d73.0186023!16s%2Fg%2F11f60y0hg7?entry=ttu&g_ep=EgoyMDI2MDkyOS4wIKXMDSoASAFQAw%3D%3D",
        "id": 45,
        "identity_source": "hex_id",
        "last_scrape_status": "2026-10-04 15:04:24.679199",
        "last_scraped": null,
        "name": "H&M",
        "place": {
          "address": null,
          "category": null,
          "cid": "12587450028825470894",
          "competitor_count": 1,
          "confidence": 3,
          "created_at": "2026-10-02 13:06:57",
          "google_place_id": "ChIJDWUR5zHD5zsRrmcfLBybr64",
          "hex_id": "0x3be7c331e711650d:0xaeaf9b1c2c1f67ae",
          "id": 54,
          "identity_label": "ChIJDWUR5zHD5zsRrmcfLBybr64",
          "identity_source": "hex_id",
          "kgmid": "/g/11f60y0hg7",
          "latitude": 19.0217777,
          "longitude": 73.0186023,
          "name": "H&M",
          "place_key": "place:0x3be7c331e711650d:0xaeaf9b1c2c1f67ae",
          "place_url": "https://www.google.com/maps/place/?q=place_id:ChIJDWUR5zHD5zsRrmcfLBybr64",
          "project_count": 1,
          "rating": null,
          "review_count": null,
          "updated_at": "2026-10-02 13:06:57"
        },
        "place_id": 54,
        "place_key": "place:0x3be7c331e711650d:0xaeaf9b1c2c1f67ae",
        "post_count": 0,
        "posts_collected": 0,
        "project_id": 11,
        "rating": null,
        "rating_distribution": null,
        "review_count": null,
        "shared_with_projects": 0,
        "status": "active"
      }
    ],
    "posts": [
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/Pantaloons/data=!4m7!3m6!1s0x3be7c3bd9be46b9d:0xfb1de664b3b92329!8m2!3d19.0224547!4d73.017665!16s%2Fg%2F11g6xq928d!19sChIJnWvkm73D5zsRKSO5s2TmHfs?authuser=0&hl=en&g_ep=EgoyMDI2MDkyOC4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 38,
        "competitor_name": "Pantaloons",
        "content_hash": "bf9042a7271438322dc67d83d44d00c5e0b5df69afa449e86b31e5bf0afe028c",
        "cta": "Call now",
        "detected_keywords": [],
        "detected_topic": "General Update",
        "id": 62,
        "image_urls": [
          "https://lh3.googleusercontent.com/geougc/AF1QipOISWlG8L9BZQBLLYAvAzKf4XYxuc6IhRhq-iGh=h400-no"
        ],
        "is_own_profile": false,
        "is_public": false,
        "post_source": "owner",
        "post_url": null,
        "published_date": "2026-10-01T13:01:00.126835",
        "raw_data": {
          "post_source": "owner"
        },
        "scrape_date": "2026-10-04 13:01:09",
        "text_content": "A few styling tweaks can change the whole vibe. \n \nHere’s some inspiration for your next accessory move."
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/Pantaloons/data=!4m7!3m6!1s0x3be7c3bd9be46b9d:0xfb1de664b3b92329!8m2!3d19.0224547!4d73.017665!16s%2Fg%2F11g6xq928d!19sChIJnWvkm73D5zsRKSO5s2TmHfs?authuser=0&hl=en&g_ep=EgoyMDI2MDkyOC4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 38,
        "competitor_name": "Pantaloons",
        "content_hash": "eaa7610fcf4f48395c55bced408019e3f40ddeb915ebb693f11504bf1fc1124a",
        "cta": "Call now",
        "detected_keywords": [],
        "detected_topic": "General Update",
        "id": 52,
        "image_urls": [
          "https://lh3.googleusercontent.com/geougc/AF1QipOISWlG8L9BZQBLLYAvAzKf4XYxuc6IhRhq-iGh=h400-no"
        ],
        "is_own_profile": false,
        "is_public": false,
        "post_source": "owner",
        "post_url": "https://search.google.com/local/posts?q=Pantaloons&ludocid=18094872198030893865&lpsid=CIHM0ogKEPHcsMyHvtSiFg&source=sh/x/loc/post&lsig=AB86z5XvWVSCDM9Ryr7ZPoSCWFQP",
        "published_date": "2026-10-01T04:45:24.438801",
        "raw_data": {
          "post_source": "owner"
        },
        "scrape_date": "2026-10-04 04:46:25",
        "text_content": "A few styling tweaks can change the whole vibe. \n \nHere’s some inspiration for your next accessory move."
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/Pantaloons/data=!4m7!3m6!1s0x3be7c3bd9be46b9d:0xfb1de664b3b92329!8m2!3d19.0224547!4d73.017665!16s%2Fg%2F11g6xq928d!19sChIJnWvkm73D5zsRKSO5s2TmHfs?authuser=0&hl=en&g_ep=EgoyMDI2MDkyOC4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 38,
        "competitor_name": "Pantaloons",
        "content_hash": "f218967f5aae6f354e75570cd445f1ee38fa58846d65c8d9d32dbcf9068716a0",
        "cta": "Call now",
        "detected_keywords": [
          "new"
        ],
        "detected_topic": "Updates & Announcements",
        "id": 53,
        "image_urls": [
          "https://lh3.googleusercontent.com/geougc/AF1QipN-zkJzKQCHcpvfYm05c4SHmJK7BsnsVR0PSZ-K=h400-no"
        ],
        "is_own_profile": false,
        "is_public": false,
        "post_source": "owner",
        "post_url": "https://search.google.com/local/posts?q=Pantaloons&ludocid=18094872198030893865&lpsid=CIHM0ogKEPi1nNHWhe_8ugE&source=sh/x/loc/post&lsig=AB86z5XvWVSCDM9Ryr7ZPoSCWFQP",
        "published_date": "2026-09-15T00:00:00",
        "raw_data": {
          "post_source": "owner"
        },
        "scrape_date": "2026-10-04 04:46:26",
        "text_content": "Modern details are giving desi styles a whole new spin.\n\nIntroducing The Runway Edit Vol. 02: Serving Desi."
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/Pantaloons/data=!4m7!3m6!1s0x3be7c3bd9be46b9d:0xfb1de664b3b92329!8m2!3d19.0224547!4d73.017665!16s%2Fg%2F11g6xq928d!19sChIJnWvkm73D5zsRKSO5s2TmHfs?authuser=0&hl=en&g_ep=EgoyMDI2MDkyOC4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 38,
        "competitor_name": "Pantaloons",
        "content_hash": "85215de754fd6a7a154b936ed811dbfcdf91d8ecff5d0eaa5932688436b7afff",
        "cta": "Call now",
        "detected_keywords": [
          "collection"
        ],
        "detected_topic": "New Collection",
        "id": 54,
        "image_urls": [],
        "is_own_profile": false,
        "is_public": false,
        "post_source": "owner",
        "post_url": "https://search.google.com/local/posts?q=Pantaloons&ludocid=18094872198030893865&lpsid=CIHM0ogKEID9g_WQrezIkAE&source=sh/x/loc/post&lsig=AB86z5XvWVSCDM9Ryr7ZPoSCWFQP",
        "published_date": "2026-08-24T00:00:00",
        "raw_data": {
          "post_source": "owner"
        },
        "scrape_date": "2026-10-04 04:46:26",
        "text_content": "The Runway Edit Vol 01: Literature Core is here. Plaids, pleats, ruffles and tailored details bring a literary-inspired wardrobe to life. Limited collection. Available at select stores."
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/Pantaloons/data=!4m7!3m6!1s0x3be7c3bd9be46b9d:0xfb1de664b3b92329!8m2!3d19.0224547!4d73.017665!16s%2Fg%2F11g6xq928d!19sChIJnWvkm73D5zsRKSO5s2TmHfs?authuser=0&hl=en&g_ep=EgoyMDI2MDkyOC4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 38,
        "competitor_name": "Pantaloons",
        "content_hash": "cc6c28ca09e8dfcad3f1c5dd0703e36c70fd9ffdc3ae30f7a74d80501404d7d7",
        "cta": "Call now",
        "detected_keywords": [
          "store",
          "visit"
        ],
        "detected_topic": "Store & Visit",
        "id": 55,
        "image_urls": [
          "https://lh3.googleusercontent.com/geougc/AF1QipNnO02dyaC-6lXEJPZa0cwbyAVX2-LOLeExHQUm=h400-no"
        ],
        "is_own_profile": false,
        "is_public": false,
        "post_source": "owner",
        "post_url": "https://search.google.com/local/posts?q=Pantaloons&ludocid=18094872198030893865&lpsid=CIHM0ogKEO6Yxd3-5OqXmgE&source=sh/x/loc/post&lsig=AB86z5XvWVSCDM9Ryr7ZPoSCWFQP",
        "published_date": "2026-08-15T00:00:00",
        "raw_data": {
          "post_source": "owner"
        },
        "scrape_date": "2026-10-04 04:46:26",
        "text_content": "For those who rewrite the rules of self-expression.\nMake the season your own with the Pantaloons AW’26 collection - contemporary styles, versatile looks and new ways to wear what feels like you.\nFind your unique look for every mood and occasion. Visit your nearest Pantaloons store in Sector 40, Mumbai today!"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/Pantaloons/data=!4m7!3m6!1s0x3be7c3bd9be46b9d:0xfb1de664b3b92329!8m2!3d19.0224547!4d73.017665!16s%2Fg%2F11g6xq928d!19sChIJnWvkm73D5zsRKSO5s2TmHfs?authuser=0&hl=en&g_ep=EgoyMDI2MDkyOC4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 38,
        "competitor_name": "Pantaloons",
        "content_hash": "df8952caffca6531f33dc8b6d49657746e42f33c5ad0c8f23e5a6c4760852fcd",
        "cta": "Call now",
        "detected_keywords": [
          "store",
          "visit"
        ],
        "detected_topic": "Store & Visit",
        "id": 56,
        "image_urls": [],
        "is_own_profile": false,
        "is_public": false,
        "post_source": "owner",
        "post_url": "https://search.google.com/local/posts?q=Pantaloons&ludocid=18094872198030893865&lpsid=CIHM0ogKEJzQ07HTt7Wv9QE&source=sh/x/loc/post&lsig=AB86z5XvWVSCDM9Ryr7ZPoSCWFQP",
        "published_date": "2026-08-14T00:00:00",
        "raw_data": {
          "post_source": "owner"
        },
        "scrape_date": "2026-10-04 04:46:26",
        "text_content": "New season. New layers. New ways to wear your style.\nThe Pantaloons AW’26 story starts here, with versatile new-season styles designed for everyday dressing and every occasion.\nVisit your nearest Pantaloons store in Sector 40, Mumbai and find your new-season favorites"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/search/?api=1&query=Max+Fashion+Nexus+Seawoods",
        "competitor_id": 40,
        "competitor_name": "Max Fashion - Nexus Seawoods",
        "content_hash": "237d06bc8d429b46007ba258accd5c774f04bcb4119a843f5968fd439583f576",
        "cta": "Book",
        "detected_keywords": [],
        "detected_topic": "General Update",
        "id": 50,
        "image_urls": [],
        "is_own_profile": false,
        "is_public": false,
        "post_source": "owner",
        "post_url": "https://search.google.com/local/posts?q=Max+-+Nexus+Seawoods+Mall&ludocid=10562442747350085404&lpsid=CIHM0ogKELSo95mu3c6AfQ&source=sh/x/loc/post&lsig=AB86z5XaZp2nzILxChFjr_b61ldL",
        "published_date": "2026-08-14T00:00:00",
        "raw_data": {
          "post_source": "owner"
        },
        "scrape_date": "2026-10-02 13:41:52",
        "text_content": "“Max URB_N UN-MUTE is back with, 5 cities. 5 live shows. 5 winners.\n\n  More bars. More beats. More stories. \n\n  The culture is getting louder.\n  And this time, you’re part of the movement.”\n\n  #MaxURB_NUnmute #IndiaGetsLoud #MaxFashion"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/search/?api=1&query=Max+Fashion+Nexus+Seawoods",
        "competitor_id": 40,
        "competitor_name": "Max Fashion - Nexus Seawoods",
        "content_hash": "6e72a12fd7e8502f8633bbe0205140ad96068b279f904f15db3244803374aef3",
        "cta": "Book",
        "detected_keywords": [],
        "detected_topic": "General Update",
        "id": 51,
        "image_urls": [],
        "is_own_profile": false,
        "is_public": false,
        "post_source": "owner",
        "post_url": "https://search.google.com/local/posts?q=Max+-+Nexus+Seawoods+Mall&ludocid=10562442747350085404&lpsid=CIHM0ogKEKbroffnqMSUHQ&source=sh/x/loc/post&lsig=AB86z5XaZp2nzILxChFjr_b61ldL",
        "published_date": "2026-07-31T00:00:00",
        "raw_data": {
          "post_source": "owner"
        },
        "scrape_date": "2026-10-02 13:41:53",
        "text_content": "“Max URB_N UN-MUTE is back with, 5 cities. 5 live shows. 5 winners.\n\n  More bars. More beats. More stories. \n\n  The culture is getting louder.\n  And this time, you’re part of the movement.”\n\n  #MaxURB_NUnmute #IndiaGetsLoud #MaxFashion"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/Pantaloons/data=!4m7!3m6!1s0x3be7c3bd9be46b9d:0xfb1de664b3b92329!8m2!3d19.0224547!4d73.017665!16s%2Fg%2F11g6xq928d!19sChIJnWvkm73D5zsRKSO5s2TmHfs?authuser=0&hl=en&g_ep=EgoyMDI2MDkyOC4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 38,
        "competitor_name": "Pantaloons",
        "content_hash": "edf4a1c548bc5d11a5a48b1cccdd1797dc113df1a17b5e32ce29bedd7ee9ec81",
        "cta": "Call now",
        "detected_keywords": [
          "new arrivals",
          "latest"
        ],
        "detected_topic": "New Collection",
        "id": 57,
        "image_urls": [
          "https://lh3.googleusercontent.com/geougc/AF1QipMEY_QKQNiX_PtdH_-spPmZe-cYmxYuCpKFD0O0=h400-no"
        ],
        "is_own_profile": false,
        "is_public": false,
        "post_source": "owner",
        "post_url": "https://search.google.com/local/posts?q=Pantaloons&ludocid=18094872198030893865&lpsid=CIHM0ogKEJGrlYXousPrYg&source=sh/x/loc/post&lsig=AB86z5XvWVSCDM9Ryr7ZPoSCWFQP",
        "published_date": "2026-07-30T00:00:00",
        "raw_data": {
          "post_source": "owner"
        },
        "scrape_date": "2026-10-04 04:46:27",
        "text_content": "Step into the season with the new arrivals at Pantaloons and discover styles inspired by the latest trends. Explore stylish men's clothing and elegant women's clothing, including shirts, dresses, tops, jeans, kurtas, and seasonal essentials for every occasion. Whether you're updating your everyday wardrobe or dressing for a special occasion, you'll find styles that are comfortable, versatile, and easy to wear. It's the perfect time to update your wardrobe. Visit your nearest Pantaloons store and see what's new."
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/Pantaloons/data=!4m7!3m6!1s0x3be7c3bd9be46b9d:0xfb1de664b3b92329!8m2!3d19.0224547!4d73.017665!16s%2Fg%2F11g6xq928d!19sChIJnWvkm73D5zsRKSO5s2TmHfs?authuser=0&hl=en&g_ep=EgoyMDI2MDkyOC4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 38,
        "competitor_name": "Pantaloons",
        "content_hash": "cbef3eab879bf83c63d159604e44e6c321e3b509ef62a6f5a2851a2741da3a13",
        "cta": "Call now",
        "detected_keywords": [
          "offer",
          "offers",
          "sale",
          "end of season"
        ],
        "detected_topic": "Offers & Discounts",
        "id": 58,
        "image_urls": [
          "https://lh3.googleusercontent.com/geougc/AF1QipPlN5uYWmKxU6t9GhqbKZkwcsXvVQcJ_DMEjeUY=h400-no"
        ],
        "is_own_profile": false,
        "is_public": false,
        "post_source": "owner",
        "post_url": "https://search.google.com/local/posts?q=Pantaloons&ludocid=18094872198030893865&lpsid=CIHM0ogKELze3LO_xu7SjwE&source=sh/x/loc/post&lsig=AB86z5XvWVSCDM9Ryr7ZPoSCWFQP",
        "published_date": "2026-07-24T00:00:00",
        "raw_data": {
          "post_source": "owner"
        },
        "scrape_date": "2026-10-04 04:46:27",
        "text_content": "Offer Ending Soon!\n\nThe Pantaloons End of Season Sale is in its final days! Grab Buy 2 Get 2 FREE on a wide range of styles for men, women, and kids. From everyday essentials to trend-setting outfits, discover incredible fashion at unbeatable value. Shop your favourites, refresh your wardrobe, and make every purchase count before these exciting offers come to an end. Visit Pantaloons store at Sector 40 or shop online before it's too late!\n\nT&C apply*"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/Pantaloons/data=!4m7!3m6!1s0x3be7c3bd9be46b9d:0xfb1de664b3b92329!8m2!3d19.0224547!4d73.017665!16s%2Fg%2F11g6xq928d!19sChIJnWvkm73D5zsRKSO5s2TmHfs?authuser=0&hl=en&g_ep=EgoyMDI2MDkyOC4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 38,
        "competitor_name": "Pantaloons",
        "content_hash": "683039c1897cdb8eac7c3cd43653bc84d410bb1184bef166054183915c6c015a",
        "cta": "Call now",
        "detected_keywords": [
          "offer",
          "sale",
          "deals",
          "end of season"
        ],
        "detected_topic": "Offers & Discounts",
        "id": 59,
        "image_urls": [
          "https://lh3.googleusercontent.com/geougc/AF1QipPQ08Gi5SkaDP8R75gi7gDtclVGTGQ7o5lMOUx9=h400-no"
        ],
        "is_own_profile": false,
        "is_public": false,
        "post_source": "owner",
        "post_url": "https://search.google.com/local/posts?q=Pantaloons&ludocid=18094872198030893865&lpsid=CIHM0ogKELvouNjc_cWLggE&source=sh/x/loc/post&lsig=AB86z5XvWVSCDM9Ryr7ZPoSCWFQP",
        "published_date": "2026-07-23T00:00:00",
        "raw_data": {
          "post_source": "owner"
        },
        "scrape_date": "2026-10-04 04:46:27",
        "text_content": "End of Season Sale is here! 🛍️\n\nRefresh your wardrobe with the Pantaloons End of Season Sale! Enjoy Buy 2 Get 2 FREE* on a wide range of trendy women's fashion, including dresses, tops, ethnic wear, western wear, footwear, handbags, and accessories. Visit Pantaloons in Sector 40, before the offer ends. Don't miss these exciting fashion deals. \n\n*T&C Apply."
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/Pantaloons/data=!4m7!3m6!1s0x3be7c3bd9be46b9d:0xfb1de664b3b92329!8m2!3d19.0224547!4d73.017665!16s%2Fg%2F11g6xq928d!19sChIJnWvkm73D5zsRKSO5s2TmHfs?authuser=0&hl=en&g_ep=EgoyMDI2MDkyOC4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 38,
        "competitor_name": "Pantaloons",
        "content_hash": "40004234f03bbe97b7c3942bb698aa2bece383122b6183cbd64b7cfc340dae13",
        "cta": "Call now",
        "detected_keywords": [
          "offer",
          "offers",
          "sale",
          "save",
          "deal",
          "end of season"
        ],
        "detected_topic": "Offers & Discounts",
        "id": 60,
        "image_urls": [
          "https://lh3.googleusercontent.com/geougc/AF1QipMT4LrTqxQvye6reTltakcTrXtrl1jdW2-dDSm5=h400-no"
        ],
        "is_own_profile": false,
        "is_public": false,
        "post_source": "owner",
        "post_url": "https://search.google.com/local/posts?q=Pantaloons&ludocid=18094872198030893865&lpsid=CIHM0ogKEMCHqZvmocqOvAE&source=sh/x/loc/post&lsig=AB86z5XvWVSCDM9Ryr7ZPoSCWFQP",
        "published_date": "2026-07-17T00:00:00",
        "raw_data": {
          "post_source": "owner"
        },
        "scrape_date": "2026-10-04 04:46:27",
        "text_content": "Pantaloons' End of Season Sale just got bigger! Style more. Save more with the Buy 2 Get 2 FREE offer. \n\nMake the most of the season's biggest shopping event with Buy 2 Get 2 FREE on a wide range of styles across Pantaloons brands. Explore the latest collections in menswear, womenswear, kids' wear, footwear, handbags, accessories, and more, and enjoy incredible value while refreshing your wardrobe. \n\nFrom everyday essentials to trend-forward fashion, find everything you need for every occasion at unbeatable offers. Hurry, this exclusive deal is valid only from 17th to 19th July. Shop the End of Season Sale at Pantaloons in Sector 40, Mumbai or online before the offer ends. \n\n*T&C Apply."
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/Pantaloons/data=!4m7!3m6!1s0x3be7c3bd9be46b9d:0xfb1de664b3b92329!8m2!3d19.0224547!4d73.017665!16s%2Fg%2F11g6xq928d!19sChIJnWvkm73D5zsRKSO5s2TmHfs?authuser=0&hl=en&g_ep=EgoyMDI2MDkyOC4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 38,
        "competitor_name": "Pantaloons",
        "content_hash": "d171f3138659f65829c9e22d87fbc00f97dd5d5baf9435645d8f70c42e28a4ea",
        "cta": "Buy",
        "detected_keywords": [
          "offers",
          "sale"
        ],
        "detected_topic": "Offers & Discounts",
        "id": 61,
        "image_urls": [
          "https://lh3.googleusercontent.com/geougc/AF1QipPcrUATTpjf_e-E0HmRGQSGKLB6AnxrbAlkw88e=h400-no"
        ],
        "is_own_profile": false,
        "is_public": false,
        "post_source": "owner",
        "post_url": "https://search.google.com/local/posts?q=Pantaloons&ludocid=18094872198030893865&lpsid=CIHM0ogKEIbu8rOXofetpAE&source=sh/x/loc/post&lsig=AB86z5XvWVSCDM9Ryr7ZPoSCWFQP",
        "published_date": "2026-07-10T00:00:00",
        "raw_data": {
          "post_source": "owner"
        },
        "scrape_date": "2026-10-04 04:46:28",
        "text_content": "Fashion, elevated. Savings, unmissable. Only at Pantaloons. \n\nShop the season's sale with up to 50% off on menswear, womenswear, kidswear and more, from refined western silhouettes and graceful ethnic wear to everyday essentials, footwear and accessories. \n\nRefresh your wardrobe for the season ahead or build on your everyday staples while the offers last. The time to shop well is now. Walk into your nearest Pantaloons store and make these pieces yours. \n\n*T&C Apply."
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/AND+-+Nexus+Seawoods+Mall/data=!4m7!3m6!1s0x3be7c3bd87e26ef7:0xf000aa052dafb82b!8m2!3d19.0213252!4d73.0187137!16s%2Fg%2F11dxkbd1sx!19sChIJ927ih73D5zsRK7ivLQWqAPA?authuser=0&hl=en&g_ep=EgoyMDI2MDkyOC4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 36,
        "competitor_name": "AND - Nexus Seawoods Mall",
        "content_hash": "c031eef1a8acf8cdfc353d2affd89bc94913bc5c23a1013ce7857194cb2eb41c",
        "cta": null,
        "detected_keywords": [
          "store",
          "visit",
          "shopping experience"
        ],
        "detected_topic": "Store & Visit",
        "id": 67,
        "image_urls": [],
        "is_own_profile": false,
        "is_public": false,
        "post_source": "owner",
        "post_url": null,
        "published_date": "2026-07-06T14:24:31.208277",
        "raw_data": {
          "post_source": "owner"
        },
        "scrape_date": "2026-10-04 14:25:40",
        "text_content": "Response from the owner 3 months agoDear Arpita, we are glad you had a lovely shopping experience at our store. Nargis will surely be delighted to hear your feedback. Thank you, we look forward to your next visit."
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/AND+-+Nexus+Seawoods+Mall/data=!4m7!3m6!1s0x3be7c3bd87e26ef7:0xf000aa052dafb82b!8m2!3d19.0213252!4d73.0187137!16s%2Fg%2F11dxkbd1sx!19sChIJ927ih73D5zsRK7ivLQWqAPA?authuser=0&hl=en&g_ep=EgoyMDI2MDkyOC4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 36,
        "competitor_name": "AND - Nexus Seawoods Mall",
        "content_hash": "c8327faa73c1637d492ab2af647f531e23e1b6c3a4dab232a0c46ced1a110b56",
        "cta": null,
        "detected_keywords": [
          "store",
          "stores",
          "visit",
          "shopping experience"
        ],
        "detected_topic": "Store & Visit",
        "id": 66,
        "image_urls": [],
        "is_own_profile": false,
        "is_public": false,
        "post_source": "owner",
        "post_url": null,
        "published_date": "2026-07-06T14:24:21.109252",
        "raw_data": {
          "post_source": "owner"
        },
        "scrape_date": "2026-10-04 14:25:40",
        "text_content": "3 months ago I had a great experience with Nargis going out of the way to arrange tops from other stores and helping with offers. And all with a smile. Rare to meet such a customer care executive.\nFrom ArpitaLike Share Response from the owner 3 months agoDear Arpita, we are glad you had a lovely shopping experience at our store. Nargis will surely be delighted to hear your feedback. Thank you, we look forward to your next visit."
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/AND+-+Nexus+Seawoods+Mall/data=!4m7!3m6!1s0x3be7c3bd87e26ef7:0xf000aa052dafb82b!8m2!3d19.0213252!4d73.0187137!16s%2Fg%2F11dxkbd1sx!19sChIJ927ih73D5zsRK7ivLQWqAPA?authuser=0&hl=en&g_ep=EgoyMDI2MDkyOC4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 36,
        "competitor_name": "AND - Nexus Seawoods Mall",
        "content_hash": "97bc44a5250cb2ccdf7d12a20691175cd23071b667a0d9c75ba30e67e3efe2e4",
        "cta": null,
        "detected_keywords": [
          "store",
          "stores",
          "visit",
          "shopping experience"
        ],
        "detected_topic": "Store & Visit",
        "id": 65,
        "image_urls": [
          "https://lh3.googleusercontent.com/a/ACg8ocIJRxCnhO06w9lp8mdQpvb3-xdWHJ5VxefYIl-xstNAyjwffw=w36-h36-p-rp-mo-br100"
        ],
        "is_own_profile": false,
        "is_public": false,
        "post_source": "owner",
        "post_url": null,
        "published_date": "2026-07-06T14:24:09.410403",
        "raw_data": {
          "post_source": "owner"
        },
        "scrape_date": "2026-10-04 14:25:39",
        "text_content": "Arpita Sarkar9 reviews · 1 photo3 months ago I had a great experience with Nargis going out of the way to arrange tops from other stores and helping with offers. And all with a smile. Rare to meet such a customer care executive.\nFrom ArpitaLike Share Response from the owner 3 months agoDear Arpita, we are glad you had a lovely shopping experience at our store. Nargis will surely be delighted to hear your feedback. Thank you, we look forward to your next visit."
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://maps.app.goo.gl/TqVEmxxQJYKnVSLc8",
        "competitor_id": 46,
        "competitor_name": "TRENDS",
        "content_hash": "227089f1c8f093d788d712b4bf734203a78f6beff10d1fd0268749c46c7c81ae",
        "cta": "Call now",
        "detected_keywords": [
          "workwear",
          "trousers"
        ],
        "detected_topic": "Workwear & Formals",
        "id": 68,
        "image_urls": [
          "https://lh3.googleusercontent.com/geougc/AF1QipOhSDjeHwnxJ82EEV-OsvDuuxz2LMj_I-Sp5WAA=h400-no"
        ],
        "is_own_profile": false,
        "is_public": false,
        "post_source": "owner",
        "post_url": "https://search.google.com/local/posts?q=TRENDS&ludocid=6463393496138288600&lpsid=CIHM0ogKENaBurmDoNDPlgE&source=sh/x/loc/post&lsig=AB86z5X02s-f3D095bgBymdXEvzQ",
        "published_date": "2026-04-15T00:00:00",
        "raw_data": {
          "post_source": "owner"
        },
        "scrape_date": "2026-10-04 15:06:37",
        "text_content": "Designed for the rhythm of modern workdays. Sleek waistcoats, wide-leg trousers, and refined neutrals come together to create a look that feels polished yet effortless. \r\n\r\nExplore the latest Women’s Workwear at your nearest TRENDS store.\r\n\r\n#TRENDS #SpringCollection2026"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://maps.app.goo.gl/TqVEmxxQJYKnVSLc8",
        "competitor_id": 46,
        "competitor_name": "TRENDS",
        "content_hash": "9ebae3eb30730dd3ec2b32fab1899946b8f345b7a2c7d6549817752e8440758a",
        "cta": "Learn more",
        "detected_keywords": [
          "workwear",
          "trousers"
        ],
        "detected_topic": "Workwear & Formals",
        "id": 69,
        "image_urls": [
          "https://lh3.googleusercontent.com/geougc/AF1QipPHJ0VQJWfwpVJUNBn0kCZuRXoz2QxZ0HfmcC3Y=h400-no"
        ],
        "is_own_profile": false,
        "is_public": false,
        "post_source": "owner",
        "post_url": "https://search.google.com/local/posts?q=TRENDS&ludocid=6463393496138288600&lpsid=CIHM0ogKEPPF4tarrbOZZg&source=sh/x/loc/post&lsig=AB86z5X02s-f3D095bgBymdXEvzQ",
        "published_date": "2026-04-15T00:00:00",
        "raw_data": {
          "post_source": "owner"
        },
        "scrape_date": "2026-10-04 15:06:37",
        "text_content": "Designed for the rhythm of modern workdays. Sleek waistcoats, wide-leg trousers, and refined neutrals come together to create a look that feels polished yet effortless. \r\n\r\nExplore the latest Women’s Workwear at your nearest TRENDS store.\r\n\r\n#TRENDS #SpringCollection2026"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://maps.app.goo.gl/TqVEmxxQJYKnVSLc8",
        "competitor_id": 46,
        "competitor_name": "TRENDS",
        "content_hash": "74df44b7e17b3dbee9107d511ad585abf9cb5091d25792f017bc7518bb8ef4d3",
        "cta": "Call now",
        "detected_keywords": [
          "stores"
        ],
        "detected_topic": "Store & Visit",
        "id": 70,
        "image_urls": [
          "https://lh3.googleusercontent.com/geougc/AF1QipPzJ7wlhQWh0P3HaBCCTK5yDvXNsi-94GZKRWD0=h400-no"
        ],
        "is_own_profile": false,
        "is_public": false,
        "post_source": "owner",
        "post_url": "https://search.google.com/local/posts?q=TRENDS&ludocid=6463393496138288600&lpsid=CIHM0ogKELfthL_nldPAiAE&source=sh/x/loc/post&lsig=AB86z5X02s-f3D095bgBymdXEvzQ",
        "published_date": "2026-04-14T00:00:00",
        "raw_data": {
          "post_source": "owner"
        },
        "scrape_date": "2026-10-04 15:06:38",
        "text_content": "Serving looks. Not just spreadsheets. \r\n\r\nClean lines, rich colour and effortless drape come together in this luxe set, proving that minimalism can still command a room \r\nAvailable now at TRENDS stores.\r\n\r\n#TRENDS #SpringCollection2026"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://maps.app.goo.gl/TqVEmxxQJYKnVSLc8",
        "competitor_id": 46,
        "competitor_name": "TRENDS",
        "content_hash": "501543c6774b1b171175e9f3e5783a472efc4b17e3d1467d682188c871e39667",
        "cta": "Call now",
        "detected_keywords": [
          "stores"
        ],
        "detected_topic": "Store & Visit",
        "id": 71,
        "image_urls": [
          "https://lh3.googleusercontent.com/geougc/AF1QipNHEpWFQzc_OMMzXrxSR4wxhzDQlFZsJO9H_pQ3=h400-no"
        ],
        "is_own_profile": false,
        "is_public": false,
        "post_source": "owner",
        "post_url": "https://search.google.com/local/posts?q=TRENDS&ludocid=6463393496138288600&lpsid=CIHM0ogKEJeArMuI8J39pwE&source=sh/x/loc/post&lsig=AB86z5X02s-f3D095bgBymdXEvzQ",
        "published_date": "2026-04-14T00:00:00",
        "raw_data": {
          "post_source": "owner"
        },
        "scrape_date": "2026-10-04 15:06:38",
        "text_content": "Serving looks. Not just spreadsheets. \r\n\r\nClean lines, rich colour and effortless drape come together in this luxe set, proving that minimalism can still command a room \r\nAvailable now at TRENDS stores.\r\n\r\n#TRENDS #SpringCollection2026"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://maps.app.goo.gl/TqVEmxxQJYKnVSLc8",
        "competitor_id": 46,
        "competitor_name": "TRENDS",
        "content_hash": "51a2a20788691ad01086478adf7432aabd8831d5269955e4ce101e3ad88249e9",
        "cta": "Call now",
        "detected_keywords": [
          "collection",
          "latest"
        ],
        "detected_topic": "New Collection",
        "id": 72,
        "image_urls": [
          "https://lh3.googleusercontent.com/geougc/AF1QipNTiYnWfVbsOpI-SkQHOGcGj3npR63-c4widR7E=h400-no"
        ],
        "is_own_profile": false,
        "is_public": false,
        "post_source": "owner",
        "post_url": "https://search.google.com/local/posts?q=TRENDS&ludocid=6463393496138288600&lpsid=CIHM0ogKEN-6lIPd_YK13gE&source=sh/x/loc/post&lsig=AB86z5X02s-f3D095bgBymdXEvzQ",
        "published_date": "2026-04-09T00:00:00",
        "raw_data": {
          "post_source": "owner"
        },
        "scrape_date": "2026-10-04 15:06:38",
        "text_content": "Elevate your escapes with effortless style. Structured with rich textures and refined patterns, this polo keeps you sharp from dawn to dusk. Shop the latest collection at your nearest TRENDS store.\r\n\r\n#TRENDS #SpringCollection2026"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://maps.app.goo.gl/TqVEmxxQJYKnVSLc8",
        "competitor_id": 46,
        "competitor_name": "TRENDS",
        "content_hash": "1ea6a4b3c949fc23e20439fd0877ba233a88b4f790e57d220df12987d85a87c2",
        "cta": "Call now",
        "detected_keywords": [
          "collection",
          "latest"
        ],
        "detected_topic": "New Collection",
        "id": 73,
        "image_urls": [
          "https://lh3.googleusercontent.com/geougc/AF1QipP1HN8MwLbvnlYaevjQ_r7-Qbk1mNMpuDMzAbzO=h400-no"
        ],
        "is_own_profile": false,
        "is_public": false,
        "post_source": "owner",
        "post_url": "https://search.google.com/local/posts?q=TRENDS&ludocid=6463393496138288600&lpsid=CIHM0ogKEI6cw4eQ1Zb_mAE&source=sh/x/loc/post&lsig=AB86z5X02s-f3D095bgBymdXEvzQ",
        "published_date": "2026-04-09T00:00:00",
        "raw_data": {
          "post_source": "owner"
        },
        "scrape_date": "2026-10-04 15:06:38",
        "text_content": "Elevate your escapes with effortless style. Structured with rich textures and refined patterns, this polo keeps you sharp from dawn to dusk. Shop the latest collection at your nearest TRENDS store.\r\n\r\n#TRENDS #SpringCollection2026"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://maps.app.goo.gl/TqVEmxxQJYKnVSLc8",
        "competitor_id": 46,
        "competitor_name": "TRENDS",
        "content_hash": "bf645241dc833d3f32d0238bc74ad2f674a893bcc8ba68855fcec064735b0960",
        "cta": "Call now",
        "detected_keywords": [
          "polo"
        ],
        "detected_topic": "Casual & Streetwear",
        "id": 74,
        "image_urls": [
          "https://lh3.googleusercontent.com/geougc/AF1QipPDnPiuq15KsVxSaMHf2YlgJev0XWjr1RkjgByh=h400-no"
        ],
        "is_own_profile": false,
        "is_public": false,
        "post_source": "owner",
        "post_url": "https://search.google.com/local/posts?q=TRENDS&ludocid=6463393496138288600&lpsid=CIHM0ogKELPfiO6KmdvrIg&source=sh/x/loc/post&lsig=AB86z5X02s-f3D095bgBymdXEvzQ",
        "published_date": "2026-04-08T00:00:00",
        "raw_data": {
          "post_source": "owner"
        },
        "scrape_date": "2026-10-04 15:06:39",
        "text_content": "Built for holidays, a textured polo in a classic colourway that stays with you.\r\n\r\nShop now.\r\n\r\n#TRENDS #SpringCollection2026"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://maps.app.goo.gl/TqVEmxxQJYKnVSLc8",
        "competitor_id": 46,
        "competitor_name": "TRENDS",
        "content_hash": "54e3288ce716be5d228e8cb219f38b283c969c03d4ce39c7118d900bb7a20740",
        "cta": "Call now",
        "detected_keywords": [
          "polo"
        ],
        "detected_topic": "Casual & Streetwear",
        "id": 75,
        "image_urls": [
          "https://lh3.googleusercontent.com/geougc/AF1QipP1LOQFkKP-b2u3QKSUoC--4Sq5Zr3fxT0iPeUC=h400-no"
        ],
        "is_own_profile": false,
        "is_public": false,
        "post_source": "owner",
        "post_url": "https://search.google.com/local/posts?q=TRENDS&ludocid=6463393496138288600&lpsid=CIHM0ogKELHSmKDbwJ7yzAE&source=sh/x/loc/post&lsig=AB86z5X02s-f3D095bgBymdXEvzQ",
        "published_date": "2026-04-08T00:00:00",
        "raw_data": {
          "post_source": "owner"
        },
        "scrape_date": "2026-10-04 15:06:39",
        "text_content": "Built for holidays, a textured polo in a classic colourway that stays with you.\r\n\r\nShop now.\r\n\r\n#TRENDS #SpringCollection2026"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/Pantaloons/data=!4m7!3m6!1s0x3be7c3bd9be46b9d:0xfb1de664b3b92329!8m2!3d19.0224547!4d73.017665!16s%2Fg%2F11g6xq928d!19sChIJnWvkm73D5zsRKSO5s2TmHfs?authuser=0&hl=en&g_ep=EgoyMDI2MDkyOC4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 38,
        "competitor_name": "Pantaloons",
        "content_hash": "b5b26ba2843d149c08f62e2d6824f712d6f3a8ae33c8b1032f9cc531307aa0d5",
        "cta": null,
        "detected_keywords": [
          "sale",
          "end of season"
        ],
        "detected_topic": "Offers & Discounts",
        "id": 64,
        "image_urls": [],
        "is_own_profile": false,
        "is_public": true,
        "post_source": "public",
        "post_url": null,
        "published_date": "2026-07-06T13:01:04.623475",
        "raw_data": {
          "author": "LateBloomerMusic",
          "content_type": "public_content",
          "post_source": "public",
          "rating": 1,
          "relative_date": "3 months ago"
        },
        "scrape_date": "2026-10-04 13:01:09",
        "text_content": "LateBloomerMusicLocal Guide · 69 reviews · 11 photos3 months ago Absolutely fed up with the staff at this Pantaloons outlet. As an Insignia member, I was promised advance SMS notifications for the ‘End of Season Sale’ — never received one. When I asked the floor staff directly on 23rd June, they … MoreLike Share Response from the owner 2 months agoHi, we certainly don't want you to feel this way. Please contact our Customer Care at 1800 103 7527 between 10 am to 10 pm or mail us at customercare@abfrl.adityabirla.com so that we can assist you further with it."
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/Pantaloons/data=!4m7!3m6!1s0x3be7c3bd9be46b9d:0xfb1de664b3b92329!8m2!3d19.0224547!4d73.017665!16s%2Fg%2F11g6xq928d!19sChIJnWvkm73D5zsRKSO5s2TmHfs?authuser=0&hl=en&g_ep=EgoyMDI2MDkyOC4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 38,
        "competitor_name": "Pantaloons",
        "content_hash": "adb35334ae572288b4d337bc9a0db1a97d16229de38c2d5bc86d20f2fd294510",
        "cta": null,
        "detected_keywords": [
          "collection",
          "arrival"
        ],
        "detected_topic": "New Collection",
        "id": 63,
        "image_urls": [],
        "is_own_profile": false,
        "is_public": true,
        "post_source": "public",
        "post_url": null,
        "published_date": "2026-05-07T13:01:02.725507",
        "raw_data": {
          "author": "Rohini Rathod",
          "content_type": "public_content",
          "post_source": "public",
          "rating": 3,
          "relative_date": "5 months ago"
        },
        "scrape_date": "2026-10-04 13:01:09",
        "text_content": "Rohini Rathod2 reviews5 months ago This pantaloons look like a factory outlet .. big space but no management. Cloths are not aligned properly and everything looks overlaping. Old stuff new stuff all put together. Usually after arrival of new summer collection old cloths … MoreLike Share Response from the owner 5 months agoHi Rohini, we regret the inconvenience caused to you. Please contact our Customer Care at 1800 103 7527 between 10 am to 10 pm or mail us at customercare@abfrl.adityabirla.com"
      }
    ],
    "stats": {
      "captcha_latest_run": false,
      "competitors_count": 11,
      "duplicates_skipped_latest_run": 0,
      "failures_latest_run": 0,
      "generated_content_count": 0,
      "generated_content_used": 0,
      "images_downloaded_latest_run": 8,
      "last_scrape_at": "2026-10-04 15:04:24.679199",
      "last_scrape_status": "success",
      "latest_run": {
        "captcha_encountered": 0,
        "competitor_names": [
          "TRENDS"
        ],
        "competitors_processed": 1,
        "details": [
          {
            "business_verified": true,
            "captcha_required": false,
            "competitor": "TRENDS",
            "competitor_id": 46,
            "duplicates_skipped": 0,
            "error": null,
            "gmap_url": "https://maps.app.goo.gl/TqVEmxxQJYKnVSLc8",
            "images_downloaded": 8,
            "new_posts": 8,
            "owner_posts": 8,
            "place_profile": {
              "address": "Grand Central Mall, Sector 40, Seawoods, Navi Mumbai, Maharashtra 400706, India",
              "category": null,
              "name": "TRENDS",
              "rating": 4.1,
              "rating_distribution": {
                "1": 152,
                "2": 122,
                "3": 514,
                "4": 1164,
                "5": 1412
              },
              "review_count": 3364
            },
            "posts_found": 8,
            "public_posts": 0,
            "reviews_saved": 0,
            "status": "SUCCESS",
            "window_days": 180
          }
        ],
        "duplicates_skipped": 0,
        "duration_seconds": 135,
        "end_time": "2026-10-04 15:06:39.851423",
        "error_info": null,
        "failures": 0,
        "has_captcha_issue": false,
        "has_errors": false,
        "id": 61,
        "images_downloaded": 8,
        "new_posts": 8,
        "posts_found": 8,
        "project_id": 11,
        "start_time": "2026-10-04 15:04:24.679199",
        "status": "success"
      },
      "new_posts_latest_run": 8,
      "owner_posts": 24,
      "posts_last_7_days": 26,
      "project_id": 11,
      "public_posts": 2,
      "top_keywords": [
        {
          "count": 5,
          "keyword": "store"
        },
        {
          "count": 5,
          "keyword": "visit"
        },
        {
          "count": 4,
          "keyword": "stores"
        },
        {
          "count": 4,
          "keyword": "sale"
        },
        {
          "count": 3,
          "keyword": "shopping experience"
        },
        {
          "count": 3,
          "keyword": "collection"
        },
        {
          "count": 3,
          "keyword": "latest"
        },
        {
          "count": 3,
          "keyword": "offer"
        }
      ],
      "top_topics": [
        {
          "count": 7,
          "topic": "Store & Visit"
        },
        {
          "count": 4,
          "topic": "General Update"
        },
        {
          "count": 4,
          "topic": "New Collection"
        },
        {
          "count": 4,
          "topic": "Offers & Discounts"
        },
        {
          "count": 2,
          "topic": "Workwear & Formals"
        }
      ],
      "total_posts": 26,
      "totals": {
        "captcha_interventions": 0,
        "competitors_processed": 21,
        "duplicates_skipped": 6,
        "failed_attempts": 13,
        "images_downloaded": 20,
        "new_posts": 26,
        "posts_found": 34,
        "success_rate": 38.1,
        "successful_runs": 8,
        "total_runs": 21
      },
      "unique_businesses": 11
    },
    "topics": [
      {
        "competitor_count": 3,
        "competitors_using": "3 of 11",
        "count": 7,
        "detected_topic": "Store & Visit",
        "occurrence_percentage": 27.3,
        "total_competitors": 11
      },
      {
        "competitor_count": 2,
        "competitors_using": "2 of 11",
        "count": 4,
        "detected_topic": "General Update",
        "occurrence_percentage": 18.2,
        "total_competitors": 11
      },
      {
        "competitor_count": 2,
        "competitors_using": "2 of 11",
        "count": 4,
        "detected_topic": "New Collection",
        "occurrence_percentage": 18.2,
        "total_competitors": 11
      },
      {
        "competitor_count": 1,
        "competitors_using": "1 of 11",
        "count": 4,
        "detected_topic": "Offers & Discounts",
        "occurrence_percentage": 9.1,
        "total_competitors": 11
      },
      {
        "competitor_count": 1,
        "competitors_using": "1 of 11",
        "count": 2,
        "detected_topic": "Workwear & Formals",
        "occurrence_percentage": 9.1,
        "total_competitors": 11
      },
      {
        "competitor_count": 1,
        "competitors_using": "1 of 11",
        "count": 2,
        "detected_topic": "Casual & Streetwear",
        "occurrence_percentage": 9.1,
        "total_competitors": 11
      },
      {
        "competitor_count": 1,
        "competitors_using": "1 of 11",
        "count": 1,
        "detected_topic": "Updates & Announcements",
        "occurrence_percentage": 9.1,
        "total_competitors": 11
      }
    ],
    "keywords": [
      {
        "count": 5,
        "keyword": "store"
      },
      {
        "count": 5,
        "keyword": "visit"
      },
      {
        "count": 4,
        "keyword": "stores"
      },
      {
        "count": 4,
        "keyword": "sale"
      },
      {
        "count": 3,
        "keyword": "shopping experience"
      },
      {
        "count": 3,
        "keyword": "collection"
      },
      {
        "count": 3,
        "keyword": "latest"
      },
      {
        "count": 3,
        "keyword": "offer"
      },
      {
        "count": 3,
        "keyword": "offers"
      },
      {
        "count": 3,
        "keyword": "end of season"
      },
      {
        "count": 2,
        "keyword": "workwear"
      },
      {
        "count": 2,
        "keyword": "trousers"
      },
      {
        "count": 2,
        "keyword": "polo"
      },
      {
        "count": 1,
        "keyword": "new"
      },
      {
        "count": 1,
        "keyword": "new arrivals"
      },
      {
        "count": 1,
        "keyword": "deals"
      },
      {
        "count": 1,
        "keyword": "save"
      },
      {
        "count": 1,
        "keyword": "deal"
      }
    ],
    "ideas": [],
    "market_gaps": [
      {
        "actionable_strategy": "Address the 'Offers & Discounts' complaints head-on in your Google Maps posts and profile: publish the guarantee, policy or service change that removes that exact friction for customers.",
        "affected_competitors": [
          "Pantaloons"
        ],
        "badge": "Critical Opportunity",
        "badge_color": "terracotta",
        "category": "Customer Sentiment Deficit",
        "competitor_weakness": "1 captured negative review(s) mention 'Offers & Discounts' — main sources: Pantaloons. Example: \"LateBloomerMusicLocal Guide · 69 reviews · 11 photos3 months ago Absolutely fed up with the staff at this Pantaloons outlet. As an Insignia member, I was \"",
        "expected_impact": "Convert dissatisfied rival customers into first-time visitors",
        "icon_type": "shield-alert",
        "id": "gap-policy-friction",
        "title": "Customer Friction & Complaints in Offers & Discounts"
      },
      {
        "actionable_strategy": "Publish consistently (e.g. 2x weekly) with offers and updates; out-posting the busiest rival (13 captured posts) puts your profile in front of local searchers first.",
        "affected_competitors": [
          "W Nexus Seawoods, Mumbai",
          "Max Fashion - Nexus Seawoods",
          "Westside - Nexus Seawoods",
          "Levi's - Nexus Seawoods"
        ],
        "badge": "High Impact",
        "badge_color": "amber",
        "category": "Organic Visibility Void",
        "competitor_weakness": "8 of 11 tracked competitors have fewer than 3 captured Google Maps updates (W Nexus Seawoods, Mumbai, Max Fashion - Nexus Seawoods, Westside - Nexus Seawoods…). Most active so far: Pantaloons (13 posts), TRENDS (8 posts).",
        "expected_impact": "Out-publish 8 less active rival(s) on the Google Maps feed",
        "icon_type": "flame",
        "id": "gap-content-cadence",
        "title": "Google Maps Content Publishing Vacuum"
      },
      {
        "actionable_strategy": "Lift visible trust above 3.7★: showcase five-star service stories, refresh photos, and answer every review so your profile reads better than the weakest tracked rival.",
        "affected_competitors": [
          "W Nexus Seawoods, Mumbai"
        ],
        "badge": "Competitive Edge",
        "badge_color": "sage",
        "category": "Local Trust Deficit",
        "competitor_weakness": "W Nexus Seawoods, Mumbai sits at 3.7★ (130 reviews) against a tracked-market average of 4.12★, while AND - Nexus Seawoods Mall leads at 4.5★.",
        "expected_impact": "Out-rank W Nexus Seawoods, Mumbai (3.7★) on local trust signals",
        "icon_type": "trending-up",
        "id": "gap-rating-quality",
        "title": "Rating Quality Gap vs W Nexus Seawoods, Mumbai"
      },
      {
        "actionable_strategy": "Re-scrape the competitors without captured reviews so sentiment, rating distribution and complaint analysis cover the whole market before deciding the next campaign.",
        "affected_competitors": [
          "TRENDS",
          "W Nexus Seawoods, Mumbai",
          "Max Fashion - Nexus Seawoods",
          "Westside - Nexus Seawoods"
        ],
        "badge": "Quick Win",
        "badge_color": "sage",
        "category": "Data Coverage",
        "competitor_weakness": "3 review(s) captured for 2 of 11 competitors; no reviews captured yet for 9 (TRENDS, W Nexus Seawoods, Mumbai, Max Fashion - Nexus Seawoods…).",
        "expected_impact": "Complete review intelligence across every tracked competitor",
        "icon_type": "clock",
        "id": "gap-review-evidence",
        "title": "Review Evidence Coverage Gap"
      }
    ]
  },
  "7": {
    "project": {
      "competitor_count": 17,
      "created_at": "2026-09-29 15:05:37",
      "field": "cafe ,food ,cofee ,mocha ,macha",
      "gmap_url": null,
      "id": 7,
      "is_online": 0,
      "location": "bandra",
      "name": "Brew and Bold Cafe Bandra",
      "our_profile": "cafe ,stylish ,cozy",
      "own_place_id": 58,
      "place": {
        "address": "bandra",
        "category": null,
        "cid": null,
        "confidence": 1,
        "created_at": "2026-10-04 15:29:25",
        "google_place_id": null,
        "hex_id": null,
        "id": 58,
        "identity_label": "addr:brew and bold cafe bandra|bandra",
        "identity_source": "name_address",
        "kgmid": null,
        "latitude": null,
        "longitude": null,
        "name": "Brew and Bold Cafe Bandra",
        "place_key": "addr:brew and bold cafe bandra|bandra",
        "place_url": "https://www.google.com/maps/search/?api=1&query=Brew%20and%20Bold%20Cafe%20Bandra%20bandra",
        "rating": null,
        "review_count": null,
        "updated_at": "2026-10-04 15:29:25"
      },
      "place_id": 58,
      "place_key": "addr:brew and bold cafe bandra|bandra",
      "place_url": "https://www.google.com/maps/search/?api=1&query=Brew%20and%20Bold%20Cafe%20Bandra%20bandra"
    },
    "competitors": [
      {
        "added_at": "2026-09-29 15:06:33",
        "address": "600 hill crest Building Ground floor Ambedkar Rd, Pali Mala Rd, near Arvind store, Bandra West, Mumbai, Maharashtra 400050",
        "business_key": "mokai cafe pali hill",
        "category": null,
        "gmap_url": "https://www.google.com/maps/place/Mokai+Cafe+Pali+Hill/data=!4m7!3m6!1s0x3be7c9001fb6e177:0xa52f12f1036bb24e!8m2!3d19.0633484!4d72.8295262!16s%2Fg%2F11vwtj0822!19sChIJd-G2HwDJ5zsRTrJrA_ESL6U?authuser=0&hl=en&g_ep=EgoyMDI2MDkyMy4wIJJjKgBIAVAD&rclk=1",
        "id": 17,
        "identity_source": "hex_id",
        "last_scrape_status": "2026-10-04 15:15:06.110268",
        "last_scraped": "2026-09-29 20:13:53",
        "name": "Mokai Cafe Pali Hill",
        "place": {
          "address": "Coffee shop · 600 hill crest Building Ground floor Ambedkar Rd, Pali Mala Rd, near Arvind store",
          "category": null,
          "cid": "11902753166517318222",
          "competitor_count": 1,
          "confidence": 3,
          "created_at": "2026-09-29 15:06:33",
          "google_place_id": "ChIJd-G2HwDJ5zsRTrJrA_ESL6U",
          "hex_id": "0x3be7c9001fb6e177:0xa52f12f1036bb24e",
          "id": 22,
          "identity_label": "ChIJd-G2HwDJ5zsRTrJrA_ESL6U",
          "identity_source": "hex_id",
          "kgmid": "/g/11vwtj0822",
          "latitude": 19.0633484,
          "longitude": 72.8295262,
          "name": "Mokai Cafe Pali Hill",
          "place_key": "place:0x3be7c9001fb6e177:0xa52f12f1036bb24e",
          "place_url": "https://www.google.com/maps/place/?q=place_id:ChIJd-G2HwDJ5zsRTrJrA_ESL6U",
          "project_count": 1,
          "rating": null,
          "review_count": null,
          "updated_at": "2026-09-29 20:36:33"
        },
        "place_id": 22,
        "place_key": "place:0x3be7c9001fb6e177:0xa52f12f1036bb24e",
        "post_count": 3,
        "posts_collected": 3,
        "project_id": 7,
        "rating": 4.3,
        "rating_distribution": "{\"5\": 1144, \"4\": 326, \"3\": 119, \"2\": 60, \"1\": 110}",
        "review_count": 1759,
        "shared_with_projects": 0,
        "status": "timeout"
      },
      {
        "added_at": "2026-09-29 15:07:26",
        "address": "Shop No 1, No 33, Mayflower Building Perry Road, New Kantwadi Rd, Bandra West, Mumbai, Maharashtra 400050",
        "business_key": "blue tokai coffee roasters bandra",
        "category": null,
        "gmap_url": "https://www.google.com/maps/place/Blue+Tokai+Coffee+Roasters+%7C+Bandra/data=!4m7!3m6!1s0x3be7c96bae4baaab:0x27f9cc1563722ef4!8m2!3d19.0603995!4d72.8243282!16s%2Fg%2F11g8t_v0r1!19sChIJq6pLrmvJ5zsR9C5yYxXM-Sc?authuser=0&hl=en&g_ep=EgoyMDI2MDkyMy4wIJJjKgBIAVAD&rclk=1",
        "id": 26,
        "identity_source": "hex_id",
        "last_scrape_status": "2026-10-04 15:15:06.110268",
        "last_scraped": "2026-09-29 15:22:25",
        "name": "Blue Tokai Coffee Roasters | Bandra",
        "place": {
          "address": null,
          "category": null,
          "cid": "2880557828914949876",
          "competitor_count": 1,
          "confidence": 3,
          "created_at": "2026-09-29 15:07:26",
          "google_place_id": "ChIJq6pLrmvJ5zsR9C5yYxXM-Sc",
          "hex_id": "0x3be7c96bae4baaab:0x27f9cc1563722ef4",
          "id": 31,
          "identity_label": "ChIJq6pLrmvJ5zsR9C5yYxXM-Sc",
          "identity_source": "hex_id",
          "kgmid": "/g/11g8t_v0r1",
          "latitude": 19.0603995,
          "longitude": 72.8243282,
          "name": "Blue Tokai Coffee Roasters | Bandra",
          "place_key": "place:0x3be7c96bae4baaab:0x27f9cc1563722ef4",
          "place_url": "https://www.google.com/maps/place/?q=place_id:ChIJq6pLrmvJ5zsR9C5yYxXM-Sc",
          "project_count": 1,
          "rating": null,
          "review_count": null,
          "updated_at": "2026-09-29 20:37:26"
        },
        "place_id": 31,
        "place_key": "place:0x3be7c96bae4baaab:0x27f9cc1563722ef4",
        "post_count": 10,
        "posts_collected": 10,
        "project_id": 7,
        "rating": 4.4,
        "rating_distribution": "{\"5\": 873, \"4\": 387, \"3\": 141, \"2\": 28, \"1\": 42}",
        "review_count": 1471,
        "shared_with_projects": 0,
        "status": "active"
      },
      {
        "added_at": "2026-09-29 15:06:40",
        "address": "Ground Floor, Platina, C-59, G Block, Bandra Kurla Complex, Bandra East, Mumbai, Maharashtra 400098",
        "business_key": "third wave coffee",
        "category": "Specialty Coffee Shop",
        "gmap_url": "https://www.google.com/maps/search/?api=1&query=Third+Wave+Coffee+Bandra+West",
        "id": 21,
        "identity_source": "name_address",
        "last_scrape_status": "2026-10-04 15:15:06.110268",
        "last_scraped": "2026-09-29 15:20:16",
        "name": "Third Wave Coffee",
        "place": {
          "address": "Linking Road, Bandra West, Mumbai",
          "category": "Specialty Coffee Shop",
          "cid": null,
          "competitor_count": 1,
          "confidence": 1,
          "created_at": "2026-09-29 15:06:40",
          "google_place_id": null,
          "hex_id": null,
          "id": 26,
          "identity_label": "addr:third wave coffee|linking road bandra west mumbai",
          "identity_source": "name_address",
          "kgmid": null,
          "latitude": null,
          "longitude": null,
          "name": "Third Wave Coffee",
          "place_key": "addr:third wave coffee|linking road bandra west mumbai",
          "place_url": "https://www.google.com/maps/search/?api=1&query=Third%20Wave%20Coffee%20Linking%20Road%2C%20Bandra%20West%2C%20Mumbai",
          "project_count": 1,
          "rating": null,
          "review_count": null,
          "updated_at": "2026-09-29 20:36:40"
        },
        "place_id": 26,
        "place_key": "addr:third wave coffee|linking road bandra west mumbai",
        "post_count": 3,
        "posts_collected": 3,
        "project_id": 7,
        "rating": 4.7,
        "rating_distribution": "{\"5\": 243, \"4\": 29, \"3\": 12, \"2\": 3, \"1\": 8}",
        "review_count": 676,
        "shared_with_projects": 0,
        "status": "active"
      },
      {
        "added_at": "2026-09-29 15:06:43",
        "address": "Bandra Kurla Complex Rd, inside Bpcl West, G Block BKC, Bandra Kurla Complex, Bandra West, Mumbai, Maharashtra 400050",
        "business_key": "cafe coffee day",
        "category": "Chain Cafe / Food",
        "gmap_url": "https://www.google.com/maps/search/?api=1&query=Cafe+Coffee+Day+Linking+Road+Bandra",
        "id": 22,
        "identity_source": "name_address",
        "last_scrape_status": "2026-10-04 15:15:06.110268",
        "last_scraped": "2026-09-29 15:20:59",
        "name": "Cafe Coffee Day",
        "place": {
          "address": "Linking Road, Bandra West, Mumbai",
          "category": "Chain Cafe / Food",
          "cid": null,
          "competitor_count": 1,
          "confidence": 1,
          "created_at": "2026-09-29 15:06:43",
          "google_place_id": null,
          "hex_id": null,
          "id": 27,
          "identity_label": "addr:cafe coffee day|linking road bandra west mumbai",
          "identity_source": "name_address",
          "kgmid": null,
          "latitude": null,
          "longitude": null,
          "name": "Cafe Coffee Day",
          "place_key": "addr:cafe coffee day|linking road bandra west mumbai",
          "place_url": "https://www.google.com/maps/search/?api=1&query=Cafe%20Coffee%20Day%20Linking%20Road%2C%20Bandra%20West%2C%20Mumbai",
          "project_count": 1,
          "rating": null,
          "review_count": null,
          "updated_at": "2026-09-29 20:36:42"
        },
        "place_id": 27,
        "place_key": "addr:cafe coffee day|linking road bandra west mumbai",
        "post_count": 0,
        "posts_collected": 0,
        "project_id": 7,
        "rating": 3.8,
        "rating_distribution": "{\"5\": 96, \"4\": 69, \"3\": 53, \"2\": 11, \"1\": 21}",
        "review_count": 781,
        "shared_with_projects": 0,
        "status": "active"
      },
      {
        "added_at": "2026-09-29 15:06:34",
        "address": "Shop no. 6 and 7, Silver Croft, 16th Rd, near Khane Khas, Bandra West, Mumbai, Maharashtra 400050",
        "business_key": "bokka coffee",
        "category": null,
        "gmap_url": "https://www.google.com/maps/place/Bokka+Coffee/data=!4m7!3m6!1s0x3be7c9e567d1d7e7:0xc146a4025025ea1c!8m2!3d19.0656334!4d72.830873!16s%2Fg%2F11svffd5sh!19sChIJ59fRZ-XJ5zsRHOolUAKkRsE?authuser=0&hl=en&g_ep=EgoyMDI2MDkyMy4wIJJjKgBIAVAD&rclk=1",
        "id": 18,
        "identity_source": "hex_id",
        "last_scrape_status": "2026-10-04 15:15:06.110268",
        "last_scraped": "2026-09-29 15:18:37",
        "name": "Bokka Coffee",
        "place": {
          "address": "Coffee shop · Shop no. 6 and 7, Silver Croft, 16th Rd, near Khane Khas",
          "category": null,
          "cid": "13926999227531389468",
          "competitor_count": 1,
          "confidence": 3,
          "created_at": "2026-09-29 15:06:34",
          "google_place_id": "ChIJ59fRZ-XJ5zsRHOolUAKkRsE",
          "hex_id": "0x3be7c9e567d1d7e7:0xc146a4025025ea1c",
          "id": 23,
          "identity_label": "ChIJ59fRZ-XJ5zsRHOolUAKkRsE",
          "identity_source": "hex_id",
          "kgmid": "/g/11svffd5sh",
          "latitude": 19.0656334,
          "longitude": 72.830873,
          "name": "Bokka Coffee",
          "place_key": "place:0x3be7c9e567d1d7e7:0xc146a4025025ea1c",
          "place_url": "https://www.google.com/maps/place/?q=place_id:ChIJ59fRZ-XJ5zsRHOolUAKkRsE",
          "project_count": 1,
          "rating": null,
          "review_count": null,
          "updated_at": "2026-09-29 20:36:34"
        },
        "place_id": 23,
        "place_key": "place:0x3be7c9e567d1d7e7:0xc146a4025025ea1c",
        "post_count": 6,
        "posts_collected": 6,
        "project_id": 7,
        "rating": 4.2,
        "rating_distribution": "{\"5\": 385, \"4\": 161, \"3\": 57, \"2\": 20, \"1\": 43}",
        "review_count": 666,
        "shared_with_projects": 0,
        "status": "active"
      },
      {
        "added_at": "2026-09-29 15:06:31",
        "address": "Silvilla House, Chapel Rd, next to Lovely Stores, St Sebastian Colony, Ranwar, Bandra West, Mumbai, Maharashtra 400050",
        "business_key": "tokyo matcha bar cafe",
        "category": "Coffee shop · Silvilla House, Chapel Rd, next to Lovely Stores",
        "gmap_url": "https://www.google.com/maps/place/Tokyo+Matcha+Bar+%26+Cafe/data=!4m7!3m6!1s0x3be7c94bd9ffb9c3:0xe3820fc467efa98b!8m2!3d19.0528007!4d72.8288095!16s%2Fg%2F11kq4yd_lp!19sChIJw7n_2UvJ5zsRi6nvZ8QPguM?authuser=0&hl=en&g_ep=EgoyMDI2MDkyMy4wIJJjKgBIAVAD&rclk=1",
        "id": 16,
        "identity_source": "hex_id",
        "last_scrape_status": "2026-10-04 15:15:06.110268",
        "last_scraped": "2026-09-29 15:19:23",
        "name": "Tokyo Matcha Bar & Cafe",
        "place": {
          "address": null,
          "category": "Coffee shop · Silvilla House, Chapel Rd, next to Lovely Stores",
          "cid": "16393682929813793163",
          "competitor_count": 1,
          "confidence": 3,
          "created_at": "2026-09-29 15:06:31",
          "google_place_id": "ChIJw7n_2UvJ5zsRi6nvZ8QPguM",
          "hex_id": "0x3be7c94bd9ffb9c3:0xe3820fc467efa98b",
          "id": 21,
          "identity_label": "ChIJw7n_2UvJ5zsRi6nvZ8QPguM",
          "identity_source": "hex_id",
          "kgmid": "/g/11kq4yd_lp",
          "latitude": 19.0528007,
          "longitude": 72.8288095,
          "name": "Tokyo Matcha Bar & Cafe",
          "place_key": "place:0x3be7c94bd9ffb9c3:0xe3820fc467efa98b",
          "place_url": "https://www.google.com/maps/place/?q=place_id:ChIJw7n_2UvJ5zsRi6nvZ8QPguM",
          "project_count": 1,
          "rating": null,
          "review_count": null,
          "updated_at": "2026-09-29 20:36:31"
        },
        "place_id": 21,
        "place_key": "place:0x3be7c94bd9ffb9c3:0xe3820fc467efa98b",
        "post_count": 6,
        "posts_collected": 6,
        "project_id": 7,
        "rating": 3.9,
        "rating_distribution": "{\"5\": 205, \"4\": 70, \"3\": 27, \"2\": 19, \"1\": 56}",
        "review_count": 377,
        "shared_with_projects": 0,
        "status": "active"
      },
      {
        "added_at": "2026-09-29 15:09:06",
        "address": "Plot no 160, 29th Rd, next to Sigdi restaurant, TPS III, Bandra West, Mumbai, Maharashtra 400050",
        "business_key": "bru baabaa caf",
        "category": null,
        "gmap_url": "https://www.google.com/maps/place/bru+baabaa+caf%C3%A9/data=!4m7!3m6!1s0x3be7c94a387288f9:0x9e1af733fa10373e!8m2!3d19.0615779!4d72.8334489!16s%2Fg%2F11y715fbnr!19sChIJ-YhyOErJ5zsRPjcQ-jP3Gp4?authuser=0&hl=en&g_ep=EgoyMDI2MDkyMy4wIJJjKgBIAVAD&rclk=1",
        "id": 27,
        "identity_source": "hex_id",
        "last_scrape_status": "2026-10-04 15:15:06.110268",
        "last_scraped": "2026-09-29 15:22:54",
        "name": "bru baabaa café",
        "place": {
          "address": null,
          "category": null,
          "cid": "11392690009997850430",
          "competitor_count": 1,
          "confidence": 3,
          "created_at": "2026-09-29 15:09:06",
          "google_place_id": "ChIJ-YhyOErJ5zsRPjcQ-jP3Gp4",
          "hex_id": "0x3be7c94a387288f9:0x9e1af733fa10373e",
          "id": 32,
          "identity_label": "ChIJ-YhyOErJ5zsRPjcQ-jP3Gp4",
          "identity_source": "hex_id",
          "kgmid": "/g/11y715fbnr",
          "latitude": 19.0615779,
          "longitude": 72.8334489,
          "name": "bru baabaa café",
          "place_key": "place:0x3be7c94a387288f9:0x9e1af733fa10373e",
          "place_url": "https://www.google.com/maps/place/?q=place_id:ChIJ-YhyOErJ5zsRPjcQ-jP3Gp4",
          "project_count": 1,
          "rating": null,
          "review_count": null,
          "updated_at": "2026-09-29 20:39:06"
        },
        "place_id": 32,
        "place_key": "place:0x3be7c94a387288f9:0x9e1af733fa10373e",
        "post_count": 9,
        "posts_collected": 9,
        "project_id": 7,
        "rating": 4.8,
        "rating_distribution": "{\"5\": 175, \"4\": 29, \"3\": 3, \"2\": 2, \"1\": 3}",
        "review_count": 212,
        "shared_with_projects": 0,
        "status": "active"
      },
      {
        "added_at": "2026-09-29 15:06:36",
        "address": "7th, PD Hinduja Rd, Khar, Khar West, Mumbai, Maharashtra 400052",
        "business_key": "four chairs cafe best cafe near hinduja hospital bandra",
        "category": "Coffee shop · 7th, PD Hinduja Rd",
        "gmap_url": "https://www.google.com/maps/place/Four+Chairs+Cafe+%7C+Best+Cafe+Near+Hinduja+Hospital+Bandra/data=!4m7!3m6!1s0x3be7c9dd524ee9d5:0xc0762dd675bdb48e!8m2!3d19.0673844!4d72.8360308!16s%2Fg%2F11yx7y5z08!19sChIJ1elOUt3J5zsRjrS9ddYtdsA?authuser=0&hl=en&g_ep=EgoyMDI2MDkyMy4wIJJjKgBIAVAD&rclk=1",
        "id": 19,
        "identity_source": "hex_id",
        "last_scrape_status": "2026-10-04 15:15:06.110268",
        "last_scraped": "2026-09-29 15:23:39",
        "name": "Four Chairs Cafe | Best Cafe Near Hinduja Hospital Bandra",
        "place": {
          "address": null,
          "category": "Coffee shop · 7th, PD Hinduja Rd",
          "cid": "13868322501655639182",
          "competitor_count": 1,
          "confidence": 3,
          "created_at": "2026-09-29 15:06:36",
          "google_place_id": "ChIJ1elOUt3J5zsRjrS9ddYtdsA",
          "hex_id": "0x3be7c9dd524ee9d5:0xc0762dd675bdb48e",
          "id": 24,
          "identity_label": "ChIJ1elOUt3J5zsRjrS9ddYtdsA",
          "identity_source": "hex_id",
          "kgmid": "/g/11yx7y5z08",
          "latitude": 19.0673844,
          "longitude": 72.8360308,
          "name": "Four Chairs Cafe | Best Cafe Near Hinduja Hospital Bandra",
          "place_key": "place:0x3be7c9dd524ee9d5:0xc0762dd675bdb48e",
          "place_url": "https://www.google.com/maps/place/?q=place_id:ChIJ1elOUt3J5zsRjrS9ddYtdsA",
          "project_count": 1,
          "rating": null,
          "review_count": null,
          "updated_at": "2026-09-29 20:36:36"
        },
        "place_id": 24,
        "place_key": "place:0x3be7c9dd524ee9d5:0xc0762dd675bdb48e",
        "post_count": 8,
        "posts_collected": 8,
        "project_id": 7,
        "rating": 4.7,
        "rating_distribution": "{\"5\": 139, \"4\": 23, \"3\": 2, \"2\": 3, \"1\": 5}",
        "review_count": 172,
        "shared_with_projects": 0,
        "status": "active"
      },
      {
        "added_at": "2026-09-29 15:06:39",
        "address": "Shop No.5, Pearl Haven, Chapel Rd, St Sebastian Colony, W, Bandra West, Mumbai, Maharashtra 400050",
        "business_key": "haiku fka method bandra",
        "category": "Cafe ·",
        "gmap_url": "https://www.google.com/maps/place/Haiku+%28fka+Method+Bandra%29/data=!4m7!3m6!1s0x3be7c90bc10415ef:0x3508e5abd151f164!8m2!3d19.0505612!4d72.8267888!16s%2Fg%2F11kl9v_843!19sChIJ7xUEwQvJ5zsRZPFR0avlCDU?authuser=0&hl=en&g_ep=EgoyMDI2MDkyMy4wIJJjKgBIAVAD&rclk=1",
        "id": 20,
        "identity_source": "hex_id",
        "last_scrape_status": "2026-10-04 15:15:06.110268",
        "last_scraped": "2026-09-29 15:21:42",
        "name": "Haiku (fka Method Bandra)",
        "place": {
          "address": "Shop No.5, Pearl Haven, Chapel Rd",
          "category": "Cafe ·",
          "cid": "3821556809937842532",
          "competitor_count": 1,
          "confidence": 3,
          "created_at": "2026-09-29 15:06:39",
          "google_place_id": "ChIJ7xUEwQvJ5zsRZPFR0avlCDU",
          "hex_id": "0x3be7c90bc10415ef:0x3508e5abd151f164",
          "id": 25,
          "identity_label": "ChIJ7xUEwQvJ5zsRZPFR0avlCDU",
          "identity_source": "hex_id",
          "kgmid": "/g/11kl9v_843",
          "latitude": 19.0505612,
          "longitude": 72.8267888,
          "name": "Haiku (fka Method Bandra)",
          "place_key": "place:0x3be7c90bc10415ef:0x3508e5abd151f164",
          "place_url": "https://www.google.com/maps/place/?q=place_id:ChIJ7xUEwQvJ5zsRZPFR0avlCDU",
          "project_count": 1,
          "rating": null,
          "review_count": null,
          "updated_at": "2026-09-29 20:36:39"
        },
        "place_id": 25,
        "place_key": "place:0x3be7c90bc10415ef:0x3508e5abd151f164",
        "post_count": 1,
        "posts_collected": 1,
        "project_id": 7,
        "rating": 4.6,
        "rating_distribution": "{\"5\": 125, \"4\": 25, \"3\": 8, \"2\": 2, \"1\": 6}",
        "review_count": 166,
        "shared_with_projects": 0,
        "status": "active"
      },
      {
        "added_at": "2026-09-29 15:06:44",
        "address": "Pali Hill, Bandra West, Mumbai",
        "business_key": "the coffee bean tea leaf",
        "category": "International Cafe Chain",
        "gmap_url": "https://www.google.com/maps/search/?api=1&query=The+Coffee+Bean+%26+Tea+Leaf+Pali+Hill+Bandra",
        "id": 23,
        "identity_source": "name_address",
        "last_scrape_status": "2026-10-04 15:15:06.110268",
        "last_scraped": "2026-09-29 15:24:11",
        "name": "The Coffee Bean & Tea Leaf",
        "place": {
          "address": "Pali Hill, Bandra West, Mumbai",
          "category": "International Cafe Chain",
          "cid": null,
          "competitor_count": 1,
          "confidence": 1,
          "created_at": "2026-09-29 15:06:44",
          "google_place_id": null,
          "hex_id": null,
          "id": 28,
          "identity_label": "addr:the coffee bean tea leaf|pali hill bandra west mumbai",
          "identity_source": "name_address",
          "kgmid": null,
          "latitude": null,
          "longitude": null,
          "name": "The Coffee Bean & Tea Leaf",
          "place_key": "addr:the coffee bean tea leaf|pali hill bandra west mumbai",
          "place_url": "https://www.google.com/maps/search/?api=1&query=The%20Coffee%20Bean%20%26%20Tea%20Leaf%20Pali%20Hill%2C%20Bandra%20West%2C%20Mumbai",
          "project_count": 1,
          "rating": null,
          "review_count": null,
          "updated_at": "2026-09-29 20:36:44"
        },
        "place_id": 28,
        "place_key": "addr:the coffee bean tea leaf|pali hill bandra west mumbai",
        "post_count": 0,
        "posts_collected": 0,
        "project_id": 7,
        "rating": null,
        "rating_distribution": null,
        "review_count": null,
        "shared_with_projects": 0,
        "status": "active"
      },
      {
        "added_at": "2026-09-29 15:06:46",
        "address": "Hill Road, Bandra West, Mumbai",
        "business_key": "brew bloom",
        "category": "Local Cafe / Bakery",
        "gmap_url": "https://www.google.com/maps/search/?api=1&query=Brew+and+Bloom+Bandra+West",
        "id": 24,
        "identity_source": "name_address",
        "last_scrape_status": "2026-10-04 15:15:06.110268",
        "last_scraped": "2026-09-29 15:24:43",
        "name": "Brew & Bloom",
        "place": {
          "address": "Hill Road, Bandra West, Mumbai",
          "category": "Local Cafe / Bakery",
          "cid": null,
          "competitor_count": 1,
          "confidence": 1,
          "created_at": "2026-09-29 15:06:45",
          "google_place_id": null,
          "hex_id": null,
          "id": 29,
          "identity_label": "addr:brew bloom|hill road bandra west mumbai",
          "identity_source": "name_address",
          "kgmid": null,
          "latitude": null,
          "longitude": null,
          "name": "Brew & Bloom",
          "place_key": "addr:brew bloom|hill road bandra west mumbai",
          "place_url": "https://www.google.com/maps/search/?api=1&query=Brew%20%26%20Bloom%20Hill%20Road%2C%20Bandra%20West%2C%20Mumbai",
          "project_count": 1,
          "rating": null,
          "review_count": null,
          "updated_at": "2026-09-29 20:36:45"
        },
        "place_id": 29,
        "place_key": "addr:brew bloom|hill road bandra west mumbai",
        "post_count": 0,
        "posts_collected": 0,
        "project_id": 7,
        "rating": null,
        "rating_distribution": null,
        "review_count": null,
        "shared_with_projects": 0,
        "status": "active"
      },
      {
        "added_at": "2026-09-29 15:06:46",
        "address": "Linking Road, Bandra West, Mumbai",
        "business_key": "theobroma",
        "category": "Cafe / Chocolate Specialist",
        "gmap_url": "https://www.google.com/maps/search/?api=1&query=Theobroma+Cafe+Bandra",
        "id": 25,
        "identity_source": "name_address",
        "last_scrape_status": "2026-10-04 15:15:06.110268",
        "last_scraped": "2026-09-29 15:25:23",
        "name": "Theobroma",
        "place": {
          "address": "Linking Road, Bandra West, Mumbai",
          "category": "Cafe / Chocolate Specialist",
          "cid": null,
          "competitor_count": 1,
          "confidence": 1,
          "created_at": "2026-09-29 15:06:46",
          "google_place_id": null,
          "hex_id": null,
          "id": 30,
          "identity_label": "addr:theobroma|linking road bandra west mumbai",
          "identity_source": "name_address",
          "kgmid": null,
          "latitude": null,
          "longitude": null,
          "name": "Theobroma",
          "place_key": "addr:theobroma|linking road bandra west mumbai",
          "place_url": "https://www.google.com/maps/search/?api=1&query=Theobroma%20Linking%20Road%2C%20Bandra%20West%2C%20Mumbai",
          "project_count": 1,
          "rating": null,
          "review_count": null,
          "updated_at": "2026-09-29 20:36:46"
        },
        "place_id": 30,
        "place_key": "addr:theobroma|linking road bandra west mumbai",
        "post_count": 0,
        "posts_collected": 0,
        "project_id": 7,
        "rating": null,
        "rating_distribution": null,
        "review_count": null,
        "shared_with_projects": 0,
        "status": "active"
      },
      {
        "added_at": "2026-09-29 21:15:30",
        "address": null,
        "business_key": "the bluebop cafe",
        "category": null,
        "gmap_url": "https://www.google.com/maps/place/The+Bluebop+Cafe/data=!4m7!3m6!1s0x3be7c95021a04b5f:0x1e122adaa621ca8c!8m2!3d19.0726389!4d72.8343718!16s%2Fg%2F11h7sw_v2_!19sChIJX0ugIVDJ5zsRjMohptoqEh4?authuser=0&hl=en&g_ep=EgoyMDI2MDkyNy4xIJJjKgBIAVAD&rclk=1",
        "id": 32,
        "identity_source": "hex_id",
        "last_scrape_status": "2026-10-04 15:15:06.110268",
        "last_scraped": null,
        "name": "The Bluebop Cafe",
        "place": {
          "address": null,
          "category": null,
          "cid": "2166841489297099404",
          "competitor_count": 1,
          "confidence": 3,
          "created_at": "2026-09-29 21:15:30",
          "google_place_id": "ChIJX0ugIVDJ5zsRjMohptoqEh4",
          "hex_id": "0x3be7c95021a04b5f:0x1e122adaa621ca8c",
          "id": 38,
          "identity_label": "ChIJX0ugIVDJ5zsRjMohptoqEh4",
          "identity_source": "hex_id",
          "kgmid": "/g/11h7sw_v2_",
          "latitude": 19.0726389,
          "longitude": 72.8343718,
          "name": "The Bluebop Cafe",
          "place_key": "place:0x3be7c95021a04b5f:0x1e122adaa621ca8c",
          "place_url": "https://www.google.com/maps/place/?q=place_id:ChIJX0ugIVDJ5zsRjMohptoqEh4",
          "project_count": 1,
          "rating": null,
          "review_count": null,
          "updated_at": "2026-09-30 02:45:30"
        },
        "place_id": 38,
        "place_key": "place:0x3be7c95021a04b5f:0x1e122adaa621ca8c",
        "post_count": 0,
        "posts_collected": 0,
        "project_id": 7,
        "rating": null,
        "rating_distribution": null,
        "review_count": null,
        "shared_with_projects": 0,
        "status": "active"
      },
      {
        "added_at": "2026-09-30 10:36:25",
        "address": "Shop No 6, 29, New Kantwadi Rd, off Perry Cross Road",
        "business_key": "boojee cafe",
        "category": "Cafe",
        "gmap_url": "https://www.google.com/maps/place/Boojee+Cafe/data=!4m7!3m6!1s0x3be7c950382c58a5:0x31ebdefaca4c2e32!8m2!3d19.0606827!4d72.824591!16s%2Fg%2F11hzhfyyzf!19sChIJpVgsOFDJ5zsRMi5Myvre6zE?authuser=0&hl=en&g_ep=EgoyMDI2MDkyNy4xIJJjKgBIAVAD&rclk=1",
        "id": 33,
        "identity_source": "hex_id",
        "last_scrape_status": "2026-10-04 15:15:06.110268",
        "last_scraped": null,
        "name": "Boojee Cafe",
        "place": {
          "address": "Shop No 6, 29, New Kantwadi Rd, off Perry Cross Road",
          "category": "Cafe",
          "cid": "3597213896102653490",
          "competitor_count": 1,
          "confidence": 3,
          "created_at": "2026-09-30 10:36:24",
          "google_place_id": "ChIJpVgsOFDJ5zsRMi5Myvre6zE",
          "hex_id": "0x3be7c950382c58a5:0x31ebdefaca4c2e32",
          "id": 40,
          "identity_label": "ChIJpVgsOFDJ5zsRMi5Myvre6zE",
          "identity_source": "hex_id",
          "kgmid": "/g/11hzhfyyzf",
          "latitude": 19.0606827,
          "longitude": 72.824591,
          "name": "Boojee Cafe",
          "place_key": "place:0x3be7c950382c58a5:0x31ebdefaca4c2e32",
          "place_url": "https://www.google.com/maps/place/?q=place_id:ChIJpVgsOFDJ5zsRMi5Myvre6zE",
          "project_count": 1,
          "rating": null,
          "review_count": null,
          "updated_at": "2026-09-30 10:36:24"
        },
        "place_id": 40,
        "place_key": "place:0x3be7c950382c58a5:0x31ebdefaca4c2e32",
        "post_count": 0,
        "posts_collected": 0,
        "project_id": 7,
        "rating": null,
        "rating_distribution": null,
        "review_count": null,
        "shared_with_projects": 0,
        "status": "active"
      },
      {
        "added_at": "2026-09-30 10:36:34",
        "address": "Shop no.1, Natalwala Bungalow, 41, B.J. Rd",
        "business_key": "grounded cafe",
        "category": "Cafe",
        "gmap_url": "https://www.google.com/maps/place/Grounded+Cafe/data=!4m7!3m6!1s0x3be7c95022672f03:0xa6ac6c0757efe70f!8m2!3d19.0477868!4d72.8208858!16s%2Fg%2F11sd51gfbl!19sChIJAy9nIlDJ5zsRD-fvVwdsrKY?authuser=0&hl=en&g_ep=EgoyMDI2MDkyNy4xIJJjKgBIAVAD&rclk=1",
        "id": 34,
        "identity_source": "hex_id",
        "last_scrape_status": "2026-10-04 15:15:06.110268",
        "last_scraped": null,
        "name": "Grounded Cafe",
        "place": {
          "address": "Shop no.1, Natalwala Bungalow, 41, B.J. Rd",
          "category": "Cafe",
          "cid": "12010093085086181135",
          "competitor_count": 1,
          "confidence": 3,
          "created_at": "2026-09-30 10:36:34",
          "google_place_id": "ChIJAy9nIlDJ5zsRD-fvVwdsrKY",
          "hex_id": "0x3be7c95022672f03:0xa6ac6c0757efe70f",
          "id": 41,
          "identity_label": "ChIJAy9nIlDJ5zsRD-fvVwdsrKY",
          "identity_source": "hex_id",
          "kgmid": "/g/11sd51gfbl",
          "latitude": 19.0477868,
          "longitude": 72.8208858,
          "name": "Grounded Cafe",
          "place_key": "place:0x3be7c95022672f03:0xa6ac6c0757efe70f",
          "place_url": "https://www.google.com/maps/place/?q=place_id:ChIJAy9nIlDJ5zsRD-fvVwdsrKY",
          "project_count": 1,
          "rating": null,
          "review_count": null,
          "updated_at": "2026-09-30 10:36:33"
        },
        "place_id": 41,
        "place_key": "place:0x3be7c95022672f03:0xa6ac6c0757efe70f",
        "post_count": 0,
        "posts_collected": 0,
        "project_id": 7,
        "rating": null,
        "rating_distribution": null,
        "review_count": null,
        "shared_with_projects": 0,
        "status": "active"
      },
      {
        "added_at": "2026-09-30 10:36:36",
        "address": "Durga Chambers, Waterfield Road, above Pernia's Pop Up MEN",
        "business_key": "earth cafe waterfield",
        "category": "Cafe",
        "gmap_url": "https://www.google.com/maps/place/Earth+Cafe+@+Waterfield/data=!4m7!3m6!1s0x3be7c9be9b3857c9:0x69f91c41e32b5181!8m2!3d19.0590714!4d72.834038!16s%2Fg%2F11fj7mg427!19sChIJyVc4m77J5zsRgVEr40Ec-Wk?authuser=0&hl=en&g_ep=EgoyMDI2MDkyNy4xIJJjKgBIAVAD&rclk=1",
        "id": 35,
        "identity_source": "hex_id",
        "last_scrape_status": "2026-10-04 15:15:06.110268",
        "last_scraped": null,
        "name": "Earth Cafe @ Waterfield",
        "place": {
          "address": "Durga Chambers, Waterfield Road, above Pernia's Pop Up MEN",
          "category": "Cafe",
          "cid": "7636165712493105537",
          "competitor_count": 1,
          "confidence": 3,
          "created_at": "2026-09-30 10:36:36",
          "google_place_id": "ChIJyVc4m77J5zsRgVEr40Ec-Wk",
          "hex_id": "0x3be7c9be9b3857c9:0x69f91c41e32b5181",
          "id": 42,
          "identity_label": "ChIJyVc4m77J5zsRgVEr40Ec-Wk",
          "identity_source": "hex_id",
          "kgmid": "/g/11fj7mg427",
          "latitude": 19.0590714,
          "longitude": 72.834038,
          "name": "Earth Cafe @ Waterfield",
          "place_key": "place:0x3be7c9be9b3857c9:0x69f91c41e32b5181",
          "place_url": "https://www.google.com/maps/place/?q=place_id:ChIJyVc4m77J5zsRgVEr40Ec-Wk",
          "project_count": 1,
          "rating": null,
          "review_count": null,
          "updated_at": "2026-09-30 10:36:35"
        },
        "place_id": 42,
        "place_key": "place:0x3be7c9be9b3857c9:0x69f91c41e32b5181",
        "post_count": 0,
        "posts_collected": 0,
        "project_id": 7,
        "rating": null,
        "rating_distribution": null,
        "review_count": null,
        "shared_with_projects": 0,
        "status": "active"
      },
      {
        "added_at": "2026-10-04 15:14:32",
        "address": "Shop No. 1, Hardik Villa, Sherly Rajan Rd, next to Rizvi Collage, Rizvi Complex, Chuim, Bandra West, Mumbai, Maharashtra 400050, India",
        "business_key": "the good stuff bandra",
        "category": null,
        "gmap_url": "https://www.google.com/maps/place/The+Good+Stuff+%7C+Bandra/data=!4m7!3m6!1s0x3be7c900326aa277:0x811f92c4d3116811!8m2!3d19.067332!4d72.82518!16s%2Fg%2F11wxgr3lql!19sChIJd6JqMgDJ5zsREWgR08SSH4E?authuser=0&hl=en&g_ep=EgoyMDI2MDkzMC4wIJJjKgBIAVAD&rclk=1",
        "id": 47,
        "identity_source": "hex_id",
        "last_scrape_status": "2026-10-04 15:15:06.110268",
        "last_scraped": "2026-10-04 15:16:31",
        "name": "The Good Stuff | Bandra",
        "place": {
          "address": null,
          "category": null,
          "cid": "9304316729223112721",
          "competitor_count": 1,
          "confidence": 3,
          "created_at": "2026-10-04 15:14:32",
          "google_place_id": "ChIJd6JqMgDJ5zsREWgR08SSH4E",
          "hex_id": "0x3be7c900326aa277:0x811f92c4d3116811",
          "id": 57,
          "identity_label": "ChIJd6JqMgDJ5zsREWgR08SSH4E",
          "identity_source": "hex_id",
          "kgmid": "/g/11wxgr3lql",
          "latitude": 19.067332,
          "longitude": 72.82518,
          "name": "The Good Stuff | Bandra",
          "place_key": "place:0x3be7c900326aa277:0x811f92c4d3116811",
          "place_url": "https://www.google.com/maps/place/?q=place_id:ChIJd6JqMgDJ5zsREWgR08SSH4E",
          "project_count": 1,
          "rating": null,
          "review_count": null,
          "updated_at": "2026-10-04 15:14:31"
        },
        "place_id": 57,
        "place_key": "place:0x3be7c900326aa277:0x811f92c4d3116811",
        "post_count": 0,
        "posts_collected": 0,
        "project_id": 7,
        "rating": 4.9,
        "rating_distribution": null,
        "review_count": null,
        "shared_with_projects": 0,
        "status": "active"
      }
    ],
    "posts": [
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/Blue+Tokai+Coffee+Roasters+%7C+Bandra/data=!4m7!3m6!1s0x3be7c96bae4baaab:0x27f9cc1563722ef4!8m2!3d19.0603995!4d72.8243282!16s%2Fg%2F11g8t_v0r1!19sChIJq6pLrmvJ5zsR9C5yYxXM-Sc?authuser=0&hl=en&g_ep=EgoyMDI2MDkyMy4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 26,
        "competitor_name": "Blue Tokai Coffee Roasters | Bandra",
        "content_hash": "99708ae6a258f6606df7819122a2882af65648ed4e9ba971aeaa9301a8a8c53a",
        "cta": null,
        "detected_keywords": [
          "coffee"
        ],
        "detected_topic": "Coffee & Beverages",
        "id": 23,
        "image_urls": [],
        "is_own_profile": false,
        "is_public": false,
        "post_source": "owner",
        "post_url": "https://search.google.com/local/posts?q=Blue+Tokai+Coffee+Roasters+%7C+Bandra&ludocid=2880557828914949876&lpsid=CIHM0ogKEMLLlqjqhvHPrAE&source=sh/x/loc/post&lsig=AB86z5X14MbgXQl3FxuUwJYlaFda",
        "published_date": "2026-09-29T15:42:06.722145",
        "raw_data": {
          "post_source": "owner"
        },
        "scrape_date": "2026-09-29 15:12:43",
        "text_content": "Wherever the day takes you, take good coffee with you. 🕺\n\n#bluetokaieasypour #specialtycoffee #coffeeonthego"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/Blue+Tokai+Coffee+Roasters+%7C+Bandra/data=!4m7!3m6!1s0x3be7c96bae4baaab:0x27f9cc1563722ef4!8m2!3d19.0603995!4d72.8243282!16s%2Fg%2F11g8t_v0r1!19sChIJq6pLrmvJ5zsR9C5yYxXM-Sc?authuser=0&hl=en&g_ep=EgoyMDI2MDkyMy4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 26,
        "competitor_name": "Blue Tokai Coffee Roasters | Bandra",
        "content_hash": "3e6b7ad077ee71c8c9a7a8ae862fd9f52501d5f6d67c297aec62bf80f1fbe0c5",
        "cta": null,
        "detected_keywords": [],
        "detected_topic": "General Update",
        "id": 24,
        "image_urls": [
          "https://lh3.googleusercontent.com/geougc/AF1QipM71fBpYxKfijlu1WfmSkp6zuGGHlfmX7PBgCmv=h400-no"
        ],
        "is_own_profile": false,
        "is_public": false,
        "post_source": "owner",
        "post_url": "https://search.google.com/local/posts?q=Blue+Tokai+Coffee+Roasters+%7C+Bandra&ludocid=2880557828914949876&lpsid=CIHM0ogKEPjx-8-y3Z_iDw&source=sh/x/loc/post&lsig=AB86z5X14MbgXQl3FxuUwJYlaFda",
        "published_date": "2026-09-29T08:42:08.463490",
        "raw_data": {
          "post_source": "owner"
        },
        "scrape_date": "2026-09-29 15:12:43",
        "text_content": "Swipe to peel back the layers and see what it takes to get to the heart of your cup. ☕\n\n#bluetokaicoffeeeducation #coffeecherryanatomy #coffeecherry #specialtycoffee #allaboutcoffee"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/Blue+Tokai+Coffee+Roasters+%7C+Bandra/data=!4m7!3m6!1s0x3be7c96bae4baaab:0x27f9cc1563722ef4!8m2!3d19.0603995!4d72.8243282!16s%2Fg%2F11g8t_v0r1!19sChIJq6pLrmvJ5zsR9C5yYxXM-Sc?authuser=0&hl=en&g_ep=EgoyMDI2MDkyMy4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 26,
        "competitor_name": "Blue Tokai Coffee Roasters | Bandra",
        "content_hash": "ec3520a53f923566cbc15eb09c740e75ef6340d265f35e6ec1e8475c03ecca2a",
        "cta": null,
        "detected_keywords": [],
        "detected_topic": "General Update",
        "id": 25,
        "image_urls": [
          "https://lh3.googleusercontent.com/geougc/AF1QipPtkTWQaolGh4W1RjWQU7f07qjQxAyKsZwOxdQI=h400-no"
        ],
        "is_own_profile": false,
        "is_public": false,
        "post_source": "owner",
        "post_url": "https://search.google.com/local/posts?q=Blue+Tokai+Coffee+Roasters+%7C+Bandra&ludocid=2880557828914949876&lpsid=CIHM0ogKEMfrn_LVtP3LLw&source=sh/x/loc/post&lsig=AB86z5X14MbgXQl3FxuUwJYlaFda",
        "published_date": "2026-09-23T20:42:10.147986",
        "raw_data": {
          "post_source": "owner"
        },
        "scrape_date": "2026-09-29 15:12:43",
        "text_content": "You know that one brewing tip you’ve heard a hundred times but still swear by? 👀\n\nDrop yours below. ☕\n\n#bluetokaibrews #brewingtips #peopleofbluetokai #coffeecommunity"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/Blue+Tokai+Coffee+Roasters+%7C+Bandra/data=!4m7!3m6!1s0x3be7c96bae4baaab:0x27f9cc1563722ef4!8m2!3d19.0603995!4d72.8243282!16s%2Fg%2F11g8t_v0r1!19sChIJq6pLrmvJ5zsR9C5yYxXM-Sc?authuser=0&hl=en&g_ep=EgoyMDI2MDkyMy4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 26,
        "competitor_name": "Blue Tokai Coffee Roasters | Bandra",
        "content_hash": "a7951b279b444fa626643b5557a01ad62802eb1cea4c724229eda48ab6004484",
        "cta": null,
        "detected_keywords": [],
        "detected_topic": "General Update",
        "id": 26,
        "image_urls": [
          "https://lh3.googleusercontent.com/geougc/AF1QipNK0-ZMho1cbBKRkk-4tPscvTeTBMKrr0tqZwpX=h400-no"
        ],
        "is_own_profile": false,
        "is_public": false,
        "post_source": "owner",
        "post_url": "https://search.google.com/local/posts?q=Blue+Tokai+Coffee+Roasters+%7C+Bandra&ludocid=2880557828914949876&lpsid=CIHM0ogKEMiwu7GN8e_xkAE&source=sh/x/loc/post&lsig=AB86z5X14MbgXQl3FxuUwJYlaFda",
        "published_date": "2026-09-22T20:42:11.365189",
        "raw_data": {
          "post_source": "owner"
        },
        "scrape_date": "2026-09-29 15:12:43",
        "text_content": "Little things happening around our cafés that make us stop and notice. 🪄\n\n#peopleofbluetokai #bluetokaimoments #littlethingsinlife #momentsaroundcoffee #trial"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/Blue+Tokai+Coffee+Roasters+%7C+Bandra/data=!4m7!3m6!1s0x3be7c96bae4baaab:0x27f9cc1563722ef4!8m2!3d19.0603995!4d72.8243282!16s%2Fg%2F11g8t_v0r1!19sChIJq6pLrmvJ5zsR9C5yYxXM-Sc?authuser=0&hl=en&g_ep=EgoyMDI2MDkyMy4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 26,
        "competitor_name": "Blue Tokai Coffee Roasters | Bandra",
        "content_hash": "16d0db7c759a56c530305ea105abbefc707bb0da7796c963ce2e6d36a2f29152",
        "cta": null,
        "detected_keywords": [],
        "detected_topic": "General Update",
        "id": 27,
        "image_urls": [
          "https://lh3.googleusercontent.com/geougc/AF1QipOeqihdGllAhmxQHZGc8urcB_Z1uiD9xcM2qy8-=h400-no"
        ],
        "is_own_profile": false,
        "is_public": false,
        "post_source": "owner",
        "post_url": "https://search.google.com/local/posts?q=Blue+Tokai+Coffee+Roasters+%7C+Bandra&ludocid=2880557828914949876&lpsid=CIHM0ogKEM6Xo6qQ5qHKDQ&source=sh/x/loc/post&lsig=AB86z5X14MbgXQl3FxuUwJYlaFda",
        "published_date": "2026-09-22T00:00:00",
        "raw_data": {
          "post_source": "owner"
        },
        "scrape_date": "2026-09-29 15:12:43",
        "text_content": "Little things happening around our cafés that make us stop and notice. 🪄\n\n#peopleofbluetokai #bluetokaimoments #littlethingsinlife #momentsaroundcoffee #bluetokaicommunity"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/Blue+Tokai+Coffee+Roasters+%7C+Bandra/data=!4m7!3m6!1s0x3be7c96bae4baaab:0x27f9cc1563722ef4!8m2!3d19.0603995!4d72.8243282!16s%2Fg%2F11g8t_v0r1!19sChIJq6pLrmvJ5zsR9C5yYxXM-Sc?authuser=0&hl=en&g_ep=EgoyMDI2MDkyMy4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 26,
        "competitor_name": "Blue Tokai Coffee Roasters | Bandra",
        "content_hash": "8f103bfa98c48d9084a66582b1bf5636b1816ccad51b4ef12a7143118e5585db",
        "cta": null,
        "detected_keywords": [],
        "detected_topic": "General Update",
        "id": 28,
        "image_urls": [],
        "is_own_profile": false,
        "is_public": false,
        "post_source": "owner",
        "post_url": "https://search.google.com/local/posts?q=Blue+Tokai+Coffee+Roasters+%7C+Bandra&ludocid=2880557828914949876&lpsid=CIHM0ogKEMf-696o6sudZg&source=sh/x/loc/post&lsig=AB86z5X14MbgXQl3FxuUwJYlaFda",
        "published_date": "2026-09-21T00:00:00",
        "raw_data": {
          "post_source": "owner"
        },
        "scrape_date": "2026-09-29 15:12:43",
        "text_content": "Our latest BT hotlist ☕️\n\nWhat are some of your favourites? ✍️\n\n#bluetokaihotlist #bluetokaibrews #whattoorderatbt #recentfavsatbluetokai #caferecommendations"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/Blue+Tokai+Coffee+Roasters+%7C+Bandra/data=!4m7!3m6!1s0x3be7c96bae4baaab:0x27f9cc1563722ef4!8m2!3d19.0603995!4d72.8243282!16s%2Fg%2F11g8t_v0r1!19sChIJq6pLrmvJ5zsR9C5yYxXM-Sc?authuser=0&hl=en&g_ep=EgoyMDI2MDkyMy4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 26,
        "competitor_name": "Blue Tokai Coffee Roasters | Bandra",
        "content_hash": "fa798ae954ab9bfb0745ed99648d2c5ff9c61777b51315cbef089d2d33e75272",
        "cta": null,
        "detected_keywords": [
          "coffee"
        ],
        "detected_topic": "Coffee & Beverages",
        "id": 29,
        "image_urls": [
          "https://lh3.googleusercontent.com/geougc/AF1QipMUCZTE9xKx6VCWKWBU_hQhqOkFg4pjizeLZZZK=h400-no"
        ],
        "is_own_profile": false,
        "is_public": false,
        "post_source": "owner",
        "post_url": "https://search.google.com/local/posts?q=Blue+Tokai+Coffee+Roasters+%7C+Bandra&ludocid=2880557828914949876&lpsid=CIHM0ogKEMrQ7NaEqtuuJg&source=sh/x/loc/post&lsig=AB86z5X14MbgXQl3FxuUwJYlaFda",
        "published_date": "2026-09-20T00:00:00",
        "raw_data": {
          "post_source": "owner"
        },
        "scrape_date": "2026-09-29 15:12:43",
        "text_content": "There’s always more to a coffee run. 🎉\n\nAnd if there’s a barista who makes yours a little better, give them a shoutout in the comments below. 💙\n\n#bluetokaibrews #baristasofbluetokai #peopleofbluetokai #coffeerun"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/Blue+Tokai+Coffee+Roasters+%7C+Bandra/data=!4m7!3m6!1s0x3be7c96bae4baaab:0x27f9cc1563722ef4!8m2!3d19.0603995!4d72.8243282!16s%2Fg%2F11g8t_v0r1!19sChIJq6pLrmvJ5zsR9C5yYxXM-Sc?authuser=0&hl=en&g_ep=EgoyMDI2MDkyMy4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 26,
        "competitor_name": "Blue Tokai Coffee Roasters | Bandra",
        "content_hash": "daafde0ef3385b0b7daba0beb7476bb5022bf0dfacf35e3ae640d292ca13d5ca",
        "cta": null,
        "detected_keywords": [
          "latte",
          "mocha"
        ],
        "detected_topic": "Coffee & Beverages",
        "id": 30,
        "image_urls": [
          "https://lh3.googleusercontent.com/geougc/AF1QipNPJGhpH4QderyTk-Pfe_lFPOBVPFs_KSEuzi3M=h400-no"
        ],
        "is_own_profile": false,
        "is_public": false,
        "post_source": "owner",
        "post_url": "https://search.google.com/local/posts?q=Blue+Tokai+Coffee+Roasters+%7C+Bandra&ludocid=2880557828914949876&lpsid=CIHM0ogKEI670Zav3JzEtAE&source=sh/x/loc/post&lsig=AB86z5X14MbgXQl3FxuUwJYlaFda",
        "published_date": "2026-09-19T00:00:00",
        "raw_data": {
          "post_source": "owner"
        },
        "scrape_date": "2026-09-29 15:12:43",
        "text_content": "Protein up your routine. 💪☕️\n\nAll our regular sandwiches are now available on protein bread, with ≈11g of protein in 2 slices. Just ask our baristas to add this option if you’d like a higher protein meal. 💙 \n\nAnd in select cafés, make sure to try our Iced Sea Salt Protein Mocha and Protein Iced Latte, with 21g of protein each.\n\nPick your usual. Or switch it up. 👀\n\n#bluetokaiproteinmenu #proteinupyourroutine #proteinbreadsandwich #proteincoffee"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/Blue+Tokai+Coffee+Roasters+%7C+Bandra/data=!4m7!3m6!1s0x3be7c96bae4baaab:0x27f9cc1563722ef4!8m2!3d19.0603995!4d72.8243282!16s%2Fg%2F11g8t_v0r1!19sChIJq6pLrmvJ5zsR9C5yYxXM-Sc?authuser=0&hl=en&g_ep=EgoyMDI2MDkyMy4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 26,
        "competitor_name": "Blue Tokai Coffee Roasters | Bandra",
        "content_hash": "fc351129f465c2bf10da61c0ecb058e0ce97972632c2aca8883784dd3dc17610",
        "cta": null,
        "detected_keywords": [
          "new"
        ],
        "detected_topic": "Updates & Announcements",
        "id": 31,
        "image_urls": [
          "https://lh3.googleusercontent.com/geougc/AF1QipMEIYf0eG02UGgfKj2Zq7TcTNfAXhrbyi6MnKQ3=h400-no"
        ],
        "is_own_profile": false,
        "is_public": false,
        "post_source": "owner",
        "post_url": "https://search.google.com/local/posts?q=Blue+Tokai+Coffee+Roasters+%7C+Bandra&ludocid=2880557828914949876&lpsid=CIHM0ogKEM2S3sKYg--ujAE&source=sh/x/loc/post&lsig=AB86z5X14MbgXQl3FxuUwJYlaFda",
        "published_date": "2026-09-15T00:00:00",
        "raw_data": {
          "post_source": "owner"
        },
        "scrape_date": "2026-09-29 15:12:43",
        "text_content": "This September, we’re turning the pages on stories rooted in history, bringing us closer to the people, places, and moments that shaped the world around us. 📚\n\nOur friends at Bahrisons in Delhi and Hyderabad, Pagdandi in Pune, Atta Galatta in Bengaluru, and Storyteller Bookstore in Kolkata are joining us with their picks for this month’s theme.\n\nEvery month, we’ll bring you more recommendations from our favourite independent bookstores, each around a new theme.\n\nReading along? Share your historic reads in the comments or tag us in your current reads with #BTBookClub 💙\n\n#bluetokaibookclub #bluetokaibookrecommendations #historicreads #septemberbookrecommendations"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/Blue+Tokai+Coffee+Roasters+%7C+Bandra/data=!4m7!3m6!1s0x3be7c96bae4baaab:0x27f9cc1563722ef4!8m2!3d19.0603995!4d72.8243282!16s%2Fg%2F11g8t_v0r1!19sChIJq6pLrmvJ5zsR9C5yYxXM-Sc?authuser=0&hl=en&g_ep=EgoyMDI2MDkyMy4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 26,
        "competitor_name": "Blue Tokai Coffee Roasters | Bandra",
        "content_hash": "ad0a58fa4aef072b29dc352fca28df4a5b399b704b2e891172830ad01a0793ed",
        "cta": null,
        "detected_keywords": [
          "coffee"
        ],
        "detected_topic": "Coffee & Beverages",
        "id": 32,
        "image_urls": [
          "https://lh3.googleusercontent.com/geougc/AF1QipM51kQhq5A0VXIAEMlKmARzGqW9QxWwwYWTsoL0=h400-no"
        ],
        "is_own_profile": false,
        "is_public": false,
        "post_source": "owner",
        "post_url": "https://search.google.com/local/posts?q=Blue+Tokai+Coffee+Roasters+%7C+Bandra&ludocid=2880557828914949876&lpsid=CIHM0ogKENzqlLCCw7DqzgE&source=sh/x/loc/post&lsig=AB86z5X14MbgXQl3FxuUwJYlaFda",
        "published_date": "2026-09-13T00:00:00",
        "raw_data": {
          "post_source": "owner"
        },
        "scrape_date": "2026-09-29 15:12:43",
        "text_content": "The monsoon leaves behind petrichor, and a little green everywhere. But once upon a time, it left behind a new way to taste coffee. \n\nSwipe for the tale behind Monsoon Malabar.🌧️\n\n#bluetokaicoffee #monsoonmalabarcoffee #storiesofcoffee #specialtycoffee #monsoonseason"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/bru+baabaa+caf%C3%A9/data=!4m7!3m6!1s0x3be7c94a387288f9:0x9e1af733fa10373e!8m2!3d19.0615779!4d72.8334489!16s%2Fg%2F11y715fbnr!19sChIJ-YhyOErJ5zsRPjcQ-jP3Gp4?authuser=0&hl=en&g_ep=EgoyMDI2MDkyMy4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 27,
        "competitor_name": "bru baabaa café",
        "content_hash": "ce7b6ad97378cd6f5760f81aaa83482129ba484809c0ac26d27cf180535d14d2",
        "cta": null,
        "detected_keywords": [
          "frappe"
        ],
        "detected_topic": "Coffee & Beverages",
        "id": 33,
        "image_urls": [],
        "is_own_profile": false,
        "is_public": false,
        "post_source": "owner",
        "post_url": "https://search.google.com/local/posts?q=bru+baabaa+caf%C3%A9&ludocid=11392690009997850430&lpsid=CIHM0ogKEJfRnKHTmNb9sAE&source=sh/x/loc/post&lsig=AB86z5VBXyHIjz02j3ozRUwUmM_m",
        "published_date": "2026-09-08T00:00:00",
        "raw_data": {
          "post_source": "owner"
        },
        "scrape_date": "2026-09-29 15:13:39",
        "text_content": "This frappe may cause serious cravings. 🤤\n\nCreamy hazelnut, rich caramel, and icy perfection blended into one unforgettable sip. Your new favorite starts here. ✨"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/bru+baabaa+caf%C3%A9/data=!4m7!3m6!1s0x3be7c94a387288f9:0x9e1af733fa10373e!8m2!3d19.0615779!4d72.8334489!16s%2Fg%2F11y715fbnr!19sChIJ-YhyOErJ5zsRPjcQ-jP3Gp4?authuser=0&hl=en&g_ep=EgoyMDI2MDkyMy4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 27,
        "competitor_name": "bru baabaa café",
        "content_hash": "0bc6c8b9eb35f31cba2a7ff3fe0e47013116cac88a2095939e30225bc49a5d0f",
        "cta": null,
        "detected_keywords": [
          "coffee",
          "cold brew",
          "brew"
        ],
        "detected_topic": "Coffee & Beverages",
        "id": 34,
        "image_urls": [
          "https://lh3.googleusercontent.com/geougc/AF1QipNt1SZJ32e7t3JulvqgWH6RO1rmPkcuytJ2CRV0=h400-no"
        ],
        "is_own_profile": false,
        "is_public": false,
        "post_source": "owner",
        "post_url": "https://search.google.com/local/posts?q=bru+baabaa+caf%C3%A9&ludocid=11392690009997850430&lpsid=CIHM0ogKEPbMh7DZyNauQw&source=sh/x/loc/post&lsig=AB86z5VBXyHIjz02j3ozRUwUmM_m",
        "published_date": "2026-06-18T00:00:00",
        "raw_data": {
          "post_source": "owner"
        },
        "scrape_date": "2026-09-29 15:13:39",
        "text_content": "❄️ Cool. Refreshing. Naturally Bold. ☕️\n\nBeat the heat with Bru Baabaa's signature Cold Brews - crafted for coffee lovers who like their brew chilled and full of flavor.\n\n🍒 **Cranberry Cold Brew**\nA tart and refreshing blend that's light, vibrant, and invigorating.\n\n🍊 **Orange Cold Brew**\nA citrusy twist on your favorite cold brew with bright, zesty notes.\n\n🇻🇳 **Vietnamese Cold Brew**\nStrong, smooth, creamy, and perfectly satisfying with every sip.\n\nWhether you like fruity, citrusy, or rich and bold, there's a cold brew waiting for you.\n\n📍 Visit Bru Baabaa Café and discover your perfect chill.\n\n#BruBaabaa #ColdBrew #CranberryColdBrew #OrangeColdBrew #VietnameseColdBrew #CoffeeLovers #IcedCoffee #CafeLife #MumbaiFoodies #BandraCafe #SpecialtyCoffee #SummerDrinks #BruBaabaaCafe"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/bru+baabaa+caf%C3%A9/data=!4m7!3m6!1s0x3be7c94a387288f9:0x9e1af733fa10373e!8m2!3d19.0615779!4d72.8334489!16s%2Fg%2F11y715fbnr!19sChIJ-YhyOErJ5zsRPjcQ-jP3Gp4?authuser=0&hl=en&g_ep=EgoyMDI2MDkyMy4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 27,
        "competitor_name": "bru baabaa café",
        "content_hash": "05119a410dfcd37b6e94cf80d68c88b0870ff85dd4c8e01cce6123c6629cdba4",
        "cta": null,
        "detected_keywords": [
          "mocha",
          "frappe"
        ],
        "detected_topic": "Coffee & Beverages",
        "id": 35,
        "image_urls": [
          "https://lh3.googleusercontent.com/geougc/AF1QipMvdWAM2-lQkI3QruyAUMIVqeo2HXJs_I1ttkXE=h400-no"
        ],
        "is_own_profile": false,
        "is_public": false,
        "post_source": "owner",
        "post_url": "https://search.google.com/local/posts?q=bru+baabaa+caf%C3%A9&ludocid=11392690009997850430&lpsid=CIHM0ogKEIzBnr61jpi_Gg&source=sh/x/loc/post&lsig=AB86z5VBXyHIjz02j3ozRUwUmM_m",
        "published_date": "2026-06-18T00:00:00",
        "raw_data": {
          "post_source": "owner"
        },
        "scrape_date": "2026-09-29 15:13:39",
        "text_content": "✨ Frappe Goals, Served Fresh! ✨\n\nCool, creamy, and blended to perfection - our signature frappés are made for every mood.\n\n🍫 **Nutella Mocha Frappé**\nRich hazelnut, chocolate indulgence, and pure happiness in every sip.\n\n🫐 **Blueberry Cheesecake Frappé**\nA creamy cheesecake blend swirled with juicy blueberries for the perfect sweet treat.\n\n🍊 **Tangerine Caramel Frappé**\nA refreshing fusion of citrusy tangerine and rich caramel delight.\n\nMade with premium ingredients, expertly blended, and crafted with love. ❤️\n\n📍 Visit Bru Baabaa Café and discover your new favorite frappé.\n\n#BruBaabaa #FrappeLovers #NutellaMochaFrappe #BlueberryCheesecakeFrappe #TangerineCaramelFrappe #CafeLife #CoffeeLovers #DessertDrinks #MumbaiFoodies #BandraCafe #SipSmileRepeat #BruBaabaaCafe"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/bru+baabaa+caf%C3%A9/data=!4m7!3m6!1s0x3be7c94a387288f9:0x9e1af733fa10373e!8m2!3d19.0615779!4d72.8334489!16s%2Fg%2F11y715fbnr!19sChIJ-YhyOErJ5zsRPjcQ-jP3Gp4?authuser=0&hl=en&g_ep=EgoyMDI2MDkyMy4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 27,
        "competitor_name": "bru baabaa café",
        "content_hash": "ef391f58b13f4fba997db733e130e556dd4cabe2234a7c84e5c76ba25eacbcf4",
        "cta": "Call now",
        "detected_keywords": [
          "shake"
        ],
        "detected_topic": "Coffee & Beverages",
        "id": 36,
        "image_urls": [
          "https://lh3.googleusercontent.com/geougc/AF1QipPwTS4XRgIv41zqouXe0O9P1Fs_mx0S7xbAC5v2=h400-no"
        ],
        "is_own_profile": false,
        "is_public": false,
        "post_source": "owner",
        "post_url": "https://search.google.com/local/posts?q=bru+baabaa+caf%C3%A9&ludocid=11392690009997850430&lpsid=CIHM0ogKEJOs-oWLnZ-8LQ&source=sh/x/loc/post&lsig=AB86z5VBXyHIjz02j3ozRUwUmM_m",
        "published_date": "2026-06-18T00:00:00",
        "raw_data": {
          "post_source": "owner"
        },
        "scrape_date": "2026-09-29 15:13:39",
        "text_content": "🥤 One Shake. Many Reasons to Love. \n\nLooking for the perfect blend of taste and nourishment?\n\n✨ Desi Protein Shake - Packed with wholesome protein to fuel your day.\n\n🥜 Dry Fruit Shake - Loaded with the goodness of premium dry fruits for strength and immunity.\n\n🍪 Biscoff Delight - Rich, creamy, and irresistibly indulgent in every sip.\n\nMade with premium ingredients and blended to perfection, our shakes are crafted to satisfy your cravings while keeping you energized.\n\n📍 Drop by Bru Baabaa and find your favorite shake today!\n\n#BruBaabaa #Shakes #DesiProteinShake #DryFruitShake #BiscoffDelight #HealthyDrinks #Milkshakes #CafeLife #BandraFoodies #MumbaiCafes #ProteinShake #FoodLovers #BruBaabaaCafe"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/bru+baabaa+caf%C3%A9/data=!4m7!3m6!1s0x3be7c94a387288f9:0x9e1af733fa10373e!8m2!3d19.0615779!4d72.8334489!16s%2Fg%2F11y715fbnr!19sChIJ-YhyOErJ5zsRPjcQ-jP3Gp4?authuser=0&hl=en&g_ep=EgoyMDI2MDkyMy4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 27,
        "competitor_name": "bru baabaa café",
        "content_hash": "ba3ce2c1f6ab8e1db019dd722c25c796780d48ab25e2b224f9d32a8e565ca366",
        "cta": "Call now",
        "detected_keywords": [
          "coffee"
        ],
        "detected_topic": "Coffee & Beverages",
        "id": 37,
        "image_urls": [
          "https://lh3.googleusercontent.com/geougc/AF1QipP1DLo9Dz96OVS0a7znGcf2iBrnRtEizz8EpXt9=h400-no"
        ],
        "is_own_profile": false,
        "is_public": false,
        "post_source": "owner",
        "post_url": "https://search.google.com/local/posts?q=bru+baabaa+caf%C3%A9&ludocid=11392690009997850430&lpsid=CIHM0ogKEJaN6t-n--WCdA&source=sh/x/loc/post&lsig=AB86z5VBXyHIjz02j3ozRUwUmM_m",
        "published_date": "2026-06-18T00:00:00",
        "raw_data": {
          "post_source": "owner"
        },
        "scrape_date": "2026-09-29 15:13:39",
        "text_content": "✨ Sip into something special at Bru Baabaa! ✨\n\nIntroducing our Signature Mocktails - crafted with care and made to refresh every moment.\n\n🫐Coffee Daiquiri - Bold coffee notes with a hint of citrus and natural sweetness.\n\n🥭 Mango Daiquiri - A tropical blend of juicy mangoes and zesty lime.\n\n🌶️ Picante - A vibrant mix of fresh herbs, lime, and a spicy kick.\n\nMade with fresh ingredients, no artificial flavors, and packed with refreshing goodness.\n\n📍 Visit Bru Baabaa and discover your new favorite sip.\n\n#BruBaabaa #SignatureMocktails #CoffeeDaiquiri #MangoDaiquiri #PicanteMocktail #Mocktails #CafeLife #RefreshingDrinks #CoffeeLovers #MangoSeason #FoodieKerala #CafeVibes"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/Four+Chairs+Cafe+%7C+Best+Cafe+Near+Hinduja+Hospital+Bandra/data=!4m7!3m6!1s0x3be7c9dd524ee9d5:0xc0762dd675bdb48e!8m2!3d19.0673844!4d72.8360308!16s%2Fg%2F11yx7y5z08!19sChIJ1elOUt3J5zsRjrS9ddYtdsA?authuser=0&hl=en&g_ep=EgoyMDI2MDkyMy4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 19,
        "competitor_name": "Four Chairs Cafe | Best Cafe Near Hinduja Hospital Bandra",
        "content_hash": "347c40f5a2a0a4a03a3eda11c415e24b3d2c451c883de2006d3c94c67500acb6",
        "cta": null,
        "detected_keywords": [
          "vibe",
          "cozy"
        ],
        "detected_topic": "Ambience & Decor",
        "id": 47,
        "image_urls": [],
        "is_own_profile": false,
        "is_public": false,
        "post_source": "owner",
        "post_url": null,
        "published_date": "2026-06-01T20:53:26.623878",
        "raw_data": {
          "post_source": "owner"
        },
        "scrape_date": "2026-09-29 15:23:38",
        "text_content": "Response from the owner 4 months agoThank you so much for the detailed review, Kanwal! We are thrilled to be your new Bandra hidden gem. It’s wonderful to hear you enjoyed the cozy vibe with our books, along with the smoky grilled cottage cheese, stuffed chicken, and karaage … More"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/Four+Chairs+Cafe+%7C+Best+Cafe+Near+Hinduja+Hospital+Bandra/data=!4m7!3m6!1s0x3be7c9dd524ee9d5:0xc0762dd675bdb48e!8m2!3d19.0673844!4d72.8360308!16s%2Fg%2F11yx7y5z08!19sChIJ1elOUt3J5zsRjrS9ddYtdsA?authuser=0&hl=en&g_ep=EgoyMDI2MDkyMy4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 19,
        "competitor_name": "Four Chairs Cafe | Best Cafe Near Hinduja Hospital Bandra",
        "content_hash": "032b1b605693f656f8a2522d1404474c850781d4bc5b639e9f66faefabfa9a0b",
        "cta": null,
        "detected_keywords": [
          "vibe",
          "cozy"
        ],
        "detected_topic": "Ambience & Decor",
        "id": 46,
        "image_urls": [],
        "is_own_profile": false,
        "is_public": false,
        "post_source": "owner",
        "post_url": null,
        "published_date": "2026-06-01T20:53:24.536451",
        "raw_data": {
          "post_source": "owner"
        },
        "scrape_date": "2026-09-29 15:23:38",
        "text_content": "4 months ago Found this café just 2 minutes from Linking Road and it genuinely feels like a hidden gem. … More0:01 +8Like Share Response from the owner 4 months agoThank you so much for the detailed review, Kanwal! We are thrilled to be your new Bandra hidden gem. It’s wonderful to hear you enjoyed the cozy vibe with our books, along with the smoky grilled cottage cheese, stuffed chicken, and karaage … More"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/Four+Chairs+Cafe+%7C+Best+Cafe+Near+Hinduja+Hospital+Bandra/data=!4m7!3m6!1s0x3be7c9dd524ee9d5:0xc0762dd675bdb48e!8m2!3d19.0673844!4d72.8360308!16s%2Fg%2F11yx7y5z08!19sChIJ1elOUt3J5zsRjrS9ddYtdsA?authuser=0&hl=en&g_ep=EgoyMDI2MDkyMy4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 19,
        "competitor_name": "Four Chairs Cafe | Best Cafe Near Hinduja Hospital Bandra",
        "content_hash": "20392bcdfbe2643e55d20a8e8f58a04d0819d3735493f51a14ad509e34adfa14",
        "cta": null,
        "detected_keywords": [
          "vibe",
          "cozy"
        ],
        "detected_topic": "Ambience & Decor",
        "id": 45,
        "image_urls": [
          "https://lh3.googleusercontent.com/a/ACg8ocIrS6p_DPB5rjpkPVtcKJF3o4yvUAVCsVu9KuHJTp7AXjcBuQ=w36-h36-p-rp-mo-ba12-br100"
        ],
        "is_own_profile": false,
        "is_public": false,
        "post_source": "owner",
        "post_url": null,
        "published_date": "2026-06-01T20:53:20.918963",
        "raw_data": {
          "post_source": "owner"
        },
        "scrape_date": "2026-09-29 15:23:38",
        "text_content": "Kanwal KhandwaniLocal Guide · 42 reviews · 235 photos4 months ago Found this café just 2 minutes from Linking Road and it genuinely feels like a hidden gem. … More0:01 +8Like Share Response from the owner 4 months agoThank you so much for the detailed review, Kanwal! We are thrilled to be your new Bandra hidden gem. It’s wonderful to hear you enjoyed the cozy vibe with our books, along with the smoky grilled cottage cheese, stuffed chicken, and karaage … More"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/bru+baabaa+caf%C3%A9/data=!4m7!3m6!1s0x3be7c94a387288f9:0x9e1af733fa10373e!8m2!3d19.0615779!4d72.8334489!16s%2Fg%2F11y715fbnr!19sChIJ-YhyOErJ5zsRPjcQ-jP3Gp4?authuser=0&hl=en&g_ep=EgoyMDI2MDkyMy4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 27,
        "competitor_name": "bru baabaa café",
        "content_hash": "0a8a51ba8ca3ac70ba1bd33382de0a4990b0384c12c3a82f8f66c0b43b17581f",
        "cta": "Call now",
        "detected_keywords": [
          "coffee",
          "latte",
          "mocha",
          "cocoa"
        ],
        "detected_topic": "Coffee & Beverages",
        "id": 38,
        "image_urls": [
          "https://lh3.googleusercontent.com/geougc/AF1QipNFIK_fWLDg-9tje7QRWzFbUxzBUi6Hvyjls5M4=h400-no"
        ],
        "is_own_profile": false,
        "is_public": false,
        "post_source": "owner",
        "post_url": "https://search.google.com/local/posts?q=bru+baabaa+caf%C3%A9&ludocid=11392690009997850430&lpsid=CIHM0ogKEJHCie-SxMmBogE&source=sh/x/loc/post&lsig=AB86z5VBXyHIjz02j3ozRUwUmM_m",
        "published_date": "2026-05-25T00:00:00",
        "raw_data": {
          "post_source": "owner"
        },
        "scrape_date": "2026-09-29 15:13:39",
        "text_content": "✨ New flavors, same cozy coffee experience at Bru Baabaa\nIndulge in our Signature Coffee Collection featuring:\n🍯 Honey Saffron Latte – smooth, aromatic & comforting\n🍫 Sea Salt Mocha – rich cocoa with a bold twist\n🍪 Biscoff Latte – creamy, velvety & irresistibly delicious\n\nCrafted to make every sip memorable. Which one are you trying first? 👀\n\n📍Visit bru baabaa today"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/bru+baabaa+caf%C3%A9/data=!4m7!3m6!1s0x3be7c94a387288f9:0x9e1af733fa10373e!8m2!3d19.0615779!4d72.8334489!16s%2Fg%2F11y715fbnr!19sChIJ-YhyOErJ5zsRPjcQ-jP3Gp4?authuser=0&hl=en&g_ep=EgoyMDI2MDkyMy4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 27,
        "competitor_name": "bru baabaa café",
        "content_hash": "4220ea4862ab7466a9fbea762ac6818975ba0e16e6f9b4a20cbd63f8c5002eb2",
        "cta": "Buy",
        "detected_keywords": [
          "latte",
          "matcha"
        ],
        "detected_topic": "Coffee & Beverages",
        "id": 39,
        "image_urls": [
          "https://lh3.googleusercontent.com/geougc/AF1QipNElXIcwD9GtvhgQoPQMX3T8CdQ9ZSu0WvDf9X9=h400-no"
        ],
        "is_own_profile": false,
        "is_public": false,
        "post_source": "owner",
        "post_url": "https://search.google.com/local/posts?q=bru+baabaa+caf%C3%A9&ludocid=11392690009997850430&lpsid=CIHM0ogKEMrD1ZGArYr1VA&source=sh/x/loc/post&lsig=AB86z5VBXyHIjz02j3ozRUwUmM_m",
        "published_date": "2026-05-25T00:00:00",
        "raw_data": {
          "post_source": "owner"
        },
        "scrape_date": "2026-09-29 15:13:39",
        "text_content": "💚 Matcha lovers, this one’s for you!\nDiscover our refreshing Matcha Selection at Bru Baabaa\n🥭 Mango Matcha – tropical & refreshing\n🍓 Strawberry Matcha – fruity & delightful\n🧊 Ice Matcha Latte – smooth & creamy\n\nMade with premium matcha and natural ingredients for the perfect refreshing sip.\n\n📍Drop by bru baabaa and find your favorite matcha mood.\n\n\n#BruBaabaa #MatchaSelection #MangoMatcha #StrawberryMatcha #IceMatchaLatte #MatchaLovers #CafeDrinks #RefreshingDrinks #CoffeeAndMatcha"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/bru+baabaa+caf%C3%A9/data=!4m7!3m6!1s0x3be7c94a387288f9:0x9e1af733fa10373e!8m2!3d19.0615779!4d72.8334489!16s%2Fg%2F11y715fbnr!19sChIJ-YhyOErJ5zsRPjcQ-jP3Gp4?authuser=0&hl=en&g_ep=EgoyMDI2MDkyMy4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 27,
        "competitor_name": "bru baabaa café",
        "content_hash": "ecc7e0226db8a57e92c38e647a91f3d115459b7df7cde8ae1e3c699386acc0fe",
        "cta": null,
        "detected_keywords": [
          "latte",
          "matcha"
        ],
        "detected_topic": "Coffee & Beverages",
        "id": 40,
        "image_urls": [
          "https://lh3.googleusercontent.com/geougc/AF1QipMHgtt2AdKTq53SG2QNYs-bjnBj2ikRAfWA8QgF=h400-no"
        ],
        "is_own_profile": false,
        "is_public": false,
        "post_source": "owner",
        "post_url": "https://search.google.com/local/posts?q=bru+baabaa+caf%C3%A9&ludocid=11392690009997850430&lpsid=CIHM0ogKENmPnKCVrb6QfQ&source=sh/x/loc/post&lsig=AB86z5VBXyHIjz02j3ozRUwUmM_m",
        "published_date": "2026-05-21T00:00:00",
        "raw_data": {
          "post_source": "owner"
        },
        "scrape_date": "2026-09-29 15:13:39",
        "text_content": "🍵 Matcha lovers, this one’s for you!\n\nExplore our refreshing Matcha Selection at Bru Baabaa Café 💚\n\n✨ Iced Matcha Latte\n🥭 Mango Matcha\n🍓 Strawberry Matcha\n\nPerfectly creamy, refreshing, and packed with flavour in every sip. Visit us and find your favourite matcha vibe today!\n\n#MatchaLovers #IcedMatcha #MangoMatcha #StrawberryMatcha #BruBaabaa #CafeDrinks #SpecialityCafe #MatchaTime"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/bru+baabaa+caf%C3%A9/data=!4m7!3m6!1s0x3be7c94a387288f9:0x9e1af733fa10373e!8m2!3d19.0615779!4d72.8334489!16s%2Fg%2F11y715fbnr!19sChIJ-YhyOErJ5zsRPjcQ-jP3Gp4?authuser=0&hl=en&g_ep=EgoyMDI2MDkyMy4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 27,
        "competitor_name": "bru baabaa café",
        "content_hash": "390722e3f2193cae54a406142e9916409f5b8418e2e2d0ec1118ed86370e0693",
        "cta": null,
        "detected_keywords": [
          "coffee",
          "cold coffee",
          "chai"
        ],
        "detected_topic": "Coffee & Beverages",
        "id": 41,
        "image_urls": [
          "https://lh3.googleusercontent.com/geougc/AF1QipOu04RKI_C0rxd-rrz70e3UgYDSCweJ2rvbMpdV=h400-no"
        ],
        "is_own_profile": false,
        "is_public": false,
        "post_source": "owner",
        "post_url": "https://search.google.com/local/posts?q=bru+baabaa+caf%C3%A9&ludocid=11392690009997850430&lpsid=CIHM0ogKEOuZ4Y2H_IapkgE&source=sh/x/loc/post&lsig=AB86z5VBXyHIjz02j3ozRUwUmM_m",
        "published_date": "2026-05-21T00:00:00",
        "raw_data": {
          "post_source": "owner"
        },
        "scrape_date": "2026-09-29 15:13:39",
        "text_content": "Enjoy your favorite Hot Coffee / Cold Coffee for just ₹99 + tax at Bru Baabaa Speciality Café\n\nAlso try our comforting Chai + Bun Maska combo - the perfect evening snack! 🫖🥯\n\nVisit us today and sip happiness with every cup. ❤️\n\n#BruBaabaa #SpecialityCoffee #CoffeeLovers #ColdCoffee #HotCoffee #ChaiTime #BunMaska #CafeOffers #CoffeeBreak"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/Four+Chairs+Cafe+%7C+Best+Cafe+Near+Hinduja+Hospital+Bandra/data=!4m7!3m6!1s0x3be7c9dd524ee9d5:0xc0762dd675bdb48e!8m2!3d19.0673844!4d72.8360308!16s%2Fg%2F11yx7y5z08!19sChIJ1elOUt3J5zsRjrS9ddYtdsA?authuser=0&hl=en&g_ep=EgoyMDI2MDkyMy4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 19,
        "competitor_name": "Four Chairs Cafe | Best Cafe Near Hinduja Hospital Bandra",
        "content_hash": "e7b7daf35c4509e249af2f3c323e8ba4931424450bef7024803f9d88d07674f9",
        "cta": null,
        "detected_keywords": [
          "owner"
        ],
        "detected_topic": "Service & Staff",
        "id": 44,
        "image_urls": [],
        "is_own_profile": false,
        "is_public": false,
        "post_source": "owner",
        "post_url": null,
        "published_date": "2026-05-02T20:53:20.106807",
        "raw_data": {
          "post_source": "owner"
        },
        "scrape_date": "2026-09-29 15:23:38",
        "text_content": "Response from the owner 5 months agoHi Minny,\n\nThank you so much for such a lovely review! We’re really glad you stumbled upon … More"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/Four+Chairs+Cafe+%7C+Best+Cafe+Near+Hinduja+Hospital+Bandra/data=!4m7!3m6!1s0x3be7c9dd524ee9d5:0xc0762dd675bdb48e!8m2!3d19.0673844!4d72.8360308!16s%2Fg%2F11yx7y5z08!19sChIJ1elOUt3J5zsRjrS9ddYtdsA?authuser=0&hl=en&g_ep=EgoyMDI2MDkyMy4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 19,
        "competitor_name": "Four Chairs Cafe | Best Cafe Near Hinduja Hospital Bandra",
        "content_hash": "fce47ac97144eff806d860993fbecb6f2e3f13b297214c44a502121148e0dc7e",
        "cta": null,
        "detected_keywords": [
          "coffee",
          "cold coffee"
        ],
        "detected_topic": "Coffee & Beverages",
        "id": 43,
        "image_urls": [],
        "is_own_profile": false,
        "is_public": false,
        "post_source": "owner",
        "post_url": null,
        "published_date": "2026-05-02T20:53:19.107130",
        "raw_data": {
          "post_source": "owner"
        },
        "scrape_date": "2026-09-29 15:23:38",
        "text_content": "5 months ago I stumbled upon this cafe and I’m so happy I did. They have the best food, ambience and vibes. Cool cafe with great variety of salads, Cold coffee and the best avacado on toast I’ve had in a long time. Great customer service and overall great place to hangout with friends and family. Highly recommend!! MoreLike Share Response from the owner 5 months agoHi Minny,\n\nThank you so much for such a lovely review! We’re really glad you stumbled upon … More"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/Four+Chairs+Cafe+%7C+Best+Cafe+Near+Hinduja+Hospital+Bandra/data=!4m7!3m6!1s0x3be7c9dd524ee9d5:0xc0762dd675bdb48e!8m2!3d19.0673844!4d72.8360308!16s%2Fg%2F11yx7y5z08!19sChIJ1elOUt3J5zsRjrS9ddYtdsA?authuser=0&hl=en&g_ep=EgoyMDI2MDkyMy4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 19,
        "competitor_name": "Four Chairs Cafe | Best Cafe Near Hinduja Hospital Bandra",
        "content_hash": "c88c39d2a7635b8dfb65305b4c7deff3069e1983b7ff9e8ca96e96eb945673a9",
        "cta": null,
        "detected_keywords": [
          "coffee",
          "cold coffee"
        ],
        "detected_topic": "Coffee & Beverages",
        "id": 42,
        "image_urls": [
          "https://lh3.googleusercontent.com/a/ACg8ocKC3ocpiWCmKNOOgtxxrPmSQW2Ydt6LTvp4kiEhAvzVa6hcOg=w36-h36-p-rp-mo-br100"
        ],
        "is_own_profile": false,
        "is_public": false,
        "post_source": "owner",
        "post_url": null,
        "published_date": "2026-05-02T20:53:17.072800",
        "raw_data": {
          "post_source": "owner"
        },
        "scrape_date": "2026-09-29 15:23:38",
        "text_content": "Minny Tiwari7 reviews · 4 photos5 months ago I stumbled upon this cafe and I’m so happy I did. They have the best food, ambience and vibes. Cool cafe with great variety of salads, Cold coffee and the best avacado on toast I’ve had in a long time. Great customer service and overall great place to hangout with friends and family. Highly recommend!! MoreLike Share Response from the owner 5 months agoHi Minny,\n\nThank you so much for such a lovely review! We’re really glad you stumbled upon … More"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/Tokyo+Matcha+Bar+%26+Cafe/data=!4m7!3m6!1s0x3be7c94bd9ffb9c3:0xe3820fc467efa98b!8m2!3d19.0528007!4d72.8288095!16s%2Fg%2F11kq4yd_lp!19sChIJw7n_2UvJ5zsRi6nvZ8QPguM?authuser=0&hl=en&g_ep=EgoyMDI2MDkyMy4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 16,
        "competitor_name": "Tokyo Matcha Bar & Cafe",
        "content_hash": "13c5ab12d7a158febec8588452208188223da539d798c7e1d650f1f4795d6feb",
        "cta": null,
        "detected_keywords": [
          "matcha"
        ],
        "detected_topic": "Coffee & Beverages",
        "id": 19,
        "image_urls": [],
        "is_own_profile": false,
        "is_public": true,
        "post_source": "public",
        "post_url": null,
        "published_date": "2026-09-08T20:40:52.196343",
        "raw_data": {
          "post_source": "public"
        },
        "scrape_date": "2026-09-29 15:11:08",
        "text_content": "3 weeks ago New A quaint little Cafe tucked away in the lanes of Bandra, Tokyo Matcha Bar was a cute setting for a lunch with my four year old.\nThe ramen and matcha were good. However, I ordered a  non-dairy matcha and found … MoreLike Share"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/Tokyo+Matcha+Bar+%26+Cafe/data=!4m7!3m6!1s0x3be7c94bd9ffb9c3:0xe3820fc467efa98b!8m2!3d19.0528007!4d72.8288095!16s%2Fg%2F11kq4yd_lp!19sChIJw7n_2UvJ5zsRi6nvZ8QPguM?authuser=0&hl=en&g_ep=EgoyMDI2MDkyMy4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 16,
        "competitor_name": "Tokyo Matcha Bar & Cafe",
        "content_hash": "53855b94ebb747ccffc852c151a8a78ab9405434fc454fd7a780e0eaab2eaca4",
        "cta": null,
        "detected_keywords": [
          "matcha"
        ],
        "detected_topic": "Coffee & Beverages",
        "id": 18,
        "image_urls": [
          "https://lh3.googleusercontent.com/a-/ALV-UjUlnVrx_kfX3wFxbzkZ-heUCr5HTw2FwmoW2NVDsuD56kTrXjjV=w36-h36-p-rp-mo-ba12-br100"
        ],
        "is_own_profile": false,
        "is_public": true,
        "post_source": "public",
        "post_url": null,
        "published_date": "2026-09-08T20:40:47.873863",
        "raw_data": {
          "post_source": "public"
        },
        "scrape_date": "2026-09-29 15:11:07",
        "text_content": "Riddhima KhannaLocal Guide · 34 reviews · 32 photos3 weeks ago New A quaint little Cafe tucked away in the lanes of Bandra, Tokyo Matcha Bar was a cute setting for a lunch with my four year old.\nThe ramen and matcha were good. However, I ordered a  non-dairy matcha and found … MoreLike Share"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/Four+Chairs+Cafe+%7C+Best+Cafe+Near+Hinduja+Hospital+Bandra/data=!4m7!3m6!1s0x3be7c9dd524ee9d5:0xc0762dd675bdb48e!8m2!3d19.0673844!4d72.8360308!16s%2Fg%2F11yx7y5z08!19sChIJ1elOUt3J5zsRjrS9ddYtdsA?authuser=0&hl=en&g_ep=EgoyMDI2MDkyMy4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 19,
        "competitor_name": "Four Chairs Cafe | Best Cafe Near Hinduja Hospital Bandra",
        "content_hash": "238f86cfa8f9296ed92f88e64c314c7514079397c6aa38cc28a4b29f86905fa1",
        "cta": null,
        "detected_keywords": [
          "tea"
        ],
        "detected_topic": "Coffee & Beverages",
        "id": 49,
        "image_urls": [],
        "is_own_profile": false,
        "is_public": true,
        "post_source": "public",
        "post_url": null,
        "published_date": "2026-08-30T20:53:30.455523",
        "raw_data": {
          "post_source": "public"
        },
        "scrape_date": "2026-09-29 15:23:39",
        "text_content": "a month ago Enjoyed our Saturday lunch here\nVicky served us well here\nWe had the risotto, hibiscus tea and Mediterranean hummus bowl. MoreLike Share"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/Four+Chairs+Cafe+%7C+Best+Cafe+Near+Hinduja+Hospital+Bandra/data=!4m7!3m6!1s0x3be7c9dd524ee9d5:0xc0762dd675bdb48e!8m2!3d19.0673844!4d72.8360308!16s%2Fg%2F11yx7y5z08!19sChIJ1elOUt3J5zsRjrS9ddYtdsA?authuser=0&hl=en&g_ep=EgoyMDI2MDkyMy4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 19,
        "competitor_name": "Four Chairs Cafe | Best Cafe Near Hinduja Hospital Bandra",
        "content_hash": "d2337572143fc21f8dbe343955054659cd226faac4b711b81dd65edf6641157a",
        "cta": null,
        "detected_keywords": [
          "tea"
        ],
        "detected_topic": "Coffee & Beverages",
        "id": 48,
        "image_urls": [
          "https://lh3.googleusercontent.com/a/ACg8ocKM0WJNlxH8uwJHpSC0pWiJpy30SvSeucjnSgchR52fwKdeUdA=w36-h36-p-rp-mo-ba12-br100"
        ],
        "is_own_profile": false,
        "is_public": true,
        "post_source": "public",
        "post_url": null,
        "published_date": "2026-08-30T20:53:28.355242",
        "raw_data": {
          "post_source": "public"
        },
        "scrape_date": "2026-09-29 15:23:39",
        "text_content": "Krishna IyerLocal Guide · 146 reviews · 46 photosa month ago Enjoyed our Saturday lunch here\nVicky served us well here\nWe had the risotto, hibiscus tea and Mediterranean hummus bowl. MoreLike Share"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/Tokyo+Matcha+Bar+%26+Cafe/data=!4m7!3m6!1s0x3be7c94bd9ffb9c3:0xe3820fc467efa98b!8m2!3d19.0528007!4d72.8288095!16s%2Fg%2F11kq4yd_lp!19sChIJw7n_2UvJ5zsRi6nvZ8QPguM?authuser=0&hl=en&g_ep=EgoyMDI2MDkyMy4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 16,
        "competitor_name": "Tokyo Matcha Bar & Cafe",
        "content_hash": "6c4c52338cef8569365f6e16ae1f8346302bf3ba94d00205ba271356d7729fce",
        "cta": null,
        "detected_keywords": [
          "coffee",
          "matcha"
        ],
        "detected_topic": "Coffee & Beverages",
        "id": 11,
        "image_urls": [],
        "is_own_profile": false,
        "is_public": true,
        "post_source": "public",
        "post_url": null,
        "published_date": "2026-08-30T20:40:37.559436",
        "raw_data": {
          "post_source": "public"
        },
        "scrape_date": "2026-09-29 15:11:07",
        "text_content": "a month ago I visited Tokyo matcha bar and had an amazing experience here. First I started off with their new launch Monster cookie which is like a coffee and the cookie is actually the lid it’s so fun! their matcha is obviously top notch. my favourite … More +3Like Share"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/Tokyo+Matcha+Bar+%26+Cafe/data=!4m7!3m6!1s0x3be7c94bd9ffb9c3:0xe3820fc467efa98b!8m2!3d19.0528007!4d72.8288095!16s%2Fg%2F11kq4yd_lp!19sChIJw7n_2UvJ5zsRi6nvZ8QPguM?authuser=0&hl=en&g_ep=EgoyMDI2MDkyMy4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 16,
        "competitor_name": "Tokyo Matcha Bar & Cafe",
        "content_hash": "c2ec2b3bba302d060b0b8613414cf8d6dfa4122f54d003ae53212f0cb05a61a8",
        "cta": null,
        "detected_keywords": [
          "coffee",
          "matcha"
        ],
        "detected_topic": "Coffee & Beverages",
        "id": 9,
        "image_urls": [
          "https://lh3.googleusercontent.com/a-/ALV-UjUV2PluIiKtj5lfujr8LXPzaPiGjwL1HCZV0MnyUS9GOhVymsY=w36-h36-p-rp-mo-ba12-br100"
        ],
        "is_own_profile": false,
        "is_public": true,
        "post_source": "public",
        "post_url": null,
        "published_date": "2026-08-30T20:40:33.482335",
        "raw_data": {
          "post_source": "public"
        },
        "scrape_date": "2026-09-29 15:11:07",
        "text_content": "RiyaLocal Guide · 16 reviews · 123 photosa month ago I visited Tokyo matcha bar and had an amazing experience here. First I started off with their new launch Monster cookie which is like a coffee and the cookie is actually the lid it’s so fun! their matcha is obviously top notch. my favourite … More +3Like Share"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/Mokai+Cafe+Pali+Hill/data=!4m7!3m6!1s0x3be7c9001fb6e177:0xa52f12f1036bb24e!8m2!3d19.0633484!4d72.8295262!16s%2Fg%2F11vwtj0822!19sChIJd-G2HwDJ5zsRTrJrA_ESL6U?authuser=0&hl=en&g_ep=EgoyMDI2MDkyMy4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 17,
        "competitor_name": "Mokai Cafe Pali Hill",
        "content_hash": "d95ba4c1483ff36f6876dbec3002b855cf81f65efb3b8339cfecc0c6000e6ff1",
        "cta": null,
        "detected_keywords": [
          "location",
          "road"
        ],
        "detected_topic": "Location & Access",
        "id": 5,
        "image_urls": [],
        "is_own_profile": false,
        "is_public": true,
        "post_source": "public",
        "post_url": null,
        "published_date": "2026-08-30T20:38:13.570582",
        "raw_data": {
          "post_source": "public"
        },
        "scrape_date": "2026-09-29 15:08:32",
        "text_content": "a month ago Went to this cafe recommended by a friend and it didn't disappoint me... definitely a place to check out if you're searching for places around Pali hill area, also this cafe has shifted from its earlier location  in Chapel road to this … MoreLike Share"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/Mokai+Cafe+Pali+Hill/data=!4m7!3m6!1s0x3be7c9001fb6e177:0xa52f12f1036bb24e!8m2!3d19.0633484!4d72.8295262!16s%2Fg%2F11vwtj0822!19sChIJd-G2HwDJ5zsRTrJrA_ESL6U?authuser=0&hl=en&g_ep=EgoyMDI2MDkyMy4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 17,
        "competitor_name": "Mokai Cafe Pali Hill",
        "content_hash": "1bfd4c1e725eea61afcaf6b43f552a98c8db09264186fedfa3e172325c526a96",
        "cta": null,
        "detected_keywords": [
          "location",
          "road"
        ],
        "detected_topic": "Location & Access",
        "id": 4,
        "image_urls": [
          "https://lh3.googleusercontent.com/a-/ALV-UjWLFzsqqVmgX_WagEcVvCbgoQl3jJXnUDAzQJ0EtBhDP3n_p2K6hA=w36-h36-p-rp-mo-ba12-br100"
        ],
        "is_own_profile": false,
        "is_public": true,
        "post_source": "public",
        "post_url": null,
        "published_date": "2026-08-30T20:38:11.026829",
        "raw_data": {
          "post_source": "public"
        },
        "scrape_date": "2026-09-29 15:08:32",
        "text_content": "Sushmita SinghLocal Guide · 45 reviews · 218 photosa month ago Went to this cafe recommended by a friend and it didn't disappoint me... definitely a place to check out if you're searching for places around Pali hill area, also this cafe has shifted from its earlier location  in Chapel road to this … MoreLike Share"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/Bokka+Coffee/data=!4m7!3m6!1s0x3be7c9e567d1d7e7:0xc146a4025025ea1c!8m2!3d19.0656334!4d72.830873!16s%2Fg%2F11svffd5sh!19sChIJ59fRZ-XJ5zsRHOolUAKkRsE?authuser=0&hl=en&g_ep=EgoyMDI2MDkyMy4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 18,
        "competitor_name": "Bokka Coffee",
        "content_hash": "7f7d5fb92cb5b4f385c6250e7eb5aa6b0bd7d228ff8ee46d0ff2d249e57ee2bb",
        "cta": null,
        "detected_keywords": [
          "mocha",
          "hot chocolate"
        ],
        "detected_topic": "Coffee & Beverages",
        "id": 12,
        "image_urls": [],
        "is_own_profile": false,
        "is_public": true,
        "post_source": "public",
        "post_url": null,
        "published_date": "2026-07-31T20:40:45.001540",
        "raw_data": {
          "post_source": "public"
        },
        "scrape_date": "2026-09-29 15:11:07",
        "text_content": "2 months ago We had the iced mocha and hot chocolate, and both were amazing! The iced mocha was especially outstanding—I absolutely loved it and it’s one of the best I’ve had. The hot chocolate was rich and delicious too. The staff member who served us … MoreLike Share"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/Bokka+Coffee/data=!4m7!3m6!1s0x3be7c9e567d1d7e7:0xc146a4025025ea1c!8m2!3d19.0656334!4d72.830873!16s%2Fg%2F11svffd5sh!19sChIJ59fRZ-XJ5zsRHOolUAKkRsE?authuser=0&hl=en&g_ep=EgoyMDI2MDkyMy4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 18,
        "competitor_name": "Bokka Coffee",
        "content_hash": "75d293404cf58fde1b546c19d1cab614d4e9417b96321505c05529fb5c66c19d",
        "cta": null,
        "detected_keywords": [
          "mocha",
          "hot chocolate"
        ],
        "detected_topic": "Coffee & Beverages",
        "id": 10,
        "image_urls": [
          "https://lh3.googleusercontent.com/a-/ALV-UjWXVYJ7p_ydf-IyfvMny1lUcBaZysYj6npylywHAv22jaf7gH7wQw=w36-h36-p-rp-mo-ba12-br100"
        ],
        "is_own_profile": false,
        "is_public": true,
        "post_source": "public",
        "post_url": null,
        "published_date": "2026-07-31T20:40:40.764866",
        "raw_data": {
          "post_source": "public"
        },
        "scrape_date": "2026-09-29 15:11:07",
        "text_content": "Pranav BhakareLocal Guide · 37 reviews · 108 photos2 months ago We had the iced mocha and hot chocolate, and both were amazing! The iced mocha was especially outstanding—I absolutely loved it and it’s one of the best I’ve had. The hot chocolate was rich and delicious too. The staff member who served us … MoreLike Share"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/Tokyo+Matcha+Bar+%26+Cafe/data=!4m7!3m6!1s0x3be7c94bd9ffb9c3:0xe3820fc467efa98b!8m2!3d19.0528007!4d72.8288095!16s%2Fg%2F11kq4yd_lp!19sChIJw7n_2UvJ5zsRi6nvZ8QPguM?authuser=0&hl=en&g_ep=EgoyMDI2MDkyMy4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 16,
        "competitor_name": "Tokyo Matcha Bar & Cafe",
        "content_hash": "121f7464575ea24c9ef7dac0e53f72446320faa844e196c87af7ec5156f84793",
        "cta": null,
        "detected_keywords": [
          "matcha"
        ],
        "detected_topic": "Coffee & Beverages",
        "id": 16,
        "image_urls": [],
        "is_own_profile": false,
        "is_public": true,
        "post_source": "public",
        "post_url": null,
        "published_date": "2026-07-01T20:40:45.210981",
        "raw_data": {
          "post_source": "public"
        },
        "scrape_date": "2026-09-29 15:11:07",
        "text_content": "3 months ago Loved the matcha & matchamisu! It tasted fresh. Although, matcha could have been better, their non dairy matcha options seemed overpriced. Matcha is supposed to be made in plant based milk but ig understandable. Matchamisu was super … More0:07 +4Like Share"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/Tokyo+Matcha+Bar+%26+Cafe/data=!4m7!3m6!1s0x3be7c94bd9ffb9c3:0xe3820fc467efa98b!8m2!3d19.0528007!4d72.8288095!16s%2Fg%2F11kq4yd_lp!19sChIJw7n_2UvJ5zsRi6nvZ8QPguM?authuser=0&hl=en&g_ep=EgoyMDI2MDkyMy4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 16,
        "competitor_name": "Tokyo Matcha Bar & Cafe",
        "content_hash": "a8d1de6d20ddbb3a84de1d2fba9393338dbe53c8745b456276b0497cc21b72a2",
        "cta": null,
        "detected_keywords": [
          "matcha"
        ],
        "detected_topic": "Coffee & Beverages",
        "id": 13,
        "image_urls": [
          "https://lh3.googleusercontent.com/a-/ALV-UjV5U9gpxiVJNR_Ougfzo4OthE4SXCOF2NP58sUjC2CtHNpQmJw4gg=w36-h36-p-rp-mo-ba12-br100"
        ],
        "is_own_profile": false,
        "is_public": true,
        "post_source": "public",
        "post_url": null,
        "published_date": "2026-07-01T20:40:40.985277",
        "raw_data": {
          "post_source": "public"
        },
        "scrape_date": "2026-09-29 15:11:07",
        "text_content": "KarishmaLocal Guide · 21 reviews · 40 photos3 months ago Loved the matcha & matchamisu! It tasted fresh. Although, matcha could have been better, their non dairy matcha options seemed overpriced. Matcha is supposed to be made in plant based milk but ig understandable. Matchamisu was super … More0:07 +4Like Share"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/Bokka+Coffee/data=!4m7!3m6!1s0x3be7c9e567d1d7e7:0xc146a4025025ea1c!8m2!3d19.0656334!4d72.830873!16s%2Fg%2F11svffd5sh!19sChIJ59fRZ-XJ5zsRHOolUAKkRsE?authuser=0&hl=en&g_ep=EgoyMDI2MDkyMy4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 18,
        "competitor_name": "Bokka Coffee",
        "content_hash": "ee4567778dc40f3e65769c9693b7eb7e4dba7199bff711d984bc78590163e996",
        "cta": null,
        "detected_keywords": [
          "food",
          "menu"
        ],
        "detected_topic": "Food & Menu",
        "id": 8,
        "image_urls": [],
        "is_own_profile": false,
        "is_public": true,
        "post_source": "public",
        "post_url": null,
        "published_date": "2026-07-01T20:40:37.293148",
        "raw_data": {
          "post_source": "public"
        },
        "scrape_date": "2026-09-29 15:11:07",
        "text_content": "3 months ago Bokka Coffee is exactly the kind of café you'd hope to find in Bandra, great coffee, a solid food menu, and a relaxed atmosphere that makes you want to stay longer than planned. … MoreLike Share"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/Bokka+Coffee/data=!4m7!3m6!1s0x3be7c9e567d1d7e7:0xc146a4025025ea1c!8m2!3d19.0656334!4d72.830873!16s%2Fg%2F11svffd5sh!19sChIJ59fRZ-XJ5zsRHOolUAKkRsE?authuser=0&hl=en&g_ep=EgoyMDI2MDkyMy4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 18,
        "competitor_name": "Bokka Coffee",
        "content_hash": "a1302dc211fa157fb8efb7095785139505c801264b41933de70526aad4f9d003",
        "cta": null,
        "detected_keywords": [
          "food",
          "menu"
        ],
        "detected_topic": "Food & Menu",
        "id": 7,
        "image_urls": [
          "https://lh3.googleusercontent.com/a-/ALV-UjXEwTzf91g8yVO4F9m1qZvzpDyzQ0f_c5zVtFbrZKdxuT7cOfQ=w36-h36-p-rp-mo-ba12-br100"
        ],
        "is_own_profile": false,
        "is_public": true,
        "post_source": "public",
        "post_url": null,
        "published_date": "2026-07-01T20:40:33.274888",
        "raw_data": {
          "post_source": "public"
        },
        "scrape_date": "2026-09-29 15:11:07",
        "text_content": "BIGBREWDOGLocal Guide · 189 reviews · 2,173 photos3 months ago Bokka Coffee is exactly the kind of café you'd hope to find in Bandra, great coffee, a solid food menu, and a relaxed atmosphere that makes you want to stay longer than planned. … MoreLike Share"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/Bokka+Coffee/data=!4m7!3m6!1s0x3be7c9e567d1d7e7:0xc146a4025025ea1c!8m2!3d19.0656334!4d72.830873!16s%2Fg%2F11svffd5sh!19sChIJ59fRZ-XJ5zsRHOolUAKkRsE?authuser=0&hl=en&g_ep=EgoyMDI2MDkyMy4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 18,
        "competitor_name": "Bokka Coffee",
        "content_hash": "c7688c12a497f27bc786efcf1e0e84c54a6f7daa5ec80e8708cf1a61e9a428bb",
        "cta": null,
        "detected_keywords": [
          "coffee"
        ],
        "detected_topic": "Coffee & Beverages",
        "id": 17,
        "image_urls": [],
        "is_own_profile": false,
        "is_public": true,
        "post_source": "public",
        "post_url": null,
        "published_date": "2026-06-01T20:40:51.929059",
        "raw_data": {
          "post_source": "public"
        },
        "scrape_date": "2026-09-29 15:11:07",
        "text_content": "4 months ago Visited Bokka Coffee recently and honestly, it was such a great experience! We tried their spaghetti and it was absolutely amazing super flavorful and genuinely out of the world. My friend also ordered a chicken dish and really loved it, … MoreLike Share"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/Bokka+Coffee/data=!4m7!3m6!1s0x3be7c9e567d1d7e7:0xc146a4025025ea1c!8m2!3d19.0656334!4d72.830873!16s%2Fg%2F11svffd5sh!19sChIJ59fRZ-XJ5zsRHOolUAKkRsE?authuser=0&hl=en&g_ep=EgoyMDI2MDkyMy4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 18,
        "competitor_name": "Bokka Coffee",
        "content_hash": "27b12053f56ba60eecd7f525ebac6d7e03faabe3ceccb109e6cde7d2d0372d98",
        "cta": null,
        "detected_keywords": [
          "coffee"
        ],
        "detected_topic": "Coffee & Beverages",
        "id": 14,
        "image_urls": [
          "https://lh3.googleusercontent.com/a/ACg8ocLznAW1RKnr4tzqggnJ3kzjYomCb_iunxzpaFRawtzxYGg0hg=w36-h36-p-rp-mo-ba12-br100"
        ],
        "is_own_profile": false,
        "is_public": true,
        "post_source": "public",
        "post_url": null,
        "published_date": "2026-06-01T20:40:47.622534",
        "raw_data": {
          "post_source": "public"
        },
        "scrape_date": "2026-09-29 15:11:07",
        "text_content": "Kaveri JoshiLocal Guide · 92 reviews · 336 photos4 months ago Visited Bokka Coffee recently and honestly, it was such a great experience! We tried their spaghetti and it was absolutely amazing super flavorful and genuinely out of the world. My friend also ordered a chicken dish and really loved it, … MoreLike Share"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/search/?api=1&query=Third+Wave+Coffee+Bandra+West",
        "competitor_id": 21,
        "competitor_name": "Third Wave Coffee",
        "content_hash": "31b00f6914f16d9173ba10b5585f45e8d3e1ba88d47b6d90004643fdf8d61edd",
        "cta": null,
        "detected_keywords": [
          "staff",
          "courteous"
        ],
        "detected_topic": "Service & Staff",
        "id": 21,
        "image_urls": [],
        "is_own_profile": false,
        "is_public": true,
        "post_source": "public",
        "post_url": null,
        "published_date": "2026-06-01T20:40:45.401471",
        "raw_data": {
          "post_source": "public"
        },
        "scrape_date": "2026-09-29 15:11:09",
        "text_content": "4 months ago Courteous staff, good coffee. Just Tiramisu should be improved.Order type… More +6Like Share"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/search/?api=1&query=Third+Wave+Coffee+Bandra+West",
        "competitor_id": 21,
        "competitor_name": "Third Wave Coffee",
        "content_hash": "a2d92a2704dfa9b2ef22a347ee24a1efda2cc159b2267b329760b6201af82dd0",
        "cta": null,
        "detected_keywords": [
          "staff",
          "courteous"
        ],
        "detected_topic": "Service & Staff",
        "id": 20,
        "image_urls": [
          "https://lh3.googleusercontent.com/a-/ALV-UjWPKhrZhQQBkz_Uv7ZMAD-2aJJ6qH_dNbjShX1Z6f7x4OiRN7WuZg=w36-h36-p-rp-mo-ba12-br100"
        ],
        "is_own_profile": false,
        "is_public": true,
        "post_source": "public",
        "post_url": null,
        "published_date": "2026-06-01T20:40:40.870584",
        "raw_data": {
          "post_source": "public"
        },
        "scrape_date": "2026-09-29 15:11:09",
        "text_content": "Vishaal SuryavanshiLocal Guide · 23 reviews · 148 photos4 months ago Courteous staff, good coffee. Just Tiramisu should be improved.Order type… More +6Like Share"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/search/?api=1&query=Third+Wave+Coffee+Bandra+West",
        "competitor_id": 21,
        "competitor_name": "Third Wave Coffee",
        "content_hash": "55d77a90497dd933f596e191e5f388417a0681ec4dd1929720b8a48f2b0659c9",
        "cta": null,
        "detected_keywords": [
          "service",
          "barista",
          "owner"
        ],
        "detected_topic": "Service & Staff",
        "id": 22,
        "image_urls": [],
        "is_own_profile": false,
        "is_public": true,
        "post_source": "public",
        "post_url": null,
        "published_date": "2026-04-02T20:41:02.572155",
        "raw_data": {
          "author": "Ankur Tiwari",
          "content_type": "public_content",
          "post_source": "public",
          "rating": 5,
          "relative_date": "6 months ago"
        },
        "scrape_date": "2026-09-29 15:11:10",
        "text_content": "Ankur Tiwari2 reviews6 months ago I had a fantastic time at this Third Wave Coffee Barista outlet the service was top notch and truly made my visit memorable. … MoreLike Share Response from the owner 6 months agoHi Ankur,\n\nThank you for taking the time to share your positive feedback about Third Wave … More"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/Haiku+%28fka+Method+Bandra%29/data=!4m7!3m6!1s0x3be7c90bc10415ef:0x3508e5abd151f164!8m2!3d19.0505612!4d72.8267888!16s%2Fg%2F11kl9v_843!19sChIJ7xUEwQvJ5zsRZPFR0avlCDU?authuser=0&hl=en&g_ep=EgoyMDI2MDkyMy4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 20,
        "competitor_name": "Haiku (fka Method Bandra)",
        "content_hash": "70eef0efddfa1ab1871d5232f3d95ad5d529280af45b62489f1ee266d7f5f0d1",
        "cta": null,
        "detected_keywords": [
          "vibe",
          "cozy"
        ],
        "detected_topic": "Ambience & Decor",
        "id": 15,
        "image_urls": [],
        "is_own_profile": false,
        "is_public": true,
        "post_source": "public",
        "post_url": null,
        "published_date": "2026-04-02T20:40:48.614881",
        "raw_data": {
          "author": "DISHA MANEK",
          "content_type": "public_content",
          "post_source": "public",
          "rating": 5,
          "relative_date": "6 months ago"
        },
        "scrape_date": "2026-09-29 15:11:07",
        "text_content": "DISHA MANEK10 reviews · 1 photo6 months ago I ordered the spanish tortilla (which is eggs & potato) and i reallyyyy enjoyed this soft and comforting dish😍😍\nHaiku is lovely too, super cozy with the kind of vibe that makes you want to stay for a while🤭☺️ … MoreLike Share"
      },
      {
        "canonical_post_id": null,
        "competitor_gmap_url": "https://www.google.com/maps/place/Mokai+Cafe+Pali+Hill/data=!4m7!3m6!1s0x3be7c9001fb6e177:0xa52f12f1036bb24e!8m2!3d19.0633484!4d72.8295262!16s%2Fg%2F11vwtj0822!19sChIJd-G2HwDJ5zsRTrJrA_ESL6U?authuser=0&hl=en&g_ep=EgoyMDI2MDkyMy4wIJJjKgBIAVAD&rclk=1",
        "competitor_id": 17,
        "competitor_name": "Mokai Cafe Pali Hill",
        "content_hash": "4ba4c08caa3879c1fc27771bf82939e3592c089047ed968161350484398c5838",
        "cta": null,
        "detected_keywords": [
          "food"
        ],
        "detected_topic": "Food & Menu",
        "id": 6,
        "image_urls": [],
        "is_own_profile": false,
        "is_public": true,
        "post_source": "public",
        "post_url": null,
        "published_date": "2026-04-02T20:38:25.186863",
        "raw_data": {
          "author": "Naresh Shirodkar",
          "content_type": "public_content",
          "post_source": "public",
          "rating": 5,
          "relative_date": "6 months ago"
        },
        "scrape_date": "2026-09-29 15:08:32",
        "text_content": "Naresh ShirodkarLocal Guide · 80 reviews · 459 photos6 months ago One café that has quietly become our go-to spot for comfort food over the past few months is Mokai Cafe. Tucked away in Bandra, this place manages to strike that lovely balance between relaxed café vibes and thoughtfully crafted … More0:150:08 +14Like Share"
      }
    ],
    "stats": {
      "captcha_latest_run": false,
      "competitors_count": 17,
      "duplicates_skipped_latest_run": 0,
      "failures_latest_run": 0,
      "generated_content_count": 6,
      "generated_content_used": 0,
      "images_downloaded_latest_run": 0,
      "last_scrape_at": "2026-10-04 15:15:06.110268",
      "last_scrape_status": "no_posts",
      "latest_run": {
        "captcha_encountered": 0,
        "competitor_names": [
          "The Good Stuff | Bandra"
        ],
        "competitors_processed": 1,
        "details": [
          {
            "business_verified": true,
            "captcha_required": false,
            "competitor": "The Good Stuff | Bandra",
            "competitor_id": 47,
            "duplicates_skipped": 0,
            "error": null,
            "gmap_url": "https://www.google.com/maps/place/The+Good+Stuff+%7C+Bandra/data=!4m7!3m6!1s0x3be7c900326aa277:0x811f92c4d3116811!8m2!3d19.067332!4d72.82518!16s%2Fg%2F11wxgr3lql!19sChIJd6JqMgDJ5zsREWgR08SSH4E?authuser=0&hl=en&g_ep=EgoyMDI2MDkzMC4wIJJjKgBIAVAD&rclk=1",
            "images_downloaded": 0,
            "new_posts": 0,
            "owner_posts": 0,
            "place_profile": {
              "address": "Shop No. 1, Hardik Villa, Sherly Rajan Rd, next to Rizvi Collage, Rizvi Complex, Chuim, Bandra West, Mumbai, Maharashtra 400050, India",
              "category": null,
              "name": "The Good Stuff | Bandra",
              "rating": 4.9,
              "rating_distribution": null,
              "review_count": null
            },
            "posts_found": 0,
            "public_posts": 0,
            "reviews_saved": 0,
            "status": "NO_POSTS",
            "window_days": 180
          }
        ],
        "duplicates_skipped": 0,
        "duration_seconds": 85,
        "end_time": "2026-10-04 15:16:31.233650",
        "error_info": null,
        "failures": 0,
        "has_captcha_issue": false,
        "has_errors": false,
        "id": 62,
        "images_downloaded": 0,
        "new_posts": 0,
        "posts_found": 0,
        "project_id": 7,
        "start_time": "2026-10-04 15:15:06.110268",
        "status": "no_posts"
      },
      "new_posts_latest_run": 0,
      "owner_posts": 25,
      "posts_last_7_days": 46,
      "project_id": 7,
      "public_posts": 21,
      "top_keywords": [
        {
          "count": 9,
          "keyword": "coffee"
        },
        {
          "count": 4,
          "keyword": "latte"
        },
        {
          "count": 3,
          "keyword": "cold coffee"
        },
        {
          "count": 3,
          "keyword": "vibe"
        },
        {
          "count": 3,
          "keyword": "cozy"
        },
        {
          "count": 3,
          "keyword": "mocha"
        },
        {
          "count": 2,
          "keyword": "frappe"
        },
        {
          "count": 2,
          "keyword": "matcha"
        }
      ],
      "top_topics": [
        {
          "count": 15,
          "topic": "Coffee & Beverages"
        },
        {
          "count": 5,
          "topic": "General Update"
        },
        {
          "count": 3,
          "topic": "Ambience & Decor"
        },
        {
          "count": 1,
          "topic": "Service & Staff"
        },
        {
          "count": 1,
          "topic": "Updates & Announcements"
        }
      ],
      "total_posts": 46,
      "totals": {
        "captcha_interventions": 0,
        "competitors_processed": 36,
        "duplicates_skipped": 154,
        "failed_attempts": 2,
        "images_downloaded": 111,
        "new_posts": 46,
        "posts_found": 202,
        "success_rate": 94.4,
        "successful_runs": 34,
        "total_runs": 36
      },
      "unique_businesses": 17
    },
    "topics": [
      {
        "competitor_count": 3,
        "competitors_using": "3 of 17",
        "count": 15,
        "detected_topic": "Coffee & Beverages",
        "occurrence_percentage": 17.6,
        "total_competitors": 17
      },
      {
        "competitor_count": 1,
        "competitors_using": "1 of 17",
        "count": 5,
        "detected_topic": "General Update",
        "occurrence_percentage": 5.9,
        "total_competitors": 17
      },
      {
        "competitor_count": 1,
        "competitors_using": "1 of 17",
        "count": 3,
        "detected_topic": "Ambience & Decor",
        "occurrence_percentage": 5.9,
        "total_competitors": 17
      },
      {
        "competitor_count": 1,
        "competitors_using": "1 of 17",
        "count": 1,
        "detected_topic": "Service & Staff",
        "occurrence_percentage": 5.9,
        "total_competitors": 17
      },
      {
        "competitor_count": 1,
        "competitors_using": "1 of 17",
        "count": 1,
        "detected_topic": "Updates & Announcements",
        "occurrence_percentage": 5.9,
        "total_competitors": 17
      }
    ],
    "keywords": [
      {
        "count": 9,
        "keyword": "coffee"
      },
      {
        "count": 4,
        "keyword": "latte"
      },
      {
        "count": 3,
        "keyword": "cold coffee"
      },
      {
        "count": 3,
        "keyword": "vibe"
      },
      {
        "count": 3,
        "keyword": "cozy"
      },
      {
        "count": 3,
        "keyword": "mocha"
      },
      {
        "count": 2,
        "keyword": "frappe"
      },
      {
        "count": 2,
        "keyword": "matcha"
      },
      {
        "count": 1,
        "keyword": "owner"
      },
      {
        "count": 1,
        "keyword": "new"
      },
      {
        "count": 1,
        "keyword": "cold brew"
      },
      {
        "count": 1,
        "keyword": "brew"
      },
      {
        "count": 1,
        "keyword": "shake"
      },
      {
        "count": 1,
        "keyword": "cocoa"
      },
      {
        "count": 1,
        "keyword": "chai"
      }
    ],
    "ideas": [
      {
        "generated_at": "2026-10-02 09:32:29",
        "id": 6,
        "idea_text": "{\"update_text\": \"Savor our new cold brew, crafted from freshly roasted beans, served over ice for a crisp, refreshing pick\\u2011up. Perfect for bcafe\\u2019s sunny afternoons. \\u2615\\ufe0f\\u2728\", \"keywords\": [\"cold brew\", \"roasted beans\"], \"cta\": \"Taste it today\", \"image_concept\": \"A chilled glass of cold brew on a sunlit counter, steam gently rising\", \"detected_topic\": \"Coffee & Beverages\"}",
        "project_id": 7,
        "used_flag": 0
      },
      {
        "generated_at": "2026-10-02 09:32:29",
        "id": 7,
        "idea_text": "{\"update_text\": \"Step into bcafe\\u2019s warm, book\\u2011filled corner where soft lighting meets plush seating. A cozy escape that turns every visit into a tranquil pause. \\ud83d\\udcda\\ud83d\\udc9b\", \"keywords\": [\"cozy\", \"ambience\", \"books\"], \"cta\": \"Find your corner\", \"image_concept\": \"A corner with a comfortable chair, a stack of books, and a softly glowing lamp\", \"detected_topic\": \"Ambience & Decor\"}",
        "project_id": 7,
        "used_flag": 0
      },
      {
        "generated_at": "2026-10-02 09:32:29",
        "id": 8,
        "idea_text": "{\"update_text\": \"Try our protein\\u2011powered turkey wrap on whole\\u2011grain bread, paired with a side of carrot\\u2011cucumber sticks. A balanced bite that fuels your day. \\ud83e\\udd6a\\ud83e\\udd55\", \"keywords\": [\"protein\", \"turkey wrap\", \"whole\\u2011grain\"], \"cta\": \"Grab yours now\", \"image_concept\": \"A plated turkey wrap with fresh veggies, styled on a wooden board\", \"detected_topic\": \"Food & Menu\"}",
        "project_id": 7,
        "used_flag": 0
      },
      {
        "generated_at": "2026-09-29 15:18:35",
        "id": 5,
        "idea_text": "{\"update_text\": \"Thank you for the love! Our team is dedicated to serving you the perfect chai and smiles. \\ud83d\\udc9b\", \"keywords\": [\"staff\", \"chai\"], \"cta\": \"See more\", \"image_concept\": \"Candid photo of a smiling barista handing a cup of chai to a customer, bright and friendly atmosphere.\", \"detected_topic\": \"Service & Staff\"}",
        "project_id": 7,
        "used_flag": 0
      },
      {
        "generated_at": "2026-09-29 15:18:34",
        "id": 3,
        "idea_text": "{\"update_text\": \"Craving something warm? Our signature hot chocolate is the ultimate comfort in a cozy bcafe spot. \\ud83c\\udf6b\\ud83d\\udccd\", \"keywords\": [\"hot chocolate\", \"cozy\"], \"cta\": \"Visit us\", \"image_concept\": \"Close-up of a steaming mug of hot chocolate with whipped cream on a rustic wood table, soft warm lighting.\", \"detected_topic\": \"Coffee & Beverages\"}",
        "project_id": 7,
        "used_flag": 0
      },
      {
        "generated_at": "2026-09-29 15:18:34",
        "id": 4,
        "idea_text": "{\"update_text\": \"Tucked away in bcafe, our vibe is all about slow mornings. Come find your new favorite corner. \\u2615\", \"keywords\": [\"location\", \"vibe\"], \"cta\": \"Get directions\", \"image_concept\": \"Wide shot of the cafe interior showing plants and comfortable seating, with 'Bandra' subtly visible in the window reflection.\", \"detected_topic\": \"Location & Access\"}",
        "project_id": 7,
        "used_flag": 0
      }
    ],
    "market_gaps": [
      {
        "actionable_strategy": "Publish consistently (e.g. 2x weekly) with offers and updates; out-posting the busiest rival (10 captured posts) puts your profile in front of local searchers first.",
        "affected_competitors": [
          "Cafe Coffee Day",
          "Haiku (fka Method Bandra)",
          "The Coffee Bean & Tea Leaf",
          "Brew & Bloom"
        ],
        "badge": "High Impact",
        "badge_color": "amber",
        "category": "Organic Visibility Void",
        "competitor_weakness": "10 of 17 tracked competitors have fewer than 3 captured Google Maps updates (Cafe Coffee Day, Haiku (fka Method Bandra), The Coffee Bean & Tea Leaf…). Most active so far: Blue Tokai Coffee Roasters | Bandra (10 posts), bru baabaa café (9 posts).",
        "expected_impact": "Out-publish 10 less active rival(s) on the Google Maps feed",
        "icon_type": "flame",
        "id": "gap-content-cadence",
        "title": "Google Maps Content Publishing Vacuum"
      },
      {
        "actionable_strategy": "Lift visible trust above 3.8★: showcase five-star service stories, refresh photos, and answer every review so your profile reads better than the weakest tracked rival.",
        "affected_competitors": [
          "Cafe Coffee Day"
        ],
        "badge": "Competitive Edge",
        "badge_color": "sage",
        "category": "Local Trust Deficit",
        "competitor_weakness": "Cafe Coffee Day sits at 3.8★ (781 reviews) against a tracked-market average of 4.43★, while The Good Stuff | Bandra leads at 4.9★.",
        "expected_impact": "Out-rank Cafe Coffee Day (3.8★) on local trust signals",
        "icon_type": "trending-up",
        "id": "gap-rating-quality",
        "title": "Rating Quality Gap vs Cafe Coffee Day"
      },
      {
        "actionable_strategy": "Re-scrape the competitors without captured reviews so sentiment, rating distribution and complaint analysis cover the whole market before deciding the next campaign.",
        "affected_competitors": [
          "Blue Tokai Coffee Roasters | Bandra",
          "Cafe Coffee Day",
          "bru baabaa café",
          "The Coffee Bean & Tea Leaf"
        ],
        "badge": "Quick Win",
        "badge_color": "sage",
        "category": "Data Coverage",
        "competitor_weakness": "32 review(s) captured for 6 of 17 competitors; no reviews captured yet for 11 (Blue Tokai Coffee Roasters | Bandra, Cafe Coffee Day, bru baabaa café…).",
        "expected_impact": "Complete review intelligence across every tracked competitor",
        "icon_type": "clock",
        "id": "gap-review-evidence",
        "title": "Review Evidence Coverage Gap"
      }
    ]
  }
};

const STORAGE_KEY_PROJECTS = 'mapcompete_projects_v1';
const STORAGE_KEY_ACTIVE = 'mapcompete_active_project_id_v1';
const STORAGE_KEY_DATA_PREFIX = 'mapcompete_project_data_v1_';

export function getStoredProjects() {
  try {
    const raw = typeof localStorage !== 'undefined' ? localStorage.getItem(STORAGE_KEY_PROJECTS) : null;
    if (raw) {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed) && parsed.length > 0) return parsed;
    }
  } catch (e) {
    console.warn('Error reading stored projects:', e);
  }
  return SEED_PROJECTS;
}

export function saveStoredProjects(projects) {
  if (!Array.isArray(projects) || projects.length === 0) return;
  try {
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(STORAGE_KEY_PROJECTS, JSON.stringify(projects));
    }
  } catch (e) {
    console.warn('Error saving projects to localStorage:', e);
  }
}

export function getStoredActiveProjectId() {
  try {
    if (typeof localStorage !== 'undefined') {
      const saved = localStorage.getItem(STORAGE_KEY_ACTIVE);
      if (saved) {
        const id = parseInt(saved, 10);
        if (id) return id;
      }
    }
  } catch (e) {}
  const projects = getStoredProjects();
  return projects[0]?.id || 11;
}

export function saveStoredActiveProjectId(projectId) {
  if (!projectId) return;
  try {
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(STORAGE_KEY_ACTIVE, String(projectId));
    }
  } catch (e) {}
}

export function getStoredProjectData(projectId) {
  if (!projectId) return null;
  const strId = String(projectId);
  try {
    if (typeof localStorage !== 'undefined') {
      const raw = localStorage.getItem(STORAGE_KEY_DATA_PREFIX + strId);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (parsed && typeof parsed === 'object') return parsed;
      }
    }
  } catch (e) {
    console.warn('Error reading stored project data:', e);
  }
  if (SEED_DATA[strId]) {
    return SEED_DATA[strId];
  }
  return null;
}

export function saveStoredProjectData(projectId, data) {
  if (!projectId || !data) return;
  const strId = String(projectId);
  try {
    if (typeof localStorage !== 'undefined') {
      const existing = getStoredProjectData(projectId) || {};
      const updated = { ...existing, ...data };
      localStorage.setItem(STORAGE_KEY_DATA_PREFIX + strId, JSON.stringify(updated));
    }
  } catch (e) {
    console.warn('Error saving project data to localStorage:', e);
  }
}
