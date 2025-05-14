"""
NBA API utility functions and helpers.
"""

import random
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Dict, Any, Optional

from app.config.constants import NBA_API_CONFIG

# NBA API headers with randomized user agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
]

def get_nba_headers() -> Dict[str, str]:
    """
    Get randomized headers for NBA API requests.
    
    Returns:
        Dict[str, str]: Headers dictionary with randomized User-Agent
    """
    headers = NBA_API_CONFIG["HEADERS"].copy()
    headers["User-Agent"] = random.choice(USER_AGENTS)
    return headers

def create_nba_session() -> requests.Session:
    """
    Create a requests Session with retry strategy for NBA API calls.
    
    Returns:
        requests.Session: Configured session object
    """
    retry_strategy = Retry(
        total=3,  # number of retries
        backoff_factor=0.5,  # time between retries
        status_forcelist=[429, 500, 502, 503, 504],
    )
    
    session = requests.Session()
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    
    return session

def make_nba_request(
    endpoint: str,
    params: Optional[Dict[str, Any]] = None,
    timeout: int = 15
) -> Dict[str, Any]:
    """
    Make a request to the NBA API with proper error handling and rate limiting.
    
    Args:
        endpoint (str): API endpoint (e.g., 'commonplayerinfo')
        params (Dict[str, Any], optional): Query parameters
        timeout (int): Request timeout in seconds
        
    Returns:
        Dict[str, Any]: JSON response data
        
    Raises:
        requests.exceptions.RequestException: If request fails
    """
    url = f"{NBA_API_CONFIG['BASE_URL']}/{endpoint}"
    session = create_nba_session()
    
    try:
        response = session.get(
            url,
            headers=get_nba_headers(),
            params=params or {},
            timeout=timeout
        )
        response.raise_for_status()
        
        # Random delay between requests (0.5-1.5 seconds)
        time.sleep(0.5 + random.random())
        
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"❌ NBA API request failed: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response content: {e.response.text}")
        raise
    finally:
        session.close() 