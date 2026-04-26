"""Few-shot Manim examples used to improve code generation quality."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Example:
    prompt: str
    code: str


EXAMPLES: list[Example] = [
    Example(
        prompt="Graph the sine function on a number plane with a label.",
        code="""from manim import *

class GeneratedScene(Scene):
    def construct(self):
        plane = NumberPlane(x_range=[-4, 4, 1], y_range=[-2, 2, 1])
        graph = plane.plot(lambda x: np.sin(x), x_range=[-PI, PI], color=BLUE)
        label = MathTex("y=\\sin(x)").to_edge(UP)
        self.play(Create(plane))
        self.play(Create(graph), Write(label))
        self.wait(1)
""",
    ),
    Example(
        prompt="Animate a parabola appearing on axes with the equation y = x^2 / 4.",
        code="""from manim import *

class GeneratedScene(Scene):
    def construct(self):
        plane = NumberPlane(x_range=[-4, 4, 1], y_range=[0, 5, 1])
        graph = plane.plot(lambda x: x**2 / 4, x_range=[-4, 4], color=GREEN)
        equation = MathTex("y=\\frac{x^2}{4}").next_to(plane, UP)
        self.play(Create(plane))
        self.play(Create(graph), FadeIn(equation, shift=UP))
        self.wait(1)
""",
    ),
    Example(
        prompt="Show binary search tree insertion for values 8, 4, and 10.",
        code="""from manim import *

class GeneratedScene(Scene):
    def construct(self):
        root = Circle(radius=0.35).set_stroke(BLUE, 2)
        left = Circle(radius=0.35).set_stroke(BLUE, 2).shift(LEFT * 2 + DOWN * 1.5)
        right = Circle(radius=0.35).set_stroke(BLUE, 2).shift(RIGHT * 2 + DOWN * 1.5)
        r_text = Text("8", font_size=28).move_to(root)
        l_text = Text("4", font_size=28).move_to(left)
        rr_text = Text("10", font_size=24).move_to(right)
        e1 = Line(root.get_bottom(), left.get_top())
        e2 = Line(root.get_bottom(), right.get_top())
        self.play(Create(root), Write(r_text))
        self.play(Create(left), Create(e1), Write(l_text))
        self.play(Create(right), Create(e2), Write(rr_text))
        self.wait(1)
""",
    ),
    Example(
        prompt="Visualize bubble sort on the list 5, 1, 4, 2.",
        code="""from manim import *

class GeneratedScene(Scene):
    def construct(self):
        values = [5, 1, 4, 2]
        bars = VGroup(*[
            Rectangle(width=0.7, height=0.5 + value * 0.35, fill_opacity=0.7, color=BLUE)
            for value in values
        ]).arrange(RIGHT, buff=0.3).align_to(DOWN * 2, DOWN)
        labels = VGroup(*[
            Text(str(value), font_size=24).next_to(bar, DOWN, buff=0.15)
            for value, bar in zip(values, bars)
        ])
        self.play(LaggedStart(*[GrowFromEdge(bar, DOWN) for bar in bars], lag_ratio=0.15), FadeIn(labels))
        self.play(bars[0].animate.set_color(YELLOW), bars[1].animate.set_color(YELLOW))
        self.play(Swap(bars[0], bars[1]), Swap(labels[0], labels[1]))
        self.play(*[mob.animate.set_color(BLUE) for mob in (bars[0], bars[1])])
        self.wait(1)
""",
    ),
    Example(
        prompt="Show selection sort picking the minimum element from 7, 3, 5, 1.",
        code="""from manim import *

class GeneratedScene(Scene):
    def construct(self):
        nums = ["7", "3", "5", "1"]
        boxes = VGroup(*[Square(0.9) for _ in nums]).arrange(RIGHT, buff=0.2)
        texts = VGroup(*[Text(n, font_size=30).move_to(box) for n, box in zip(nums, boxes)])
        cursor = SurroundingRectangle(boxes[-1], color=YELLOW, buff=0.08)
        title = Text("Selection Sort", font_size=34).to_edge(UP)
        self.play(Write(title), LaggedStart(*[Create(box) for box in boxes], lag_ratio=0.1), FadeIn(texts))
        self.play(Create(cursor))
        self.play(boxes[-1].animate.set_fill(GREEN, opacity=0.35))
        self.play(Swap(boxes[0], boxes[-1]), Swap(texts[0], texts[-1]))
        self.wait(1)
