"""
DTO/ŞEKİLLENDİRME MODÜLÜ: katalog verisini HTTP yanıtları için (ham SQL
göstermeden) yapısal JSON'a çevirir; veri tabanının "aktif" olup olmadığını
kontrol eder.
"""

import logging
import re
from pathlib import Path

from app.adapters.outbound.catalog.static_catalog import CATALOG, file_for

logger = logging.getLogger(__name__)

# DDL içindeki kolon satırlarını yapısal veriye çevirir (ham SQL göstermeden).
_COL_RE = re.compile(
    r"^\s*(\w+)\s+(VARCHAR|INTEGER|INT|BIGINT|DOUBLE|DATE|TIMESTAMP|BOOLEAN|TEXT)\b[^-]*(?:--\s*(.*))?$"
)


def data_ok() -> bool:
    """Katalogdaki tüm Excel veri dosyaları yerinde mi (veri tabanı 'aktif' mi)."""
    try:
        return all(Path(file_for(t)).exists() for t in CATALOG)
    except Exception:
        logger.debug("Veri dosyaları kontrol edilirken hata oluştu", exc_info=True)
        return False


def parse_columns(ddl: str):
    cols = []
    for line in ddl.splitlines():
        m = _COL_RE.match(line)
        if m:
            cols.append({
                "name": m.group(1),
                "type": m.group(2),
                "description": (m.group(3) or "").strip(),
            })
    return cols


def short_desc(passage: str) -> str:
    m = re.search(r"Açıklama:\s*(.*?)\s*\|", passage)
    return m.group(1).strip() if m else ""
