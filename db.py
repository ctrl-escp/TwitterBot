import sqlite3
from threading import RLock

LOCK = RLock()


class DatabaseSqlite3:
	default_db_filename = "database.db"

	def __init__(self, db_filename=None):
		self.db_filename = db_filename or self.default_db_filename
		self.conn = None

	def get_db(self):
		if self.conn is None:
			self.conn = sqlite3.connect(self.db_filename)
		return self.conn

	def run_query(self, query, args=None):
		result = {
			"success": False
		}
		try:
			conn = self.get_db()
			cur = conn.cursor()
			with LOCK:
				result["rows"] = cur.execute(query, args or [])
				conn.commit()
				result["success"] = True
		except Exception as exp:
			result["error"] = f"{exp}"
		return result
