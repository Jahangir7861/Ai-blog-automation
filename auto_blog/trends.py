import time
import random
import json
from pytrends.request import TrendReq
from .config import TRENDS_HL, TRENDS_TIMEZONE
from .content import query_llm

class KeywordResearcher:
    def __init__(self):
        self.pytrends = TrendReq(hl=TRENDS_HL, tz=TRENDS_TIMEZONE)

    def suggest_niches(self):
        """
        Asks LLM for 5 trending/hot niches.
        """
        prompt = """
        Suggest 5 currently trending, high-potential blog niches for 2024-2025.
        Focus on profitable, evergreen, or breakout topics (e.g., AI tools, Sustainable Living, etc.).
        Return ONLY the niche names as a JSON list of strings.
        Example: ["AI Productivity Tools", "Urban Gardening", "Digital Minimalism"]
        """
        try:
            text = query_llm(prompt)
            # clean json
            start = text.find('[')
            end = text.rfind(']') + 1
            if start != -1 and end != -1:
                return json.loads(text[start:end])
            return ["AI Tools", "Sustainable Living", "Home Office Setup", "Personal Finance", "Healthy Meal Prep"]
        except:
            return ["Technology", "Health", "Finance", "Travel", "Food"]

    def generate_seeds(self, niche, sub_niche=""):
        """
        Generates seed keywords using LLM.
        """
        prompt = f"""
        Act as a Keyword Research Expert.
        Generate 30 specific, long-tail seed keywords for the niche: "{niche}" {f'and sub-niche: "{sub_niche}"' if sub_niche else ''}.
        
        CRITICAL REQUIREMENTS:
        1. Focus ONLY on **Informational** intent (How-to, Guides, Ideas, Tips, Mistakes).
        2. Focus on **Low Competition** / Underserved topics.
        
        Include mix of:
        - "How to [niche]..."
        - "Tips for [niche]..."
        - "Why [niche]..."
        - "Examples of [niche]..."
        
        Return ONLY the keywords, one per line. No numbering.
        """
        text = query_llm(prompt)
        if not text: return []
        return [line.strip() for line in text.split('\n') if line.strip()]

    def get_trend_data(self, keywords, region='US', time_range='today 3-m'):
        """
        Fetches trend interest (0-100) from Google Trends.
        Returns a dict: {keyword: score}
        """
        scores = {}
        # Batch requests to avoid rate limits (5 at a time is pytrends limit usually)
        chunk_size = 1 # reduced to 1 to be safe and avoid 429s as much as possible with backoff
        
        # print(f"Fetching Trends data for {len(keywords)} keywords in {region}...")
        
        for kw in keywords:
            try:
                # Random sleep to play nice
                time.sleep(random.uniform(1, 2)) 
                self.pytrends.build_payload([kw], cat=0, timeframe=time_range, geo=region, gprop='')
                data = self.pytrends.interest_over_time()
                if not data.empty:
                    # Get average interest over the period
                    avg_score = data[kw].mean()
                    scores[kw] = round(avg_score, 1)
                else:
                    scores[kw] = 0
            except Exception as e:
                # print(f"Trends Error for {kw}: {e}")
                # Fallback: Assign a random low-ish score or 0
                scores[kw] = 0
        
        return scores

    def analyze_metrics_llm(self, keywords, region='US'):
        """
        Uses LLM to estimate Volume, KD, and Intent.
        """
        # Process in chunks to fit context window
        results = {}
        chunk_size = 20
        
        for i in range(0, len(keywords), chunk_size):
            chunk = keywords[i:i+chunk_size]
            
            prompt = f"""
            Analyze the following keywords for the {region} market.
            Estimate the following metrics for each:
            1. Monthly Search Volume (Volume): Number (e.g. 500, 10000)
            2. Keyword Difficulty (KD): 0-100 (0=Easy, 100=Hard)
            3. Search Intent (Intent): Informational, Commercial, Transactional, or Navigational.
            
            Keywords:
            {", ".join(chunk)}
            
            Return the result as a JSON object where keys are keywords and values are objects with "volume", "kd", "intent".
            Example:
            {{
              "keyword1": {{ "volume": 5000, "kd": 20, "intent": "Informational" }},
              ...
            }}
            """
            try:
                text = query_llm(prompt, reasoning_enabled=True)
                # Extract JSON
                start = text.find('{')
                end = text.rfind('}') + 1
                if start != -1 and end != -1:
                    json_data = json.loads(text[start:end])
                    results.update(json_data)
            except Exception as e:
                print(f"LLM Analysis failed: {e}")
                
        return results

    def analyze_niche(self, niche, sub_niche="", region='US', time_range='today 3-m'):
        """
        Orchestrates the full 7-step analysis.
        """
        # Step 1: Seeds
        seeds = self.generate_seeds(niche, sub_niche)
        if not seeds: return []
        
        # Step 2: Trends (Real Data)
        # Filter: If trend < 10, maybe discard? Let's keep data for scoring.
        trend_scores = self.get_trend_data(seeds[:10], region, time_range) # LIMIT TO 10 for speed in demo/dev
        
        # Step 3, 4, 5: Metrics (LLM)
        valid_seeds = list(trend_scores.keys())
        llm_metrics = self.analyze_metrics_llm(valid_seeds, region)
        
        final_results = []
        
        for kw in valid_seeds:
            metrics = llm_metrics.get(kw, {'volume': 0, 'kd': 50, 'intent': 'Informational'})
            
            trend = trend_scores.get(kw, 0)
            vol = metrics.get('volume', 0)
            kd = metrics.get('kd', 50)
            intent_str = metrics.get('intent', 'Informational')
            
            # --- STRICT FILTERING REMOVED (User Request) ---
            # We now allow all intents but score them appropriately
            # ---------------------------------------
            
            
            # Step 5: Intent Mapping
            intent_map = {
                'Informational': 1,
                'Commercial': 2,
                'Transactional': 2,
                'Navigational': 0
            }
            intent_score = intent_map.get(intent_str, 1)
            
            # Step 3 Validation: Volume normalization (0-100)
            vol_score = min(vol / 50.0, 100)
            
            # Step 6: Scoring Formula
            # Adjusted for Informational Focus: Boost Intent, Boost KD weight slightly
            # Intent is theoretically fixed to 1/Informational now due to filter, so it's a constant.
            # Focus on Trend & Vol mainly, KD is already low.
            
            score = (trend * 0.40) + (vol_score * 0.30) + ((100 - kd) * 0.30)
            
            final_results.append({
                'keyword': kw,
                'trend': trend,
                'volume': vol,
                'kd': kd,
                'intent': intent_str,
                'score': round(score, 1)
            })
            
        # Sort by Score
        final_results.sort(key=lambda x: x['score'], reverse=True)
        return final_results


