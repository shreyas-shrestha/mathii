from __future__ import annotations

from services.generator import render_scene_spec
from services.planner import plan_scene, scene_spec_to_prompt


def test_vector_addition_scene_spec_uses_semantic_sum() -> None:
    spec = plan_scene("Show vector addition for vectors (2, 1) and (1, 3).")

    assert spec.concept_type == "vector_addition"
    assert spec.render_strategy == "template"
    vector_sum = next(obj for obj in spec.objects if obj.name == "sum")
    assert vector_sum.properties["end"] == [3.0, 4.0]


def test_euclidean_algorithm_scene_spec_computes_correct_gcd() -> None:
    spec = plan_scene("Visualize the Euclidean algorithm for gcd(48, 18).")

    assert spec.concept_type == "euclidean_algorithm"
    assert spec.annotations[-1] == r"\gcd(48, 18) = 6"


def test_render_scene_spec_builds_vector_code_with_expected_endpoint() -> None:
    spec = plan_scene("Show vector addition for vectors (2, 1) and (1, 3).")
    code = render_scene_spec(spec)

    assert code is not None
    assert "plane.c2p(3.0, 4.0)" in code
    assert "class GeneratedScene(Scene):" in code


def test_matrix_multiplication_scene_spec_computes_result_entries() -> None:
    spec = plan_scene("Show matrix multiplication for [[1, 2], [3, 4]] times [[2], [1]].")

    assert spec.concept_type == "matrix_multiplication"
    result = next(obj for obj in spec.objects if obj.name == "result")
    assert result.properties["values"] == [[4], [10]]


def test_gradient_descent_scene_spec_has_descending_loss_values() -> None:
    spec = plan_scene("Animate gradient descent moving downhill on a loss curve.")

    assert spec.concept_type == "gradient_descent"
    y_values = [point[1] for point in spec.metadata["points"]]
    assert y_values[-1] < y_values[0]


def test_bst_scene_spec_preserves_search_tree_ordering() -> None:
    spec = plan_scene("Show binary search tree insertion for values 8, 4, and 10.")

    assert spec.concept_type == "bst_insertion"
    nodes = {obj.name: obj.properties["value"] for obj in spec.objects}
    assert nodes["left"] < nodes["root"] < nodes["right"]


def test_function_plot_scene_spec_preserves_sine_equation() -> None:
    spec = plan_scene("Graph the sine function on axes with a label.")

    assert spec.concept_type == "function_plot"
    curve = next(obj for obj in spec.objects if obj.name == "curve")
    assert curve.properties["family"] == "sine"
    assert curve.properties["equation"] == r"y=\sin(x)"


def test_function_plot_scene_spec_uses_parabola_scale_from_prompt() -> None:
    spec = plan_scene("Animate a parabola with the equation y = x^2 / 5.")

    assert spec.concept_type == "function_plot"
    curve = next(obj for obj in spec.objects if obj.name == "curve")
    assert curve.properties["scale"] == 0.2
    assert curve.properties["equation"] == r"y=\frac{x^2}{5}"


def test_generic_scene_spec_falls_back_to_llm_strategy() -> None:
    spec = plan_scene("Explain why hash tables have amortized O(1) lookup with a custom visual metaphor.")

    assert spec.concept_type == "generic_explanation"
    assert spec.render_strategy == "llm"


def test_scene_spec_to_prompt_includes_semantic_objects() -> None:
    spec = plan_scene("Show vector addition for vectors (2, 1) and (1, 3).")
    prompt = scene_spec_to_prompt(spec)

    assert "Concept type: vector_addition" in prompt
    assert "vector a" in prompt
    assert "[3.0, 4.0]" in prompt