""",
    ),
    Example(
        prompt="Show matrix multiplication for a 2x2 matrix times a 2x1 vector.",
        code="""from manim import *

class GeneratedScene(Scene):
    def construct(self):
        left = Matrix([[1, 2], [3, 4]])
        right = Matrix([[2], [1]])
        equals = MathTex("=")
        result = Matrix([[4], [10]])
        row_highlight = SurroundingRectangle(left.get_rows()[0], color=YELLOW, buff=0.05)
        col_highlight = SurroundingRectangle(right.get_columns()[0], color=GREEN, buff=0.05)
        group = VGroup(left, right, equals, result).arrange(RIGHT, buff=0.45)
        self.play(Write(group))
        self.play(Create(row_highlight), Create(col_highlight))
        self.play(Indicate(result.get_entries()[0], color=BLUE))
        self.wait(1)
""",
    ),
    Example(
        prompt="Animate gradient descent moving downhill on a loss curve.",
        code="""from manim import *

class GeneratedScene(Scene):
    def construct(self):
        axes = Axes(x_range=[-3, 3, 1], y_range=[0, 5, 1], x_length=6, y_length=3.5)
        curve = axes.plot(lambda x: 0.45 * (x - 1.2) ** 2 + 0.6, x_range=[-2.5, 2.5], color=BLUE)
        dot = Dot(axes.c2p(-1.6, 3.1), color=YELLOW)
        trail = TracedPath(dot.get_center, stroke_color=YELLOW)
        label = Text("Gradient descent", font_size=32).to_edge(UP)
        self.play(Create(axes), Create(curve), FadeIn(dot), Write(label))
        self.add(trail)
        self.play(dot.animate.move_to(axes.c2p(-0.3, 1.4)), run_time=1.2)
        self.play(dot.animate.move_to(axes.c2p(0.7, 0.72)), run_time=1.2)
        self.wait(1)
""",
    ),
    Example(
        prompt="Create a Venn diagram showing sets A and B with an overlapping intersection.",
        code="""from manim import *

class GeneratedScene(Scene):
    def construct(self):
        left = Circle(radius=1.3, color=BLUE, fill_opacity=0.35).shift(LEFT * 0.8)
        right = Circle(radius=1.3, color=GREEN, fill_opacity=0.35).shift(RIGHT * 0.8)
        label_a = Text("A", font_size=32).move_to(left.get_center() + LEFT * 0.7 + UP * 1.1)
        label_b = Text("B", font_size=32).move_to(right.get_center() + RIGHT * 0.7 + UP * 1.1)
        inter = Text("A ∩ B", font_size=28).move_to(ORIGIN)
        self.play(FadeIn(left), FadeIn(right))
        self.play(Write(label_a), Write(label_b), FadeIn(inter))
        self.wait(1)
""",
    ),
    Example(
        prompt="Animate a linked list with three nodes and a pointer moving through it.",
        code="""from manim import *

class GeneratedScene(Scene):
    def construct(self):
        nodes = VGroup(*[Rectangle(width=1.6, height=0.8) for _ in range(3)]).arrange(RIGHT, buff=0.8)
        texts = VGroup(*[
            Text(label, font_size=28).move_to(node)
            for label, node in zip(["7", "3", "9"], nodes)
        ])
        arrows = VGroup(*[
            Arrow(nodes[i].get_right(), nodes[i + 1].get_left(), buff=0.12)
            for i in range(2)
        ])
        pointer = Text("head", font_size=26).next_to(nodes[0], UP)
        self.play(LaggedStart(*[Create(node) for node in nodes], lag_ratio=0.1), FadeIn(texts))
        self.play(LaggedStart(*[GrowArrow(arrow) for arrow in arrows], lag_ratio=0.15), FadeIn(pointer))
        self.play(pointer.animate.next_to(nodes[1], UP))
        self.play(pointer.animate.next_to(nodes[2], UP))
        self.wait(1)
""",
    ),
    Example(
        prompt="Show a Fourier series approximation building a square wave.",
        code="""from manim import *

