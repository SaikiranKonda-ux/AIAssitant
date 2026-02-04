import sys
from pathlib import Path
from typing import Tuple, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from models.shared_context import SharedContext, WorkflowState


class StallDetector:
    def __init__(self, max_stalls: int = 3):
        self.max_stalls = max_stalls
        self.last_state = None
        self.state_repeat_count = 0

    def check_for_stall(self, shared_context: SharedContext) -> Tuple[bool, Optional[str]]:
        if shared_context.workflow_state in [WorkflowState.COMPLETED, WorkflowState.FAILED]:
            return False, None

        if shared_context.stall_count >= self.max_stalls:
            return True, f"Maximum stall limit ({self.max_stalls}) reached"

        if len(shared_context.agent_invocations) == 0:
            return False, None

        recent_failures = [
            inv for inv in shared_context.agent_invocations[-3:]
            if not inv.success
        ]

        if len(recent_failures) >= 2:
            return True, f"Multiple agent failures detected: {len(recent_failures)} in last 3 invocations"

        if len(shared_context.agent_invocations) > 1:
            last_invocation = shared_context.agent_invocations[-1]
            previous_invocation = shared_context.agent_invocations[-2]

            if last_invocation.agent_name == previous_invocation.agent_name:
                if not last_invocation.success:
                    return True, f"Agent {last_invocation.agent_name} failed twice consecutively"

        if shared_context.workflow_state == self.last_state:
            self.state_repeat_count += 1
        else:
            self.state_repeat_count = 0
            self.last_state = shared_context.workflow_state

        if self.state_repeat_count >= 5:
            return True, f"Workflow stuck in {shared_context.workflow_state.value} for {self.state_repeat_count} iterations"

        return False, None

    def detect_progress(self, shared_context: SharedContext) -> bool:
        if not shared_context.agent_invocations:
            return False

        if shared_context.implementation_plan:
            return True

        if shared_context.codebase_context:
            return True

        if shared_context.research_findings:
            return True

        return False

    def reset(self):
        self.last_state = None
        self.state_repeat_count = 0
