"""Structured planning layer for math-aware scene generation."""

from __future__ import annotations

import math
import re
from typing import Any, Literal

from pydantic import BaseModel, Field


class SceneObject(BaseModel):
    kind: str
    name: str
    properties: dict[str, Any] = Field(default_factory=dict)


class SceneSpec(BaseModel):
    concept_type: Literal[
        "vector_addition",
        "function_plot",
        "euclidean_algorithm",
        "matrix_multiplication",
        "gradient_descent",
        "bst_insertion",
        "generic_explanation",
    ]
    render_strategy: Literal["template", "llm"] = "llm"
    title: str
    prompt: str
    sequence: list[str] = Field(default_factory=list)
    objects: list[SceneObject] = Field(default_factory=list)
    annotations: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


def _extract_coordinate_pairs(prompt: str) -> list[tuple[float, float]]:
    pairs: list[tuple[float, float]] = []
    for x_text, y_text in re.findall(r"\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)", prompt):
        pairs.append((float(x_text), float(y_text)))
    return pairs


def _plan_vector_addition(prompt: str) -> SceneSpec:
    pairs = _extract_coordinate_pairs(prompt)
    first = pairs[0] if len(pairs) >= 1 else (2.0, 1.0)
    second = pairs[1] if len(pairs) >= 2 else (1.0, 2.0)
    vector_sum = (first[0] + second[0], first[1] + second[1])
    return SceneSpec(
        concept_type="vector_addition",
        render_strategy="template",
        title="Vector Addition",
        prompt=prompt,
        sequence=[
            "draw_plane",
            "draw_first_vector",
            "translate_second_vector_to_tip",
            "draw_sum_vector",
            "highlight_result",
        ],
        objects=[
            SceneObject(kind="vector", name="a", properties={"start": [0.0, 0.0], "end": list(first), "color": "BLUE"}),
            SceneObject(kind="vector", name="b", properties={"start": list(first), "end": list(vector_sum), "color": "GREEN"}),
            SceneObject(kind="vector", name="sum", properties={"start": [0.0, 0.0], "end": list(vector_sum), "color": "YELLOW"}),
        ],
        annotations=["a", "b", "a + b"],
        metadata={"show_parallelogram_hint": True},
    )


def _plan_function_plot(prompt: str) -> SceneSpec | None:
    prompt_lower = prompt.lower()
    if "sin" in prompt_lower or "sine" in prompt_lower:
        return SceneSpec(
            concept_type="function_plot",
            render_strategy="template",
            title="Sine Function",
            prompt=prompt,
            sequence=["draw_axes", "draw_curve", "write_equation"],
            objects=[
                SceneObject(
                    kind="function",
                    name="curve",
                    properties={
                        "family": "sine",
                        "x_range": [-math.pi, math.pi],
                        "y_range": [-1.5, 1.5],
                        "equation": r"y=\sin(x)",
                        "color": "BLUE",
                    },
                )
            ],
            annotations=[r"y=\sin(x)"],
        )
    if "parabola" in prompt_lower or "x^2" in prompt_lower or "x**2" in prompt_lower:
        equation = r"y=\frac{x^2}{4}"
        scale = 0.25
        fraction_match = re.search(r"x\^2\s*/\s*(\d+(?:\.\d+)?)", prompt_lower)
        if fraction_match:
            divisor = float(fraction_match.group(1))
            if divisor != 0:
                scale = 1.0 / divisor
                equation = rf"y=\frac{{x^2}}{{{int(divisor) if divisor.is_integer() else divisor}}}"
        return SceneSpec(
            concept_type="function_plot",
            render_strategy="template",
            title="Parabola",
            prompt=prompt,
            sequence=["draw_axes", "draw_curve", "write_equation"],
            objects=[
                SceneObject(
                    kind="function",
                    name="curve",
                    properties={
                        "family": "parabola",
                        "scale": scale,
                        "x_range": [-4.0, 4.0],
                        "y_range": [0.0, 5.0],
                        "equation": equation,
                        "color": "GREEN",
                    },
                )
            ],
            annotations=[equation],
        )
    return None


def _euclidean_steps(a: int, b: int) -> tuple[list[str], int]:
    steps: list[str] = []
    x, y = max(a, b), min(a, b)
    while y != 0:
        q, r = divmod(x, y)
        steps.append(f"{x} = {y} \\cdot {q} + {r}")
        x, y = y, r
    return steps, x


