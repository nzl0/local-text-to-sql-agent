"""
DOMAIN MODELLERİ: dış dünyaya (UI, loglama, testler) sunulan sözleşmenin
saf veri temsilleridir. Bu modül hiçbir dış kütüphaneye bağımlı değildir.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class AgentResult:
    """
    Üretim ortamının (Observability) temelidir. UI katmanı, loglama
    sistemleri ve test araçları aradığı her teknik veriyi bu pakette bulur.
    """
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
