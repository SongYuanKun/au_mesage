"""管理端：数据源配置与审计日志。"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from db.base import BaseDB


class AdminStore(BaseDB):
    def list_data_source_configs(self) -> List[Dict[str, Any]]:
        rows = self._exec(
            """
            SELECT source_id, enabled, priority, updated_at, updated_by
            FROM data_source_config
            ORDER BY priority ASC, source_id ASC
            """
        )
        for row in rows:
            row["enabled"] = bool(row.get("enabled"))
        return rows

    def seed_data_source_configs(self, items: List[Dict[str, Any]], *, changed_by: str) -> None:
        for item in items:
            self._exec(
                """
                INSERT IGNORE INTO data_source_config
                  (source_id, enabled, priority, updated_by)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    item["source_id"],
                    1 if item.get("enabled", True) else 0,
                    int(item.get("priority", 100)),
                    changed_by,
                ),
            )

    def upsert_data_source_config(
        self,
        source_id: str,
        *,
        enabled: bool,
        priority: int,
        changed_by: str,
    ) -> Dict[str, Any]:
        before = self._exec_one(
            "SELECT source_id, enabled, priority FROM data_source_config WHERE source_id = %s",
            (source_id,),
        )
        self._exec(
            """
            INSERT INTO data_source_config (source_id, enabled, priority, updated_by)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
              enabled = VALUES(enabled),
              priority = VALUES(priority),
              updated_by = VALUES(updated_by)
            """,
            (source_id, 1 if enabled else 0, priority, changed_by),
        )
        self._exec(
            """
            INSERT INTO data_source_config_history
              (source_id, enabled, priority, changed_by)
            VALUES (%s, %s, %s, %s)
            """,
            (source_id, 1 if enabled else 0, priority, changed_by),
        )
        after = self._exec_one(
            "SELECT source_id, enabled, priority, updated_at, updated_by FROM data_source_config WHERE source_id = %s",
            (source_id,),
        )
        if after:
            after["enabled"] = bool(after.get("enabled"))
        if before:
            before["enabled"] = bool(before.get("enabled"))
        return {"before": before, "after": after}

    def rollback_data_source_config(self, source_id: str, *, changed_by: str) -> Optional[Dict[str, Any]]:
        hist = self._exec_one(
            """
            SELECT enabled, priority
            FROM data_source_config_history
            WHERE source_id = %s
            ORDER BY id DESC
            LIMIT 1 OFFSET 1
            """,
            (source_id,),
        )
        if not hist:
            return None
        return self.upsert_data_source_config(
            source_id,
            enabled=bool(hist["enabled"]),
            priority=int(hist["priority"]),
            changed_by=changed_by,
        )

    def insert_audit_log(
        self,
        *,
        actor: str,
        action: str,
        target: Optional[str],
        before_value: Optional[str],
        after_value: Optional[str],
        ip: Optional[str],
        user_agent: Optional[str],
    ) -> None:
        self._exec(
            """
            INSERT INTO audit_log
              (actor, action, target, before_value, after_value, ip, user_agent)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (actor, action, target, before_value, after_value, ip, user_agent),
        )

    def query_audit_logs(
        self,
        *,
        start: Optional[str] = None,
        end: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        clauses = ["1=1"]
        params: List[Any] = []
        if start:
            clauses.append("created_at >= %s")
            params.append(start)
        if end:
            clauses.append("created_at <= %s")
            params.append(end)
        if action:
            clauses.append("action = %s")
            params.append(action)
        params.append(limit)
        query = f"""
            SELECT id, actor, action, target, before_value, after_value, ip, user_agent, created_at
            FROM audit_log
            WHERE {' AND '.join(clauses)}
            ORDER BY created_at DESC
            LIMIT %s
        """
        rows = self._exec(query, tuple(params))
        for row in rows:
            for key in ("before_value", "after_value"):
                raw = row.get(key)
                if isinstance(raw, str):
                    try:
                        row[key] = json.loads(raw)
                    except json.JSONDecodeError:
                        pass
        return rows
