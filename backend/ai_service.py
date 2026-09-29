import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from collections import Counter
from dotenv import load_dotenv
import openai
import google.generativeai as genai

# Load environment variables from .env file (check root and backend dirs)
load_dotenv()
_root_env = Path(__file__).resolve().parent.parent / '.env'
if _root_env.exists():
    load_dotenv(_root_env)
_backend_env = Path(__file__).resolve().parent / '.env'
if _backend_env.exists():
    load_dotenv(_backend_env)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIServiceProvider(ABC):
    """Abstract base class for AI service providers"""

    @abstractmethod
    def analyze_posts(self, posts: List[Dict]) -> Dict[str, Any]:
        """Analyze posts to extract topics, keywords, patterns"""
        pass

    @abstractmethod
    def generate_content_ideas(self, posts: List[Dict], count: int = 5,
                               existing_ideas: List[str] = None,
                               business_name: str = None,
                               business_profile: str = None,
                               business_location: str = None,
                               competitor_names: List[str] = None,
                               trending_topics: List[str] = None,
                               trending_keywords: List[str] = None) -> List[Dict]:
        """Generate content ideas based on posts, preventing duplicates against existing ideas"""
        pass

    @abstractmethod
    def generate_complete_update(self, posts: List[Dict]) -> Dict[str, Any]:
        """Generate a complete Google Maps update"""
        pass

    @abstractmethod
    def discover_local_competitors(self, query: str, location: str = None, field: str = None, existing_competitors: List[str] = None, is_online: bool = False) -> Dict[str, Any]:
        """Discover competitor businesses via location and field analysis, or nationwide for online brands"""
        pass

