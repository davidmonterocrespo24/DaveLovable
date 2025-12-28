"""
Tool for requesting plan approval from the user (Human-in-the-Loop)
"""

from src.utils.interaction import ask_for_approval


async def request_plan_approval(plan: str) -> str:
    """
    Request user approval for an execution plan.

    The PlanningAgent MUST call this tool after creating a plan and BEFORE delegating any tasks.

    Args:
        plan: The execution plan in markdown format with numbered steps.

    Returns:
        Approval result: "APPROVED" or user feedback/cancellation message.
    """
    feedback = await ask_for_approval(action_description=plan, context="Plan approval")

    # ask_for_approval returns None for approval, or a string for feedback/cancellation
    if feedback is None:
        approved = True
    elif feedback == "CANCELLED":
        approved = False
    else:
        approved = False

    if approved:
        return "APPROVED - Plan approved by user. You can now start delegating tasks to the Coder agent."
    elif feedback == "CANCELLED":
        return "CANCELLED - User cancelled the plan. Please inform the user that the task has been cancelled."
    else:
        return f"PLAN MODIFICATION REQUESTED - User feedback: {feedback}\n\nPlease modify the plan according to this feedback and call request_plan_approval again with the updated plan."