class GeneratedScene(Scene):
    def construct(self):
        axes = Axes(x_range=[0, TAU, PI / 2], y_range=[-1.5, 1.5, 1], x_length=6, y_length=3.5)
        approx_1 = axes.plot(lambda x: np.sin(x), color=BLUE)
        approx_3 = axes.plot(lambda x: np.sin(x) + np.sin(3 * x) / 3, color=GREEN)
        approx_5 = axes.plot(lambda x: np.sin(x) + np.sin(3 * x) / 3 + np.sin(5 * x) / 5, color=YELLOW)
        title = Text("Fourier approximation", font_size=32).to_edge(UP)
        self.play(Create(axes), Write(title))
        self.play(Create(approx_1))
        self.play(Transform(approx_1, approx_3))
        self.play(Transform(approx_1, approx_5))
        self.wait(1)
""",
    ),
    Example(
        prompt="Visualize the Euclidean algorithm computing gcd(48, 18).",
        code="""from manim import *

class GeneratedScene(Scene):
    def construct(self):
        steps = VGroup(
            MathTex("48 = 18 \\cdot 2 + 12"),
            MathTex("18 = 12 \\cdot 1 + 6"),
            MathTex("12 = 6 \\cdot 2 + 0"),
            MathTex("\\gcd(48, 18) = 6"),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        self.play(Write(steps[0]))
        self.play(Write(steps[1]))
        self.play(Write(steps[2]))
        self.play(steps[3].animate.set_color(GREEN), Write(steps[3]))
        self.wait(1)
""",
    ),
    Example(
        prompt="Animate the sieve of Eratosthenes for numbers 2 through 20.",
        code="""from manim import *

class GeneratedScene(Scene):
    def construct(self):
        nums = VGroup(*[
            Square(0.6).add(Text(str(n), font_size=20))
            for n in range(2, 21)
        ]).arrange_in_grid(rows=4, cols=5, buff=0.15)
        title = Text("Sieve of Eratosthenes", font_size=30).to_edge(UP)
        self.play(Write(title), LaggedStart(*[FadeIn(num) for num in nums], lag_ratio=0.04))
        for index in [2, 4, 6, 8]:
            self.play(nums[index].animate.set_fill(RED, opacity=0.35), run_time=0.15)
        self.play(nums[0].animate.set_fill(GREEN, opacity=0.35), nums[1].animate.set_fill(GREEN, opacity=0.35))
        self.wait(1)
""",
    ),
    Example(
        prompt="Show a geometric proof sketch of the Pythagorean theorem.",
        code="""from manim import *

class GeneratedScene(Scene):
    def construct(self):
        tri = Polygon(LEFT * 2 + DOWN, LEFT * 2 + UP * 1.5, RIGHT + DOWN, color=WHITE)
        a_sq = Square(side_length=2.5, color=BLUE).next_to(tri, LEFT, buff=0)
        b_sq = Square(side_length=3, color=GREEN).next_to(tri, DOWN, buff=0)
        c_sq = Square(side_length=3.9, color=YELLOW).rotate(np.arctan(2.5 / 3)).next_to(tri, RIGHT, buff=0)
        formula = MathTex("a^2 + b^2 = c^2").to_edge(UP)
        self.play(Create(tri))
        self.play(FadeIn(a_sq), FadeIn(b_sq), FadeIn(c_sq))
        self.play(Write(formula))
        self.wait(1)
""",
    ),
    Example(
        prompt="Compare Big-O complexity classes with animated bars.",
        code="""from manim import *

class GeneratedScene(Scene):
    def construct(self):
        labels = VGroup(*[Text(t, font_size=24) for t in ["O(1)", "O(log n)", "O(n)", "O(n^2)"]]).arrange(DOWN, aligned_edge=LEFT, buff=0.45)
        bars = VGroup(
            Rectangle(width=1.0, height=0.3, fill_color=GREEN, fill_opacity=0.7),
            Rectangle(width=1.7, height=0.3, fill_color=BLUE, fill_opacity=0.7),
            Rectangle(width=3.0, height=0.3, fill_color=YELLOW, fill_opacity=0.7),
            Rectangle(width=4.5, height=0.3, fill_color=RED, fill_opacity=0.7),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.45)
        chart = VGroup(labels, bars).arrange(RIGHT, buff=0.6)
        title = Text("Complexity growth", font_size=32).to_edge(UP)
        self.play(Write(title), FadeIn(labels))
        self.play(LaggedStart(*[GrowFromEdge(bar, LEFT) for bar in bars], lag_ratio=0.15))
        self.wait(1)
""",
    ),
    Example(
        prompt="Draw a recursion tree for Fibonacci of 4.",
        code="""from manim import *

class GeneratedScene(Scene):
    def construct(self):
        root = Text("F(4)", font_size=28)
        left = Text("F(3)", font_size=24).shift(LEFT * 2 + DOWN * 1.5)
        right = Text("F(2)", font_size=24).shift(RIGHT * 2 + DOWN * 1.5)
        ll = Text("F(2)", font_size=20).shift(LEFT * 3 + DOWN * 3)
        lr = Text("F(1)", font_size=20).shift(LEFT + DOWN * 3)
        edges = VGroup(
            Line(root.get_bottom(), left.get_top()),
            Line(root.get_bottom(), right.get_top()),
            Line(left.get_bottom(), ll.get_top()),
            Line(left.get_bottom(), lr.get_top()),
        )
        self.play(Write(root))
        self.play(Write(left), Write(right), LaggedStart(*[Create(edge) for edge in edges[:2]], lag_ratio=0.1))
        self.play(Write(ll), Write(lr), LaggedStart(*[Create(edge) for edge in edges[2:]], lag_ratio=0.1))
        self.wait(1)
""",
    ),
    Example(
        prompt="Visualize a hash table collision where two keys land in the same bucket.",
        code="""from manim import *

class GeneratedScene(Scene):
    def construct(self):
        buckets = VGroup(*[Rectangle(width=1.8, height=0.7) for _ in range(4)]).arrange(DOWN, buff=0.12)
        labels = VGroup(*[Text(str(i), font_size=22).move_to(bucket.get_left() + RIGHT * 0.25) for i, bucket in enumerate(buckets)])
        key_a = Text("cat", font_size=24).to_edge(LEFT).shift(UP * 0.7)
        key_b = Text("act", font_size=24).to_edge(LEFT).shift(DOWN * 0.2)
        chain = VGroup(Rectangle(width=1.0, height=0.45), Rectangle(width=1.0, height=0.45)).arrange(RIGHT, buff=0.15).next_to(buckets[1], RIGHT)
        chain_text = VGroup(Text("cat", font_size=18).move_to(chain[0]), Text("act", font_size=18).move_to(chain[1]))
        self.play(LaggedStart(*[Create(bucket) for bucket in buckets], lag_ratio=0.1), FadeIn(labels))
        self.play(FadeIn(key_a), FadeIn(key_b))
        self.play(GrowArrow(Arrow(key_a.get_right(), buckets[1].get_left(), buff=0.1)))
        self.play(GrowArrow(Arrow(key_b.get_right(), buckets[1].get_left(), buff=0.1)))
        self.play(FadeIn(chain), FadeIn(chain_text))
        self.wait(1)
""",
    ),
    Example(
        prompt="Show vector addition and the resulting sum vector.",
        code="""from manim import *

class GeneratedScene(Scene):
    def construct(self):
        plane = NumberPlane(x_range=[0, 5, 1], y_range=[0, 5, 1], x_length=5, y_length=5)
        v1 = Arrow(plane.c2p(0, 0), plane.c2p(3, 1), buff=0, color=BLUE)
        v2 = Arrow(plane.c2p(3, 1), plane.c2p(4, 4), buff=0, color=GREEN)
        result = Arrow(plane.c2p(0, 0), plane.c2p(4, 4), buff=0, color=YELLOW)
        label = MathTex("\\vec{u}+\\vec{v}").to_edge(UP)
        self.play(Create(plane))
        self.play(GrowArrow(v1))
        self.play(GrowArrow(v2))
        self.play(GrowArrow(result), Write(label))
        self.wait(1)
""",
    ),
]


def get_examples() -> list[tuple[str, str]]:
    """Return the few-shot library as prompt/code tuples."""

    return [(example.prompt, example.code) for example in EXAMPLES]
