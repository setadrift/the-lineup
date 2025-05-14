"""
Utility functions for data cleaning and preprocessing.
"""

def clean_player_name(name: str) -> str:
    """
    Standardize player name format.
    
    Args:
        name (str): Raw player name
        
    Returns:
        str: Cleaned player name
    """
    if ', ' in name:
        last, first = name.split(', ')
        return f"{first} {last}".strip()
    return name.strip()

def map_position(position: str) -> str:
    """
    Standardize position mapping.
    
    Args:
        position (str): Raw position string
        
    Returns:
        str: Standardized position
    """
    position = position.upper().strip()
    
    # Handle compound positions
    if '-' in position:
        pos1, pos2 = position.split('-')
        return f"{map_position(pos1)}-{map_position(pos2)}"
        
    position_map = {
        'PG': 'PG',
        'SG': 'SG',
        'SF': 'SF',
        'PF': 'PF',
        'C': 'C',
        'G': 'SG',  # Default guards to SG if not specified
        'F': 'SF',  # Default forwards to SF if not specified
        'GUARD': 'SG',
        'FORWARD': 'SF',
        'CENTER': 'C'
    }
    
    return position_map.get(position, 'UNK') 