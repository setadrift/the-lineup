"""
The Lineup - State Persistence Utilities
Save and restore draft progress across browser sessions
"""

import json
import hashlib
import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict


@dataclass
class DraftSaveState:
    """Data class for serializable draft state."""
    draft_id: str
    timestamp: str
    num_teams: int
    draft_position: int
    roster_size: int
    round: int
    current_pick_team: int
    drafted_players: List[str]
    team_rosters: Dict[int, List[str]]
    user_team_id: int
    draft_order: List[int]
    complete: bool
    status_message: str
    season: str
    draft_type: str


class DraftPersistence:
    """Handles saving and loading draft state."""
    
    @staticmethod
    def generate_draft_id(num_teams: int, draft_position: int, season: str) -> str:
        """Generate a unique draft ID based on configuration."""
        config_string = f"{num_teams}_{draft_position}_{season}_{datetime.now().strftime('%Y%m%d')}"
        return hashlib.md5(config_string.encode()).hexdigest()[:12]
    
    @staticmethod
    def save_draft_state(draft_state, config: Dict[str, Any]) -> str:
        """
        Save draft state to browser localStorage via Streamlit.
        
        Args:
            draft_state: DraftState object
            config: Draft configuration dictionary
            
        Returns:
            Draft ID for the saved state
        """
        try:
            # Create serializable state
            draft_id = DraftPersistence.generate_draft_id(
                config['num_teams'], 
                config['draft_position'], 
                config['season']
            )
            
            save_state = DraftSaveState(
                draft_id=draft_id,
                timestamp=datetime.now().isoformat(),
                num_teams=draft_state.num_teams,
                draft_position=draft_state.draft_position,
                roster_size=draft_state.roster_size,
                round=draft_state.round,
                current_pick_team=draft_state.current_pick_team,
                drafted_players=draft_state.drafted_players.copy(),
                team_rosters={k: v.copy() for k, v in draft_state.team_rosters.items()},
                user_team_id=draft_state.user_team_id,
                draft_order=draft_state.draft_order.copy(),
                complete=draft_state.complete,
                status_message=draft_state.status_message,
                season=config['season'],
                draft_type=config['draft_type']
            )
            
            # Save to session state with persistence key
            persistence_key = f"draft_save_{draft_id}"
            st.session_state[persistence_key] = asdict(save_state)
            
            # Also save to a list of saved drafts
            if "saved_drafts" not in st.session_state:
                st.session_state.saved_drafts = []
            
            # Remove old saves for same configuration (keep only latest)
            st.session_state.saved_drafts = [
                save for save in st.session_state.saved_drafts 
                if not (save['num_teams'] == config['num_teams'] and 
                       save['draft_position'] == config['draft_position'] and
                       save['season'] == config['season'])
            ]
            
            # Add new save
            st.session_state.saved_drafts.append(asdict(save_state))
            
            return draft_id
            
        except Exception as e:
            st.error(f"Failed to save draft state: {e}")
            return None
    
    @staticmethod
    def load_draft_state(draft_id: str) -> Optional[DraftSaveState]:
        """
        Load draft state from browser localStorage.
        
        Args:
            draft_id: ID of the draft to load
            
        Returns:
            DraftSaveState object or None if not found
        """
        try:
            persistence_key = f"draft_save_{draft_id}"
            
            if persistence_key in st.session_state:
                save_data = st.session_state[persistence_key]
                return DraftSaveState(**save_data)
            
            return None
            
        except Exception as e:
            st.error(f"Failed to load draft state: {e}")
            return None
    
    @staticmethod
    def get_saved_drafts() -> List[DraftSaveState]:
        """
        Get list of all saved drafts.
        
        Returns:
            List of DraftSaveState objects
        """
        try:
            if "saved_drafts" not in st.session_state:
                return []
            
            saved_drafts = []
            for save_data in st.session_state.saved_drafts:
                try:
                    saved_drafts.append(DraftSaveState(**save_data))
                except Exception:
                    continue  # Skip corrupted saves
            
            # Sort by timestamp (newest first)
            saved_drafts.sort(key=lambda x: x.timestamp, reverse=True)
            return saved_drafts
            
        except Exception as e:
            st.error(f"Failed to get saved drafts: {e}")
            return []
    
    @staticmethod
    def delete_draft_save(draft_id: str) -> bool:
        """
        Delete a saved draft.
        
        Args:
            draft_id: ID of the draft to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            # Remove from session state
            persistence_key = f"draft_save_{draft_id}"
            if persistence_key in st.session_state:
                del st.session_state[persistence_key]
            
            # Remove from saved drafts list
            if "saved_drafts" in st.session_state:
                st.session_state.saved_drafts = [
                    save for save in st.session_state.saved_drafts 
                    if save['draft_id'] != draft_id
                ]
            
            return True
            
        except Exception as e:
            st.error(f"Failed to delete draft save: {e}")
            return False
    
    @staticmethod
    def auto_save_enabled() -> bool:
        """Check if auto-save is enabled."""
        return st.session_state.get("auto_save_enabled", True)
    
    @staticmethod
    def set_auto_save(enabled: bool):
        """Enable or disable auto-save."""
        st.session_state.auto_save_enabled = enabled
    
    @staticmethod
    def cleanup_old_saves(days_to_keep: int = 7):
        """
        Clean up saves older than specified days.
        
        Args:
            days_to_keep: Number of days to keep saves
        """
        try:
            if "saved_drafts" not in st.session_state:
                return
            
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # Filter out old saves
            valid_saves = []
            for save_data in st.session_state.saved_drafts:
                try:
                    save_date = datetime.fromisoformat(save_data['timestamp'])
                    if save_date > cutoff_date:
                        valid_saves.append(save_data)
                    else:
                        # Also remove from session state
                        persistence_key = f"draft_save_{save_data['draft_id']}"
                        if persistence_key in st.session_state:
                            del st.session_state[persistence_key]
                except Exception:
                    continue  # Skip corrupted timestamps
            
            st.session_state.saved_drafts = valid_saves
            
        except Exception as e:
            st.error(f"Failed to cleanup old saves: {e}")


def restore_draft_state_to_session(save_state: DraftSaveState):
    """
    Restore a saved draft state to the current session.
    
    Args:
        save_state: DraftSaveState object to restore
    """
    try:
        # Import here to avoid circular imports
        from app.frontend.streamlit.components.draft_logic import DraftState
        
        # Create new DraftState object
        draft_state = DraftState(
            save_state.num_teams, 
            save_state.draft_position, 
            save_state.roster_size
        )
        
        # Restore all state
        draft_state.round = save_state.round
        draft_state.current_pick_team = save_state.current_pick_team
        draft_state.drafted_players = save_state.drafted_players.copy()
        draft_state.team_rosters = {k: v.copy() for k, v in save_state.team_rosters.items()}
        draft_state.user_team_id = save_state.user_team_id
        draft_state.draft_order = save_state.draft_order.copy()
        draft_state.complete = save_state.complete
        draft_state.status_message = save_state.status_message
        
        # Set session state
        st.session_state.draft_state = draft_state
        st.session_state.draft_state_initialized = True
        st.session_state.draft_started = True
        st.session_state.draft_complete = save_state.complete
        
        # Set configuration
        st.session_state.restored_config = {
            'num_teams': save_state.num_teams,
            'draft_position': save_state.draft_position,
            'season': save_state.season,
            'draft_type': save_state.draft_type
        }
        
        return True
        
    except Exception as e:
        st.error(f"Failed to restore draft state: {e}")
        return False 