def get_trending_keywords(sub_niche, limit=15):
    """
    Fetches keywords using a multi-layer strategy:
    1. Google Trends 'Rising' Related Queries
    2. Google Trends Autocomplete Suggestions
    3. AI Fallback (if others fail)
    """
    unique_keywords = set()
    
    # 1. Try Google Trends Related Queries
    try:
        pytrends = TrendReq(hl=TRENDS_HL, tz=TRENDS_TIMEZONE)
        pytrends.build_payload([sub_niche], cat=0, timeframe='now 7-d')
        
        related = pytrends.related_queries()
        if related and sub_niche in related:
            # Rising
            if related[sub_niche]['rising'] is not None:
                rising = related[sub_niche]['rising']
                unique_keywords.update(rising['query'].tolist())
            
            # Top
            if related[sub_niche]['top'] is not None:
                top = related[sub_niche]['top']
                unique_keywords.update(top['query'].head(5).tolist())
                
    except Exception as e:
        print(f"Trends API specific error: {e}")

    # 2. Try Suggestions (Autocomplete) - lighter on rate limits
    try:
        suggestions = pytrends.suggestions(sub_niche)
        for s in suggestions:
            unique_keywords.add(s['title'])
    except Exception as e:
        print(f"Suggestions API error: {e}")

    # Convert to list
    final_list = list(unique_keywords)
    
    # 3. AI Fallback / Augmentation
    # If we have very few results (< 5), ask AI to brainstorm more
    if len(final_list) < 5:
        ai_keywords = get_ai_fallback_keywords(sub_niche)
        final_list.extend(ai_keywords)
    
    # Shuffle and return unique list
    final_list = list(set(final_list))
    random.shuffle(final_list)
    return final_list[:limit]
