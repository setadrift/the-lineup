"""
The Lineup - Draft Logic Components
Modular draft state management and AI pick suggestions
"""

import pandas as pd
import streamlit as st
from typing import List, Dict, Any, Optional, Tuple


class CategoryAnalyzer:
    """Analyzes team category strengths and weaknesses."""
    
    # Define the 9 fantasy basketball categories
    CATEGORIES = {
        'z_points': {'name': 'Points', 'short': 'PTS', 'good_direction': 'high'},
        'z_rebounds': {'name': 'Rebounds', 'short': 'REB', 'good_direction': 'high'},
        'z_assists': {'name': 'Assists', 'short': 'AST', 'good_direction': 'high'},
        'z_steals': {'name': 'Steals', 'short': 'STL', 'good_direction': 'high'},
        'z_blocks': {'name': 'Blocks', 'short': 'BLK', 'good_direction': 'high'},
        'z_turnovers': {'name': 'Turnovers', 'short': 'TO', 'good_direction': 'low'},  # Lower is better
        'z_fg_pct': {'name': 'Field Goal %', 'short': 'FG%', 'good_direction': 'high'},
        'z_ft_pct': {'name': 'Free Throw %', 'short': 'FT%', 'good_direction': 'high'},
        'z_three_pm': {'name': '3-Pointers Made', 'short': '3PM', 'good_direction': 'high'}
    }
    
    def __init__(self, player_pool_df: pd.DataFrame):
        self.player_pool_df = player_pool_df
    
    def analyze_team_categories(self, roster_ids: List[str], all_team_rosters: Dict[int, List[str]] = None, user_team_id: int = None) -> Dict[str, Any]:
        """
        Analyze team's category strengths and weaknesses relative to other teams.
        
        Args:
            roster_ids: List of player IDs in the roster
            all_team_rosters: Dictionary of all team rosters {team_id: [player_ids]}
            user_team_id: ID of the user's team
            
        Returns:
            Dictionary with category analysis including relative rankings
        """
        if not roster_ids:
            return self._get_empty_analysis()
        
        # Get roster players with z-scores
        roster_df = self.player_pool_df[self.player_pool_df["player_id"].isin(roster_ids)]
        
        if roster_df.empty:
            return self._get_empty_analysis()
        
        category_analysis = {}
        
        # Calculate team rankings if we have all team data
        team_rankings = {}
        if all_team_rosters and user_team_id:
            team_rankings = self._calculate_team_rankings(all_team_rosters)
        
        for z_col, info in self.CATEGORIES.items():
            if z_col in roster_df.columns:
                # Calculate team total for this category
                team_total = roster_df[z_col].sum()
                team_avg = roster_df[z_col].mean()
                
                # Get relative ranking info
                ranking_info = team_rankings.get(z_col, {})
                user_rank = ranking_info.get('rankings', {}).get(user_team_id, None)
                total_teams = ranking_info.get('total_teams', 1)
                
                # Determine status based on relative ranking
                status = self._get_category_status_relative(user_rank, total_teams, info['good_direction'])
                
                category_analysis[z_col] = {
                    'name': info['name'],
                    'short': info['short'],
                    'team_total': team_total,
                    'team_avg': team_avg,
                    'status': status,
                    'color': self._get_status_color(status),
                    'emoji': self._get_status_emoji(status),
                    'good_direction': info['good_direction'],
                    'rank': user_rank,
                    'total_teams': total_teams,
                    'rank_suffix': self._get_rank_suffix(user_rank) if user_rank else None
                }
        
        return category_analysis
    
    def _calculate_team_rankings(self, all_team_rosters: Dict[int, List[str]]) -> Dict[str, Dict]:
        """
        Calculate rankings for all teams across all categories.
        
        Args:
            all_team_rosters: Dictionary of all team rosters
            
        Returns:
            Dictionary with ranking information for each category
        """
        team_rankings = {}
        
        for z_col, info in self.CATEGORIES.items():
            if z_col in self.player_pool_df.columns:
                team_totals = {}
                
                # Calculate totals for each team
                for team_id, roster_ids in all_team_rosters.items():
                    if roster_ids:  # Only calculate for teams with players
                        team_df = self.player_pool_df[self.player_pool_df["player_id"].isin(roster_ids)]
                        if not team_df.empty:
                            team_totals[team_id] = team_df[z_col].sum()
                        else:
                            team_totals[team_id] = 0
                    else:
                        team_totals[team_id] = 0
                
                # Sort teams by total (ascending for turnovers, descending for others)
                reverse_sort = info['good_direction'] == 'high'
                sorted_teams = sorted(team_totals.items(), key=lambda x: x[1], reverse=reverse_sort)
                
                # Create rankings (1st, 2nd, 3rd, etc.)
                rankings = {}
                for rank, (team_id, total) in enumerate(sorted_teams, 1):
                    rankings[team_id] = rank
                
                team_rankings[z_col] = {
                    'rankings': rankings,
                    'totals': team_totals,
                    'total_teams': len([t for t in all_team_rosters.keys() if all_team_rosters[t]])  # Only count teams with players
                }
        
        return team_rankings
    
    def _get_category_status_relative(self, rank: Optional[int], total_teams: int, good_direction: str) -> str:
        """
        Determine category status based on relative ranking among teams.
        
        Args:
            rank: Team's rank in this category (1 = best)
            total_teams: Total number of teams with players
            good_direction: Whether high or low values are good
            
        Returns:
            Status string: 'strong', 'average', or 'weak'
        """
        if rank is None or total_teams <= 1:
            return 'average'
        
        # Calculate percentile position
        percentile = (total_teams - rank + 1) / total_teams
        
        # Determine status based on ranking
        if percentile >= 0.67:  # Top third
            return 'strong'
        elif percentile >= 0.33:  # Middle third
            return 'average'
        else:  # Bottom third
            return 'weak'
    
    def _get_rank_suffix(self, rank: int) -> str:
        """Get ordinal suffix for ranking (1st, 2nd, 3rd, etc.)."""
        if 10 <= rank % 100 <= 20:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(rank % 10, 'th')
        return f"{rank}{suffix}"
    
    def _get_category_status(self, team_total: float, team_avg: float, good_direction: str) -> str:
        """
        Determine category status based on team performance (legacy method for backward compatibility).
        
        Args:
            team_total: Sum of z-scores for the category
            team_avg: Average z-score for the category
            good_direction: Whether high or low values are good
            
        Returns:
            Status string: 'strong', 'average', or 'weak'
        """
        # Adjust thresholds based on direction (turnovers are reverse)
        if good_direction == 'low':  # Turnovers
            if team_total <= -2:  # Very negative is good for turnovers
                return 'strong'
            elif team_total <= 0:
                return 'average'
            else:
                return 'weak'
        else:  # All other categories
            if team_total >= 3:  # Strong positive total
                return 'strong'
            elif team_total >= 0:
                return 'average'
            else:
                return 'weak'
    
    def _get_status_color(self, status: str) -> str:
        """Get color for status."""
        colors = {
            'strong': '#28A745',  # Green
            'average': '#FFC107',  # Yellow
            'weak': '#DC3545'     # Red
        }
        return colors.get(status, '#6C757D')
    
    def _get_status_emoji(self, status: str) -> str:
        """Get emoji for status."""
        emojis = {
            'strong': '🟢',
            'average': '🟡', 
            'weak': '🔴'
        }
        return emojis.get(status, '⚪')
    
    def _get_empty_analysis(self) -> Dict[str, Any]:
        """Return empty analysis for teams with no players."""
        analysis = {}
        for z_col, info in self.CATEGORIES.items():
            analysis[z_col] = {
                'name': info['name'],
                'short': info['short'],
                'team_total': 0,
                'team_avg': 0,
                'status': 'average',
                'color': '#6C757D',
                'emoji': '⚪',
                'good_direction': info['good_direction'],
                'rank': None,
                'total_teams': 1,
                'rank_suffix': None
            }
        return analysis
    
    def get_priority_needs(self, roster_ids: List[str], all_team_rosters: Dict[int, List[str]] = None, user_team_id: int = None) -> List[str]:
        """
        Get list of category z-score columns that are weak and need improvement.
        
        Args:
            roster_ids: List of player IDs in the roster
            all_team_rosters: Dictionary of all team rosters
            user_team_id: ID of the user's team
            
        Returns:
            List of z-score column names that are weak
        """
        analysis = self.analyze_team_categories(roster_ids, all_team_rosters, user_team_id)
        weak_categories = []
        
        for z_col, data in analysis.items():
            if data['status'] == 'weak':
                weak_categories.append(z_col)
        
        return weak_categories


