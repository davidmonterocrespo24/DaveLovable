"""
Tool for requesting plan approval from the user (Human-in-the-Loop)
"""


async def request_plan_approval(plan: str) -> str:
    """
    Request user approval for an execution plan.

    The PlanningAgent MUST call this tool after creating a plan and BEFORE delegating any tasks.

    Args:
        plan: The execution plan in markdown format with numbered steps.

    Returns:
        Approval result: Always returns "APPROVED" since approval is no longer required.
    """
    # Approval removed - auto-approve all plans
    return "APPROVED - Plan approved automatically. You can now start delegating tasks to the Coder agent."
