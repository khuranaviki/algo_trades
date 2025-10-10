"""
Base Agent Class for Agentic Trading System

All agents inherit from this base class for consistency and shared functionality.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
import logging


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the system

    Provides:
    - Logging infrastructure
    - State management
    - Input validation
    - Standardized interface
    """

    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize base agent

        Args:
            name: Agent identifier (e.g., "Fundamental Analyst")
            config: Configuration dictionary with agent-specific parameters
        """
        self.name = name
        self.config = config
        self.logger = self._setup_logger()
        self.state = {}
        self.created_at = datetime.now()
        self.analysis_count = 0

        self.logger.info(f"{self.name} initialized")

    def _setup_logger(self) -> logging.Logger:
        """Set up logger for this agent"""
        logger = logging.getLogger(f"Agent.{self.name}")

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

        return logger

    @abstractmethod
    async def analyze(self, ticker: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main analysis method - must be implemented by subclasses

        Args:
            ticker: Stock ticker symbol (e.g., "RELIANCE.NS")
            context: Additional context from other agents or orchestrator

        Returns:
            Dictionary with analysis results including:
            - score: float (0-100)
            - details: Dict with specific metrics
            - summary: str with human-readable summary
            - timestamp: datetime of analysis

        Example:
            {
                'score': 85.5,
                'details': {...},
                'summary': 'Strong fundamentals with 25% CAGR',
                'timestamp': '2025-10-07T10:30:00'
            }
        """
        pass

    def validate_input(self, ticker: str) -> bool:
        """
        Validate input parameters

        Args:
            ticker: Stock ticker to validate

        Returns:
            True if valid, False otherwise
        """
        if not ticker or not isinstance(ticker, str):
            self.logger.error(f"Invalid ticker: {ticker}")
            return False

        if len(ticker) < 2:
            self.logger.error(f"Ticker too short: {ticker}")
            return False

        return True

    def log_analysis(self, ticker: str, result: Dict[str, Any]) -> None:
        """
        Log analysis results for audit trail

        Args:
            ticker: Stock ticker analyzed
            result: Analysis result dictionary
        """
        score = result.get('score', 'N/A')
        summary = result.get('summary', 'No summary')

        self.logger.info(f"Analysis complete for {ticker}")
        self.logger.info(f"  Score: {score}")
        self.logger.info(f"  Summary: {summary}")

        self.analysis_count += 1

    def get_state(self) -> Dict[str, Any]:
        """
        Return current agent state for monitoring

        Returns:
            Dictionary with agent status information
        """
        uptime = (datetime.now() - self.created_at).total_seconds()

        return {
            'name': self.name,
            'status': 'active',
            'uptime_seconds': uptime,
            'analysis_count': self.analysis_count,
            'state': self.state,
            'created_at': self.created_at.isoformat()
        }

    def update_state(self, key: str, value: Any) -> None:
        """
        Update agent state

        Args:
            key: State key
            value: State value
        """
        self.state[key] = value
        self.logger.debug(f"State updated: {key} = {value}")

    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self.config.get(key, default)

    async def health_check(self) -> Dict[str, Any]:
        """
        Check agent health status

        Returns:
            Health status dictionary
        """
        return {
            'agent': self.name,
            'healthy': True,
            'uptime_seconds': (datetime.now() - self.created_at).total_seconds(),
            'analysis_count': self.analysis_count,
            'last_check': datetime.now().isoformat()
        }

    def __repr__(self) -> str:
        """String representation of agent"""
        return f"<{self.name} (analyses: {self.analysis_count})>"
