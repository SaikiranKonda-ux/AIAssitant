from ..models.schemas import UserClarification, RequirementType
from typing import List


def discussion_facilitator(requirement_text, requirement_type):
    if requirement_type != RequirementType.NEW_FEATURE_FROM_SCRATCH:
        return []

    print("\nNew Feature Discussion")
    print("=" * 60)
    print("Gathering context for implementation planning...")

    clarifications = []

    print("\n1. Technology Stack")
    tech_stack = input("Preferred technologies/frameworks (or 'skip'): ")
    if tech_stack.lower() != 'skip':
        clarifications.append(UserClarification(
            question="Technology stack preference",
            answer=tech_stack
        ))

    print("\n2. Architecture Pattern")
    architecture = input("Architecture preference (MVC, microservices, etc.) or 'skip': ")
    if architecture.lower() != 'skip':
        clarifications.append(UserClarification(
            question="Architecture pattern",
            answer=architecture
        ))

    print("\n3. Integration Requirements")
    integrations = input("External integrations needed (APIs, databases, etc.) or 'skip': ")
    if integrations.lower() != 'skip':
        clarifications.append(UserClarification(
            question="External integrations",
            answer=integrations
        ))

    print("\n4. Additional Context")
    additional = input("Any other requirements or constraints? (or 'skip'): ")
    if additional.lower() != 'skip':
        clarifications.append(UserClarification(
            question="Additional context",
            answer=additional
        ))

    print("\n" + "=" * 60)

    return clarifications
