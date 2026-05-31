# -*- coding: utf-8 -*-
import sqlite3, json
from typing import Any, Dict, List, Optional

class Database:
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            import os, platform
            if platform.system() == "Windows":
                base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or os.path.expanduser("~")
                user_dir = os.path.join(base, "VantageMail")
            elif platform.system() == "Darwin":
                user_dir = os.path.expanduser("~/Library/Application Support/VantageMail")
            else:
                user_dir = os.path.expanduser("~/.local/share/vantage-mail")
            
            if not os.path.exists(user_dir):
                os.makedirs(user_dir)
            db_path = os.path.join(user_dir, 'outlook_client.db')
            
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.fts_available = False
        self._create_tables()

    def _create_tables(self) -> None:
        cursor = self.conn.cursor()
        tables = ['folders', 'events', 'contacts', 'tasks']
        for table in tables:
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {table} (
                    id TEXT PRIMARY KEY,
                    data TEXT,
                    synced_at TEXT
                )
            """)
        # Drop emails if old schema
        try:
            cursor.execute("SELECT account_email FROM emails LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("DROP TABLE IF EXISTS emails")
        # Create emails table with compound primary key and date column
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS emails (
                id TEXT,
                account_email TEXT,
                folder_id TEXT,
                data TEXT,
                date TEXT,
                synced_at TEXT,
                PRIMARY KEY (account_email, folder_id, id)
            )
        """)
        # Schema migration: check if date column exists, if not alter table and populate
        try:
            cursor.execute("PRAGMA table_info(emails)")
            cols = [col[1] for col in cursor.fetchall()]
            if cols and "date" not in cols:
                cursor.execute("ALTER TABLE emails ADD COLUMN date TEXT")
                cursor.execute("UPDATE emails SET date = json_extract(data, '$.date')")
        except Exception as e_col:
            from utils.logger import log_error
            log_error(f"Failed to migrate emails table schema: {e_col}")
        # indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_emails_account_folder ON emails(account_email, folder_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_emails_acc_fld_date ON emails(account_email, folder_id, date)")
        # accounts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                email TEXT PRIMARY KEY,
                provider TEXT,
                config TEXT,
                created_at TEXT
            );
        """)
        self.conn.commit()

        # FTS5 virtual table setup
        try:
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS emails_fts USING fts5(
                    id,
                    account_email,
                    folder_id,
                    subject,
                    body
                );
            """)
            self.fts_available = True
        except sqlite3.OperationalError as e:
            from utils.logger import log_error
            log_error(f"FTS5 is not available in SQLite on this system: {e}")

        # Startup migration: populate emails_fts from emails if empty
        if self.fts_available:
            try:
                cursor.execute("SELECT COUNT(*) FROM emails_fts")
                fts_count = cursor.fetchone()[0]
                if fts_count == 0:
                    cursor.execute("SELECT COUNT(*) FROM emails")
                    emails_count = cursor.fetchone()[0]
                    if emails_count > 0:
                        cursor.execute("""
                            INSERT INTO emails_fts (id, account_email, folder_id, subject, body)
                            SELECT id, account_email, folder_id,
                                   json_extract(data, '$.subject'),
                                   json_extract(data, '$.body')
                            FROM emails
                        """)
                        self.conn.commit()
                        from utils.logger import log_info
                        log_info(f"FTS5 migration completed: populated {emails_count} existing emails in emails_fts.")
            except Exception as e_mig:
                from utils.logger import log_error
                log_error(f"FTS5 startup migration failed: {e_mig}")

    def upsert(self, table: str, id: str, data_dict: Dict[str, Any]) -> None:
        cursor = self.conn.cursor()
        data_str = json.dumps(data_dict)
        synced_at = data_dict.get('synced_at')
        cursor.execute(f"""
            INSERT INTO {table} (id, data, synced_at) VALUES (?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET data=excluded.data, synced_at=excluded.synced_at
        """, (id, data_str, synced_at))
        self.conn.commit()

    def get(self, table: str, id: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT data FROM {table} WHERE id=?", (id,))
        row = cursor.fetchone()
        return json.loads(row[0]) if row else None

    def get_all(self, table: str) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT data FROM {table}")
        rows = cursor.fetchall()
        return [json.loads(r[0]) for r in rows]

    def delete(self, table: str, id: str) -> None:
        cursor = self.conn.cursor()
        cursor.execute(f"DELETE FROM {table} WHERE id=?", (id,))
        self.conn.commit()

    # Account management methods
    def save_account(self, email, provider, config_dict):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO accounts (email, provider, config, created_at) VALUES (?,?,?,datetime('now'))",
            (email, provider, json.dumps(config_dict))
        )
        self.conn.commit()

    def load_accounts(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT email, provider, config, created_at FROM accounts")
        rows = cursor.fetchall()
        return [dict(email=row[0], provider=row[1], config=json.loads(row[2]), created_at=row[3]) for row in rows]

    def delete_account(self, email):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM accounts WHERE email=?", (email,))
        self.conn.commit()

    def get_cached_emails(self, account_email: str, folder_id: str, limit: Optional[int] = None) -> List[Dict]:
        cursor = self.conn.cursor()
        if limit is not None:
            cursor.execute(
                "SELECT data FROM emails WHERE account_email = ? AND folder_id = ? ORDER BY date DESC LIMIT ?",
                (account_email, folder_id, limit)
            )
        else:
            cursor.execute(
                "SELECT data FROM emails WHERE account_email = ? AND folder_id = ? ORDER BY date DESC",
                (account_email, folder_id)
            )
        rows = cursor.fetchall()
        return [json.loads(r[0]) for r in rows]

    def get_cached_email(self, account_email: str, folder_id: str, email_id: str) -> Optional[Dict]:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT data FROM emails WHERE account_email = ? AND folder_id = ? AND id = ?",
            (account_email, folder_id, str(email_id))
        )
        row = cursor.fetchone()
        return json.loads(row[0]) if row else None

    def save_cached_email(self, account_email: str, folder_id: str, email_id: str, data_dict: Dict):
        cursor = self.conn.cursor()
        date_val = data_dict.get('date')
        cursor.execute("""
            INSERT OR REPLACE INTO emails (id, account_email, folder_id, data, date, synced_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
        """, (str(email_id), account_email, folder_id, json.dumps(data_dict), date_val))
        
        if self.fts_available:
            cursor.execute(
                "DELETE FROM emails_fts WHERE account_email = ? AND folder_id = ? AND id = ?",
                (account_email, folder_id, str(email_id))
            )
            cursor.execute("""
                INSERT INTO emails_fts (id, account_email, folder_id, subject, body)
                VALUES (?, ?, ?, ?, ?)
            """, (
                str(email_id),
                account_email,
                folder_id,
                data_dict.get('subject', ''),
                data_dict.get('body', '')
            ))
        self.conn.commit()

    def batch_save_emails(self, account_email: str, folder_id: str, msgs: list):
        cursor = self.conn.cursor()
        with self.conn:  # single transaction = single commit
            for msg in msgs:
                date_val = msg.get('date')
                cursor.execute(
                    "INSERT OR REPLACE INTO emails (id, account_email, folder_id, data, date, synced_at)"
                    " VALUES (?, ?, ?, ?, ?, datetime('now'))",
                    (str(msg['id']), account_email, folder_id, json.dumps(msg), date_val)
                )
                if self.fts_available:
                    cursor.execute(
                        "DELETE FROM emails_fts WHERE account_email = ? AND folder_id = ? AND id = ?",
                        (account_email, folder_id, str(msg['id']))
                    )
                    cursor.execute("""
                        INSERT INTO emails_fts (id, account_email, folder_id, subject, body)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        str(msg['id']),
                        account_email,
                        folder_id,
                        msg.get('subject', ''),
                        msg.get('body', '')
                    ))

    def delete_cached_email(self, account_email: str, folder_id: str, email_id: str):
        cursor = self.conn.cursor()
        cursor.execute(
            "DELETE FROM emails WHERE account_email = ? AND folder_id = ? AND id = ?",
            (account_email, folder_id, str(email_id))
        )
        if self.fts_available:
            cursor.execute(
                "DELETE FROM emails_fts WHERE account_email = ? AND folder_id = ? AND id = ?",
                (account_email, folder_id, str(email_id))
            )
        self.conn.commit()

    def get_total_email_count(self) -> int:
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM emails")
        row = cursor.fetchone()
        return row[0] if row else 0

    def _sanitize_fts_query(self, query: str) -> str:
        import re
        words = re.findall(r'[a-zA-Z0-9]+', query)
        if not words:
            return ""
        terms = " AND ".join(f"{w}*" for w in words)
        return f"{{subject body}} : ({terms})"

    def search_emails(self, account_emails: List[str], query: str) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        if not account_emails or not query:
            return []
        placeholders = ', '.join('?' for _ in account_emails)
        
        if self.fts_available:
            fts_query = self._sanitize_fts_query(query)
            if not fts_query:
                return []
            sql = f"""
                SELECT e.data, e.account_email, e.folder_id
                FROM emails e
                JOIN emails_fts fts ON e.account_email = fts.account_email
                                   AND e.folder_id = fts.folder_id
                                   AND e.id = fts.id
                WHERE e.account_email IN ({placeholders})
                  AND emails_fts MATCH ?
            """
            params = list(account_emails) + [fts_query]
        else:
            like_query = f"%{query}%"
            sql = f"""
                SELECT data, account_email, folder_id FROM emails
                WHERE account_email IN ({placeholders})
                  AND (
                    json_extract(data, '$.subject') LIKE ?
                    OR json_extract(data, '$.body') LIKE ?
                  )
            """
            params = list(account_emails) + [like_query, like_query]
            
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        
        results = []
        for r in rows:
            try:
                msg = json.loads(r[0])
                msg['_account_email'] = r[1]
                msg['_folder_id'] = r[2]
                results.append(msg)
            except Exception:
                pass
        return results


