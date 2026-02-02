from ..models.schemas import RequirementClassification, UserClarification
from typing import List


def ambiguity_resolver(classification):
    if classification.confidence >= 0.8 and len(classification.ambiguities) == 0:
        return confirm_perception(classification)

    return resolve_ambiguities(classification)


def confirm_perception(classification):
    print(f"\nRequirement Classification: {classification.requirement_type.value}")
    print(f"Confidence: {classification.confidence:.2f}")
    print(f"\nReasoning:")
    print(classification.reasoning)

    confirm = input("\nConfirm this classification? (yes/no): ")

    if confirm.lower() in ["yes", "y"]:
        return classification, []

    print("\nPlease provide additional context:")
    additional_context = input("> ")

    return None, [UserClarification(
        question="Please clarify the requirement",
        answer=additional_context
    )]


def resolve_ambiguities(classification):
    print(f"\nClassification: {classification.requirement_type.value}")
    print(f"Confidence: {classification.confidence:.2f} (needs clarification)")
    print(f"\nReasoning:")
    print(classification.reasoning)

    if classification.ambiguities:
        print(f"\nAmbiguities detected ({len(classification.ambiguities)}):")

        clarifications = []
        for i, ambiguity in enumerate(classification.ambiguities, 1):
            print(f"\n{i}. {ambiguity}")
            answer = input("Your answer: ")
            clarifications.append(UserClarification(
                question=ambiguity,
                answer=answer
            ))

        return None, clarifications
    else:
        print("\nLow confidence. Please provide more context:")
        additional_context = input("> ")

        return None, [UserClarification(
            question="Provide additional context",
            answer=additional_context
        )]
