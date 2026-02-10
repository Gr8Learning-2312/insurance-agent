"""
Custom logging configuration for Insurance Claims Agent.
Logs detailed agent workflow: Request received -> Tool invocations -> Final decision
"""
import logging
import sys
from pathlib import Path
from datetime import datetime

# Create logs directory
Path("logs").mkdir(exist_ok=True)

def setup_logger(name: str = "InsuranceAgent") -> logging.Logger:
    """
    Configure logger with both file and console handlers.
    
    Format: [TIMESTAMP] [LEVEL] [Module] - Message
    Example: [2026-02-06 11:43:15] [INFO] [graph] - Request received: Claim ID 12345
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # File handler - daily rotating logs
    timestamp = datetime.now().strftime("%Y%m%d")
    file_handler = logging.FileHandler(
        f"logs/agent_{timestamp}.log",
        encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(module)s] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Global logger instance
logger = setup_logger()
