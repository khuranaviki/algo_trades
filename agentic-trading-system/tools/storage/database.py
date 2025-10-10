"""
SQLite Database Client for Agentic Trading System

Simple, file-based database - no server needed!

Tables:
- trades: All executed trades
- analysis_results: Agent analysis outputs
- backtest_results: Historical backtesting data
- agent_state: Agent state persistence
"""

import sqlite3
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import logging


class DatabaseClient:
    """
    SQLite database client for trading system

    Much simpler than PostgreSQL:
    - No server setup required
    - No configuration needed
    - Single file database
    - Perfect for single-user systems
    """

    def __init__(self, db_path: str = "storage/trading.db"):
        """
        Initialize database client

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)

        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dicts
        return conn

    def _init_database(self):
        """Create tables if they don't exist"""

        conn = self._get_connection()
        cursor = conn.cursor()

        # Trades table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                action TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                timestamp TEXT NOT NULL,
                strategy TEXT,
                fundamental_score REAL,
                technical_score REAL,
                sentiment_score REAL,
                management_score REAL,
                backtest_validated BOOLEAN,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Analysis results table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                analysis_date TEXT NOT NULL,
                score REAL,
                recommendation TEXT,
                details TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(ticker, agent_name, analysis_date)
            )
        """)

        # Backtest results table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS backtest_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                strategy TEXT NOT NULL,
                pattern TEXT,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                win_rate REAL,
                total_trades INTEGER,
                avg_return REAL,
                sharpe_ratio REAL,
                max_drawdown REAL,
                validated BOOLEAN,
                details TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(ticker, strategy, start_date, end_date)
            )
        """)

        # Agent state table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_state (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT NOT NULL UNIQUE,
                state TEXT,
                last_updated TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Portfolio positions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL UNIQUE,
                quantity INTEGER NOT NULL,
                avg_price REAL NOT NULL,
                current_price REAL,
                entry_date TEXT NOT NULL,
                last_updated TEXT,
                status TEXT DEFAULT 'OPEN',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indices
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_ticker ON trades(ticker)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_ticker ON analysis_results(ticker)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_date ON analysis_results(analysis_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_backtest_ticker ON backtest_results(ticker)")

        conn.commit()
        conn.close()

        self.logger.info(f"Database initialized at {self.db_path}")

    # Trade operations
    def save_trade(self, trade_data: Dict[str, Any]) -> int:
        """Save a trade to database"""

        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO trades (
                ticker, action, quantity, price, timestamp, strategy,
                fundamental_score, technical_score, sentiment_score, management_score,
                backtest_validated, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trade_data['ticker'],
            trade_data['action'],
            trade_data['quantity'],
            trade_data['price'],
            trade_data['timestamp'],
            trade_data.get('strategy'),
            trade_data.get('fundamental_score'),
            trade_data.get('technical_score'),
            trade_data.get('sentiment_score'),
            trade_data.get('management_score'),
            trade_data.get('backtest_validated'),
            trade_data.get('notes')
        ))

        trade_id = cursor.lastrowid
        conn.commit()
        conn.close()

        self.logger.info(f"Saved trade {trade_id}: {trade_data['action']} {trade_data['ticker']}")
        return trade_id

    def get_trades(
        self,
        ticker: Optional[str] = None,
        start_date: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get trades from database"""

        conn = self._get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM trades WHERE 1=1"
        params = []

        if ticker:
            query += " AND ticker = ?"
            params.append(ticker)

        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    # Analysis results operations
    def save_analysis(self, analysis_data: Dict[str, Any]) -> int:
        """Save agent analysis result"""

        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO analysis_results (
                ticker, agent_name, analysis_date, score, recommendation, details
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            analysis_data['ticker'],
            analysis_data['agent_name'],
            analysis_data['analysis_date'],
            analysis_data.get('score'),
            analysis_data.get('recommendation'),
            json.dumps(analysis_data.get('details', {}))
        ))

        analysis_id = cursor.lastrowid
        conn.commit()
        conn.close()

        self.logger.info(f"Saved analysis for {analysis_data['ticker']} by {analysis_data['agent_name']}")
        return analysis_id

    def get_analysis(
        self,
        ticker: str,
        agent_name: Optional[str] = None,
        analysis_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get analysis results"""

        conn = self._get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM analysis_results WHERE ticker = ?"
        params = [ticker]

        if agent_name:
            query += " AND agent_name = ?"
            params.append(agent_name)

        if analysis_date:
            query += " AND analysis_date = ?"
            params.append(analysis_date)

        query += " ORDER BY created_at DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            result = dict(row)
            result['details'] = json.loads(result['details']) if result['details'] else {}
            results.append(result)

        return results

    # Backtest results operations
    def save_backtest(self, backtest_data: Dict[str, Any]) -> int:
        """Save backtest results"""

        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO backtest_results (
                ticker, strategy, pattern, start_date, end_date,
                win_rate, total_trades, avg_return, sharpe_ratio, max_drawdown,
                validated, details
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            backtest_data['ticker'],
            backtest_data['strategy'],
            backtest_data.get('pattern'),
            backtest_data['start_date'],
            backtest_data['end_date'],
            backtest_data.get('win_rate'),
            backtest_data.get('total_trades'),
            backtest_data.get('avg_return'),
            backtest_data.get('sharpe_ratio'),
            backtest_data.get('max_drawdown'),
            backtest_data.get('validated'),
            json.dumps(backtest_data.get('details', {}))
        ))

        backtest_id = cursor.lastrowid
        conn.commit()
        conn.close()

        self.logger.info(f"Saved backtest for {backtest_data['ticker']} - {backtest_data['strategy']}")
        return backtest_id

    def get_backtest(
        self,
        ticker: str,
        strategy: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get cached backtest results"""

        conn = self._get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM backtest_results WHERE ticker = ?"
        params = [ticker]

        if strategy:
            query += " AND strategy = ?"
            params.append(strategy)

        query += " ORDER BY created_at DESC LIMIT 1"

        cursor.execute(query, params)
        row = cursor.fetchone()
        conn.close()

        if row:
            result = dict(row)
            result['details'] = json.loads(result['details']) if result['details'] else {}
            return result

        return None

    # Agent state operations
    def save_agent_state(self, agent_name: str, state: Dict[str, Any]):
        """Save agent state"""

        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO agent_state (agent_name, state, last_updated)
            VALUES (?, ?, ?)
        """, (
            agent_name,
            json.dumps(state),
            datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()

        self.logger.info(f"Saved state for {agent_name}")

    def get_agent_state(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get agent state"""

        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT state FROM agent_state WHERE agent_name = ?
        """, (agent_name,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return json.loads(row['state'])

        return None

    # Position operations
    def save_position(self, position_data: Dict[str, Any]):
        """Save or update position"""

        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO positions (
                ticker, quantity, avg_price, current_price, entry_date, last_updated, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            position_data['ticker'],
            position_data['quantity'],
            position_data['avg_price'],
            position_data.get('current_price'),
            position_data['entry_date'],
            datetime.now().isoformat(),
            position_data.get('status', 'OPEN')
        ))

        conn.commit()
        conn.close()

        self.logger.info(f"Saved position for {position_data['ticker']}")

    def get_positions(self, status: str = 'OPEN') -> List[Dict[str, Any]]:
        """Get all positions"""

        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM positions WHERE status = ? ORDER BY entry_date DESC
        """, (status,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def close_position(self, ticker: str):
        """Close a position"""

        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE positions SET status = 'CLOSED', last_updated = ?
            WHERE ticker = ? AND status = 'OPEN'
        """, (datetime.now().isoformat(), ticker))

        conn.commit()
        conn.close()

        self.logger.info(f"Closed position for {ticker}")


# Example usage
if __name__ == '__main__':
    # Initialize database
    db = DatabaseClient()

    # Save a trade
    trade = {
        'ticker': 'RELIANCE.NS',
        'action': 'BUY',
        'quantity': 10,
        'price': 2450.50,
        'timestamp': datetime.now().isoformat(),
        'strategy': 'RHS_BREAKOUT',
        'fundamental_score': 75.5,
        'technical_score': 82.3,
        'sentiment_score': 68.0,
        'management_score': 71.2,
        'backtest_validated': True,
        'notes': 'Strong bullish setup'
    }

    trade_id = db.save_trade(trade)
    print(f"Trade saved with ID: {trade_id}")

    # Get trades
    trades = db.get_trades(ticker='RELIANCE.NS', limit=10)
    print(f"\nFound {len(trades)} trades")

    # Save analysis
    analysis = {
        'ticker': 'RELIANCE.NS',
        'agent_name': 'fundamental_analyst',
        'analysis_date': datetime.now().date().isoformat(),
        'score': 75.5,
        'recommendation': 'BUY',
        'details': {'pe_ratio': 24.5, 'roe': 18.2}
    }

    db.save_analysis(analysis)

    # Get analysis
    results = db.get_analysis('RELIANCE.NS')
    print(f"\nFound {len(results)} analysis results")