def _extract_integers(prompt: str) -> list[int]:
    return [int(value) for value in re.findall(r"-?\d+", prompt)]


def _plan_euclidean(prompt: str) -> SceneSpec | None:
    prompt_lower = prompt.lower()
    if "gcd" not in prompt_lower and "euclidean algorithm" not in prompt_lower:
        return None
    values = [int(value) for value in re.findall(r"\d+", prompt)]
    if len(values) < 2:
        values = [48, 18]
    steps, gcd_value = _euclidean_steps(values[0], values[1])
    annotations = steps + [rf"\gcd({values[0]}, {values[1]}) = {gcd_value}"]
    return SceneSpec(
        concept_type="euclidean_algorithm",
        render_strategy="template",
        title="Euclidean Algorithm",
        prompt=prompt,
        sequence=["write_each_division_step", "highlight_final_gcd"],
        objects=[
            SceneObject(kind="number_pair", name="inputs", properties={"a": values[0], "b": values[1], "gcd": gcd_value})
        ],
        annotations=annotations,
    )


def _plan_matrix_multiplication(prompt: str) -> SceneSpec | None:
    prompt_lower = prompt.lower()
    if "matrix multiplication" not in prompt_lower and ("matrix" not in prompt_lower or "vector" not in prompt_lower):
        return None
    values = _extract_integers(prompt)
    left = [[1, 2], [3, 4]]
    right = [[2], [1]]
    if len(values) >= 6:
        left = [[values[0], values[1]], [values[2], values[3]]]
        right = [[values[4]], [values[5]]]
    result = [
        [left[0][0] * right[0][0] + left[0][1] * right[1][0]],
        [left[1][0] * right[0][0] + left[1][1] * right[1][0]],
    ]
    return SceneSpec(
        concept_type="matrix_multiplication",
        render_strategy="template",
        title="Matrix Multiplication",
        prompt=prompt,
        sequence=["write_operands", "highlight_row_and_column", "show_result_entries"],
        objects=[
            SceneObject(kind="matrix", name="left", properties={"values": left}),
            SceneObject(kind="matrix", name="right", properties={"values": right}),
            SceneObject(kind="matrix", name="result", properties={"values": result}),
        ],
        annotations=[f"{left[0][0]}*{right[0][0]} + {left[0][1]}*{right[1][0]} = {result[0][0]}"],
    )


def _plan_gradient_descent(prompt: str) -> SceneSpec | None:
    prompt_lower = prompt.lower()
    if "gradient descent" not in prompt_lower:
        return None
    start_x = -2.0
    minimum_x = 1.0
    metadata = {
        "curve": {"a": 0.4, "h": minimum_x, "k": 0.5},
        "points": [
            [-2.0, 0.4 * ((-2.0 - minimum_x) ** 2) + 0.5],
            [-0.5, 0.4 * ((-0.5 - minimum_x) ** 2) + 0.5],
            [0.6, 0.4 * ((0.6 - minimum_x) ** 2) + 0.5],
            [0.95, 0.4 * ((0.95 - minimum_x) ** 2) + 0.5],
        ],
        "minimum": [minimum_x, 0.5],
    }
    return SceneSpec(
        concept_type="gradient_descent",
        render_strategy="template",
        title="Gradient Descent",
        prompt=prompt,
        sequence=["draw_axes", "draw_loss_curve", "animate_optimizer_steps", "highlight_minimum"],
        objects=[
            SceneObject(kind="curve", name="loss", properties=metadata["curve"]),
            SceneObject(kind="path", name="optimizer", properties={"points": metadata["points"]}),
        ],
        annotations=["Gradient descent", "minimum"],
        metadata=metadata,
    )


def _plan_bst_insertion(prompt: str) -> SceneSpec | None:
    prompt_lower = prompt.lower()
    if "binary search tree" not in prompt_lower and "bst" not in prompt_lower:
        return None
    values = _extract_integers(prompt)
    if len(values) < 3:
        values = [8, 4, 10]
    root, left, right = values[:3]
    ordered = sorted([left, root, right])
    if root != ordered[1]:
        root = ordered[1]
        left = ordered[0]
        right = ordered[2]
    return SceneSpec(
        concept_type="bst_insertion",
        render_strategy="template",
        title="Binary Search Tree Insertion",
        prompt=prompt,
        sequence=["insert_root", "insert_left_child", "insert_right_child"],
        objects=[
            SceneObject(kind="node", name="root", properties={"value": root, "position": [0.0, 1.2]}),
            SceneObject(kind="node", name="left", properties={"value": left, "position": [-2.0, -0.3]}),
            SceneObject(kind="node", name="right", properties={"value": right, "position": [2.0, -0.3]}),
        ],
        annotations=[str(root), str(left), str(right)],
        metadata={"edges": [["root", "left"], ["root", "right"]]},
    )


