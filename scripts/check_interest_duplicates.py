from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config import Config
from database import models


def main() -> None:
    conn = models.get_connection(Config.DB_PATH)
    try:
        rows = conn.execute(
            """
            SELECT
              CASE WHEN from_user_id < to_user_id THEN from_user_id ELSE to_user_id END AS a,
              CASE WHEN from_user_id < to_user_id THEN to_user_id ELSE from_user_id END AS b,
              COUNT(*) AS c,
              SUM(CASE WHEN status = 'accepted' THEN 1 ELSE 0 END) AS accepted_count
            FROM interests
            GROUP BY a, b
            HAVING c > 1
            ORDER BY c DESC
            LIMIT 50;
            """
        ).fetchall()

        print("duplicate_pairs", len(rows))
        for r in rows:
            print(r)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