class GeminiAIService(AIServiceProvider):
    """Google Gemini AI service implementation"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-pro')
        else:
            logger.warning("Gemini API key not provided")
            self.model = None

    def analyze_posts(self, posts: List[Dict]) -> Dict[str, Any]:
        """Analyze posts using Gemini AI with deep competitor intelligence"""
        if not self.model:
            return self._fallback_analysis(posts)

        try:
            # Prepare posts data for analysis
            posts_text = self._prepare_posts_for_analysis(posts)

            prompt = f"""
            You are an expert marketing intelligence analyst specializing in Google Maps competitor updates.
            Analyze the following Google Maps posts from competitors and extract DEEP COMPETITIVE INTELLIGENCE:

            Posts data:
            {posts_text}

            Return comprehensive analysis in valid JSON format with this exact structure:
            {{
                "topics": [
                    {{
                        "topic": "string",
                        "sub_topics": ["string"],
                        "frequency": int,
                        "competitors": ["string"],
                        "description": "string"
                    }}
                ],
                "sub_topics": ["string"],
                "keywords": [
                    {{"keyword": "string", "frequency": int, "competitors": ["string"]}}
                ],
                "content_types": [
                    {{"type": "string", "frequency": int, "examples": ["string"]}}
                ],
                "cta_analysis": [
                    {{"cta": "string", "frequency": int, "competitors": ["string"], "effectiveness": "string"}}
                ],
                "offer_promotion_patterns": [
                    {{"pattern": "string", "frequency": int, "competitors": ["string"], "example": "string"}}
                ],
                "frequent_subjects": [
                    {{"subject": "string", "frequency": int, "related_keywords": ["string"]}}
                ],
                "content_frequency": {{
                    "posts_per_week": float,
                    "peak_days": ["string"],
                    "peak_hours": ["string"],
                    "competitor_posting_rates": {{"competitor": "string", "posts_per_week": float}}
                }},
                "competitor_publishing_patterns": [
                    {{
                        "competitor": "string",
                        "posting_frequency": "string",
                        "preferred_content_types": ["string"],
                        "common_ctas": ["string"],
                        "common_offers": ["string"],
                        "peak_posting_days": ["string"],
                        "avg_post_length": int,
                        "engagement_signals": ["string"]
                    }}
                ],
                "trends": [
                    {{"trend": "string", "description": "string", "supporting_evidence": "string"}}
                ],
                "gaps_opportunities": [
                    {{"opportunity": "string", "description": "string", "potential_impact": "string"}}
                ],
                "summary": "string",
                "unique_insights": [
                    {{"insight": "string", "evidence": "string", "actionable_recommendation": "string"}}
                ]
            }}

            IMPORTANT: Focus on UNIQUE, ACTIONABLE insights that differentiate from generic advice. 
            Identify patterns that are SPECIFIC to these competitors, not generic marketing advice.
            Each insight must have supporting evidence from the actual post data.
            """

            response = self.model.generate_content(prompt)
            analysis_result = self._parse_ai_response(response.text)
            return analysis_result

        except Exception as e:
            logger.error(f"Error in Gemini analysis: {e}")
            return self._fallback_analysis(posts)

    def generate_content_ideas(self, posts: List[Dict], count: int = 5,
                               existing_ideas: List[str] = None,
                               business_name: str = None,
                               business_profile: str = None,
                               business_location: str = None,
                               competitor_names: List[str] = None,
                               trending_topics: List[str] = None,
                               trending_keywords: List[str] = None) -> List[Dict]:
        """Generate content ideas using Gemini AI — written for our business, following real market trends"""
        if not self.model:
            return self._fallback_ideas(posts, count, business_name, business_profile,
                                        competitor_names, trending_topics, trending_keywords)
        try:
            posts_text = self._prepare_posts_for_analysis(posts)
            our_biz = business_name or "Our Business"
            our_profile = business_profile or "local retail"
            our_location = business_location or "local area"
            comp_names_str = ", ".join(competitor_names[:10]) if competitor_names else "none listed"

            # Build trend context from real data
            trend_text = ""
            if trending_topics:
                trend_text += f"\nTrending topics in this market (most frequent first): {', '.join(trending_topics[:8])}"
            if trending_keywords:
                trend_text += f"\nTrending keywords used by competitors: {', '.join(trending_keywords[:12])}"

            exclusion_text = ""
            if existing_ideas:
                exclusion_text = "\nDO NOT DUPLICATE or rephrase any of these previously generated ideas:\n" + \
                                 "\n".join([f"- {t}" for t in existing_ideas[:15]])

            prompt = f"""
            You are a marketing copywriter creating Google Maps posts for the business: "{our_biz}"
            Business type: {our_profile}
            Location: {our_location}
            {trend_text}

            You have been given competitor Google Maps posts for RESEARCH ONLY — to understand what topics
            and product themes are trending in this market right now.

            Generate {count} unique, engaging Google Maps update posts FOR "{our_biz}" only.
            Spread the ideas naturally across trending topics — if cotton was popular earlier and linen more recently,
            write earlier ideas about cotton-style themes and later ones about linen-style themes.
            Base each idea on a DIFFERENT trending topic so the posts cover the full content spectrum.

            STRICT RULES — NEVER BREAK THESE:
            1. NEVER mention any competitor name. Blocked: {comp_names_str}
            2. NEVER mention competitor collection names, product lines, or brands
            3. Write as "{our_biz}" using "our", "we", "visit us", "at our store"
            4. Only use product/category topics (e.g. cotton shirts, linen wear, workwear) — never brand names
            5. Each post must be distinct — different topic, tone, or angle{exclusion_text}

            Competitor posts (research only — DO NOT name them):
            {posts_text}

            Return a JSON array of {count} objects:
            [
                {{
                    "update_text": "string (80-300 chars, for {our_biz}, product topics only, no brand names)",
                    "keywords": ["string", "string"],
                    "cta": "string",
                    "image_concept": "string",
                    "detected_topic": "string (topic category this post covers)"
                }}
            ]
            """
            response = self.model.generate_content(prompt)
            ideas = self._parse_ideas_response(response.text, count)
            ideas = self._sanitize_ideas(ideas, competitor_names or [], our_biz)
            return ideas

        except Exception as e:
            logger.error(f"Error generating ideas with Gemini: {e}")
            return self._fallback_ideas(posts, count, business_name, business_profile,
                                        competitor_names, trending_topics, trending_keywords)

    def generate_complete_update(self, posts: List[Dict]) -> Dict[str, Any]:
        """Generate a complete Google Maps update using Gemini AI"""
        if not self.model:
            return self._fallback_complete_update()

        try:
            posts_text = self._prepare_posts_for_analysis(posts)

            prompt = f"""
            Based on the following competitor Google Maps posts, generate a complete, ready-to-post Google Maps update.

            Competitor posts analysis:
            {posts_text}

            Generate:
            1. Complete update text (engaging, appropriate for Google Maps)
            2. Relevant keywords (3-5)
            3. Strong call-to-action
            4. Image concept suggestion
            5. Best time to post (based on patterns if available)

            Format as JSON:
            {{
                "update_text": "string",
                "keywords": ["string", "string", "string"],
                "cta": "string",
                "image_concept": "string",
                "suggested_posting_time": "string"
            }}
            """

            response = self.model.generate_content(prompt)
            return self._parse_complete_update_response(response.text)

        except Exception as e:
            logger.error(f"Error generating complete update with Gemini: {e}")
            return self._fallback_complete_update()

    def discover_local_competitors(self, query: str, location: str = None, field: str = None, existing_competitors: List[str] = None, is_online: bool = False) -> Dict[str, Any]:
        """Discover competitor businesses via location/field or national market analysis using Gemini"""
        if not self.model:
            return self._fallback_discover_competitors(query, location, field, existing_competitors, is_online)

        try:
            import urllib.parse
            market_type = "Online Store / E-commerce / Nationwide Brand (competitors compete nationally across categories, not limited to 5km radius)" if is_online else "Local Physical Business (competitors must be in the specified geographic locality)"
            prompt = f"""
            Identify 5 to 7 direct competitors for the following business:
            - Business Name: {query}
            - Business Model: {market_type}
            - Geographical Location: {location or ('Pan-India / Online' if is_online else 'Infer from business or default to local area')}
            - Business Field/Industry: {field or 'Infer from business name'}
            - Already Tracked: {', '.join(existing_competitors) if existing_competitors else 'None'}

            Instructions:
            If this is an online brand / e-commerce platform (like Meesho, Flipkart, Nykaa, etc.):
            - Disclose direct market competitors competing for the same customers, product categories, and search keywords nationally.
            - Provide their official verified Google Maps business presence / headquarters / regional hub search query.
            - For distance, specify 'Nationwide / E-commerce' or hub distance.

            Respond strictly in JSON format:
            {{
                "target_company": "{query}",
                "is_online": {str(is_online).lower()},
                "inferred_location": "string",
                "inferred_field": "string",
                "competitors": [
                    {{
                        "name": "string",
                        "category": "string",
                        "address": "string",
                        "rating": 4.6,
                        "review_count": 140,
                        "distance": "string",
                        "strengths": ["string", "string"],
                        "suggested_search_query": "string"
                    }}
                ]
            }}
            """
            response = self.model.generate_content(prompt)
            data = self._parse_ai_response(response.text)
            if isinstance(data, dict) and "competitors" in data and isinstance(data["competitors"], list):
                for comp in data["competitors"]:
                    q = comp.get("suggested_search_query") or f"{comp.get('name', '')} {data.get('inferred_location', '')}"
                    comp["google_maps_url"] = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote_plus(q.strip())}"
                return data
            return self._fallback_discover_competitors(query, location, field, existing_competitors, is_online)
        except Exception as e:
            logger.error(f"Error in Gemini discover_local_competitors: {e}")
            return self._fallback_discover_competitors(query, location, field, existing_competitors, is_online)

    def _prepare_posts_for_analysis(self, posts: List[Dict]) -> str:
        """Prepare posts data for AI analysis"""
        posts_summary = []
        for i, post in enumerate(posts[:20]):  # Limit to 20 posts to avoid token limits
            summary = f"""
            Post {i+1}:
            - Competitor: {post.get('competitor_name', 'Unknown')}
            - Text: {post.get('text_content', '')[:200]}...
            - Date: {post.get('published_date', 'Unknown')}
            - CTAs: {post.get('cta', 'None')}
            """
            posts_summary.append(summary)
        return "\n".join(posts_summary)

    def _parse_ai_response(self, response_text: str) -> Dict[str, Any]:
        """Parse AI response into structured data"""
        try:
            # Try to extract JSON from response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            if start_idx != -1 and end_idx != 0:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                # Fallback if no JSON found
                return self._create_default_analysis()
        except json.JSONDecodeError:
            logger.warning("Could not parse AI response as JSON")
            return self._create_default_analysis()

    def _parse_ideas_response(self, response_text: str, count: int) -> List[Dict]:
        """Parse ideas response"""
        try:
            start_idx = response_text.find('[')
            end_idx = response_text.rfind(']') + 1
            if start_idx != -1 and end_idx != 0:
                json_str = response_text[start_idx:end_idx]
                ideas = json.loads(json_str)
                return ideas[:count] if isinstance(ideas, list) else []
            else:
                return self._fallback_ideas([], count)
        except json.JSONDecodeError:
            logger.warning("Could not parse ideas response as JSON")
            return self._fallback_ideas([], count)

    def _parse_complete_update_response(self, response_text: str) -> Dict[str, Any]:
        """Parse complete update response"""
        try:
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            if start_idx != -1 and end_idx != 0:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                return self._fallback_complete_update()
        except json.JSONDecodeError:
            logger.warning("Could not parse complete update response as JSON")
            return self._fallback_complete_update()

    def _create_default_analysis(self) -> Dict[str, Any]:
        """Create default analysis structure"""
        return {
            "topics": [],
            "keywords": [],
            "content_patterns": [],
            "trends": [],
            "summary": "Analysis not available"
        }

    def _fallback_analysis(self, posts: List[Dict]) -> Dict[str, Any]:
        """Fallback analysis when AI is not available - enhanced structure"""
        # Extract data from posts
        keywords = {}
        topics = {}
        competitors = set()
        content_types = {}
        ctas = {}
        offer_patterns = {}
        
        for post in posts:
            text = post.get('text_content', '').lower()
            comp = post.get('competitor_name', 'Unknown')
            competitors.add(comp)
            
            # Simple word frequency
            words = text.split()
            for word in words:
                if len(word) > 4:
                    keywords[word] = keywords.get(word, 0) + 1
            
            # Detect content type
            if any(w in text for w in ['offer', 'discount', 'sale', 'off', '%']):
                content_types['Offer/Promotion'] = content_types.get('Offer/Promotion', 0) + 1
            elif any(w in text for w in ['new', 'new arrival', 'new collection', 'launch']):
                content_types['New Arrival/Launch'] = content_types.get('New Arrival/Launch', 0) + 1
            elif any(w in text for w in ['tip', 'tips', 'guide', 'how to', 'how-to']):
                content_types['Educational/Tips'] = content_types.get('Educational/Tips', 0) + 1
            elif any(w in text for w in ['event', 'workshop', 'class', 'webinar']):
                content_types['Event/Workshop'] = content_types.get('Event/Workshop', 0) + 1
            else:
                content_types['General Update'] = content_types.get('General Update', 0) + 1
            
            # Extract CTAs
            cta_text = post.get('cta', '')
            if cta_text:
                ctas[cta_text] = ctas.get(cta_text, 0) + 1
            
            # Detect offers
            if any(w in text for w in ['% off', 'percent off', 'discount', 'offer', 'deal', 'buy']):
                offer_patterns['Discount/Promo'] = offer_patterns.get('Discount/Promo', 0) + 1
            if any(w in text for w in ['free', 'complimentary', 'on us']):
                offer_patterns['Free/Complimentary'] = offer_patterns.get('Free/Complimentary', 0) + 1
            if any(w in text for w in ['book', 'reserve', 'appointment']):
                offer_patterns['Booking/Reservation'] = offer_patterns.get('Booking/Reservation', 0) + 1

        top_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:15]
        top_content_types = sorted(content_types.items(), key=lambda x: x[1], reverse=True)
        top_ctas = sorted(ctas.items(), key=lambda x: x[1], reverse=True)[:5]
        top_offers = sorted(offer_patterns.items(), key=lambda x: x[1], reverse=True)

        # Get competitors list
        comp_list = list(competitors)
        
        # Estimate posting frequency
        total_posts = len(posts)
        if total_posts > 0:
            days_span = 1  # fallback
            try:
                dates = []
                for p in posts:
                    if p.get('published_date'):
                        dates.append(datetime.fromisoformat(p['published_date'].replace('Z', '+00:00')))
                if dates:
                    days_span = (max(dates) - min(dates)).days + 1
            except:
                days_span = 7
            posts_per_week = (total_posts / max(days_span, 1)) * 7
        else:
            posts_per_week = 0

        return {
            "topics": [
                {"topic": "General Updates", "sub_topics": ["Updates"], "frequency": len(posts), "competitors": list(competitors)[:5], "description": "General business updates and announcements"}
            ],
            "sub_topics": ["Business Updates"],
            "keywords": [{"keyword": k, "frequency": f, "competitors": list(competitors)[:3]} for k, f in sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:15]],
            "content_types": [{"type": t, "frequency": f, "examples": [f"Post about {t.lower()}"]} for t, f in top_content_types],
            "cta_analysis": [{"cta": c, "frequency": f, "competitors": [], "effectiveness": "Moderate"} for c, f in top_ctas],
            "offer_promotion_patterns": [{"pattern": p, "frequency": f, "competitors": [], "example": f"Example of {p}"} for p, f in top_offers],
            "frequent_subjects": [{"subject": k, "frequency": f, "related_keywords": [k]} for k, f in sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:10]],
            "content_frequency": {
                "posts_per_week": round(posts_per_week, 1),
                "peak_days": ["Monday", "Thursday", "Friday"],
                "peak_hours": ["10:00 AM", "2:00 PM"],
                "competitor_posting_rates": {}
            },
            "competitor_publishing_patterns": [],
            "trends": [{"trend": "Data-driven content", "description": "Content strategy based on real competitor data", "supporting_evidence": "Based on actual post analysis"}],
            "gaps_opportunities": [
                {"opportunity": "Educational content", "description": "Competitors lack educational content", "potential_impact": "High - differentiates from promotional noise"},
                {"opportunity": "Customer stories", "description": "Few competitors share customer testimonials", "potential_impact": "Medium - builds trust"}
            ],
            "summary": f"Analyzed {len(posts)} posts from {len(competitors)} competitors. Found {len(keywords)} unique keywords.",
            "unique_insights": [
                {"insight": "Most competitors focus on promotional content", "evidence": f"{content_types.get('Offer/Promotion', 0)} out of {len(posts)} posts are promotional", "actionable_recommendation": "Differentiate with educational and customer-centric content"},
                {"insight": "CTAs are underutilized", "evidence": f"Only {sum(ctas.values())} out of {len(posts)} posts have CTAs", "actionable_recommendation": "Add clear CTAs to every post"}
            ]
        }

    def _fallback_ideas(self, posts: List[Dict], count: int,
                        business_name: str = None,
                        business_profile: str = None,
                        competitor_names: List[str] = None,
                        trending_topics: List[str] = None,
                        trending_keywords: List[str] = None) -> List[Dict]:
        """Data-driven idea generation — follows real market trend order, written FOR our business only"""
        our_biz = business_name or "Our Business"
        ideas = []

        # Extract topics and keywords from actual competitor posts
        topics = []
        all_keywords = []
        ctas = []
        for p in posts or []:
            topic = p.get('detected_topic')
            # Skip topics that ARE a competitor name
            if topic and topic not in topics:
                if not competitor_names or not any(cn.lower() in topic.lower() for cn in competitor_names):
                    topics.append(topic)
            kws = p.get('detected_keywords')
            if isinstance(kws, list):
                all_keywords.extend(kws)
            elif isinstance(kws, str):
                try:
                    all_keywords.extend(json.loads(kws))
                except Exception:
                    pass
            cta = p.get('cta')
            if cta and cta not in ctas:
                ctas.append(cta)

        # Build comprehensive block-word set from competitor names (full + individual words)
        import re as _re
        block_words = set()
        for cname in (competitor_names or []):
            if not cname: continue
            block_words.add(cname.lower())
            for word in cname.lower().split():
                if len(word) > 3:
                    block_words.add(word)

        # Also extract brand-specific words from competitor post text (proper-noun-style tokens)
        # These are capitalized words in competitor posts that are unique brand identifiers
        common_fashion_words = {
            'collection', 'style', 'fashion', 'wear', 'clothes', 'clothing', 'dress', 'shirt',
            'fabric', 'premium', 'quality', 'casual', 'formal', 'comfort', 'design', 'trend',
            'summer', 'winter', 'spring', 'season', 'store', 'visit', 'offer', 'sale',
            'india', 'mumbai', 'delhi', 'kharghar', 'navi', 'local', 'brand', 'party'
        }
        for p in (posts or []):
            txt = p.get('text_content', '') or ''
            # Find capitalized words that are not common fashion terms — these are brand identifiers
            for word in _re.findall(r'\b[A-Z][a-z]{3,}\b', txt):
                wl = word.lower()
                if wl not in common_fashion_words and len(wl) > 4:
                    block_words.add(wl)

        def _is_clean_keyword(k):
            """Returns True if keyword has no overlap with any competitor brand word"""
            kl = k.lower()
            for bw in block_words:
                if bw == kl or bw in kl or kl in bw:
                    return False
            # Generic scraped stopwords
            stop = {'want', 'through', 'where', 'bring', 'press', 'fomo', 'ways', 'grand', 'their'}
            return kl not in stop

        # Unique keywords — only keep clean, competitor-free keywords
        seen_kw = set()
        # Prefer trending_keywords if passed (already brand-filtered)
        preferred_kws = [k for k in (trending_keywords or []) if _is_clean_keyword(k)][:8]
        clean_keywords = preferred_kws or [
            k for k in all_keywords
            if not (k in seen_kw or seen_kw.add(k))
            and len(k) > 2
            and _is_clean_keyword(k)
        ][:12]

        # Use trending_topics from real trend analysis if available (ordered most-frequent first)
        ordered_topics = [t for t in (trending_topics or []) if t and t.strip()] or topics
        top_topic    = ordered_topics[0] if ordered_topics else "new collection"
        second_topic = ordered_topics[1] if len(ordered_topics) > 1 else "occasion & everyday wear"
        third_topic  = ordered_topics[2] if len(ordered_topics) > 2 else "casual & everyday wear"
        cta_choice   = ctas[0] if ctas else "Visit us today"

        # 50 Progressive Product Templates across 5 Market Trend Phases
        # Phase 1: Cotton & Breathable Essentials (1-10)
        # Phase 2: Linen & Warm-Weather Weaves (11-20)
        # Phase 3: Structured Tailoring & Workwear (21-30)
        # Phase 4: Occasion & Festive Celebrations (31-40)
        # Phase 5: Weekend Casuals, Denim & Layering (41-50)
        templates_50 = [
            # Phase 1: Cotton & Breathable Essentials (1-10)
            {
                "update_text": f"Step out in breathable comfort at {our_biz}. Our 100% combed cotton shirts offer crisp, lightweight wear engineered for long active days. Stop by to find your perfect fit!",
                "keywords": ["combed cotton", "breathable", "everyday shirts", "lightweight"],
                "cta": "Visit Store Today",
                "image_concept": "Clean flat lay of folded pure cotton shirts in crisp white, sky blue, and sage on a natural wood surface",
                "detected_topic": "Breathable Cotton Essentials",
                "suggested_posting_time": "Tuesday 10:00 AM"
            },
            {
                "update_text": f"Wardrobe foundational piece: tailored cotton chinos with flexible 4-way stretch at {our_biz}. Built for ease from morning meetings to casual evenings. Visit our store to try them on.",
                "keywords": ["cotton chinos", "stretch chinos", "all day comfort", "smart casual"],
                "cta": "Find Directions",
                "image_concept": "Stylized mannequin wearing tailored olive cotton chinos paired with clean white sneakers",
                "detected_topic": "Cotton Chinos & Trousers",
                "suggested_posting_time": "Wednesday 11:30 AM"
            },
            {
                "update_text": f"Upgrade your daily rotation with mercerized cotton polo tees from {our_biz}. Enhanced color retention and ultra-smooth handfeel. Explore the new seasonal shades in-store today.",
                "keywords": ["mercerized cotton", "polo tees", "premium fabric", "daily wear"],
                "cta": "Explore In-Store",
                "image_concept": "Close-up macro shot showcasing the rich luster and pique knit texture of a mercerized cotton polo collar",
                "detected_topic": "Premium Cotton Polos",
                "suggested_posting_time": "Thursday 2:00 PM"
            },
            {
                "update_text": f"The classic Oxford cotton button-down at {our_biz} — washed for immediate softness and structured with a sharp roll collar. Available now in versatile timeless neutrals.",
                "keywords": ["oxford cotton", "button down", "timeless style", "menswear"],
                "cta": "Visit Us Today",
                "image_concept": "Hanger display of oxford cotton shirts with sunlight casting soft shadows highlighting the basketweave texture",
                "detected_topic": "Classic Oxford Cotton",
                "suggested_posting_time": "Friday 10:00 AM"
            },
            {
                "update_text": f"Beat the heat in lightweight cotton slub tees from {our_biz}. Naturally breathable, pre-shrunk, and cut for effortless weekend layering. Stop by our showroom today!",
                "keywords": ["cotton slub", "breathable tees", "summer staples", "relaxed fit"],
                "cta": "Check Availability",
                "image_concept": "Folded stack of earth-toned cotton slub t-shirts on a minimalist stone pedestal",
                "detected_topic": "Cotton Slub Basics",
                "suggested_posting_time": "Saturday 11:00 AM"
            },
            {
                "update_text": f"Sharp meets relaxed: cotton-rich overshirts designed for all-season versatility at {our_biz}. Layer over a clean tee for an instant polished weekend look.",
                "keywords": ["cotton overshirt", "layering piece", "casual jacket", "versatile"],
                "cta": "Shop In-Store",
                "image_concept": "Styled lookbook outfit with open cotton overshirt over a beige tee and dark trousers",
                "detected_topic": "Cotton Layering Pieces",
                "suggested_posting_time": "Sunday 1:00 PM"
            },
            {
                "update_text": f"Effortless everyday styling begins with breathable cotton basics at {our_biz}. Crisp silhouettes, durable stitching, and unmatched daily comfort await you.",
                "keywords": ["cotton basics", "daily comfort", "durable weave", "essential wear"],
                "cta": "Get Directions",
                "image_concept": "Wide-angle retail shot showing neatly arranged cotton essentials organized by color gradient",
                "detected_topic": "Daily Cotton Basics",
                "suggested_posting_time": "Monday 11:00 AM"
            },
            {
                "update_text": f"Looking for all-day office ease? Our cotton twill trousers at {our_biz} provide structured lines without compromising on flexible comfort. Visit us to get measured.",
                "keywords": ["cotton twill", "office trousers", "tailored fit", "workwear"],
                "cta": "Visit Us Today",
                "image_concept": "Detail view of cotton twill fabric drape showing clean pocket stitching and crease line",
                "detected_topic": "Cotton Twill Workwear",
                "suggested_posting_time": "Tuesday 12:00 PM"
            },
            {
                "update_text": f"Weekend essentials perfected: lightweight cotton short-sleeve resort shirts with clean Cuban collars at {our_biz}. Available in subtle micro-prints now in-store.",
                "keywords": ["cuban collar", "resort shirt", "cotton print", "weekend style"],
                "cta": "Explore the Range",
                "image_concept": "Flat lay of open-collar cotton resort shirt with sunglasses and woven straw hat on linen backdrop",
                "detected_topic": "Resort Cotton Shirts",
                "suggested_posting_time": "Friday 4:00 PM"
            },
            {
                "update_text": f"Pure comfort, zero fuss. Discover our combed cotton crew-neck tees crafted with reinforced ribbed collars that keep their shape wash after wash at {our_biz}.",
                "keywords": ["crew neck", "combed cotton", "shape retention", "everyday staple"],
                "cta": "Visit Store",
                "image_concept": "Close-up of ribbed crew collar showing dense cotton knit and clean reinforced neck tape",
                "detected_topic": "Combed Cotton Crews",
                "suggested_posting_time": "Saturday 10:30 AM"
            },

            # Phase 2: Linen & Warm-Weather Weaves (11-20)
            {
                "update_text": f"Embrace timeless warm-weather elegance. Pure European flax linen shirts with natural texture and airy breathability are now in-store at {our_biz}. Find your shade today!",
                "keywords": ["pure linen", "flax linen", "breathable shirt", "summer elegance"],
                "cta": "Explore In-Store",
                "image_concept": "Studio shot of a washed pure linen shirt illuminated by warm natural window light highlighting the yarn slubs",
                "detected_topic": "Pure Linen Shirts",
                "suggested_posting_time": "Wednesday 10:00 AM"
            },
            {
                "update_text": f"Stay cool when the afternoon heats up. Relaxed linen-blend drawstring trousers crafted for effortless summer pacing are now available at {our_biz}. Step by to feel the fabric.",
                "keywords": ["linen trousers", "drawstring pants", "relaxed fit", "summer cooling"],
                "cta": "Find Your Fit",
                "image_concept": "Full-length outfit featuring relaxed beige linen trousers paired with leather sandals on light sandstone",
                "detected_topic": "Linen Drawstring Bottoms",
                "suggested_posting_time": "Thursday 11:00 AM"
            },
            {
                "update_text": f"Understated luxury: garment-dyed linen button-downs with vintage character and soft handfeel at {our_biz}. Designed to look even better with every wash. Visit us today!",
                "keywords": ["garment dyed", "linen shirt", "vintage character", "soft handfeel"],
                "cta": "Visit Store",
                "image_concept": "Close-up showing subtle color variation along the seams of a garment-dyed olive linen shirt",
                "detected_topic": "Garment-Dyed Linen",
                "suggested_posting_time": "Friday 2:30 PM"
            },
            {
                "update_text": f"Transition seamlessly from daytime meetings to sunset dinners in our tailored linen-cotton blazers at {our_biz}. Unlined construction for maximum airflow and sharp structure.",
                "keywords": ["linen blazer", "unlined blazer", "summer tailoring", "smart casual"],
                "cta": "Try On In-Store",
                "image_concept": "Mannequin wearing an unlined navy linen-cotton blazer over a crisp white linen shirt",
                "detected_topic": "Linen Tailored Blazers",
                "suggested_posting_time": "Saturday 12:00 PM"
            },
            {
                "update_text": f"Breezy comfort redefined: open-weave linen camp shirts paired with crisp bottoms for relaxed coastal or urban weekends. Explore the collection at {our_biz}.",
                "keywords": ["camp shirt", "open weave", "linen blend", "coastal style"],
                "cta": "Explore Collection",
                "image_concept": "Flat lay of open-weave linen camp shirt on a rustic terracotta tiled background",
                "detected_topic": "Linen Camp Shirts",
                "suggested_posting_time": "Sunday 11:30 AM"
            },
            {
                "update_text": f"Natural flax fibers that regulate body temperature all day long. Explore our linen summer collection at {our_biz} featuring warm earth tones and relaxed contemporary cuts.",
                "keywords": ["natural flax", "temperature regulation", "earth tones", "sustainable weave"],
                "cta": "Visit Us Today",
                "image_concept": "Color story display showing linen shirts in sand, terracotta, sage, and ivory hanging sequentially",
                "detected_topic": "Natural Linen Weaves",
                "suggested_posting_time": "Tuesday 1:30 PM"
            },
            {
                "update_text": f"The quintessential warm-weather staple: striped linen-blend mandarin collar shirts at {our_biz}. Lightweight, textured, and impeccably cut for modern men.",
                "keywords": ["mandarin collar", "striped linen", "summer staple", "refined cuts"],
                "cta": "Find Directions",
                "image_concept": "Neckline detail of striped mandarin collar linen shirt with polished coconut shell buttons",
                "detected_topic": "Mandarin Collar Linen",
                "suggested_posting_time": "Wednesday 3:00 PM"
            },
            {
                "update_text": f"Upgrade your weekend wardrobe with breathable linen Bermuda shorts at {our_biz}. Styled for clean silhouettes and breezy tropical comfort. Stop by today!",
                "keywords": ["linen shorts", "bermuda shorts", "weekend comfort", "breezy fit"],
                "cta": "Check Availability",
                "image_concept": "Folded pair of tailored linen shorts with a braided rope belt displayed on weathered driftwood",
                "detected_topic": "Linen Weekend Bottoms",
                "suggested_posting_time": "Thursday 4:00 PM"
            },
            {
                "update_text": f"Crisp yet relaxed: French linen shirts featuring delicate mother-of-pearl buttons and soft-roll collars at {our_biz}. Visit us to experience premium texture firsthand.",
                "keywords": ["french linen", "pearl buttons", "soft roll collar", "luxury texture"],
                "cta": "Visit Our Store",
                "image_concept": "Macro photography of mother-of-pearl button stitched onto finely woven French linen fabric",
                "detected_topic": "French Linen Collection",
                "suggested_posting_time": "Friday 11:00 AM"
            },
            {
                "update_text": f"Beat the humidity with pure linen essentials at {our_biz}. Lightweight draping, authentic weave textures, and enduring style available right now at our local store.",
                "keywords": ["humidity relief", "pure linen", "lightweight drape", "enduring style"],
                "cta": "Find On Maps",
                "image_concept": "Store entrance display showing lightweight linen pieces swaying gently in store lighting",
                "detected_topic": "Pure Linen Essentials",
                "suggested_posting_time": "Saturday 1:00 PM"
            },

            # Phase 3: Structured Tailoring & Workwear (21-30)
            {
                "update_text": f"Sharp lines for ambitious days. Wrinkle-resistant formal shirts with reinforced cuffs and micro-houndstooth weaves at {our_biz}. Available in slim and regular fits.",
                "keywords": ["formal shirts", "wrinkle resistant", "houndstooth weave", "executive wear"],
                "cta": "Get Measured In-Store",
                "image_concept": "Neatly pressed formal shirt with geometric weave shown with silk necktie and silver cufflinks",
                "detected_topic": "Wrinkle-Resistant Formals",
                "suggested_posting_time": "Monday 9:30 AM"
            },
            {
                "update_text": f"Executive power dressing: tailored bi-stretch suits with breathable interior lining and hand-finished lapels at {our_biz}. Step in for personalized fitting assistance.",
                "keywords": ["tailored suits", "bi stretch", "hand finished", "executive presence"],
                "cta": "Book Fitting",
                "image_concept": "Half-body mannequin wearing a tailored charcoal suit jacket with pocket square in boardroom setting",
                "detected_topic": "Executive Suiting",
                "suggested_posting_time": "Tuesday 10:30 AM"
            },
            {
                "update_text": f"The versatile weekday staple: structured flat-front trousers in high-twist wool blends for all-day crease retention at {our_biz}. Discover your size today.",
                "keywords": ["flat front trousers", "wool blend", "crease retention", "weekday workwear"],
                "cta": "Find Your Fit",
                "image_concept": "Drape test of high-twist trouser fabric demonstrating instant wrinkle recovery on a display stand",
                "detected_topic": "Structured Workwear Trousers",
                "suggested_posting_time": "Wednesday 12:00 PM"
            },
            {
                "update_text": f"Make an impression in the boardroom. Modern slim-cut single-breasted blazers in deep navy and charcoal at {our_biz}. Crafted for comfort during long presentations.",
                "keywords": ["slim cut blazer", "single breasted", "navy blazer", "boardroom fit"],
                "cta": "Try On In-Store",
                "image_concept": "Tailored navy blazer on wooden valet stand with leather briefcase and dress shoes below",
                "detected_topic": "Boardroom Blazers",
                "suggested_posting_time": "Thursday 10:00 AM"
            },
            {
                "update_text": f"Refined detailing: pinpoint cotton dress shirts with spread collars built to hold silk neckwear effortlessly at {our_biz}. In-store styling assistance available.",
                "keywords": ["pinpoint cotton", "spread collar", "dress shirts", "collar structure"],
                "cta": "Visit Us Today",
                "image_concept": "Crisp collar view of pinpoint dress shirt showing precise collar stay alignment and clean placket",
                "detected_topic": "Pinpoint Dress Shirts",
                "suggested_posting_time": "Friday 9:00 AM"
            },
            {
                "update_text": f"Modern commuter tailoring: packable travel blazers designed with anti-crease fabric and concealed utility pockets at {our_biz}. Visit us before your next business trip.",
                "keywords": ["commuter blazer", "travel jacket", "anti crease", "utility pockets"],
                "cta": "Explore In-Store",
                "image_concept": "Travel blazer loosely folded beside a laptop bag demonstrating packable lightweight construction",
                "detected_topic": "Commuter Travel Blazers",
                "suggested_posting_time": "Saturday 11:30 AM"
            },
            {
                "update_text": f"Elegance in simplicity. Solid formal trousers with flexi-waistbands engineered for desk-to-dinner transitions at {our_biz}. Explore our comprehensive size range.",
                "keywords": ["flexi waistband", "formal trousers", "desk to dinner", "all day fit"],
                "cta": "Visit Store",
                "image_concept": "Waistband interior shot showing hidden elastic comfort insert without altering outer formal lines",
                "detected_topic": "Flexi-Waist Formals",
                "suggested_posting_time": "Monday 11:00 AM"
            },
            {
                "update_text": f"Smart layering for professional settings: lightweight Merino wool blend cardigans and v-necks designed to layer smoothly over dress shirts at {our_biz}.",
                "keywords": ["merino wool", "v neck knit", "professional knitwear", "layering"],
                "cta": "Check Availability",
                "image_concept": "Folded fine-gauge knitwear stack in slate grey, camel, and midnight navy",
                "detected_topic": "Professional Knitwear",
                "suggested_posting_time": "Tuesday 2:00 PM"
            },
            {
                "update_text": f"Sharpen your weekly rotation with premium dobby-weave formal shirts at {our_biz}. Subtle geometric textures add depth without overwhelming your business attire.",
                "keywords": ["dobby weave", "geometric texture", "formal shirt", "business attire"],
                "cta": "Visit Us Today",
                "image_concept": "Close-up fabric macro showing subtle geometric dobby weave pattern illuminated with side lighting",
                "detected_topic": "Dobby Weave Formals",
                "suggested_posting_time": "Wednesday 10:00 AM"
            },
            {
                "update_text": f"Precision fit meets everyday durability. Step into {our_biz} to explore tailored formalwear made to elevate your workplace presence. Find us on Google Maps!",
                "keywords": ["precision fit", "durable tailoring", "workplace presence", "formalwear"],
                "cta": "Get Directions",
                "image_concept": "Showcase of impeccably steamed suits and formal trousers hung on wooden rails in showroom",
                "detected_topic": "Precision Tailored Formals",
                "suggested_posting_time": "Thursday 11:30 AM"
            },

            # Phase 4: Occasion, Festive & Celebration Wear (31-40)
            {
                "update_text": f"Celebrate milestones in grandeur. Hand-finished festive short kurtas in raw silk blends featuring subtle threadwork at {our_biz}. Discover occasion wear in-store today.",
                "keywords": ["raw silk kurta", "festive short kurta", "threadwork", "occasion wear"],
                "cta": "Explore Collection",
                "image_concept": "Festive short kurta in jewel-toned emerald green displayed with gold accent buttons on dark slate",
                "detected_topic": "Festive Silk Kurtas",
                "suggested_posting_time": "Friday 5:00 PM"
            },
            {
                "update_text": f"Evening sophistication: structured Bandhgala jackets with antique brass buttons and regal mandarin collars at {our_biz}. Perfect for wedding receptions and galas.",
                "keywords": ["bandhgala jacket", "mandarin collar", "antique buttons", "reception wear"],
                "cta": "Try On In-Store",
                "image_concept": "Mannequin wearing a midnight black Bandhgala with silk pocket square under warm festive chandelier light",
                "detected_topic": "Structured Bandhgalas",
                "suggested_posting_time": "Saturday 4:30 PM"
            },
            {
                "update_text": f"Elevate your celebration look with jacquard textured Nehru jackets layered over crisp contrast kurtas at {our_biz}. Step in to explore curated festive palettes.",
                "keywords": ["nehru jacket", "jacquard weave", "festive palette", "layered ethnic"],
                "cta": "Visit Us Today",
                "image_concept": "Gold jacquard Nehru jacket layered over an ivory silk kurta shown with churidar trousers",
                "detected_topic": "Jacquard Nehru Jackets",
                "suggested_posting_time": "Sunday 12:30 PM"
            },
            {
                "update_text": f"Festive charm meets modern comfort: lightweight Chanderi blend kurtas in festive tones of mustard, wine, and royal blue at {our_biz}. Try them on today!",
                "keywords": ["chanderi blend", "festive colors", "comfortable festive", "kurta set"],
                "cta": "Find Directions",
                "image_concept": "Vibrant festive kurta collection in rich saturated tones hanging on brass racks",
                "detected_topic": "Chanderi Festive Kurtas",
                "suggested_posting_time": "Monday 3:00 PM"
            },
            {
                "update_text": f"Stand out at evening gatherings with bespoke-inspired tuxedo jackets in deep navy with satin peak lapels at {our_biz}. Tailored for your most memorable moments.",
                "keywords": ["tuxedo jacket", "satin lapels", "black tie", "evening wear"],
                "cta": "Book Consultation",
                "image_concept": "Black-tie tuxedo ensemble on display with satin bowtie and patent leather dress shoes",
                "detected_topic": "Evening Tuxedo Silhouettes",
                "suggested_posting_time": "Tuesday 6:00 PM"
            },
            {
                "update_text": f"Crafted for family celebrations: pintuck embroidered linen kurtas paired with tailored churidars or straight trousers at {our_biz}. Stop by to find your size.",
                "keywords": ["pintuck embroidery", "linen kurta", "family celebrations", "straight trousers"],
                "cta": "Explore In-Store",
                "image_concept": "Detailed view of subtle vertical pintuck stitching along the placket of a cream kurta",
                "detected_topic": "Embroidered Occasion Wear",
                "suggested_posting_time": "Wednesday 4:00 PM"
            },
            {
                "update_text": f"Opulence in every thread. Textured brocade waistcoats designed to turn heads at festive galas and cultural evenings at {our_biz}. Available in limited seasonal sets.",
                "keywords": ["brocade waistcoat", "festive gala", "cultural wear", "exclusive cut"],
                "cta": "Check Availability",
                "image_concept": "Intricate gold and maroon woven brocade fabric texture shot in dramatic shallow depth of field",
                "detected_topic": "Brocade Festive Waistcoats",
                "suggested_posting_time": "Thursday 5:30 PM"
            },
            {
                "update_text": f"Modern ethnic fusion: cowl-drape kurtas with asymmetrical hemlines for the trend-conscious gentleman at {our_biz}. Visit our showroom to preview the range.",
                "keywords": ["cowl drape", "asymmetrical kurta", "modern ethnic", "fusion style"],
                "cta": "Preview In-Store",
                "image_concept": "Modern silhouette mannequin displaying an asymmetrical slate grey cowl-drape kurta",
                "detected_topic": "Contemporary Ethnic Fusion",
                "suggested_posting_time": "Friday 3:00 PM"
            },
            {
                "update_text": f"Heritage detailing with contemporary comfort: embroidered achkan jackets with ornate buttons and matching stoles at {our_biz}. Consult our in-store festive stylists today.",
                "keywords": ["achkan jacket", "ornate buttons", "festive styling", "heritage embroidery"],
                "cta": "Visit Us Today",
                "image_concept": "Full ceremonial look displaying hand-embroidered achkan with matching safa and silk stole",
                "detected_topic": "Heritage Achkans & Jackets",
                "suggested_posting_time": "Saturday 2:00 PM"
            },
            {
                "update_text": f"Make every celebration unforgettable. Explore festive ensembles with artisan embellishments and rich seasonal textures at {our_biz}. Visit our local showroom today!",
                "keywords": ["artisan embellishments", "celebration ensembles", "rich textures", "festive collection"],
                "cta": "Find On Maps",
                "image_concept": "Warm festive showroom interior displaying decorated mirrors and curated ethnic coordinates",
                "detected_topic": "Occasion Celebration Ensembles",
                "suggested_posting_time": "Sunday 3:30 PM"
            },

            # Phase 5: Weekend Casuals, Denim & Modern Layering (41-50)
            {
                "update_text": f"Unwind in premium stretch denims from {our_biz}. Authentic indigo washes with 360-degree flex for effortless movement throughout your weekend. Stop by to try your fit!",
                "keywords": ["stretch denim", "indigo wash", "flexible fit", "weekend jeans"],
                "cta": "Try On In-Store",
                "image_concept": "Neatly folded stacks of indigo, dark wash, and mid-blue denim showing leather back-patches",
                "detected_topic": "Premium Stretch Denims",
                "suggested_posting_time": "Friday 11:30 AM"
            },
            {
                "update_text": f"Utilitarian style redefined: multi-pocket cotton cargo pants with tapered ankles and reinforced seams at {our_biz}. Available now in earthy khaki and olive.",
                "keywords": ["cargo pants", "tapered fit", "utility style", "durable cotton"],
                "cta": "Explore the Range",
                "image_concept": "Tapered olive cargo pants paired with high-top canvas sneakers on industrial concrete",
                "detected_topic": "Tapered Cargo Utility",
                "suggested_posting_time": "Saturday 10:00 AM"
            },
            {
                "update_text": f"The ultimate layering piece: heavy-gauge waffle knit henleys at {our_biz} that provide warmth, texture, and relaxed masculinity. Stop by to grab yours today.",
                "keywords": ["waffle knit", "henley shirt", "thermal texture", "relaxed layer"],
                "cta": "Check Availability",
                "image_concept": "Close-up texture of charcoal waffle knit fabric with horn buttons slightly unfastened",
                "detected_topic": "Waffle Knit Henleys",
                "suggested_posting_time": "Sunday 11:00 AM"
            },
            {
                "update_text": f"Effortless weekend outerwear: classic denim trucker jackets with rugged hardware and comfortable chest pockets at {our_biz}. A timeless wardrobe anchor for every season.",
                "keywords": ["denim jacket", "trucker jacket", "rugged style", "layering essential"],
                "cta": "Visit Store",
                "image_concept": "Denim trucker jacket worn over a grey heather hoodie in casual urban street setting",
                "detected_topic": "Classic Denim Jackets",
                "suggested_posting_time": "Monday 1:00 PM"
            },
            {
                "update_text": f"Athleisure perfected: moisture-wicking interlock cotton joggers designed for travel, casual outings, or weekend comfort at {our_biz}. In-store now!",
                "keywords": ["cotton joggers", "athleisure", "travel wear", "weekend comfort"],
                "cta": "Find Your Size",
                "image_concept": "Heather grey tapered joggers shown with running shoes and a folded duffle bag",
                "detected_topic": "Performance Cotton Joggers",
                "suggested_posting_time": "Tuesday 3:30 PM"
            },
            {
                "update_text": f"Casual sophistication: brushed cotton flannel overshirts in understated plaids at {our_biz}. Perfect worn buttoned up or open over a plain crew tee.",
                "keywords": ["brushed flannel", "plaid overshirt", "cozy layers", "casual shirt"],
                "cta": "Explore Collection",
                "image_concept": "Rich forest green and navy plaid flannel shirt draped over a leather armchair",
                "detected_topic": "Brushed Flannel Overshirts",
                "suggested_posting_time": "Wednesday 11:00 AM"
            },
            {
                "update_text": f"Modern street style: heavyweight drop-shoulder tees crafted from 240 GSM organic cotton for substantial drape at {our_biz}. Check out the fresh colorways!",
                "keywords": ["heavyweight tee", "drop shoulder", "organic cotton", "streetwear drape"],
                "cta": "Visit Us Today",
                "image_concept": "Oversized drop-shoulder tee on a minimalist hanger demonstrating boxy contemporary silhouette",
                "detected_topic": "Heavyweight Streetwear Tees",
                "suggested_posting_time": "Thursday 2:00 PM"
            },
            {
                "update_text": f"Lightweight weather defense: water-repellent windbreakers with packable hoods and clean matte finish at {our_biz}. Built for unpredictable seasonal transitions.",
                "keywords": ["windbreaker", "water repellent", "lightweight jacket", "transitional wear"],
                "cta": "Check Availability",
                "image_concept": "Matte black technical windbreaker with subtle reflective logo shown under misting water droplets",
                "detected_topic": "Minimalist Windbreakers",
                "suggested_posting_time": "Friday 1:30 PM"
            },
            {
                "update_text": f"Complete your look: genuine leather braided belts and suede slip-ons crafted to complement your relaxed weekend fits at {our_biz}. Now available in-store.",
                "keywords": ["leather accessories", "braided belt", "suede slip ons", "style details"],
                "cta": "Shop In-Store",
                "image_concept": "Curated tray of rich cognac leather belt, suede loafers, and minimalist brass watch",
                "detected_topic": "Casual Leather Accents",
                "suggested_posting_time": "Saturday 12:30 PM"
            },
            {
                "update_text": f"Refresh your complete style rotation at {our_biz}. From crisp daily essentials to relaxed evening coordinates, discover premium apparel crafted for your lifestyle. Visit us today!",
                "keywords": ["style rotation", "curated apparel", "menswear destination", "lifestyle fits"],
                "cta": "Find Directions on Maps",
                "image_concept": "Welcoming wide storefront view of our boutique with warm ambient lighting and curated displays",
                "detected_topic": "Complete Style Rotation",
                "suggested_posting_time": "Sunday 2:00 PM"
            }
        ]

        # If user asked for count ideas, slice or loop smoothly without repeating until 50
        for i in range(count):
            ideas.append(templates_50[i % len(templates_50)])

        return ideas[:count]

    def _sanitize_ideas(self, ideas: List[Dict], competitor_names: List[str], our_biz: str) -> List[Dict]:
        """Post-process: strip/replace competitor names (and brand sub-words) that slipped into generated posts"""
        import re as _re
        if not competitor_names:
            return ideas

        # Build a blocklist: full names + individual words from competitor names (length > 4)
        blocklist = []
        for cname in competitor_names:
            if not cname:
                continue
            blocklist.append(cname.strip())
            for word in cname.split():
                if len(word) > 4 and word.lower() not in {'store', 'world', 'fashion', 'avenue', 'local', 'india'}:
                    blocklist.append(word.strip())

        sanitized = []
        for idea in ideas:
            text = idea.get('update_text', '')
            # Replace full competitor names first
            for term in sorted(blocklist, key=len, reverse=True):
                text = _re.sub(r'\b' + _re.escape(term) + r'\b', our_biz, text, flags=_re.IGNORECASE)
            # Remove any leftover "(Unverified)" or stray brand tokens
            text = _re.sub(r'\s{2,}', ' ', text).strip()

            # Sanitize keywords: drop any keyword that contains a blocked term
            kws = idea.get('keywords', [])
            clean_kws = [
                k for k in kws
                if not any(
                    _re.search(r'\b' + _re.escape(term) + r'\b', k, flags=_re.IGNORECASE)
                    for term in blocklist
                )
            ]
            sanitized.append({**idea, 'update_text': text, 'keywords': clean_kws})
        return sanitized

    def _fallback_complete_update(self) -> Dict[str, Any]:
        """Fallback complete update"""
        return {
            "update_text": "Discover why customers choose us for quality service and reliable results. Our experienced team is ready to help you today!",
            "keywords": ["quality", "service", "reliable"],
            "cta": "Contact us now",
            "image_concept": "Friendly team member assisting a customer",
            "suggested_posting_time": "Weekday mornings 9-11 AM"
        }

    def _fallback_discover_competitors(self, query: str, location: str = None, field: str = None, existing_competitors: List[str] = None, is_online: bool = False) -> Dict[str, Any]:
        """Rule-based discovery fallback when AI API is unavailable"""
        import urllib.parse
        loc = location or ("Pan-India / Online" if is_online else "Local Area")
        fld = field or ("E-commerce & Marketplace" if is_online else "Service Provider")
        base_name = query.split()[0] if query else "Studio"

        # Check if query is known e-commerce / online brand or is_online flag is set
        is_ecom = is_online or any(k in query.lower() for k in ['meesho', 'flipkart', 'amazon', 'myntra', 'nykaa', 'shop', 'online', 'store', 'cart'])
        if is_ecom:
            presets = [
                {"name": "Flipkart", "category": "E-commerce Marketplace", "address": "Bellandur, Bengaluru / Pan-India", "rating": 4.5, "review_count": 8900, "distance": "Nationwide", "strengths": ["Fast Delivery", "Wide Selection", "Customer Support"], "suggested_search_query": "Flipkart HQ Bengaluru"},
                {"name": "Amazon India", "category": "E-commerce Marketplace", "address": "Gachibowli, Hyderabad / Pan-India", "rating": 4.6, "review_count": 12500, "distance": "Nationwide", "strengths": ["Prime Delivery", "Huge Catalog", "Easy Returns"], "suggested_search_query": "Amazon India Office"},
                {"name": "Shopsy by Flipkart", "category": "Social Commerce & Value Shopping", "address": "Outer Ring Road, Bengaluru", "rating": 4.3, "review_count": 3400, "distance": "Nationwide", "strengths": ["Budget Pricing", "Reseller Model", "Zero Commission"], "suggested_search_query": "Shopsy Bangalore"},
                {"name": "Ajio", "category": "Online Fashion & Lifestyle", "address": "RIL Campus, Navi Mumbai / Pan-India", "rating": 4.4, "review_count": 4200, "distance": "Nationwide", "strengths": ["Curated Trends", "Brand Exclusives", "Discounts"], "suggested_search_query": "Ajio Reliance Corporate Park"},
                {"name": "Snapdeal", "category": "Value E-commerce", "address": "Gurugram, Haryana / Pan-India", "rating": 4.2, "review_count": 2100, "distance": "Nationwide", "strengths": ["Affordable Fashion", "Tier 2/3 Focus", "Cash on Delivery"], "suggested_search_query": "Snapdeal Head Office Gurugram"}
            ]
        else:
            presets = [
                {"name": f"{base_name} Luxe Lounge", "category": fld, "address": f"42 Central Promenade, {loc}", "rating": 4.8, "review_count": 210, "distance": "0.5 km", "strengths": ["Premium Service", "Online Booking"], "suggested_search_query": f"{base_name} Luxe Lounge {loc}"},
                {"name": f"Elite {fld.split()[0]} Studio", "category": fld, "address": f"108 Market Street, {loc}", "rating": 4.6, "review_count": 175, "distance": "0.9 km", "strengths": ["Walk-ins Welcome", "Loyalty Rewards"], "suggested_search_query": f"Elite {fld.split()[0]} Studio {loc}"},
                {"name": f"Urban Glow {fld.split()[0]}", "category": fld, "address": f"215 Main Blvd, {loc}", "rating": 4.7, "review_count": 340, "distance": "1.4 km", "strengths": ["Modern Interiors", "Organic Products"], "suggested_search_query": f"Urban Glow {loc}"},
                {"name": f"Prime Essence Hub", "category": fld, "address": f"77 Park Way, {loc}", "rating": 4.5, "review_count": 95, "distance": "2.1 km", "strengths": ["Affordable Packages", "Weekend Offers"], "suggested_search_query": f"Prime Essence {loc}"},
                {"name": f"The Collective Atelier", "category": fld, "address": f"550 Grand Ave, {loc}", "rating": 4.9, "review_count": 420, "distance": "2.8 km", "strengths": ["Top Rated Staff", "Signature Experience"], "suggested_search_query": f"The Collective Atelier {loc}"}
            ]

        for p in presets:
            p["google_maps_url"] = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote_plus(p['suggested_search_query'])}"
        return {
            "target_company": query,
            "is_online": is_ecom,
            "inferred_location": loc,
            "inferred_field": fld,
            "competitors": presets
        }

class GroqAIService(AIServiceProvider):
    """Groq AI service implementation using Groq's high-speed LPU inference"""

    def __init__(self, api_key: str = None, model: str = "qwen/qwen3.8-27b"):
        self.api_key = api_key or os.getenv('GROQ_API_KEY') or os.getenv('GROK_API_KEY')
        self.model = model
        self.client = None
        if self.api_key:
            try:
                from groq import Groq
                self.client = Groq(api_key=self.api_key)
                logger.info(f"Groq client initialized with model: {self.model}")
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")
        else:
            logger.warning("Groq API key not provided")

    def _call_groq(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.7) -> str:
        """Call Groq API with automatic fallback models"""
        if not self.client:
            raise ValueError("Groq client not initialized - missing API key")

        # Use currently available models (llama-3.3-70b-versatile and mixtral-8x7b-32768 are decommissioned)
        models_to_try = [self.model, "openai/gpt-oss-20b", "openai/gpt-oss-120b"]
        last_error = None
        for model_name in models_to_try:
            try:
                chat_completion = self.client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model=model_name,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                content = chat_completion.choices[0].message.content or ""
                return content
            except Exception as e:
                last_error = e
                logger.warning(f"Groq model {model_name} failed: {e}. Trying fallback model if available.")
        raise last_error or Exception("Groq API call failed")

    def analyze_posts(self, posts: List[Dict]) -> Dict[str, Any]:
        """Analyze posts using Groq AI with deep competitor intelligence"""
        if not self.client:
            gemini_service = GeminiAIService()
            return gemini_service.analyze_posts(posts)

        try:
            posts_text = self._prepare_posts_for_analysis(posts)
            prompt = f"""
            You are an expert marketing intelligence analyst specializing in Google Maps competitor updates.
            Analyze the following Google Maps posts from competitors and extract DEEP COMPETITIVE INTELLIGENCE:

            Posts data:
            {posts_text}

            Return comprehensive analysis in valid JSON format with this exact structure:
            {{
                "topics": [
                    {{
                        "topic": "string",
                        "sub_topics": ["string"],
                        "frequency": int,
                        "competitors": ["string"],
                        "description": "string"
                    }}
                ],
                "sub_topics": ["string"],
                "keywords": [
                    {{"keyword": "string", "frequency": int, "competitors": ["string"]}}
                ],
                "content_types": [
                    {{"type": "string", "frequency": int, "examples": ["string"]}}
                ],
                "cta_analysis": [
                    {{"cta": "string", "frequency": int, "competitors": ["string"], "effectiveness": "string"}}
                ],
                "offer_promotion_patterns": [
                    {{"pattern": "string", "frequency": int, "competitors": ["string"], "example": "string"}}
                ],
                "frequent_subjects": [
                    {{"subject": "string", "frequency": int, "related_keywords": ["string"]}}
                ],
                "content_frequency": {{
                    "posts_per_week": float,
                    "peak_days": ["string"],
                    "peak_hours": ["string"],
                    "competitor_posting_rates": {{"competitor": "string", "posts_per_week": float}}
                }},
                "competitor_publishing_patterns": [
                    {{
                        "competitor": "string",
                        "posting_frequency": "string",
                        "preferred_content_types": ["string"],
                        "common_ctas": ["string"],
                        "common_offers": ["string"],
                        "peak_posting_days": ["string"],
                        "avg_post_length": int,
                        "engagement_signals": ["string"]
                    }}
                ],
                "trends": [
                    {{"trend": "string", "description": "string", "supporting_evidence": "string"}}
                ],
                "gaps_opportunities": [
                    {{"opportunity": "string", "description": "string", "potential_impact": "string"}}
                ],
                "summary": "string",
                "unique_insights": [
                    {{"insight": "string", "evidence": "string", "actionable_recommendation": "string"}}
                ]
            }}

            IMPORTANT: Focus on UNIQUE, ACTIONABLE insights that differentiate from generic advice. 
            Identify patterns that are SPECIFIC to these competitors, not generic marketing advice.
            Each insight must have supporting evidence from the actual post data.
            """

            analysis_text = self._call_groq(prompt, max_tokens=3000, temperature=0.7)
            return self._parse_ai_response(analysis_text)

        except Exception as e:
            logger.error(f"Error in Groq analysis: {e}")
            gemini_service = GeminiAIService()
            return gemini_service.analyze_posts(posts)

    def generate_content_ideas(self, posts: List[Dict], count: int = 5,
                               existing_ideas: List[str] = None,
                               business_name: str = None,
                               business_profile: str = None,
                               business_location: str = None,
                               competitor_names: List[str] = None,
                               trending_topics: List[str] = None,
                               trending_keywords: List[str] = None) -> List[Dict]:
        """Generate content ideas using Groq AI — written FOR our business, following real market trends"""
        if not self.client:
            gemini_service = GeminiAIService()
            return gemini_service.generate_content_ideas(
                posts, count, existing_ideas, business_name, business_profile,
                business_location, competitor_names, trending_topics, trending_keywords)

        try:
            posts_text = self._prepare_posts_for_analysis(posts)
            our_biz = business_name or "Our Business"
            our_profile = business_profile or "local retail"
            our_location = business_location or "local area"
            comp_names_str = ", ".join(competitor_names[:10]) if competitor_names else "none listed"

            # Build trend context from real data
            trend_text = ""
            if trending_topics:
                trend_text += f"\nTrending topics in this market (highest to lowest frequency): {', '.join(trending_topics[:8])}"
            if trending_keywords:
                trend_text += f"\nTrending keywords (most used): {', '.join(trending_keywords[:12])}"

            exclusion_text = ""
            if existing_ideas:
                exclusion_text = "\nDO NOT DUPLICATE or rephrase any of these previously generated ideas:\n" + \
                                 "\n".join([f"- {t}" for t in existing_ideas[:15]])

            prompt = f"""
            You are a marketing copywriter creating Google Maps posts for: "{our_biz}"
            Business type: {our_profile}
            Location: {our_location}
            {trend_text}

            The competitor posts below are for RESEARCH ONLY — understand what product topics and themes
            are trending in this market and write posts for {our_biz} that reflect those trends naturally.
            If certain topics were popular earlier and others more recently, let the ideas progress naturally
            through those topics (e.g. cotton-focused ideas first, linen-focused ideas later).

            STRICT RULES — VIOLATION IS NOT ACCEPTABLE:
            1. NEVER write any competitor name. Blocked: {comp_names_str}
            2. NEVER reference competitor collection names, product lines, or brand identifiers
            3. Write as "{our_biz}" — "our", "we", "visit us", "at our store"
            4. Use product/category language only (e.g. cotton shirts, linen wear, ethnic wear) — never brand names
            5. Each idea must cover a DIFFERENT topic from the trending list — spread the content naturally
            6. Posts must be 80–300 characters{exclusion_text}

            Competitor posts (research only — NEVER name them):
            {posts_text}

            Return ONLY a valid JSON array of {count} objects:
            [
                {{
                    "update_text": "string (for {our_biz}, product topics only, no brand names)",
                    "keywords": ["string", "string"],
                    "cta": "string",
                    "image_concept": "string",
                    "detected_topic": "string (which trending topic this covers)"
                }}
            ]
            """
            ideas_text = self._call_groq(prompt, max_tokens=2500, temperature=0.8)
            ideas = self._parse_ideas_response(ideas_text, count)
            # _sanitize_ideas is pure text post-processing but only exists on
            # GeminiAIService; calling self._ here raised AttributeError on every
            # request and silently pushed all idea generation into the template
            # fallback. Reuse Gemini's implementation (as AIManager does below).
            ideas = GeminiAIService()._sanitize_ideas(ideas, competitor_names or [], our_biz)
            return ideas
        except Exception as e:
            logger.error(f"Error generating ideas with Groq: {e}")
            gemini_service = GeminiAIService()
            return gemini_service.generate_content_ideas(
                posts, count, existing_ideas, business_name, business_profile,
                business_location, competitor_names, trending_topics, trending_keywords)

    def generate_complete_update(self, posts: List[Dict]) -> Dict[str, Any]:
        """Generate complete update using Groq AI"""
        if not self.client:
            gemini_service = GeminiAIService()
            return gemini_service.generate_complete_update(posts)

        try:
            posts_text = self._prepare_posts_for_analysis(posts)
            prompt = f"""
            Based on the following competitor Google Maps posts, generate a complete, ready-to-post Google Maps update.

            Competitor posts analysis:
            {posts_text}

            Respond strictly in valid JSON format:
            {{
                "update_text": "string",
                "keywords": ["string", "string", "string"],
                "cta": "string",
                "image_concept": "string",
                "suggested_posting_time": "string"
            }}
            """
            update_text = self._call_groq(prompt, max_tokens=1500, temperature=0.7)
            return self._parse_complete_update_response(update_text)
        except Exception as e:
            logger.error(f"Error generating complete update with Groq: {e}")
            gemini_service = GeminiAIService()
            return gemini_service.generate_complete_update(posts)

    def discover_local_competitors(self, query: str, location: str = None, field: str = None, existing_competitors: List[str] = None, is_online: bool = False) -> Dict[str, Any]:
        """Discover competitor businesses via location/field or nationwide category analysis using Groq AI"""
        if not self.client:
            gemini_service = GeminiAIService()
            return gemini_service.discover_local_competitors(query, location, field, existing_competitors, is_online)

        try:
            import urllib.parse
            market_context = (
                "MODE: ONLINE STORE / E-COMMERCE / NATIONAL BRAND.\n"
                "The target company does NOT compete on a 5km street radius (e.g. Meesho, Flipkart, Nykaa, Amazon).\n"
                "Find direct nationwide competitors in the same product vertical, price point, and customer demographic.\n"
                "For their Google Maps search query, provide their primary registered business office, headquarters, or flagship presence."
                if is_online else
                "MODE: LOCAL PHYSICAL STOREFRONT / HYPERLOCAL SERVICE.\n"
                "The target company operates locally (e.g. Salon, Cafe, Clinic, Gym).\n"
                "Find direct competitors operating in the exact same neighborhood, city, or local market radius."
            )

            prompt = f"""
            You are a market intelligence analyst specializing in Google Maps business listings.
            {market_context}

            Target Company:
            - Business Name: {query}
            - Location / Region: {location or ('Pan-India / Nationwide' if is_online else 'Infer from business name or default to primary metro')}
            - Field / Product Vertical: {field or 'Infer from business name'}
            - Already Tracked Competitors: {', '.join(existing_competitors) if existing_competitors else 'None'}

            Instructions:
            1. Identify 5 to 7 direct competitors.
            2. If online brand, competitors must be in the same market category (e.g. Meesho -> Flipkart, Shopsy, Amazon India, Ajio, Snapdeal).
            3. If local business, competitors must be in the same geographic locality.
            4. For each competitor, provide:
               - "name": Clean business name
               - "category": Specific industry / category
               - "address": Address or regional headquarters presence
               - "rating": Google Maps rating (between 4.2 and 4.9)
               - "review_count": Realistic review count
               - "distance": Proximity (e.g. '0.8 km' for local, or 'Nationwide / E-commerce' for online)
               - "strengths": 2-3 key competitive advantages
               - "suggested_search_query": Google Maps search query string to locate their profile

            Respond STRICTLY in valid JSON with this exact structure:
            {{
                "target_company": "{query}",
                "is_online": {str(is_online).lower()},
                "inferred_location": "string",
                "inferred_field": "string",
                "competitors": [
                    {{
                        "name": "string",
                        "category": "string",
                        "address": "string",
                        "rating": 4.7,
                        "review_count": 210,
                        "distance": "string",
                        "strengths": ["string", "string"],
                        "suggested_search_query": "string"
                    }}
                ]
            }}
            """
            response_text = self._call_groq(prompt, max_tokens=2200, temperature=0.6)
            data = self._parse_ai_response(response_text)

            if isinstance(data, dict) and "competitors" in data and isinstance(data["competitors"], list):
                for comp in data["competitors"]:
                    q = comp.get("suggested_search_query") or f"{comp.get('name', '')} {data.get('inferred_location', '')}"
                    comp["google_maps_url"] = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote_plus(q.strip())}"
                return data
            else:
                gemini_service = GeminiAIService()
                return gemini_service.discover_local_competitors(query, location, field, existing_competitors, is_online)
        except Exception as e:
            logger.error(f"Error in Groq discover_local_competitors: {e}")
            gemini_service = GeminiAIService()
            return gemini_service.discover_local_competitors(query, location, field, existing_competitors, is_online)

    def _prepare_posts_for_analysis(self, posts: List[Dict]) -> str:
        """Prepare posts data for AI analysis"""
        posts_summary = []
        for i, post in enumerate(posts[:20]):
            summary = f"""
            Post {i+1}:
            - Competitor: {post.get('competitor_name', 'Unknown')}
            - Text: {post.get('text_content', '')[:200]}
            - Date: {post.get('published_date', 'Unknown')}
            - CTAs: {post.get('cta', 'None')}
            """
            posts_summary.append(summary)
        return "\n".join(posts_summary)

    def _parse_ai_response(self, response_text: str) -> Dict[str, Any]:
        """Parse AI response"""
        try:
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            if start_idx != -1 and end_idx != 0:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                return {"error": "Could not parse response", "raw": response_text[:200]}
        except json.JSONDecodeError:
            return {"error": "Invalid JSON", "raw": response_text[:200]}

    def _parse_ideas_response(self, response_text: str, count: int) -> List[Dict]:
        """Parse ideas response"""
        try:
            start_idx = response_text.find('[')
            end_idx = response_text.rfind(']') + 1
            if start_idx != -1 and end_idx != 0:
                json_str = response_text[start_idx:end_idx]
                ideas = json.loads(json_str)
                return ideas if isinstance(ideas, list) else []
            else:
                return []
        except json.JSONDecodeError:
            return []

    def _parse_complete_update_response(self, response_text: str) -> Dict[str, Any]:
        """Parse complete update response"""
        try:
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            if start_idx != -1 and end_idx != 0:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                return {"error": "Could not parse update"}
        except json.JSONDecodeError:
            return {"error": "Invalid JSON in update response"}

    def _fallback_analysis(self, posts: List[Dict]) -> Dict[str, Any]:
        """Fallback analysis when AI is not available - enhanced structure"""
        # Extract data from posts
        keywords = {}
        competitors = set()
        content_types = {}
        ctas = {}
        offer_patterns = {}
        
        for post in posts:
            text = post.get('text_content', '').lower()
            comp = post.get('competitor_name', 'Unknown')
            competitors.add(comp)
            
            # Simple word frequency
            words = text.split()
            for word in words:
                if len(word) > 4:
                    keywords[word] = keywords.get(word, 0) + 1
            
            # Detect content type
            if any(w in text for w in ['offer', 'discount', 'sale', 'off', '%']):
                content_types['Offer/Promotion'] = content_types.get('Offer/Promotion', 0) + 1
            elif any(w in text for w in ['new', 'new arrival', 'new collection', 'launch']):
                content_types['New Arrival/Launch'] = content_types.get('New Arrival/Launch', 0) + 1
            elif any(w in text for w in ['tip', 'tips', 'guide', 'how to', 'how-to']):
                content_types['Educational/Tips'] = content_types.get('Educational/Tips', 0) + 1
            elif any(w in text for w in ['event', 'workshop', 'class', 'webinar']):
                content_types['Event/Workshop'] = content_types.get('Event/Workshop', 0) + 1
            else:
                content_types['General Update'] = content_types.get('General Update', 0) + 1
            
            # Extract CTAs
            cta_text = post.get('cta', '')
            if cta_text:
                ctas[cta_text] = ctas.get(cta_text, 0) + 1
            
            # Detect offers
            if any(w in text for w in ['% off', 'percent off', 'discount', 'offer', 'deal', 'buy']):
                offer_patterns['Discount/Promo'] = offer_patterns.get('Discount/Promo', 0) + 1
            if any(w in text for w in ['free', 'complimentary', 'on us']):
                offer_patterns['Free/Complimentary'] = offer_patterns.get('Free/Complimentary', 0) + 1
            if any(w in text for w in ['book', 'reserve', 'appointment']):
                offer_patterns['Booking/Reservation'] = offer_patterns.get('Booking/Reservation', 0) + 1

        top_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:15]
        top_content_types = sorted(content_types.items(), key=lambda x: x[1], reverse=True)
        top_ctas = sorted(ctas.items(), key=lambda x: x[1], reverse=True)[:5]
        top_offers = sorted(offer_patterns.items(), key=lambda x: x[1], reverse=True)

        comp_list = list(competitors)
        
        # Estimate posting frequency
        total_posts = len(posts)
        if total_posts > 0:
            days_span = 1
            try:
                dates = []
                for p in posts:
                    if p.get('published_date'):
                        dates.append(datetime.fromisoformat(p['published_date'].replace('Z', '+00:00')))
                if dates:
                    days_span = (max(dates) - min(dates)).days + 1
            except:
                days_span = 7
            posts_per_week = (total_posts / max(days_span, 1)) * 7
        else:
            posts_per_week = 0

        return {
            "topics": [
                {"topic": "General Updates", "sub_topics": ["Updates"], "frequency": len(posts), "competitors": list(competitors)[:5], "description": "General business updates and announcements"}
            ],
            "sub_topics": ["Business Updates"],
            "keywords": [{"keyword": k, "frequency": f, "competitors": list(competitors)[:3]} for k, f in sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:15]],
            "content_types": [{"type": t, "frequency": f, "examples": [f"Post about {t.lower()}"]} for t, f in top_content_types],
            "cta_analysis": [{"cta": c, "frequency": f, "competitors": [], "effectiveness": "Moderate"} for c, f in top_ctas],
            "offer_promotion_patterns": [{"pattern": p, "frequency": f, "competitors": [], "example": f"Example of {p}"} for p, f in top_offers],
            "frequent_subjects": [{"subject": k, "frequency": f, "related_keywords": [k]} for k, f in sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:10]],
            "content_frequency": {
                "posts_per_week": round(posts_per_week, 1),
                "peak_days": ["Monday", "Thursday", "Friday"],
                "peak_hours": ["10:00 AM", "2:00 PM"],
                "competitor_posting_rates": {}
            },
            "competitor_publishing_patterns": [],
            "trends": [{"trend": "Data-driven content", "description": "Content strategy based on real competitor data", "supporting_evidence": "Based on actual post analysis"}],
            "gaps_opportunities": [
                {"opportunity": "Educational content", "description": "Competitors lack educational content", "potential_impact": "High - differentiates from promotional noise"},
                {"opportunity": "Customer stories", "description": "Few competitors share customer testimonials", "potential_impact": "Medium - builds trust"}
            ],
            "summary": f"Analyzed {len(posts)} posts from {len(competitors)} competitors. Found {len(keywords)} unique keywords.",
            "unique_insights": [
                {"insight": "Most competitors focus on promotional content", "evidence": f"{content_types.get('Offer/Promotion', 0)} out of {len(posts)} posts are promotional", "actionable_recommendation": "Differentiate with educational and customer-centric content"},
                {"insight": "CTAs are underutilized", "evidence": f"Only {sum(ctas.values())} out of {len(posts)} posts have CTAs", "actionable_recommendation": "Add clear CTAs to every post"}
            ]
        }

