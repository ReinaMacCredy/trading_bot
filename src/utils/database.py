import logging
import sqlite3
import os
import json
from datetime import datetime
from src.config.config_loader import get_config

logger = logging.getLogger('database')

class Database:
    """Database abstraction layer for signal storage"""
    
    def __init__(self, db_path=None):
        """
        Initialize the database
        
        Args:
            db_path: Path to the database file, if None uses the one from config
        """
        config = get_config()
        self.use_database = getattr(config, 'use_database', False)
        if not self.use_database:
            logger.warning("Database is disabled. Using in-memory storage only.")
            self.conn = None
            self.signals = []
            return
            
        self.db_type = getattr(config, 'db_type', 'sqlite')
        
        if self.db_type == 'sqlite':
            if not db_path:
                db_path = 'trading_bot.db'
                
            # Ensure directory exists
            os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else '.', exist_ok=True)
            
            try:
                self.conn = sqlite3.connect(db_path)
                self.conn.row_factory = sqlite3.Row
                self._create_tables()
                logger.info(f"Connected to SQLite database at {db_path}")
            except Exception as e:
                logger.error(f"Error connecting to SQLite database: {e}")
                self.conn = None
                self.signals = []
        else:
            # Future support for other databases
            logger.error(f"Unsupported database type: {self.db_type}")
            self.conn = None
            self.signals = []
    
    def _create_tables(self):
        """Create the necessary tables if they don't exist"""
        if not self.conn:
            return
            
        try:
            cursor = self.conn.cursor()
            
            # Create signals table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    strategy_code TEXT NOT NULL,
                    entry_price REAL NOT NULL,
                    tp_price REAL NOT NULL,
                    sl_price REAL NOT NULL,
                    ratio TEXT,
                    status TEXT,
                    imminent INTEGER,
                    author TEXT,
                    created_at TEXT,
                    metadata TEXT
                )
            ''')
            
            # Create index on symbol and strategy_code
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_symbol_strategy 
                ON signals (symbol, strategy_code)
            ''')
            
            self.conn.commit()
            logger.debug("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
    
    def store_signal(self, signal):
        """Store a signal in the database"""
        if not self.use_database or not self.conn:
            self.signals.append(signal)
            return True
            
        try:
            cursor = self.conn.cursor()
            
            # Store metadata as JSON if it exists
            metadata = None
            if 'metadata' in signal:
                metadata = json.dumps(signal['metadata'])
                
            # Check for duplicates within the last minute
            cursor.execute('''
                SELECT COUNT(*) as count FROM signals 
                WHERE symbol = ? AND strategy_code = ? 
                AND created_at > datetime('now', '-60 seconds')
            ''', (signal['symbol'], signal['strategy_code']))
            
            result = cursor.fetchone()
            if result['count'] > 0:
                logger.warning(f"Duplicate signal detected for {signal['symbol']}-{signal['strategy_code']}")
                return False
            
            # Insert the signal
            cursor.execute('''
                INSERT INTO signals 
                (symbol, strategy_code, entry_price, tp_price, sl_price, ratio, status, imminent, author, created_at, metadata) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?)
            ''', (
                signal['symbol'],
                signal['strategy_code'],
                signal['entry_price'],
                signal['tp_price'],
                signal['sl_price'],
                signal['ratio'],
                signal['status'],
                signal['imminent'],
                signal['author'],
                metadata
            ))
            
            self.conn.commit()
            logger.debug(f"Signal stored in database: {signal['symbol']}-{signal['strategy_code']}")
            return True
        except Exception as e:
            logger.error(f"Error storing signal in database: {e}")
            self.signals.append(signal)  # Fallback to in-memory storage
            return True  # Return True because we stored it in memory
    
    def get_signals(self, symbol=None, strategy_code=None, limit=100):
        """Get signals from the database"""
        if not self.use_database or not self.conn:
            # Filter in-memory signals
            filtered = self.signals
            if symbol:
                filtered = [s for s in filtered if s['symbol'] == symbol]
            if strategy_code:
                filtered = [s for s in filtered if s['strategy_code'] == strategy_code]
            return filtered[-limit:]  # Return last 'limit' signals
            
        try:
            cursor = self.conn.cursor()
            
            query = "SELECT * FROM signals"
            params = []
            
            if symbol or strategy_code:
                query += " WHERE"
                
                if symbol:
                    query += " symbol = ?"
                    params.append(symbol)
                    
                    if strategy_code:
                        query += " AND strategy_code = ?"
                        params.append(strategy_code)
                elif strategy_code:
                    query += " strategy_code = ?"
                    params.append(strategy_code)
            
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            
            rows = cursor.fetchall()
            result = []
            
            for row in rows:
                signal = dict(row)
                
                # Parse metadata if it exists
                if signal['metadata']:
                    try:
                        signal['metadata'] = json.loads(signal['metadata'])
                    except:
                        pass
                        
                result.append(signal)
                
            return result
        except Exception as e:
            logger.error(f"Error getting signals from database: {e}")
            return []
    
    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
            logger.debug("Database connection closed")

# Create a global instance
db = Database() 