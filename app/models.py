"""AgentResult: agent.ask()'ün döndürdüğü sonuç paketi. UI, CLI ve loglama
aradığı her teknik veriyi burada bulur."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class AgentResult:
    question: str
    tables: List[str]
    sql: str
    columns: Optional[List[str]] = None
    rows: Optional[List[Dict[str, Any]]] = None
    insight: str = ""
    retry_count: int = 0
    # Otomatik onarım denemelerinin yapısal kaydı. Her öğe bir düzeltmeyi
    # temsil eder: {attempt, error, broken_sql, fixed_sql}. UI turuncu
    # "otomatik düzeltme" rozetlerini doğrudan bu listeden besler.
    auto_fixes: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None
