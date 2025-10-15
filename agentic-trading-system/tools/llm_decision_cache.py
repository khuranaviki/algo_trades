"""
LLM Decision Cache

Caches LLM synthesis decisions to reduce API calls and enable learning from past decisions.
Uses a similarity-based lookup to find similar historical scenarios.
"""

import json
import hashlib
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging
from pathlib import Path


class LLMDecisionCache:
    """
    Cache for LLM conflict resolution decisions

    Features:
    1. Cache exact matches (same ticker + similar scores)
    2. Find similar historical decisions
    3. Learn patterns over time
    4. Reduce LLM dependency
    """

    def __init__(self, cache_dir: str = "storage/llm_decisions"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.cache_file = self.cache_dir / "decisions.jsonl"
        self.stats_file = self.cache_dir / "cache_stats.json"

        self.logger = logging.getLogger(__name__)
        self.stats = self._load_stats()

    def _load_stats(self) -> Dict[str, Any]:
        """Load cache statistics"""
        if self.stats_file.exists():
            with open(self.stats_file, 'r') as f:
                return json.load(f)
        return {
            'total_decisions': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'similar_matches': 0,
            'hit_rate': 0.0
        }

    def _save_stats(self):
        """Save cache statistics"""
        if self.stats['total_decisions'] > 0:
            self.stats['hit_rate'] = (
                (self.stats['cache_hits'] + self.stats['similar_matches']) /
                self.stats['total_decisions']
            ) * 100

        with open(self.stats_file, 'w') as f:
            json.dump(self.stats, f, indent=2)

    def _create_cache_key(
        self,
        ticker: str,
        agent_scores: Dict[str, float],
        conflict_level: str,
        composite_score: float
    ) -> str:
        """
        Create cache key for exact matching

        Key includes:
        - Ticker
        - Rounded agent scores (to nearest 5)
        - Conflict level
        - Rounded composite score
        """
        # Round scores to nearest 5 to increase cache hits
        rounded_scores = {
            agent: round(score / 5) * 5
            for agent, score in agent_scores.items()
        }
        rounded_composite = round(composite_score / 5) * 5

        key_data = {
            'ticker': ticker,
            'scores': rounded_scores,
            'conflict': conflict_level,
            'composite': rounded_composite
        }

        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()

    def _calculate_similarity(
        self,
        scores1: Dict[str, float],
        scores2: Dict[str, float]
    ) -> float:
        """
        Calculate similarity between two score sets

        Returns similarity score 0-1 (1 = identical)
        """
        if set(scores1.keys()) != set(scores2.keys()):
            return 0.0

        total_diff = 0
        for agent in scores1.keys():
            diff = abs(scores1[agent] - scores2[agent])
            total_diff += diff

        # Average difference across agents
        avg_diff = total_diff / len(scores1)

        # Convert to similarity (closer = higher)
        # Max diff is 100, so normalize
        similarity = max(0, 1 - (avg_diff / 50))  # 50 point diff = 0 similarity

        return similarity

    def get_cached_decision(
        self,
        ticker: str,
        agent_scores: Dict[str, float],
        conflict_info: Dict[str, Any],
        composite_score: float,
        similarity_threshold: float = 0.85
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached decision if available

        Args:
            ticker: Stock ticker
            agent_scores: Agent scores
            conflict_info: Conflict information
            composite_score: Composite score
            similarity_threshold: Min similarity for match (0-1)

        Returns:
            Cached decision or None
        """
        self.stats['total_decisions'] += 1

        # Try exact match first
        cache_key = self._create_cache_key(
            ticker, agent_scores,
            conflict_info['conflict_level'],
            composite_score
        )

        if not self.cache_file.exists():
            self.stats['cache_misses'] += 1
            self._save_stats()
            return None

        # Load all cached decisions
        cached_decisions = []
        with open(self.cache_file, 'r') as f:
            for line in f:
                cached_decisions.append(json.loads(line))

        # Look for exact match
        for entry in cached_decisions:
            if entry['cache_key'] == cache_key:
                self.stats['cache_hits'] += 1
                self._save_stats()

                self.logger.info(
                    f"✅ Cache HIT (exact): {ticker} "
                    f"(cached {entry.get('cached_at', 'unknown')})"
                )

                return entry['decision']

        # Look for similar match
        best_match = None
        best_similarity = 0.0

        for entry in cached_decisions:
            # Must be same ticker and conflict level
            if (entry['ticker'] != ticker or
                entry['conflict_level'] != conflict_info['conflict_level']):
                continue

            # Calculate similarity
            similarity = self._calculate_similarity(
                agent_scores,
                entry['agent_scores']
            )

            # Also consider composite score similarity
            composite_diff = abs(composite_score - entry['composite_score'])
            composite_similarity = max(0, 1 - (composite_diff / 30))

            # Combined similarity (weighted average)
            total_similarity = (similarity * 0.7 + composite_similarity * 0.3)

            if total_similarity > best_similarity and total_similarity >= similarity_threshold:
                best_similarity = total_similarity
                best_match = entry

        if best_match:
            self.stats['similar_matches'] += 1
            self._save_stats()

            self.logger.info(
                f"✅ Cache HIT (similar {best_similarity:.2%}): {ticker} "
                f"(cached {best_match.get('cached_at', 'unknown')})"
            )

            # Add metadata about match quality
            decision = best_match['decision'].copy()
            decision['cache_match_quality'] = best_similarity
            decision['from_cache'] = True

            return decision

        # No match found
        self.stats['cache_misses'] += 1
        self._save_stats()

        self.logger.info(f"❌ Cache MISS: {ticker}")
        return None

    def cache_decision(
        self,
        ticker: str,
        agent_scores: Dict[str, float],
        conflict_info: Dict[str, Any],
        composite_score: float,
        decision: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Cache an LLM decision for future use

        Args:
            ticker: Stock ticker
            agent_scores: Agent scores that led to this decision
            conflict_info: Conflict information
            composite_score: Composite score
            decision: LLM synthesis decision
            metadata: Additional metadata
        """
        cache_key = self._create_cache_key(
            ticker, agent_scores,
            conflict_info['conflict_level'],
            composite_score
        )

        entry = {
            'cache_key': cache_key,
            'ticker': ticker,
            'agent_scores': agent_scores,
            'conflict_level': conflict_info['conflict_level'],
            'conflict_details': {
                'variance': conflict_info.get('variance'),
                'std_dev': conflict_info.get('std_dev'),
                'disagreements': len(conflict_info.get('disagreements', []))
            },
            'composite_score': composite_score,
            'decision': decision,
            'cached_at': datetime.now().isoformat(),
            'metadata': metadata or {}
        }

        # Append to cache file
        with open(self.cache_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')

        self.logger.info(f"💾 Cached decision for {ticker} (key: {cache_key[:8]}...)")

    def get_statistics(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return self.stats.copy()

    def analyze_patterns(self, min_occurrences: int = 3) -> List[Dict[str, Any]]:
        """
        Analyze cached decisions to find patterns

        Args:
            min_occurrences: Minimum times a pattern must occur

        Returns:
            List of identified patterns
        """
        if not self.cache_file.exists():
            return []

        # Load all decisions
        decisions = []
        with open(self.cache_file, 'r') as f:
            for line in f:
                decisions.append(json.loads(line))

        # Group by pattern
        patterns = {}

        for entry in decisions:
            # Create pattern signature
            pattern_key = (
                entry['conflict_level'],
                round(entry['composite_score'] / 10) * 10,  # Group by 10s
                entry['decision'].get('final_recommendation', 'HOLD')
            )

            if pattern_key not in patterns:
                patterns[pattern_key] = {
                    'conflict_level': pattern_key[0],
                    'score_range': f"{pattern_key[1]}-{pattern_key[1]+10}",
                    'recommendation': pattern_key[2],
                    'count': 0,
                    'tickers': [],
                    'avg_confidence': 0,
                    'confidences': []
                }

            patterns[pattern_key]['count'] += 1
            patterns[pattern_key]['tickers'].append(entry['ticker'])
            patterns[pattern_key]['confidences'].append(
                entry['decision'].get('confidence', 0)
            )

        # Calculate averages and filter
        identified_patterns = []
        for pattern_data in patterns.values():
            if pattern_data['count'] >= min_occurrences:
                pattern_data['avg_confidence'] = (
                    sum(pattern_data['confidences']) / len(pattern_data['confidences'])
                )
                del pattern_data['confidences']  # Remove raw data
                identified_patterns.append(pattern_data)

        # Sort by count
        identified_patterns.sort(key=lambda x: x['count'], reverse=True)

        return identified_patterns

    def export_training_data(self, output_file: str = "llm_training_data.json"):
        """
        Export cached decisions as training data for future model fine-tuning

        Args:
            output_file: Path to export file
        """
        if not self.cache_file.exists():
            self.logger.warning("No cache data to export")
            return

        training_data = []

        with open(self.cache_file, 'r') as f:
            for line in f:
                entry = json.loads(line)

                # Format for training
                training_sample = {
                    'input': {
                        'ticker': entry['ticker'],
                        'agent_scores': entry['agent_scores'],
                        'conflict_level': entry['conflict_level'],
                        'composite_score': entry['composite_score']
                    },
                    'output': entry['decision'],
                    'timestamp': entry['cached_at']
                }

                training_data.append(training_sample)

        output_path = self.cache_dir / output_file
        with open(output_path, 'w') as f:
            json.dump(training_data, f, indent=2)

        self.logger.info(
            f"📤 Exported {len(training_data)} training samples to {output_path}"
        )