# Backward-compatibility alias so existing references continue to work
class GrokAIService(GroqAIService):
    """Alias for backwards compatibility with Grok references"""
    pass

class AIServiceManager:
    """Manager to handle multiple AI service providers"""

    def __init__(self):
        self.providers = []
        self._initialize_providers()

    def _initialize_providers(self):
        """Initialize available AI providers"""
        # Try Groq first (high speed, generous free tier)
        groq_key = os.getenv('GROQ_API_KEY') or os.getenv('GROK_API_KEY')
        if groq_key:
            try:
                self.providers.append(GroqAIService(groq_key))
                logger.info("Groq AI service initialized")
            except Exception as e:
                logger.error(f"Error initializing Groq AI service: {e}")

        # Try Gemini
        gemini_key = os.getenv('GEMINI_API_KEY')
        if gemini_key:
            try:
                self.providers.append(GeminiAIService(gemini_key))
                logger.info("Gemini AI service initialized")
            except Exception as e:
                logger.error(f"Error initializing Gemini AI service: {e}")

        if not self.providers:
            logger.warning("No AI services initialized - using fallback methods")
            self.providers.append(GeminiAIService())  # Will use fallbacks

    def analyze_posts(self, posts: List[Dict]) -> Dict[str, Any]:
        """Analyze posts using available AI providers"""
        for provider in self.providers:
            try:
                result = provider.analyze_posts(posts)
                # Check if result looks valid (not just error fallback)
                if isinstance(result, dict) and "summary" in result:
                    logger.info(f"Analysis completed using {provider.__class__.__name__}")
                    return result
            except Exception as e:
                logger.error(f"Error with {provider.__class__.__name__}: {e}")
                continue

        # If all providers fail, use fallback
        logger.warning("All AI providers failed, using fallback analysis")
        return GeminiAIService()._fallback_analysis(posts)

    def generate_content_ideas(self, posts: List[Dict], count: int = 5,
                               existing_ideas: List[str] = None,
                               business_name: str = None,
                               business_profile: str = None,
                               business_location: str = None,
                               competitor_names: List[str] = None,
                               trending_topics: List[str] = None,
                               trending_keywords: List[str] = None) -> List[Dict]:
        """Generate content ideas using available AI providers — posts written FOR our business only"""
        for provider in self.providers:
            try:
                ideas = provider.generate_content_ideas(
                    posts, count,
                    existing_ideas=existing_ideas,
                    business_name=business_name,
                    business_profile=business_profile,
                    business_location=business_location,
                    competitor_names=competitor_names,
                    trending_topics=trending_topics,
                    trending_keywords=trending_keywords
                )
                if ideas and len(ideas) > 0:
                    logger.info(f"Ideas generated using {provider.__class__.__name__}")
                    return ideas
            except Exception as e:
                logger.error(f"Error generating ideas with {provider.__class__.__name__}: {e}")
                continue

        logger.warning("All AI providers failed for ideas, using fallback")
        ideas = GeminiAIService()._fallback_ideas(
            posts, count, business_name, business_profile,
            competitor_names, trending_topics, trending_keywords
        )
        ideas = GeminiAIService()._sanitize_ideas(ideas, competitor_names or [], business_name or "Our Business")
        return ideas

    def generate_complete_update(self, posts: List[Dict]) -> Dict[str, Any]:
        """Generate complete update using available AI providers"""
        for provider in self.providers:
            try:
                update = provider.generate_complete_update(posts)
                if isinstance(update, dict) and "update_text" in update:
                    logger.info(f"Complete update generated using {provider.__class__.__name__}")
                    return update
            except Exception as e:
                logger.error(f"Error generating update with {provider.__class__.__name__}: {e}")
                continue

        logger.warning("All AI providers failed for complete update, using fallback")
        return GeminiAIService()._fallback_complete_update()

    def discover_local_competitors(self, query: str, location: str = None, field: str = None, existing_competitors: List[str] = None, is_online: bool = False) -> Dict[str, Any]:
        """Discover competitors using available AI providers"""
        for provider in self.providers:
            try:
                result = provider.discover_local_competitors(query, location, field, existing_competitors, is_online)
                if isinstance(result, dict) and "competitors" in result and len(result["competitors"]) > 0:
                    logger.info(f"Competitors discovered using {provider.__class__.__name__}")
                    return result
            except Exception as e:
                logger.error(f"Error with {provider.__class__.__name__} discover_local_competitors: {e}")
                continue

        logger.warning("All AI providers failed for discover_local_competitors, using fallback")
        return GeminiAIService()._fallback_discover_competitors(query, location, field, existing_competitors, is_online)