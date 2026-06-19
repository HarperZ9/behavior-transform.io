# Transitional stub — re-exports from classifier_orig while modules are extracted.
# Delete classifier_orig.py in Task 11 once all modules are in place.
from classifier_orig import *  # noqa: F401, F403
from classifier_orig import main  # noqa: F401
from classifier._audit import _AUDIT_PATH, _audit_write, audit_log_cmd  # noqa: F401
from classifier._policy import (  # noqa: F401
    PolicyDef, _load_policy_def, _active_policy,
    policy_list_cmd, policy_show_cmd, policy_activate_cmd,
    policy_save_cmd, policy_delete_cmd, policy_diff_cmd,
    policy_export_cmd, policy_import_cmd,
)
from classifier._ci import fence_check, probe_cmd, status_cmd, hook_install, hook_remove  # noqa: F401
from classifier._analysis import (  # noqa: F401
    _BASELINE_PATH, budget_summary, save_baseline, drift_report,
    pipeline_report, unified_report, enforce_plan,
    modulate_report, window_report, compound_report,
)
from classifier._context import (  # noqa: F401
    _context_files, _split_paragraphs, analyze_context,
    annotate_file, validate_file, ctx_fix,
)
