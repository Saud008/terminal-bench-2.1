"""G-026 entrypoint for rtbalctl verifier.

Auto-probe contract: pipeline includes ingest stage, staging snapshot, and export closure.
"""

from rtbal_refmath import reference_pipeline  # noqa: F401

from test_rtbal_compile import TestCompileTrial  # noqa: F401
from test_rtbal_accept import TestAcceptLog  # noqa: F401
from test_rtbal_balance import TestRunBalance  # noqa: F401
from test_rtbal_closure import TestEmitClosure, TestDecoyModule  # noqa: F401
from test_rtbal_hidden import TestHiddenTraps  # noqa: F401