class DraftState:
    """Manages draft state and progression."""
    
    def __init__(self, num_teams: int, draft_position: int, roster_size: int = 13):
        self.num_teams = num_teams
        self.draft_position = draft_position
        self.roster_size = roster_size
        self.round = 1
        self.current_pick_team = 1
        self.drafted_players = []
        self.team_rosters = {i: [] for i in range(1, num_teams + 1)}
        self.user_team_id = draft_position
        self.draft_order = list(range(1, num_teams + 1))
        self.complete = False
        self.status_message = ""
    
    def advance_pick(self):
        """Advance to the next pick using serpentine logic."""
        idx = self.draft_order.index(self.current_pick_team)
        if idx + 1 < len(self.draft_order):
            self.current_pick_team = self.draft_order[idx + 1]
        else:
            # End of round: increment round, reverse order
            self.round += 1
            self.draft_order = self.draft_order[::-1]
            self.current_pick_team = self.draft_order[0]
    
    def is_complete(self) -> bool:
        """Check if draft is complete."""
        return all(len(roster) >= self.roster_size for roster in self.team_rosters.values())
    
    def draft_player(self, player_id: str, team_id: int, player_name: str = ""):
        """Draft a player to a team."""
        self.team_rosters[team_id].append(player_id)
        self.drafted_players.append(player_id)
        if player_name:
            self.status_message = f"Team {team_id} drafted {player_name}!"
    
    def get_user_roster_ids(self) -> List[str]:
        """Get the user's current roster player IDs."""
        return self.team_rosters[self.user_team_id]


