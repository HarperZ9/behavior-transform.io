# Transitional stub — re-exports from classifier_orig while modules are extracted.
# Delete classifier_orig.py in Task 11 once all modules are in place.
from classifier_orig import *  # noqa: F401, F403
from classifier_orig import main  # noqa: F401
from classifier._audit import _AUDIT_PATH, _audit_write, audit_log_cmd  # noqa: F401