def infer_scene_spec(prompt: str) -> SceneSpec:
    prompt_lower = prompt.lower()
    if "vector addition" in prompt_lower or ("vector" in prompt_lower and ("add" in prompt_lower or "sum" in prompt_lower)):
        return _plan_vector_addition(prompt)

    function_spec = _plan_function_plot(prompt)
    if function_spec is not None:
        return function_spec

    euclidean_spec = _plan_euclidean(prompt)
    if euclidean_spec is not None:
        return euclidean_spec

    matrix_spec = _plan_matrix_multiplication(prompt)
    if matrix_spec is not None:
        return matrix_spec

    gradient_spec = _plan_gradient_descent(prompt)
    if gradient_spec is not None:
        return gradient_spec

    bst_spec = _plan_bst_insertion(prompt)
    if bst_spec is not None:
        return bst_spec

    return SceneSpec(
        concept_type="generic_explanation",
        render_strategy="llm",
        title="Generated Explanation",
        prompt=prompt,
        sequence=["introduce_concept", "build_visual", "summarize"],
        annotations=[],
        metadata={"needs_llm_layout": True},
    )


def validate_scene_spec(spec: SceneSpec) -> SceneSpec:
    if spec.concept_type == "vector_addition":
        vectors = {obj.name: obj for obj in spec.objects if obj.kind == "vector"}
        for key in ("a", "b", "sum"):
            if key not in vectors:
                raise ValueError(f"Vector scene is missing '{key}'")
        a_end = vectors["a"].properties["end"]
        b_start = vectors["b"].properties["start"]
        b_end = vectors["b"].properties["end"]
        sum_end = vectors["sum"].properties["end"]
        if b_start != a_end:
            raise ValueError("Second vector must start at the tip of the first vector")
        expected_sum = [b_end[0], b_end[1]]
        if sum_end != expected_sum:
            raise ValueError("Sum vector endpoint must match the translated second vector endpoint")

    if spec.concept_type == "euclidean_algorithm" and not spec.annotations:
        raise ValueError("Euclidean algorithm scenes require at least one derivation step")

    if spec.concept_type == "matrix_multiplication":
        matrices = {obj.name: obj.properties["values"] for obj in spec.objects if obj.kind == "matrix"}
        left = matrices["left"]
        right = matrices["right"]
        result = matrices["result"]
        if len(left[0]) != len(right):
            raise ValueError("Matrix multiplication dimensions do not align")
        expected = [
            [left[0][0] * right[0][0] + left[0][1] * right[1][0]],
            [left[1][0] * right[0][0] + left[1][1] * right[1][0]],
        ]
        if result != expected:
            raise ValueError("Matrix multiplication result is incorrect")

    if spec.concept_type == "gradient_descent":
        points = spec.metadata.get("points", [])
        if len(points) < 2:
            raise ValueError("Gradient descent scenes require multiple optimizer steps")
        y_values = [point[1] for point in points]
        if y_values[-1] > y_values[0]:
            raise ValueError("Gradient descent path should move toward lower loss")

    if spec.concept_type == "bst_insertion":
        nodes = {obj.name: obj.properties for obj in spec.objects if obj.kind == "node"}
        root = nodes["root"]["value"]
        left = nodes["left"]["value"]
        right = nodes["right"]["value"]
        if not (left < root < right):
            raise ValueError("BST insertion scene must preserve left < root < right ordering")

    return spec


def scene_spec_to_prompt(spec: SceneSpec) -> str:
    lines = [
        f"Title: {spec.title}",
        f"Concept type: {spec.concept_type}",
        "Animation sequence:",
        *[f"- {step}" for step in spec.sequence],
    ]
    if spec.objects:
        lines.append("Objects:")
        for obj in spec.objects:
            lines.append(f"- {obj.kind} {obj.name}: {obj.properties}")
    if spec.annotations:
        lines.append("Labels / equations:")
        for annotation in spec.annotations:
            lines.append(f"- {annotation}")
    lines.append("Original prompt:")
    lines.append(spec.prompt)
    return "\n".join(lines)


def plan_scene(prompt: str) -> SceneSpec:
    return validate_scene_spec(infer_scene_spec(prompt))