class PickSuggestionEngine:
    """Generates intelligent pick suggestions with reasoning."""
    
    def __init__(self, player_pool_df: pd.DataFrame):
        self.player_pool_df = player_pool_df
        self.category_analyzer = CategoryAnalyzer(player_pool_df)
    
    def get_suggestions(
        self, 
        available_players: pd.DataFrame, 
        user_roster_ids: List[str], 
        current_round: int, 
        draft_position: int, 
        num_teams: int,
        max_suggestions: int = 5,
        all_team_rosters: Dict[int, List[str]] = None,
        user_team_id: int = None
    ) -> List[Dict[str, Any]]:
        """
        Generate pick suggestions with reasoning.
        
        Args:
            available_players: DataFrame of available players
            user_roster_ids: List of user's current roster player IDs
            current_round: Current draft round
            draft_position: User's draft position
            num_teams: Number of teams in draft
            max_suggestions: Maximum number of suggestions to return
            all_team_rosters: Dictionary of all team rosters for relative analysis
            user_team_id: User's team ID for relative analysis
            
        Returns:
            List of suggestion dictionaries
        """
        suggestions = []
        
        if len(available_players) == 0:
            return suggestions
        
        # Get user's current roster for analysis
        user_roster_df = self.player_pool_df[
            self.player_pool_df["player_id"].isin(user_roster_ids)
        ] if user_roster_ids else pd.DataFrame()
        
        # Get category needs (now with relative rankings if available)
        weak_categories = self.category_analyzer.get_priority_needs(
            user_roster_ids, all_team_rosters, user_team_id
        )
        
        # Analyze top 10 available players
        top_players = available_players.head(10)
        
        for idx, player in top_players.iterrows():
            reasoning_parts = []
            priority_score = 0
            
            # 1. Position Scarcity Analysis
            position = player['position']
            position_available = available_players[
                available_players['position'].str.contains(position.split('-')[0], na=False)
            ]
            elite_position_count = len(position_available[position_available['total_z_score'] > 5])
            
            if elite_position_count <= 3:
                reasoning_parts.append(f"Only {elite_position_count} elite {position}s left")
                priority_score += 15
            elif elite_position_count <= 5:
                reasoning_parts.append(f"Limited elite {position} options remaining")
                priority_score += 10
            
            # 2. Category Need Analysis (Enhanced with relative rankings)
            if weak_categories:
                player_strengths = []
                for weak_cat in weak_categories:
                    if weak_cat in player and pd.notna(player[weak_cat]) and player[weak_cat] > 1:
                        cat_info = self.category_analyzer.CATEGORIES[weak_cat]
                        player_strengths.append(cat_info['short'])
                        priority_score += 20  # Higher priority for addressing relative weaknesses
                
                if player_strengths:
                    reasoning_parts.append(f"Addresses team weaknesses: {', '.join(player_strengths)}")
            
            # 3. Value vs ADP Analysis
            if pd.notna(player['adp']):
                current_pick_number = ((current_round - 1) * num_teams) + draft_position
                adp_value = player['adp'] - current_pick_number
                
                if adp_value > 12:
                    reasoning_parts.append(f"Excellent value - typically drafted {int(adp_value)} picks later")
                    priority_score += 20
                elif adp_value > 6:
                    reasoning_parts.append(f"Good value - ADP suggests pick {int(player['adp'])}")
                    priority_score += 10
                elif adp_value < -6:
                    reasoning_parts.append(f"Reaching early - ADP is pick {int(player['adp'])}")
                    priority_score -= 5
            
            # 4. Team Need Assessment (Position)
            if len(user_roster_df) > 0:
                team_positions = user_roster_df['position'].str.split('-').explode().value_counts()
                main_position = position.split('-')[0]
                position_count = team_positions.get(main_position, 0)
                
                if position_count == 0:
                    reasoning_parts.append(f"Fills {main_position} need")
                    priority_score += 12
                elif position_count == 1 and main_position in ['C', 'PG']:
                    reasoning_parts.append(f"Adds {main_position} depth")
                    priority_score += 8
            
            # 5. Z-Score Tier Analysis (Enhanced with Advanced Stats)
            z_score = player['total_z_score']
            next_player_z = top_players.iloc[min(idx + 1, len(top_players) - 1)]['total_z_score'] if idx < len(top_players) - 1 else 0
            z_drop = z_score - next_player_z
            
            # Advanced stats bonus evaluation
            advanced_bonus = 0
            advanced_insights = []
            
            # Usage rate evaluation
            if 'usage_rate' in player and pd.notna(player['usage_rate']):
                usage = player['usage_rate']
                if usage > 0.28:  # High usage (28%+)
                    advanced_bonus += 3
                    advanced_insights.append("High usage player")
                elif usage > 0.25:  # Above average usage
                    advanced_bonus += 1
                    advanced_insights.append("Above average usage")
            
            # Efficiency evaluation
            if 'true_shooting_pct' in player and pd.notna(player['true_shooting_pct']):
                ts_pct = player['true_shooting_pct']
                if ts_pct > 0.60:  # Elite efficiency (60%+ TS)
                    advanced_bonus += 4
                    advanced_insights.append("Elite shooting efficiency")
                elif ts_pct > 0.55:  # Good efficiency
                    advanced_bonus += 2
                    advanced_insights.append("Good shooting efficiency")
                elif ts_pct < 0.50:  # Poor efficiency
                    advanced_bonus -= 2
                    advanced_insights.append("Below average efficiency")
            
            # PER evaluation
            if 'player_efficiency_rating' in player and pd.notna(player['player_efficiency_rating']):
                per = player['player_efficiency_rating']
                if per > 25:  # Elite PER
                    advanced_bonus += 3
                    advanced_insights.append("Elite PER")
                elif per > 20:  # Very good PER
                    advanced_bonus += 2
                    advanced_insights.append("Strong PER")
                elif per > 15:  # Above average PER
                    advanced_bonus += 1
            
            # Age factor for upside/decline risk
            if 'age' in player and pd.notna(player['age']):
                age = player['age']
                if age <= 25:
                    advanced_bonus += 2
                    advanced_insights.append("Young with upside")
                elif age <= 27:
                    advanced_bonus += 1
                    advanced_insights.append("Prime age")
                elif age >= 32:
                    advanced_bonus -= 1
                    advanced_insights.append("Veteran (age risk)")
            
            # Games played consistency
            if 'games_played' in player and pd.notna(player['games_played']):
                gp = player['games_played']
                if gp >= 70:
                    advanced_bonus += 1
                    advanced_insights.append("Durable (70+ games)")
                elif gp < 50:
                    advanced_bonus -= 2
                    advanced_insights.append("Injury concerns")
            
            # Apply advanced bonus to priority score
            priority_score += advanced_bonus
            
            # Add advanced insights to reasoning
            if advanced_insights:
                reasoning_parts.extend(advanced_insights[:2])  # Limit to top 2 insights
            
            # Traditional tier analysis
            if z_score > 10:
                reasoning_parts.append("Elite tier player")
                priority_score += 15
            elif z_score > 7:
                reasoning_parts.append("High-tier option")
                priority_score += 10
            elif z_score > 4:
                reasoning_parts.append("Solid contributor")
                priority_score += 5
            
            if z_drop > 2:
                reasoning_parts.append("Significant tier drop after this pick")
                priority_score += 8
            
            # 6. Round-specific logic
            if current_round <= 3:
                if z_score > 8:
                    reasoning_parts.append("Top-tier talent for early rounds")
                    priority_score += 10
            elif current_round <= 6:
                if z_score > 5:
                    reasoning_parts.append("Strong mid-round value")
                    priority_score += 8
            else:
                if z_score > 2:
                    reasoning_parts.append("Good late-round upside")
                    priority_score += 5
            
            # 7. Next pick timing
            picks_until_next = (num_teams * 2) - draft_position if current_round % 2 == 1 else draft_position - 1
            if picks_until_next > 20:
                reasoning_parts.append(f"Long wait until next pick ({picks_until_next} picks)")
                priority_score += 5
            
            # Create suggestion
            if reasoning_parts:
                main_reason = reasoning_parts[0]
                additional_reasons = reasoning_parts[1:3]  # Limit to avoid clutter
                
                suggestion = {
                    'player_name': player['name'],
                    'player_id': player['player_id'],
                    'position': player['position'],
                    'z_score': player['total_z_score'],
                    'adp': player['adp'],
                    'main_reason': main_reason,
                    'additional_reasons': additional_reasons,
                    'priority_score': priority_score,
                    'reasoning_text': f"{main_reason}" + (f" • {' • '.join(additional_reasons)}" if additional_reasons else "")
                }
                suggestions.append(suggestion)
        
        # Sort by priority score and return top suggestions
        suggestions.sort(key=lambda x: x['priority_score'], reverse=True)
        return suggestions[:max_suggestions]


