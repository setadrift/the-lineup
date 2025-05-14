"""
Logging configuration and utilities.
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional

def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    level: int = logging.INFO,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Set up a logger with console and optional file output.
    
    Args:
        name (str): Logger name
        log_file (str, optional): Path to log file
        level (int): Logging level
        format_string (str, optional): Custom format string
        
    Returns:
        logging.Logger: Configured logger
    """
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    formatter = logging.Formatter(format_string)
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if log_file specified)
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def log_execution_time(logger: logging.Logger, start_time: float, operation: str):
    """
    Log the execution time of an operation.
    
    Args:
        logger (logging.Logger): Logger instance
        start_time (float): Start time from time.time()
        operation (str): Description of the operation
    """
    import time
    duration = time.time() - start_time
    logger.info(f"✨ {operation} completed in {duration:.2f} seconds")

def log_error_with_context(
    logger: logging.Logger,
    error: Exception,
    context: dict,
    level: int = logging.ERROR
):
    """
    Log an error with additional context information.
    
    Args:
        logger (logging.Logger): Logger instance
        error (Exception): The error that occurred
        context (dict): Additional context information
        level (int): Logging level for this error
    """
    error_type = type(error).__name__
    error_msg = str(error)
    
    context_str = "\n".join(f"  {k}: {v}" for k, v in context.items())
    
    message = f"""❌ {error_type}: {error_msg}
Context:
{context_str}"""
    
    logger.log(level, message, exc_info=True)

# Example usage:
if __name__ == "__main__":
    # Set up logger
    logger = setup_logger(
        "the_lineup",
        log_file="logs/app.log"
    )
    
    # Example logging
    try:
        logger.info("🚀 Starting application...")
        raise ValueError("Example error")
    except Exception as e:
        log_error_with_context(
            logger,
            e,
            context={
                "operation": "startup",
                "environment": "development"
            }
        ) 