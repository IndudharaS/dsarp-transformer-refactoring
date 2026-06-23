from copy import deepcopy
from typing import Any


RULE_RECOMMENDATIONS: dict[str, dict[str, Any]] = {
    "godComponent": {
        "recommendation": "Extract Component + Split Responsibilities",
        "reason": (
            "The component appears to concentrate too many responsibilities and "
            "should be decomposed into smaller cohesive components."
        ),
        "risk": "Medium",
        "steps": [
            "Identify responsibility clusters inside the god component",
            "Create smaller cohesive components for each responsibility group",
            "Move related classes or functions to the new components",
            "Introduce a facade if external callers depend on the original component",
            "Run regression tests and dependency analysis",
        ],
        "expectedImpact": (
            "Improves cohesion, reduces maintenance complexity, and lowers coupling."
        ),
        "testingAdvice": (
            "Run unit tests, integration tests, and compare component dependency "
            "metrics before and after refactoring."
        ),
        "recommendationConfidence": 0.75,
    },
    "unstableDep": {
        "recommendation": "Introduce Interface + Apply Dependency Inversion",
        "reason": (
            "A stable component depends on a more unstable component. Dependency "
            "inversion can reduce instability propagation."
        ),
        "risk": "Medium",
        "steps": [
            "Identify the stable component depending on the unstable component",
            "Create an abstraction or interface in the stable layer",
            "Make the unstable component implement the abstraction",
            "Replace the direct dependency with an interface dependency",
            "Recalculate instability and run tests",
        ],
        "expectedImpact": (
            "Improves dependency direction and reduces architecture erosion."
        ),
        "testingAdvice": (
            "Run unit tests, integration tests, and verify dependency direction "
            "using graph analysis."
        ),
        "recommendationConfidence": 0.75,
    },
    "cyclicDep": {
        "recommendation": "Introduce Interface + Extract Shared Component",
        "reason": (
            "The affected components form a dependency cycle. Introducing "
            "abstractions or extracting shared logic can break the cycle."
        ),
        "risk": "High",
        "steps": [
            "Identify the dependency edge causing the cycle",
            "Extract shared responsibility into a separate component",
            "Introduce an interface for cross-component communication",
            "Redirect dependencies through the abstraction",
            "Remove the direct cyclic dependency",
            "Run regression tests and verify the cycle is removed",
        ],
        "expectedImpact": (
            "Reduces cyclic coupling and improves maintainability."
        ),
        "testingAdvice": (
            "Run unit tests, integration tests, and dependency graph validation."
        ),
        "recommendationConfidence": 0.75,
    },
}


def build_rule_recommendation(smell: dict[str, Any]) -> dict[str, Any]:
    smell_type = smell.get("smellType")
    if smell_type not in RULE_RECOMMENDATIONS:
        raise ValueError(f"No rule recommendation exists for {smell_type}.")

    recommendation = deepcopy(RULE_RECOMMENDATIONS[smell_type])
    recommendation["targetComponents"] = list(smell["affectedElements"])
    return recommendation