class AIOpponent:
    """Handles AI opponent drafting logic."""
    
    @staticmethod
    def make_pick(available_players: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """
        Make an AI pick based on simple best available logic.
        
        Args:
            available_players: DataFrame of available players
            
        Returns:
            Dictionary with picked player info or None if no players available
        """
        if len(available_players) == 0:
            return None
        
        # Simple strategy: pick highest z-score player
        best_player = available_players.iloc[0]
        return {
            'player_id': best_player['player_id'],
            'player_name': best_player['name'],
            'position': best_player['position'],
            'z_score': best_player['total_z_score']
        }


def initialize_draft_state(num_teams: int, draft_position: int) -> DraftState:
    """
    Initialize draft state in Streamlit session.
    
    Args:
        num_teams: Number of teams in the draft
        draft_position: User's draft position
        
    Returns:
        DraftState instance
    """
    if "draft_state" not in st.session_state:
        st.session_state.draft_state = DraftState(num_teams, draft_position)
        st.session_state.draft_state_initialized = True
    
    return st.session_state.draft_state


def get_available_players(player_pool_df: pd.DataFrame, drafted_players: List[str]) -> pd.DataFrame:
    """
    Get players that haven't been drafted yet.
    
    Args:
        player_pool_df: Full player pool DataFrame
        drafted_players: List of drafted player IDs
        
    Returns:
        DataFrame of available players
    """
    return player_pool_df[~player_pool_df["player_id"].isin(drafted_players)] 