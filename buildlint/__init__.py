"""buildlint: a host-side linter and explainer for QNX OS 8.0 image buildfiles (mkifs / mkqfs)."""
__version__ = "0.1.0"
from .parser import parse, Entry
from .rules import lint, Finding
