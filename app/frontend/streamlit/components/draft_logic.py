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
    
    def detect_punt_strategies(self, roster_ids: List[str], all_team_rosters: Dict[int, List[str]] = None, 
                              user_team_id: int = None, min_players: int = 3) -> Dict[str, Any]:
        """
        Detect potential punt strategies based on team composition and rankings.
        
        Args:
            roster_ids: List of player IDs in the roster
            all_team_rosters: Dictionary of all team rosters
            user_team_id: ID of the user's team
            min_players: Minimum number of players needed to detect punt strategies
            
        Returns:
            Dictionary with punt strategy analysis
        """
        if len(roster_ids) < min_players:
            return {
                'punt_categories': [],
                'punt_recommendations': [],
                'strategy_confidence': 'low',
                'message': f"Need at least {min_players} players to detect punt strategies"
            }
        
        analysis = self.analyze_team_categories(roster_ids, all_team_rosters, user_team_id)
        roster_df = self.player_pool_df[self.player_pool_df["player_id"].isin(roster_ids)]
        
        punt_candidates = []
        punt_recommendations = []
        
        # More conservative punt detection criteria
        for z_col, data in analysis.items():
            category_info = self.CATEGORIES[z_col]
            team_total = data['team_total']
            team_rank = data.get('rank')
            total_teams = data.get('total_teams', 1)
            
            # Punt detection criteria - more conservative
            is_punt_candidate = False
            confidence = 'low'
            reason = ""
            
            # Only consider punt if we have multiple teams and clear ranking data
            if team_rank and total_teams >= 6:  # Need at least 6 teams for meaningful comparison
                
                # Criteria 1: Bottom 20% in rankings (much more conservative than 25%)
                bottom_quintile_threshold = total_teams * 0.80
                if team_rank >= bottom_quintile_threshold and team_total < -1:  # Also require negative total
                    is_punt_candidate = True
                    confidence = 'high'
                    reason = f"Ranked {data['rank_suffix']} of {total_teams} teams with weak total"
                
                # Criteria 2: Last place with very weak total
                elif team_rank == total_teams and team_total < -2:
                    is_punt_candidate = True
                    confidence = 'medium'
                    reason = f"Last place ({data['rank_suffix']}) with very weak total ({team_total:.1f})"
            
            # Criteria 3: Extremely negative team total (rare cases without ranking)
            elif category_info['good_direction'] == 'high' and team_total < -4:  # Much more conservative threshold
                is_punt_candidate = True
                confidence = 'medium'
                reason = f"Extremely low team total ({team_total:.1f})"
            
            # Criteria 4: Extremely positive turnover total (bad for turnovers) 
            elif category_info['good_direction'] == 'low' and team_total > 4:  # More conservative threshold
                is_punt_candidate = True
                confidence = 'medium'
                reason = f"Very high turnover total ({team_total:.1f})"
            
            # Criteria 5: Percentage categories with consistently poor performers (more conservative)
            elif z_col in ['z_fg_pct', 'z_ft_pct'] and len(roster_df) >= 6:  # Need more players
                # Check if most players are significantly below average
                poor_performers = len(roster_df[roster_df[z_col] < -1.0])  # More stringent threshold
                total_players = len(roster_df)
                
                if poor_performers >= total_players * 0.75:  # 75% of players must be significantly poor
                    is_punt_candidate = True
                    confidence = 'medium'
                    reason = f"{poor_performers}/{total_players} players significantly below average"
            
            if is_punt_candidate:
                punt_candidates.append({
                    'category': z_col,
                    'name': category_info['name'],
                    'short': category_info['short'],
                    'confidence': confidence,
                    'reason': reason,
                    'team_total': team_total,
                    'rank': team_rank,
                    'rank_suffix': data.get('rank_suffix', 'N/A')
                })
        
        # Generate punt strategy recommendations only for high confidence punts
        if punt_candidates:
            # Sort by confidence and impact
            punt_candidates.sort(key=lambda x: (
                {'high': 3, 'medium': 2, 'low': 1}[x['confidence']], 
                abs(x['team_total'])
            ), reverse=True)
            
            # Only generate recommendations for high confidence punts or top medium confidence punt
            high_confidence_punts = [p for p in punt_candidates if p['confidence'] == 'high']
            
            if high_confidence_punts:
                for punt_cat in high_confidence_punts[:2]:  # Limit to top 2 high confidence punts
                    recommendations = self._generate_punt_recommendations(punt_cat, roster_df)
                    punt_recommendations.extend(recommendations)
            elif punt_candidates and punt_candidates[0]['confidence'] == 'medium':
                # Only include top medium confidence punt if no high confidence punts
                recommendations = self._generate_punt_recommendations(punt_candidates[0], roster_df)
                punt_recommendations.extend(recommendations)
        
        # Determine overall strategy confidence - much more conservative
        high_confidence_punts = [p for p in punt_candidates if p['confidence'] == 'high']
        medium_confidence_punts = [p for p in punt_candidates if p['confidence'] == 'medium']
        
        if len(high_confidence_punts) >= 2:  # Need 2 high confidence punts
            strategy_confidence = 'high'
        elif len(high_confidence_punts) >= 1 and len(medium_confidence_punts) >= 1:
            strategy_confidence = 'medium'
        elif len(high_confidence_punts) >= 1:
            strategy_confidence = 'low'
        else:
            strategy_confidence = 'none'
        
        return {
            'punt_categories': punt_candidates,
            'punt_recommendations': punt_recommendations,
            'strategy_confidence': strategy_confidence,
            'message': self._generate_punt_strategy_message(punt_candidates, strategy_confidence)
        }
    
    def _generate_punt_recommendations(self, punt_category: Dict[str, Any], roster_df: pd.DataFrame) -> List[str]:
        """
        Generate specific recommendations for a punt strategy.
        
        Args:
            punt_category: Dictionary with punt category information
            roster_df: DataFrame of current roster players
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        category = punt_category['category']
        cat_name = punt_category['name']
        cat_short = punt_category['short']
        
        # Category-specific punt recommendations
        if category == 'z_ft_pct':
            recommendations.extend([
                f"Target high-volume, low-FT% players (Giannis, Simmons, Drummond types)",
                f"Prioritize big men who get blocks/rebounds but hurt FT%",
                f"Avoid guards who rely on free throws for scoring"
            ])
        
        elif category == 'z_fg_pct':
            recommendations.extend([
                f"Target high-volume scorers regardless of efficiency",
                f"Prioritize players with high usage rates and 3PM",
                f"Focus on assists, steals, and counting stats over shooting %"
            ])
        
        elif category == 'z_three_pm':
            recommendations.extend([
                f"Focus on traditional big men (centers, power forwards)",
                f"Target players strong in rebounds, blocks, FG%",
                f"Don't worry about 3-point shooting from your picks"
            ])
        
        elif category == 'z_assists':
            recommendations.extend([
                f"Target scoring-focused guards and wings",
                f"Prioritize big men who contribute in other categories",
                f"Focus on points, rebounds, blocks over playmaking"
            ])
        
        elif category == 'z_steals':
            recommendations.extend([
                f"Focus on big men and low-steal guards",
                f"Prioritize size and interior presence",
                f"Target players strong in blocks, rebounds, scoring"
            ])
        
        elif category == 'z_blocks':
            recommendations.extend([
                f"Target guards and small forwards",
                f"Focus on perimeter stats (3PM, assists, steals)",
                f"Don't prioritize interior presence"
            ])
        
        elif category == 'z_turnovers':
            # Note: Low turnovers is good, so punting means accepting high turnovers
            recommendations.extend([
                f"Target high-usage, high-assist players",
                f"Focus on playmakers who handle the ball frequently",
                f"Prioritize offensive production over ball security"
            ])
        
        elif category == 'z_rebounds':
            recommendations.extend([
                f"Target guards and perimeter players",
                f"Focus on assists, steals, 3PM, and scoring",
                f"Don't prioritize size or interior presence"
            ])
        
        elif category == 'z_points':
            recommendations.extend([
                f"Target defensive specialists and role players",
                f"Focus on efficiency stats (FG%, FT%) and defensive stats",
                f"Prioritize assists, steals, blocks over scoring"
            ])
        
        return recommendations[:3]  # Limit to top 3 recommendations
    
    def _generate_punt_strategy_message(self, punt_categories: List[Dict[str, Any]], confidence: str) -> str:
        """
        Generate a user-friendly message about punt strategy detection.
        
        Args:
            punt_categories: List of detected punt categories
            confidence: Overall confidence level
            
        Returns:
            Strategy message string
        """
        if not punt_categories:
            return "No clear punt strategies detected - focus on balanced team building"
        
        if confidence == 'high':
            top_punt = punt_categories[0]
            return f"🎯 Your team is naturally punting {top_punt['name']} - lean into it! ({top_punt['reason']})"
        
        elif confidence == 'medium':
            if len(punt_categories) == 1:
                punt_cat = punt_categories[0]
                return f"💡 Consider punting {punt_cat['name']} - {punt_cat['reason']}"
            else:
                cat_names = [p['short'] for p in punt_categories[:2]]
                return f"💡 Consider punting {' and '.join(cat_names)} based on current team composition"
        
        elif confidence == 'low':
            punt_cat = punt_categories[0]
            return f"⚠️ Possible punt strategy: {punt_cat['name']} - monitor team development"
        
        else:
            return "📊 Team composition suggests balanced strategy approach"
    
    def get_punt_friendly_players(self, available_players: pd.DataFrame, punt_categories: List[str], 
                                 top_n: int = 10) -> pd.DataFrame:
        """
        Get players who are strong in non-punt categories and weak in punt categories.
        
        Args:
            available_players: DataFrame of available players
            punt_categories: List of z-score column names being punted
            top_n: Number of top players to return
            
        Returns:
            DataFrame of punt-friendly players
        """
        if not punt_categories or available_players.empty:
            return available_players.head(top_n)
        
        # Define non-punt categories (categories we want to be strong in)
        all_categories = list(self.CATEGORIES.keys())
        non_punt_categories = [cat for cat in all_categories if cat not in punt_categories]
        
        # Calculate punt-friendly score for each player
        punt_scores = []
        
        for idx, player in available_players.iterrows():
            punt_friendly_score = 0
            
            # Positive points for being strong in non-punt categories
            for cat in non_punt_categories:
                if cat in player and pd.notna(player[cat]):
                    z_score = player[cat]
                    # Adjust for turnovers (negative is good)
                    if cat == 'z_turnovers':
                        z_score = -z_score
                    punt_friendly_score += max(0, z_score)  # Only positive contributions
            
            # Bonus for being weak in punt categories (we don't care about these)
            for cat in punt_categories:
                if cat in player and pd.notna(player[cat]):
                    z_score = player[cat]
                    # For punt categories, being weak is actually good for our strategy
                    if cat == 'z_turnovers':
                        # For turnovers, high turnovers (positive z-score) is bad normally,
                        # but if we're punting turnovers, we don't care
                        punt_friendly_score += 0  # Neutral
                    else:
                        # For other categories, being weak doesn't hurt our punt strategy
                        punt_friendly_score += 0  # Neutral
            
            punt_scores.append(punt_friendly_score)
        
        # Add punt scores to dataframe and sort
        available_with_scores = available_players.copy()
        available_with_scores['punt_friendly_score'] = punt_scores
        
        # Sort by punt-friendly score, then by total z-score as tiebreaker
        available_with_scores = available_with_scores.sort_values(
            ['punt_friendly_score', 'total_z_score'], 
            ascending=[False, False]
        )
        
        return available_with_scores.head(top_n)
    
    def detect_roster_construction_warnings(self, roster_ids: List[str], min_players: int = 3) -> Dict[str, Any]:
        """
        Detect roster construction warnings and potential issues.
        
        Args:
            roster_ids: List of player IDs in the roster
            min_players: Minimum number of players needed to detect warnings
            
        Returns:
            Dictionary with roster construction warnings
        """
        if len(roster_ids) < min_players:
            return {
                'warnings': [],
                'risk_level': 'low',
                'message': f"Need at least {min_players} players to assess roster construction"
            }
        
        # Get roster players with all available data
        roster_df = self.player_pool_df[self.player_pool_df["player_id"].isin(roster_ids)]
        
        if roster_df.empty:
            return {
                'warnings': [],
                'risk_level': 'low',
                'message': "No player data available for roster analysis"
            }
        
        warnings = []
        risk_factors = []
        
        # 1. Injury Risk Analysis (Games Played)
        if 'games_played' in roster_df.columns:
            low_gp_players = roster_df[roster_df['games_played'] < 50]
            very_low_gp_players = roster_df[roster_df['games_played'] < 30]
            
            if len(very_low_gp_players) >= 2:
                warnings.append({
                    'type': 'injury_risk',
                    'severity': 'high',
                    'title': 'High Injury Risk',
                    'message': f"{len(very_low_gp_players)} players with <30 games played",
                    'recommendation': "Target more durable players (70+ games)",
                    'affected_players': very_low_gp_players['name'].tolist()
                })
                risk_factors.append('high_injury_risk')
            elif len(low_gp_players) >= 3:
                warnings.append({
                    'type': 'injury_risk',
                    'severity': 'medium',
                    'title': 'Moderate Injury Risk',
                    'message': f"{len(low_gp_players)} players with <50 games played",
                    'recommendation': "Consider adding more reliable players",
                    'affected_players': low_gp_players['name'].tolist()
                })
                risk_factors.append('moderate_injury_risk')
        
        # 2. Age-Related Concerns
        if 'age' in roster_df.columns:
            old_players = roster_df[roster_df['age'] >= 33]
            very_old_players = roster_df[roster_df['age'] >= 35]
            
            if len(very_old_players) >= 2:
                warnings.append({
                    'type': 'age_risk',
                    'severity': 'high',
                    'title': 'Aging Core',
                    'message': f"{len(very_old_players)} players aged 35+",
                    'recommendation': "Balance with younger players for consistency",
                    'affected_players': very_old_players['name'].tolist()
                })
                risk_factors.append('aging_core')
            elif len(old_players) >= 4:
                warnings.append({
                    'type': 'age_risk',
                    'severity': 'medium',
                    'title': 'Veteran Heavy',
                    'message': f"{len(old_players)} players aged 33+",
                    'recommendation': "Consider adding younger players for upside",
                    'affected_players': old_players['name'].tolist()
                })
                risk_factors.append('veteran_heavy')
        
        # 3. Position Balance Analysis
        if 'position' in roster_df.columns:
            # Count positions (handle the actual database format)
            position_counts = {}
            multi_position_players = 0
            
            # Map actual position values to simplified categories
            position_mapping = {
                'Guard': 'Guard',
                'Point Guard': 'Guard', 
                'Shooting Guard': 'Guard',
                'Forward': 'Forward',
                'Small Forward': 'Forward',
                'Power Forward': 'Forward', 
                'Center': 'Center',
                'Forward-Center': 'Big',  # Hybrid big man
                'Center-Forward': 'Big',  # Hybrid big man
                'Guard-Forward': 'Wing'   # Hybrid wing
            }
            
            for pos_string in roster_df['position']:
                if pd.notna(pos_string):
                    # Handle hyphenated positions
                    if '-' in pos_string:
                        multi_position_players += 1
                        # For hyphenated positions, use the mapping or primary position
                        mapped_pos = position_mapping.get(pos_string, pos_string.split('-')[0])
                    else:
                        mapped_pos = position_mapping.get(pos_string, pos_string)
                    
                    position_counts[mapped_pos] = position_counts.get(mapped_pos, 0) + 1
            
            # Check for position imbalances using the actual position categories
            total_players = len(roster_df)
            
            # Too many of one position
            for pos, count in position_counts.items():
                if count >= max(4, total_players * 0.4):  # 40% or 4+ players
                    warnings.append({
                        'type': 'position_imbalance',
                        'severity': 'medium',
                        'title': f'Too Many {pos}s',
                        'message': f"{count} {pos}s may limit flexibility",
                        'recommendation': f"Consider diversifying away from {pos}",
                        'affected_players': roster_df[roster_df['position'].str.contains(pos, na=False)]['name'].tolist()
                    })
                    risk_factors.append('position_imbalance')
            
            # Missing key positions (if we have enough players) - updated for real position format
            if total_players >= 6:
                # Check for basic position coverage
                has_guards = any('Guard' in pos for pos in position_counts.keys())
                has_forwards = any('Forward' in pos for pos in position_counts.keys()) 
                has_centers = any('Center' in pos for pos in position_counts.keys())
                has_bigs = any(pos in ['Big', 'Center'] for pos in position_counts.keys())
                
                missing_positions = []
                if not has_guards:
                    missing_positions.append('Guards')
                if not (has_forwards or has_centers):  # Need either forwards or centers
                    missing_positions.append('Frontcourt players')
                if not (has_centers or has_bigs):
                    missing_positions.append('Centers')
                
                if len(missing_positions) >= 1:
                    warnings.append({
                        'type': 'position_gap',
                        'severity': 'medium',
                        'title': 'Position Gaps',
                        'message': f"Missing {', '.join(missing_positions)} representation",
                        'recommendation': f"Target {missing_positions[0]}",
                        'affected_players': []
                    })
                    risk_factors.append('position_gaps')
        
        # 4. Usage Rate and Ball Dominance
        if 'usage_rate' in roster_df.columns:
            high_usage_players = roster_df[roster_df['usage_rate'] > 0.28]
            very_high_usage_players = roster_df[roster_df['usage_rate'] > 0.32]
            
            if len(very_high_usage_players) >= 3:
                warnings.append({
                    'type': 'usage_conflict',
                    'severity': 'high',
                    'title': 'Ball Dominance Issues',
                    'message': f"{len(very_high_usage_players)} players with 32%+ usage",
                    'recommendation': "These players may conflict - consider role players",
                    'affected_players': very_high_usage_players['name'].tolist()
                })
                risk_factors.append('usage_conflict')
            elif len(high_usage_players) >= 4:
                warnings.append({
                    'type': 'usage_conflict',
                    'severity': 'medium',
                    'title': 'High Usage Concentration',
                    'message': f"{len(high_usage_players)} players with 28%+ usage",
                    'recommendation': "Monitor for potential usage conflicts",
                    'affected_players': high_usage_players['name'].tolist()
                })
                risk_factors.append('moderate_usage_conflict')
        
        # 5. Efficiency Concerns
        if 'true_shooting_pct' in roster_df.columns:
            # Check if true_shooting_pct is in decimal format (0.0-1.0) or percentage format
            max_ts = roster_df['true_shooting_pct'].max()
            
            if max_ts <= 1.0:  # Decimal format (0.0-1.0)
                inefficient_players = roster_df[roster_df['true_shooting_pct'] < 0.50]
                very_inefficient_players = roster_df[roster_df['true_shooting_pct'] < 0.45]
                threshold_display = "50% TS"
                very_threshold_display = "45% TS"
            else:  # Percentage format (0-100)
                inefficient_players = roster_df[roster_df['true_shooting_pct'] < 50]
                very_inefficient_players = roster_df[roster_df['true_shooting_pct'] < 45]
                threshold_display = "50% TS"
                very_threshold_display = "45% TS"
            
            # Only flag if we have multiple inefficient players (more conservative)
            if len(very_inefficient_players) >= 3:  # Need at least 3 very inefficient players
                warnings.append({
                    'type': 'efficiency_risk',
                    'severity': 'high',
                    'title': 'Poor Shooting Efficiency',
                    'message': f"{len(very_inefficient_players)} players with <{very_threshold_display}",
                    'recommendation': "Add efficient shooters to balance team",
                    'affected_players': very_inefficient_players['name'].tolist()
                })
                risk_factors.append('efficiency_risk')
            elif len(inefficient_players) >= 5:  # Need at least 5 inefficient players
                warnings.append({
                    'type': 'efficiency_risk',
                    'severity': 'medium',
                    'title': 'Below Average Efficiency',
                    'message': f"{len(inefficient_players)} players with <{threshold_display}",
                    'recommendation': "Consider targeting more efficient players",
                    'affected_players': inefficient_players['name'].tolist()
                })
                risk_factors.append('moderate_efficiency_risk')
        
        # 6. Team Chemistry and Fit
        if 'team' in roster_df.columns:
            # Check for too many players from same NBA team
            team_counts = roster_df['team'].value_counts()
            overloaded_teams = team_counts[team_counts >= 3]
            
            if len(overloaded_teams) > 0:
                for nba_team, count in overloaded_teams.items():
                    warnings.append({
                        'type': 'team_concentration',
                        'severity': 'medium',
                        'title': f'Too Many {nba_team} Players',
                        'message': f"{count} players from {nba_team}",
                        'recommendation': "Diversify across NBA teams for schedule balance",
                        'affected_players': roster_df[roster_df['team'] == nba_team]['name'].tolist()
                    })
                    risk_factors.append('team_concentration')
        
        # Determine overall risk level
        high_risk_warnings = [w for w in warnings if w['severity'] == 'high']
        medium_risk_warnings = [w for w in warnings if w['severity'] == 'medium']
        
        if len(high_risk_warnings) >= 2:
            risk_level = 'high'
        elif len(high_risk_warnings) >= 1 or len(medium_risk_warnings) >= 3:
            risk_level = 'medium'
        elif len(warnings) > 0:
            risk_level = 'low'
        else:
            risk_level = 'none'
        
        # Generate summary message
        if risk_level == 'high':
            message = f"⚠️ High risk roster - {len(high_risk_warnings)} major concerns detected"
        elif risk_level == 'medium':
            message = f"💡 Moderate concerns - {len(warnings)} roster issues to address"
        elif risk_level == 'low':
            message = f"✅ Minor issues - {len(warnings)} small concerns to monitor"
        else:
            message = "✅ Solid roster construction - no major concerns detected"
        
        return {
            'warnings': warnings,
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'message': message,
            'total_warnings': len(warnings),
            'high_severity_count': len(high_risk_warnings),
            'medium_severity_count': len(medium_risk_warnings)
        }


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
        
        # Detect punt strategies if we have enough players
        punt_analysis = self.category_analyzer.detect_punt_strategies(
            user_roster_ids, all_team_rosters, user_team_id
        )
        punt_categories = [p['category'] for p in punt_analysis.get('punt_categories', [])]
        punt_confidence = punt_analysis.get('strategy_confidence', 'none')
        
        # Analyze top 10 available players
        top_players = available_players.head(10)
        
        for idx, player in top_players.iterrows():
            reasoning_parts = []
            priority_score = 0
            
            # 1. Punt Strategy Analysis (NEW - High Priority)
            if punt_categories and punt_confidence in ['high', 'medium']:
                punt_bonus = 0
                punt_insights = []
                
                # Check if player fits punt strategy
                for punt_cat in punt_categories:
                    if punt_cat in player and pd.notna(player[punt_cat]):
                        punt_z_score = player[punt_cat]
                        
                        # For punt categories, we don't care if they're weak (or even prefer it)
                        # For non-punt categories, we want them to be strong
                        all_categories = list(self.category_analyzer.CATEGORIES.keys())
                        non_punt_categories = [cat for cat in all_categories if cat not in punt_categories]
                        
                        # Calculate punt-friendly score
                        non_punt_strength = 0
                        for non_punt_cat in non_punt_categories:
                            if non_punt_cat in player and pd.notna(player[non_punt_cat]):
                                cat_z = player[non_punt_cat]
                                # Adjust for turnovers (negative is good)
                                if non_punt_cat == 'z_turnovers':
                                    cat_z = -cat_z
                                non_punt_strength += max(0, cat_z)
                        
                        # Bonus for being strong in non-punt categories
                        if non_punt_strength > 5:  # Strong in multiple non-punt categories
                            punt_bonus += 15
                            punt_insights.append("Excellent punt strategy fit")
                        elif non_punt_strength > 3:
                            punt_bonus += 10
                            punt_insights.append("Good punt strategy fit")
                        elif non_punt_strength > 1:
                            punt_bonus += 5
                            punt_insights.append("Decent punt strategy fit")
                
                # Add punt strategy reasoning
                if punt_insights:
                    reasoning_parts.extend(punt_insights[:1])  # Add top punt insight
                    priority_score += punt_bonus
                    
                    # Add specific punt strategy context
                    if punt_confidence == 'high':
                        punt_cat_names = [self.category_analyzer.CATEGORIES[cat]['short'] for cat in punt_categories[:2]]
                        reasoning_parts.append(f"Fits {'/'.join(punt_cat_names)} punt strategy")
            
            # 2. Position Scarcity Analysis
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
            
            # 3. Category Need Analysis (Enhanced with relative rankings and punt awareness)
            if weak_categories:
                player_strengths = []
                for weak_cat in weak_categories:
                    # Skip weak categories that we're punting
                    if weak_cat in punt_categories:
                        continue
                        
                    if weak_cat in player and pd.notna(player[weak_cat]) and player[weak_cat] > 1:
                        cat_info = self.category_analyzer.CATEGORIES[weak_cat]
                        player_strengths.append(cat_info['short'])
                        priority_score += 20  # Higher priority for addressing relative weaknesses
                
                if player_strengths:
                    reasoning_parts.append(f"Addresses team weaknesses: {', '.join(player_strengths)}")
            
            # 4. Value vs ADP Analysis
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
            
            # 5. Team Need Assessment (Position)
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
            
            # 6. Z-Score Tier Analysis (Enhanced with Advanced Stats)
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
            
            # 7. Round-specific logic
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
            
            # 8. Next pick timing
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
    # Check if we need to reinitialize due to configuration changes
    needs_reinit = False
    
    if "draft_state" not in st.session_state:
        needs_reinit = True
    else:
        # Check if configuration has changed
        current_state = st.session_state.draft_state
        if (current_state.num_teams != num_teams or 
            current_state.draft_position != draft_position or
            current_state.user_team_id != draft_position):
            needs_reinit = True
    
    if needs_reinit:
        st.session_state.draft_state = DraftState(num_teams, draft_position)
        st.session_state.draft_state_initialized = True
        # Clear any existing draft progress when configuration changes
        if "draft_started" in st.session_state:
            st.session_state.draft_started = False
        if "draft_complete" in st.session_state:
            st.session_state.draft_complete = False
    
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


class DraftAnalytics:
    """Comprehensive post-draft analytics and team projections."""
    
    def __init__(self, player_pool_df: pd.DataFrame):
        self.player_pool_df = player_pool_df
        self.category_analyzer = CategoryAnalyzer(player_pool_df)
    
    def generate_draft_recap(self, draft_state: 'DraftState', config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive draft recap analytics.
        
        Args:
            draft_state: Completed draft state
            config: Draft configuration
            
        Returns:
            Dictionary with complete draft analytics
        """
        # Analyze each team
        team_analyses = {}
        league_stats = {
            'total_picks': len(draft_state.drafted_players),
            'rounds_completed': draft_state.round - 1 if not draft_state.is_complete() else draft_state.roster_size,
            'teams': config['num_teams'],
            'season': config['season']
        }
        
        # Get all team projections
        for team_id, roster_ids in draft_state.team_rosters.items():
            if roster_ids:  # Only analyze teams with players
                team_analysis = self._analyze_team_comprehensive(
                    team_id, roster_ids, draft_state.team_rosters, draft_state.user_team_id
                )
                team_analyses[team_id] = team_analysis
        
        # Generate league-wide insights
        league_insights = self._generate_league_insights(team_analyses, draft_state.user_team_id)
        
        # Calculate competitive balance
        competitive_balance = self._calculate_competitive_balance(team_analyses)
        
        # Generate strategic recommendations
        strategic_insights = self._generate_strategic_insights(team_analyses, draft_state.user_team_id)
        
        return {
            'team_analyses': team_analyses,
            'league_stats': league_stats,
            'league_insights': league_insights,
            'competitive_balance': competitive_balance,
            'strategic_insights': strategic_insights,
            'user_team_id': draft_state.user_team_id,
            'draft_complete': draft_state.is_complete()
        }
    
    def _analyze_team_comprehensive(self, team_id: int, roster_ids: List[str], 
                                   all_team_rosters: Dict[int, List[str]], 
                                   user_team_id: int) -> Dict[str, Any]:
        """
        Comprehensive analysis of a single team.
        
        Args:
            team_id: Team ID to analyze
            roster_ids: List of player IDs on the team
            all_team_rosters: All team rosters for relative analysis
            user_team_id: User's team ID
            
        Returns:
            Dictionary with comprehensive team analysis
        """
        # Get team roster data
        roster_df = self.player_pool_df[self.player_pool_df["player_id"].isin(roster_ids)]
        
        if roster_df.empty:
            return self._get_empty_team_analysis(team_id)
        
        # Basic team stats
        team_stats = {
            'team_id': team_id,
            'is_user_team': team_id == user_team_id,
            'roster_size': len(roster_ids),
            'total_z_score': roster_df['total_z_score'].sum(),
            'avg_z_score': roster_df['total_z_score'].mean(),
            'top_player': roster_df.loc[roster_df['total_z_score'].idxmax(), 'name'],
            'top_player_z_score': roster_df['total_z_score'].max()
        }
        
        # Category analysis with rankings
        category_analysis = self.category_analyzer.analyze_team_categories(
            roster_ids, all_team_rosters, user_team_id
        )
        
        # Position analysis
        position_analysis = self._analyze_team_positions(roster_df)
        
        # Punt strategy detection
        punt_analysis = self.category_analyzer.detect_punt_strategies(
            roster_ids, all_team_rosters, user_team_id
        )
        
        # Roster construction warnings
        construction_warnings = self.category_analyzer.detect_roster_construction_warnings(roster_ids)
        
        # Advanced team metrics
        advanced_metrics = self._calculate_advanced_team_metrics(roster_df)
        
        # Team projection and grade
        team_projection = self._calculate_team_projection(category_analysis, punt_analysis, construction_warnings)
        
        return {
            'team_stats': team_stats,
            'category_analysis': category_analysis,
            'position_analysis': position_analysis,
            'punt_analysis': punt_analysis,
            'construction_warnings': construction_warnings,
            'advanced_metrics': advanced_metrics,
            'team_projection': team_projection,
            'roster_df': roster_df
        }
    
    def _analyze_team_positions(self, roster_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze team position distribution and balance."""
        if roster_df.empty:
            return {'position_counts': {}, 'balance_score': 0, 'flexibility': 'Low'}
        
        # Count positions (handle multi-position players)
        position_counts = {}
        multi_position_players = 0
        
        # Map actual position values to simplified categories
        position_mapping = {
            'Guard': 'Guard',
            'Point Guard': 'Guard',
            'Shooting Guard': 'Guard',
            'Forward': 'Forward', 
            'Small Forward': 'Forward',
            'Power Forward': 'Forward',
            'Center': 'Center',
            'Forward-Center': 'Big',    # Hybrid big man
            'Center-Forward': 'Big',    # Hybrid big man
            'Guard-Forward': 'Wing'     # Hybrid wing
        }
        
        for pos_string in roster_df['position']:
            if pd.notna(pos_string):
                # Handle hyphenated positions
                if '-' in pos_string:
                    multi_position_players += 1
                
                mapped_pos = position_mapping.get(pos_string, pos_string)
                position_counts[mapped_pos] = position_counts.get(mapped_pos, 0) + 1
        
        # Calculate balance score (0-100)
        total_players = len(roster_df)
        
        # Expected distribution for 3 main position types + hybrids
        expected_counts = {
            'Guard': total_players * 0.35,    # ~35% guards
            'Forward': total_players * 0.35,  # ~35% forwards  
            'Center': total_players * 0.20,   # ~20% centers
            'Big': total_players * 0.05,      # ~5% hybrid bigs
            'Wing': total_players * 0.05      # ~5% hybrid wings
        }
        
        balance_score = 0
        if total_players > 0:
            # Calculate balance based on how close we are to expected distribution
            for pos, expected in expected_counts.items():
                actual = position_counts.get(pos, 0)
                deviation = abs(actual - expected) / max(expected, 1)
                # Score: 20 points max per position, reduced by deviation
                position_score = max(0, 20 - (deviation * 10))
                balance_score += position_score
        
        # Flexibility bonus for multi-position players
        flexibility_bonus = min(20, multi_position_players * 5)
        balance_score += flexibility_bonus
        
        # Determine flexibility rating
        if multi_position_players >= 4:
            flexibility = 'High'
        elif multi_position_players >= 2:
            flexibility = 'Medium'
        else:
            flexibility = 'Low'
        
        return {
            'position_counts': position_counts,
            'multi_position_players': multi_position_players,
            'balance_score': min(100, balance_score),
            'flexibility': flexibility,
            'total_players': total_players
        }
    
    def _calculate_advanced_team_metrics(self, roster_df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate advanced team metrics for deeper analysis."""
        if roster_df.empty:
            return {}
        
        metrics = {}
        
        # Age analysis
        if 'age' in roster_df.columns:
            metrics['avg_age'] = roster_df['age'].mean()
            metrics['age_range'] = roster_df['age'].max() - roster_df['age'].min()
            metrics['young_players'] = len(roster_df[roster_df['age'] <= 25])
            metrics['veteran_players'] = len(roster_df[roster_df['age'] >= 30])
        
        # Games played analysis (durability)
        if 'games_played' in roster_df.columns:
            metrics['avg_games_played'] = roster_df['games_played'].mean()
            metrics['durable_players'] = len(roster_df[roster_df['games_played'] >= 70])
            metrics['injury_prone_players'] = len(roster_df[roster_df['games_played'] < 50])
        
        # Usage and efficiency analysis
        if 'usage_rate' in roster_df.columns:
            metrics['avg_usage_rate'] = roster_df['usage_rate'].mean()
            metrics['high_usage_players'] = len(roster_df[roster_df['usage_rate'] > 0.25])
        
        if 'true_shooting_pct' in roster_df.columns:
            metrics['avg_true_shooting'] = roster_df['true_shooting_pct'].mean()
            metrics['efficient_players'] = len(roster_df[roster_df['true_shooting_pct'] > 0.55])
        
        # Team chemistry indicators
        if 'team' in roster_df.columns:
            nba_teams = roster_df['team'].value_counts()
            metrics['nba_team_diversity'] = len(nba_teams)
            metrics['max_players_same_team'] = nba_teams.max() if len(nba_teams) > 0 else 0
        
        # Z-score distribution analysis
        z_score_std = roster_df['total_z_score'].std()
        metrics['z_score_consistency'] = 'High' if z_score_std < 3 else 'Medium' if z_score_std < 6 else 'Low'
        metrics['elite_players'] = len(roster_df[roster_df['total_z_score'] > 8])
        metrics['solid_contributors'] = len(roster_df[(roster_df['total_z_score'] >= 3) & (roster_df['total_z_score'] <= 8)])
        metrics['depth_players'] = len(roster_df[roster_df['total_z_score'] < 3])
        
        return metrics
    
    def _calculate_team_projection(self, category_analysis: Dict[str, Any], 
                                  punt_analysis: Dict[str, Any], 
                                  construction_warnings: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall team projection and grade."""
        
        # Base score from category performance - much more conservative scoring
        category_score = 0
        strong_categories = 0
        weak_categories = 0
        
        for cat_data in category_analysis.values():
            if cat_data['status'] == 'strong':
                category_score += 8   # Further reduced from 12
                strong_categories += 1
            elif cat_data['status'] == 'average':
                category_score += 3   # Further reduced from 6
            else:  # weak
                category_score += 0   # No points for weak categories
                weak_categories += 1
        
        # Punt strategy bonus - more conservative
        punt_bonus = 0
        punt_confidence = punt_analysis.get('strategy_confidence', 'none')
        if punt_confidence == 'high':
            punt_bonus = 6    # Further reduced from 8
        elif punt_confidence == 'medium':
            punt_bonus = 3    # Further reduced from 4
        
        # Construction penalty - more significant impact
        construction_penalty = 0
        risk_level = construction_warnings.get('risk_level', 'none')
        if risk_level == 'high':
            construction_penalty = 30  # Increased from 25
        elif risk_level == 'medium':
            construction_penalty = 20  # Increased from 15
        elif risk_level == 'low':
            construction_penalty = 10  # Increased from 8
        
        # Additional penalties for poor team balance
        if weak_categories >= 6:  # More than half categories weak
            construction_penalty += 15  # Increased penalty
        elif weak_categories >= 4:  # Many weak categories
            construction_penalty += 8   # Increased penalty
        
        # Bonus for strong teams (but more conservative)
        strong_team_bonus = 0
        if strong_categories >= 7:  # Need majority + 1 to be truly strong
            strong_team_bonus = 10
        elif strong_categories >= 5:  # Many strong
            strong_team_bonus = 5
        elif strong_categories >= 3:  # Some strong
            strong_team_bonus = 2
        
        # Calculate final score (0-100) with more realistic expectations
        base_score = 35  # Further reduced base score
        final_score = max(0, min(100, base_score + category_score + punt_bonus + strong_team_bonus - construction_penalty))
        
        # Much more realistic letter grade thresholds
        if final_score >= 90:
            grade = 'A+'
        elif final_score >= 85:
            grade = 'A'
        elif final_score >= 80:
            grade = 'A-'
        elif final_score >= 75:
            grade = 'B+'
        elif final_score >= 70:
            grade = 'B'
        elif final_score >= 65:
            grade = 'B-'
        elif final_score >= 60:
            grade = 'C+'
        elif final_score >= 55:
            grade = 'C'
        elif final_score >= 50:
            grade = 'C-'
        elif final_score >= 45:
            grade = 'D+'
        elif final_score >= 40:
            grade = 'D'
        elif final_score >= 35:
            grade = 'D-'
        else:
            grade = 'F'
        
        # More realistic projection summary
        if final_score >= 85:
            outlook = 'Championship Contender'
        elif final_score >= 75:
            outlook = 'Playoff Contender'
        elif final_score >= 65:
            outlook = 'Competitive Team'
        elif final_score >= 55:
            outlook = 'Average Team'
        elif final_score >= 45:
            outlook = 'Developing Team'
        else:
            outlook = 'Rebuilding Team'
        
        return {
            'final_score': final_score,
            'grade': grade,
            'outlook': outlook,
            'strong_categories': strong_categories,
            'weak_categories': weak_categories,
            'category_score': category_score,
            'punt_bonus': punt_bonus,
            'construction_penalty': construction_penalty,
            'strong_team_bonus': strong_team_bonus,
            'base_score': base_score
        }
    
    def _generate_league_insights(self, team_analyses: Dict[int, Dict], user_team_id: int) -> Dict[str, Any]:
        """Generate league-wide insights and comparisons."""
        
        if not team_analyses:
            return {}
        
        # Calculate league averages
        total_scores = [analysis['team_stats']['total_z_score'] for analysis in team_analyses.values()]
        avg_scores = [analysis['team_stats']['avg_z_score'] for analysis in team_analyses.values()]
        projection_scores = [analysis['team_projection']['final_score'] for analysis in team_analyses.values()]
        
        league_avg_total = sum(total_scores) / len(total_scores)
        league_avg_player = sum(avg_scores) / len(avg_scores)
        league_avg_projection = sum(projection_scores) / len(projection_scores)
        
        # Find league leaders
        best_team_id = max(team_analyses.keys(), key=lambda x: team_analyses[x]['team_projection']['final_score'])
        worst_team_id = min(team_analyses.keys(), key=lambda x: team_analyses[x]['team_projection']['final_score'])
        
        # User team ranking
        user_projection = team_analyses.get(user_team_id, {}).get('team_projection', {}).get('final_score', 0)
        user_rank = sum(1 for analysis in team_analyses.values() 
                       if analysis['team_projection']['final_score'] > user_projection) + 1
        
        # Category dominance analysis
        category_leaders = {}
        for category in self.category_analyzer.CATEGORIES.keys():
            best_team = max(team_analyses.keys(), 
                          key=lambda x: team_analyses[x]['category_analysis'][category]['team_total'])
            category_leaders[category] = {
                'team_id': best_team,
                'total': team_analyses[best_team]['category_analysis'][category]['team_total'],
                'category_name': team_analyses[best_team]['category_analysis'][category]['name']
            }
        
        return {
            'league_averages': {
                'total_z_score': league_avg_total,
                'avg_z_score_per_player': league_avg_player,
                'projection_score': league_avg_projection
            },
            'league_leaders': {
                'best_team': best_team_id,
                'worst_team': worst_team_id,
                'best_score': team_analyses[best_team_id]['team_projection']['final_score'],
                'worst_score': team_analyses[worst_team_id]['team_projection']['final_score']
            },
            'user_standing': {
                'rank': user_rank,
                'total_teams': len(team_analyses),
                'percentile': (len(team_analyses) - user_rank + 1) / len(team_analyses) * 100
            },
            'category_leaders': category_leaders
        }
    
    def _calculate_competitive_balance(self, team_analyses: Dict[int, Dict]) -> Dict[str, Any]:
        """Calculate competitive balance metrics for the league."""
        
        if len(team_analyses) < 2:
            return {'balance_score': 100, 'competitiveness': 'High'}
        
        projection_scores = [analysis['team_projection']['final_score'] for analysis in team_analyses.values()]
        
        # Calculate standard deviation of projection scores
        mean_score = sum(projection_scores) / len(projection_scores)
        variance = sum((score - mean_score) ** 2 for score in projection_scores) / len(projection_scores)
        std_dev = variance ** 0.5
        
        # Calculate balance score (lower std dev = higher balance)
        # Scale: 0-100 where 100 is perfectly balanced
        balance_score = max(0, 100 - (std_dev * 2))
        
        # Determine competitiveness level
        if balance_score >= 80:
            competitiveness = 'Very High'
        elif balance_score >= 65:
            competitiveness = 'High'
        elif balance_score >= 50:
            competitiveness = 'Medium'
        elif balance_score >= 35:
            competitiveness = 'Low'
        else:
            competitiveness = 'Very Low'
        
        # Calculate score spread
        score_spread = max(projection_scores) - min(projection_scores)
        
        return {
            'balance_score': balance_score,
            'competitiveness': competitiveness,
            'score_spread': score_spread,
            'std_deviation': std_dev,
            'mean_score': mean_score
        }
    
    def _generate_strategic_insights(self, team_analyses: Dict[int, Dict], user_team_id: int) -> Dict[str, Any]:
        """Generate strategic insights and recommendations."""
        
        insights = {
            'draft_trends': [],
            'strategic_observations': [],
            'user_recommendations': []
        }
        
        if not team_analyses:
            return insights
        
        # Analyze draft trends - only include legitimate punt strategies
        punt_strategies = {}
        for team_id, analysis in team_analyses.items():
            punt_analysis = analysis.get('punt_analysis', {})
            punt_confidence = punt_analysis.get('strategy_confidence', 'none')
            
            # Only count teams with meaningful punt strategies
            if punt_confidence in ['high', 'medium']:
                punt_cats = punt_analysis.get('punt_categories', [])
                for punt_cat in punt_cats:
                    if punt_cat.get('confidence') in ['high', 'medium']:
                        cat_name = punt_cat.get('short', 'Unknown')
                        punt_strategies[cat_name] = punt_strategies.get(cat_name, 0) + 1
        
        # Most punted categories (only if multiple teams are punting)
        if punt_strategies:
            most_punted = max(punt_strategies.items(), key=lambda x: x[1])
            if most_punted[1] >= 2:  # At least 2 teams punting
                insights['draft_trends'].append(f"Most punted category: {most_punted[0]} ({most_punted[1]} teams)")
        
        # Position scarcity analysis (more realistic)
        all_rosters = []
        for analysis in team_analyses.values():
            if 'roster_df' in analysis:
                all_rosters.append(analysis['roster_df'])
        
        if all_rosters:
            combined_df = pd.concat(all_rosters, ignore_index=True)
            
            # Map actual position values to simplified categories for analysis
            position_mapping = {
                'Guard': 'Guard',
                'Point Guard': 'Guard',
                'Shooting Guard': 'Guard', 
                'Forward': 'Forward',
                'Small Forward': 'Forward',
                'Power Forward': 'Forward',
                'Center': 'Center',
                'Forward-Center': 'Center',  # Count as centers for scarcity
                'Center-Forward': 'Center',  # Count as centers for scarcity
                'Guard-Forward': 'Forward'   # Count as forwards
            }
            
            position_counts = {}
            for pos_string in combined_df['position']:
                if pd.notna(pos_string):
                    mapped_pos = position_mapping.get(pos_string, pos_string)
                    position_counts[mapped_pos] = position_counts.get(mapped_pos, 0) + 1
            
            if position_counts:
                # Find positions that are significantly under-drafted
                total_players = sum(position_counts.values())
                avg_per_position = total_players / 3  # 3 main categories: Guard, Forward, Center
                
                underrepresented = []
                for pos in ['Guard', 'Forward', 'Center']:
                    count = position_counts.get(pos, 0)
                    if count < avg_per_position * 0.6:  # 40% below average
                        underrepresented.append((pos, count))
                
                if underrepresented:
                    least_drafted = min(underrepresented, key=lambda x: x[1])
                    insights['draft_trends'].append(f"Underrepresented position: {least_drafted[0]} ({least_drafted[1]} players)")
        
        # Strategic observations with realistic thresholds
        high_scoring_teams = sum(1 for analysis in team_analyses.values() 
                               if analysis['team_projection']['final_score'] >= 75)  # More realistic threshold
        
        strong_contenders = sum(1 for analysis in team_analyses.values() 
                              if analysis['team_projection']['outlook'] in ['Championship Contender', 'Playoff Contender'])
        
        total_teams = len(team_analyses)
        
        if strong_contenders >= total_teams * 0.5:
            insights['strategic_observations'].append(
                f"Highly competitive league: {strong_contenders}/{total_teams} teams are strong contenders"
            )
        elif strong_contenders >= total_teams * 0.3:
            insights['strategic_observations'].append(
                f"Balanced league: {strong_contenders}/{total_teams} teams are competitive"
            )
        else:
            insights['strategic_observations'].append(
                f"Top-heavy league: Only {strong_contenders}/{total_teams} teams are strong contenders"
            )
        
        # Add grade distribution insight
        a_tier_teams = sum(1 for analysis in team_analyses.values() 
                          if analysis['team_projection']['grade'].startswith('A'))
        
        if a_tier_teams >= total_teams * 0.4:
            insights['strategic_observations'].append(
                f"Strong draft class: {a_tier_teams}/{total_teams} teams earned A-tier grades"
            )
        elif a_tier_teams <= total_teams * 0.15:
            insights['strategic_observations'].append(
                f"Challenging draft: Only {a_tier_teams}/{total_teams} teams earned A-tier grades"
            )
        
        # User-specific recommendations with more nuanced analysis
        if user_team_id in team_analyses:
            user_analysis = team_analyses[user_team_id]
            user_score = user_analysis['team_projection']['final_score']
            user_grade = user_analysis['team_projection']['grade']
            user_outlook = user_analysis['team_projection']['outlook']
            
            # Primary recommendation based on grade and outlook
            if user_score >= 80:
                insights['user_recommendations'].append(f"Excellent draft! Your team is a {user_outlook.lower()}.")
            elif user_score >= 70:
                insights['user_recommendations'].append(f"Strong draft! Your {user_outlook.lower()} has good potential.")
            elif user_score >= 60:
                insights['user_recommendations'].append(f"Solid foundation. Focus on waiver wire to improve from {user_outlook.lower()}.")
            elif user_score >= 50:
                insights['user_recommendations'].append(f"Average draft. Look for breakout players and strategic trades.")
            else:
                insights['user_recommendations'].append(f"Challenging draft. Consider aggressive waiver moves and trades.")
            
            # Category-specific advice (only for meaningful weaknesses)
            user_category_analysis = user_analysis.get('category_analysis', {})
            weak_cats = []
            for cat, data in user_category_analysis.items():
                if data['status'] == 'weak' and data.get('rank'):
                    # Only suggest if team is in bottom third
                    total_teams_in_cat = data.get('total_teams', 1)
                    if data['rank'] >= total_teams_in_cat * 0.67:
                        weak_cats.append(cat)
            
            # Filter out punt categories from recommendations
            punt_analysis = user_analysis.get('punt_analysis', {})
            punt_categories = [p['category'] for p in punt_analysis.get('punt_categories', [])]
            meaningful_weak_cats = [cat for cat in weak_cats if cat not in punt_categories]
            
            if meaningful_weak_cats:
                cat_names = [user_category_analysis[cat]['short'] for cat in meaningful_weak_cats[:2]]
                insights['user_recommendations'].append(f"Priority targets: Players strong in {', '.join(cat_names)}")
            
            # Punt strategy advice
            punt_confidence = punt_analysis.get('strategy_confidence', 'none')
            if punt_confidence == 'high':
                punt_cats = [p['short'] for p in punt_analysis.get('punt_categories', [])]
                if punt_cats:
                    insights['user_recommendations'].append(f"Continue punting {'/'.join(punt_cats[:2])} - strategy is working well")
        
        return insights
    
    def _get_empty_team_analysis(self, team_id: int) -> Dict[str, Any]:
        """Return empty analysis for teams with no players."""
        return {
            'team_stats': {
                'team_id': team_id,
                'roster_size': 0,
                'total_z_score': 0,
                'avg_z_score': 0
            },
            'category_analysis': {},
            'position_analysis': {'position_counts': {}, 'balance_score': 0},
            'punt_analysis': {'punt_categories': [], 'strategy_confidence': 'none'},
            'construction_warnings': {'warnings': [], 'risk_level': 'none'},
            'advanced_metrics': {},
            'team_projection': {'final_score': 0, 'grade': 'F', 'outlook': 'No Players'}
        } 