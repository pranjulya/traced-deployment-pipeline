"""Read-only local lookup tool.

Only fixture keys are reachable and there are no arbitrary parameters; the
tool can never expand the agent's capabilities.
"""


class ToolError(Exception):
    def __init__(self, safe_code="TOOL_FAILURE"):
        super().__init__(safe_code)
        self.safe_code = safe_code
        self.safe_error_code = safe_code


class LookupTool:
    alias = "lookup"
    FIXTURES = {
        "alpha": "alpha-value",
        "beta": "beta-value",
    }

    def __init__(self, fail_next=0):
        self.calls = 0
        self._fail_next = fail_next

    def lookup(self, key):
        self.calls += 1
        if self._fail_next > 0:
            self._fail_next -= 1
            raise ToolError("TOOL_FAILURE")
        if key not in self.FIXTURES:
            raise ToolError("TOOL_NOT_FOUND")
        return self.FIXTURES[key]
