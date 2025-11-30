"""
Query processing and enhancement for better retrieval.
Handles query understanding, expansion, and normalization.
"""

import re
from typing import List, Optional, Set, Tuple

import structlog

logger = structlog.get_logger()


class QueryProcessor:
    """
    Query processor for enhancing search queries.

    Features:
    - Query normalization
    - Synonym expansion
    - Intent classification
    - Entity extraction
    - Query rewriting
    """

    def __init__(self):
        # Planning domain synonyms
        self.synonyms = {
            # Building types
            "extension": ["addition", "enlargement", "outbuilding"],
            "loft": ["attic", "roof space", "dormer", "mansard"],
            "basement": ["cellar", "subterranean", "underground"],
            "conservatory": ["sunroom", "garden room", "orangery"],
            "garage": ["car port", "parking space"],
            "outbuilding": ["garden building", "shed", "summer house", "annexe"],

            # Planning terms
            "planning permission": ["planning consent", "planning approval", "development permission"],
            "permitted development": ["pd rights", "pd", "prior approval"],
            "building regulations": ["building control", "building regs"],
            "conservation area": ["conservation", "protected area", "heritage area"],
            "listed building": ["heritage building", "historic building", "grade listed"],
            "article 4": ["article 4 direction", "article four"],

            # Work types
            "demolition": ["knock down", "tear down", "removal"],
            "renovation": ["refurbishment", "restoration", "modernization"],
            "change of use": ["use class", "conversion"],

            # Dimensions
            "height": ["tall", "high", "metres high"],
            "depth": ["deep", "metres deep"],
            "width": ["wide", "metres wide"],
        }

        # Intent patterns
        self.intent_patterns = {
            "requirement_check": [
                r"do i need",
                r"is .* required",
                r"will i need",
                r"do .* require",
                r"is it necessary",
            ],
            "process_inquiry": [
                r"how (do|can) i",
                r"what is the process",
                r"how long does",
                r"what are the steps",
                r"how to apply",
            ],
            "rule_inquiry": [
                r"what are the rules",
                r"what are the regulations",
                r"what is allowed",
                r"what is the limit",
                r"maximum .* allowed",
            ],
            "cost_inquiry": [
                r"how much does .* cost",
                r"what is the fee",
                r"application fee",
                r"how much for",
            ],
            "time_inquiry": [
                r"how long",
                r"time .* take",
                r"duration",
                r"when will",
            ],
        }

        # UK postcode pattern
        self.postcode_pattern = re.compile(
            r"\b([A-Z]{1,2}\d{1,2}[A-Z]?\s*\d[A-Z]{2})\b",
            re.IGNORECASE
        )

        # Borough detection patterns
        self.borough_patterns = {
            "Camden": [
                r"\bcamden\b", r"\bhampstead\b", r"\bbelsize\b",
                r"\bprimrose hill\b", r"\bkentish town\b", r"\bgospel oak\b",
                r"\bholborn\b", r"\bbloomsbury\b", r"\bking'?s cross\b",
                r"\bwest hampstead\b", r"\bswiss cottage\b",
                r"\bnw3\b", r"\bnw5\b", r"\bnw1\b", r"\bwc1\b",
            ],
            "Barnet": [
                r"\bbarnet\b", r"\bfinchley\b", r"\bgolders green\b",
                r"\bhendon\b", r"\bmill hill\b", r"\bedgware\b",
                r"\btotteridge\b", r"\bwhetstone\b", r"\bfriern barnet\b",
                r"\bn3\b", r"\bn2\b", r"\bnw4\b", r"\bnw7\b", r"\bnw11\b",
            ],
            "Westminster": [
                r"\bwestminster\b", r"\bmarylebone\b", r"\bmayfair\b",
                r"\bsoho\b", r"\bfitzrovia\b", r"\bpimlico\b",
                r"\bbelgravia\b", r"\bpadding?ton\b", r"\bbayswater\b",
                r"\bw1\b", r"\bw2\b", r"\bsw1\b", r"\bnw8\b",
            ],
            "Brent": [
                r"\bbrent\b", r"\bwembley\b", r"\bwillesden\b",
                r"\bkilburn\b", r"\bneasden\b", r"\bkingsbury\b",
                r"\bharlesden\b", r"\balperton\b", r"\bstonebridge\b",
                r"\bnw10\b", r"\bnw2\b", r"\bha0\b", r"\bha9\b",
            ],
            "Haringey": [
                r"\bharingey\b", r"\bhighgate\b", r"\bcrouch end\b",
                r"\bmuswell hill\b", r"\bhornsey\b", r"\btottenham\b",
                r"\bwood green\b", r"\bbounds green\b", r"\bstroud green\b",
                r"\bn6\b", r"\bn8\b", r"\bn10\b", r"\bn22\b",
            ],
        }

        # Topic detection patterns
        self.topic_patterns = {
            "basement": [
                r"\bbasement\b", r"\bsubterranean\b", r"\bcellar\b",
                r"\bunderground\b", r"\blower ground\b", r"\blight well\b",
            ],
            "extension": [
                r"\bextension\b", r"\brear extension\b", r"\bside extension\b",
                r"\bwrap.?around\b", r"\bsingle.?storey\b", r"\bdouble.?storey\b",
                r"\bground floor extension\b",
            ],
            "loft": [
                r"\bloft\b", r"\bdormer\b", r"\broof extension\b",
                r"\bmansard\b", r"\battic\b", r"\broof conversion\b",
                r"\bhip.?to.?gable\b",
            ],
            "roof": [
                r"\broof\b", r"\brooflight\b", r"\bskylight\b",
                r"\bsolar panel\b", r"\bpv panel\b", r"\bantenna\b",
                r"\bchimney\b", r"\bvelux\b",
            ],
            "windows": [
                r"\bwindow\b", r"\bglazing\b", r"\bfenestration\b",
                r"\bfront elevation\b", r"\breplacement window\b",
            ],
            "conservation": [
                r"\bconservation area\b", r"\bheritage\b", r"\blisted building\b",
                r"\barticle 4\b", r"\bgrade.?[iI]{1,3}\b", r"\bhistoric\b",
            ],
            "permitted_development": [
                r"\bpermitted development\b", r"\bpd rights?\b",
                r"\bprior approval\b", r"\bprior notification\b",
            ],
            "change_of_use": [
                r"\bchange of use\b", r"\buse class\b", r"\bconversion\b",
                r"\bflat conversion\b", r"\bhmo\b",
            ],
        }

    def process_query(self, query: str) -> dict:
        """
        Process and enhance a query.

        Returns:
            Dict with processed query info:
            - normalized: cleaned query
            - expanded: query with synonyms
            - intent: detected intent
            - entities: extracted entities
            - borough: detected borough
            - topic: detected topic
            - postcode: detected postcode
        """
        normalized = self._normalize(query)

        return {
            "original": query,
            "normalized": normalized,
            "expanded": self._expand_synonyms(normalized),
            "intent": self._detect_intent(normalized),
            "entities": self._extract_entities(normalized),
            "borough": self._detect_borough(query),
            "topic": self._detect_topic(normalized),
            "postcode": self._extract_postcode(query),
            "keywords": self._extract_keywords(normalized),
        }

    def _normalize(self, query: str) -> str:
        """Normalize query text."""
        # Lowercase
        normalized = query.lower().strip()
        # Remove extra whitespace
        normalized = " ".join(normalized.split())
        # Remove punctuation except hyphens and apostrophes
        normalized = re.sub(r"[^\w\s\-'?]", " ", normalized)
        return normalized

    def _expand_synonyms(self, query: str) -> str:
        """Expand query with synonyms."""
        expanded_terms = []

        for term, synonyms in self.synonyms.items():
            if term in query:
                expanded_terms.extend(synonyms)

        if expanded_terms:
            return f"{query} {' '.join(expanded_terms)}"
        return query

    def _detect_intent(self, query: str) -> str:
        """Detect query intent."""
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    return intent
        return "general_inquiry"

    def _extract_entities(self, query: str) -> dict:
        """Extract named entities from query."""
        entities = {
            "dimensions": [],
            "dates": [],
            "building_parts": [],
        }

        # Extract dimensions
        dimension_pattern = r"(\d+(?:\.\d+)?)\s*(metres?|m|feet|ft|cm)"
        for match in re.finditer(dimension_pattern, query, re.IGNORECASE):
            entities["dimensions"].append({
                "value": float(match.group(1)),
                "unit": match.group(2).lower(),
            })

        # Extract building parts
        building_parts = [
            "front", "rear", "side", "roof", "basement", "ground floor",
            "first floor", "garden", "boundary", "wall", "window", "door",
        ]
        for part in building_parts:
            if part in query:
                entities["building_parts"].append(part)

        return entities

    def _detect_borough(self, query: str) -> Optional[str]:
        """Detect borough from query."""
        for borough, patterns in self.borough_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    return borough
        return None

    def _detect_topic(self, query: str) -> Optional[str]:
        """Detect planning topic from query."""
        for topic, patterns in self.topic_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    return topic
        return None

    def _extract_postcode(self, query: str) -> Optional[str]:
        """Extract UK postcode from query."""
        match = self.postcode_pattern.search(query)
        if match:
            return match.group(1).upper().replace(" ", " ")
        return None

    def _extract_keywords(self, query: str) -> List[str]:
        """Extract important keywords from query."""
        # Remove stop words
        stop_words = {
            "a", "an", "the", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "must", "shall",
            "can", "need", "dare", "ought", "used", "to", "of", "in",
            "for", "on", "with", "at", "by", "from", "as", "into",
            "through", "during", "before", "after", "above", "below",
            "between", "under", "again", "further", "then", "once",
            "here", "there", "when", "where", "why", "how", "all",
            "each", "few", "more", "most", "other", "some", "such",
            "no", "nor", "not", "only", "own", "same", "so", "than",
            "too", "very", "just", "i", "me", "my", "we", "our",
        }

        words = re.findall(r"\b\w+\b", query)
        keywords = [w for w in words if w not in stop_words and len(w) > 2]

        return keywords

    def generate_search_queries(self, query: str) -> List[str]:
        """
        Generate multiple search queries for better retrieval.

        Returns multiple variations of the query for ensemble search.
        """
        processed = self.process_query(query)
        queries = [processed["normalized"]]

        # Add expanded version
        if processed["expanded"] != processed["normalized"]:
            queries.append(processed["expanded"])

        # Add topic-specific query
        if processed["topic"]:
            topic_query = f"{processed['topic']} {processed['normalized']}"
            queries.append(topic_query)

        # Add borough-specific query
        if processed["borough"]:
            borough_query = f"{processed['borough']} {processed['normalized']}"
            queries.append(borough_query)

        # Add keyword-focused query
        if processed["keywords"]:
            keyword_query = " ".join(processed["keywords"][:5])
            queries.append(keyword_query)

        return queries

    def rewrite_for_retrieval(self, query: str) -> str:
        """
        Rewrite query for optimal retrieval.

        Transforms conversational queries into search-friendly format.
        """
        processed = self.process_query(query)

        # Start with normalized query
        rewritten = processed["normalized"]

        # Add context based on intent
        intent = processed["intent"]
        if intent == "requirement_check":
            rewritten = f"planning permission requirements {rewritten}"
        elif intent == "process_inquiry":
            rewritten = f"planning application process {rewritten}"
        elif intent == "rule_inquiry":
            rewritten = f"planning rules regulations {rewritten}"

        # Add topic context
        if processed["topic"]:
            rewritten = f"{processed['topic']} {rewritten}"

        return rewritten


# Global instance
query_processor = QueryProcessor()
