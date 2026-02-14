from dataclasses import dataclass
from typing import Optional, List, Dict


@dataclass
class TaskResult:
    summary: str
    artifacts: Optional[List[str]] = None
    metadata: Optional[Dict] = None
