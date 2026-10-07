from __future__ import annotations

from itertools import combinations, permutations, product
import math
from typing import Hashable, Iterable


Vertex = Hashable
Edge = tuple[Vertex, Vertex]


class Graph:
    def __init__(
        self,
        vertices: Iterable[Vertex] = (),
        edges: Iterable[Edge] = (),
    ) -> None:
        self._adjacency: dict[Vertex, set[Vertex]] = {}
        for vertex in vertices:
            self.add_vertex(vertex)
        for first, second in edges:
            self.add_edge(first, second)

    def add_vertex(self, vertex: Vertex) -> None:
        self._adjacency.setdefault(vertex, set())

    def add_edge(self, first: Vertex, second: Vertex) -> None:
        if first == second:
            raise ValueError("Self-loops are not supported")
        if second in self._adjacency.get(first, set()):
            raise ValueError(f"Duplicate edge: {first!r}--{second!r}")
        self.add_vertex(first)
        self.add_vertex(second)
        self._adjacency[first].add(second)
        self._adjacency[second].add(first)

    @property
    def vertices(self) -> tuple[Vertex, ...]:
        return tuple(self._adjacency)

    @property
    def edges(self) -> tuple[Edge, ...]:
        result: list[Edge] = []
        seen: set[frozenset[Vertex]] = set()
        for first, neighbors in self._adjacency.items():
            for second in neighbors:
                edge = frozenset((first, second))
                if edge not in seen:
                    result.append((first, second))
                    seen.add(edge)
        return tuple(result)

    def neighbors(self, vertex: Vertex) -> frozenset[Vertex]:
        if vertex not in self._adjacency:
            raise KeyError(f"Unknown vertex: {vertex!r}")
        return frozenset(self._adjacency[vertex])

    def degree(self, vertex: Vertex) -> int:
        return len(self.neighbors(vertex))

    def connected_components(self) -> tuple[frozenset[Vertex], ...]:
        remaining = set(self.vertices)
        components: list[frozenset[Vertex]] = []
        while remaining:
            start = remaining.pop()
            component = {start}
            stack = [start]
            while stack:
                current = stack.pop()
                for neighbor in self._adjacency[current]:
                    if neighbor in remaining:
                        remaining.remove(neighbor)
                        component.add(neighbor)
                        stack.append(neighbor)
            components.append(frozenset(component))
        return tuple(components)

    def induced_subgraph(self, vertices: Iterable[Vertex]) -> Graph:
        selected = set(vertices)
        return Graph(
            selected,
            (
                (first, second)
                for first, second in self.edges
                if first in selected and second in selected
            ),
        )


def _has_kuratowski_subdivision(
    graph: Graph,
    branch_count: int,
    target_pairs: tuple[tuple[int, int], ...],
) -> bool:
    candidates = tuple(
        vertex
        for vertex in graph.vertices
        if graph.degree(vertex) >= (4 if branch_count == 5 else 3)
    )
    if len(candidates) < branch_count:
        return False

    for branches in combinations(candidates, branch_count):
        branch_set = set(branches)
        paths_by_pair: dict[tuple[Vertex, Vertex], list[tuple[Vertex, ...]]] = {}
        for first_index, second_index in target_pairs:
            first = branches[first_index]
            second = branches[second_index]
            paths = _simple_paths_between(graph, first, second, branch_set)
            if not paths:
                break
            paths_by_pair[(first, second)] = paths
        else:
            ordered_pairs = tuple(paths_by_pair)
            if _can_choose_disjoint_paths(paths_by_pair, ordered_pairs):
                return True
    return False


def _simple_paths_between(
    graph: Graph,
    start: Vertex,
    target: Vertex,
    branch_vertices: set[Vertex],
) -> list[tuple[Vertex, ...]]:
    paths: list[tuple[Vertex, ...]] = []

    def visit(current: Vertex, path: list[Vertex], visited: set[Vertex]) -> None:
        if current == target:
            paths.append(tuple(path))
            return
        for neighbor in graph.neighbors(current):
            if neighbor in visited:
                continue
            if neighbor in branch_vertices and neighbor != target:
                continue
            visited.add(neighbor)
            path.append(neighbor)
            visit(neighbor, path, visited)
            path.pop()
            visited.remove(neighbor)

    visit(start, [start], {start})
    return sorted(paths, key=len)


def _can_choose_disjoint_paths(
    paths_by_pair: dict[tuple[Vertex, Vertex], list[tuple[Vertex, ...]]],
    ordered_pairs: tuple[tuple[Vertex, Vertex], ...],
    index: int = 0,
    used_internal_vertices: frozenset[Vertex] = frozenset(),
) -> bool:
    if index == len(ordered_pairs):
        return True
    pair = ordered_pairs[index]
    for path in paths_by_pair[pair]:
        internal_vertices = frozenset(path[1:-1])
        if used_internal_vertices.isdisjoint(internal_vertices):
            if _can_choose_disjoint_paths(
                paths_by_pair,
                ordered_pairs,
                index + 1,
                used_internal_vertices | internal_vertices,
            ):
                return True
    return False


def _find_kuratowski_subdivision(graph: Graph) -> str | None:
    k5_pairs = tuple(combinations(range(5), 2))
    k33_pairs = tuple((left, right) for left in range(3) for right in range(3, 6))
    if _has_kuratowski_subdivision(graph, 5, k5_pairs):
        return "K5 subdivision"

    for left_side in combinations(graph.vertices, 3):
        remaining = tuple(vertex for vertex in graph.vertices if vertex not in left_side)
        for right_side in combinations(remaining, 3):
            branch_vertices = left_side + right_side
            branch_set = set(branch_vertices)
            paths_by_pair: dict[tuple[Vertex, Vertex], list[tuple[Vertex, ...]]] = {}
            for left_index, right_index in k33_pairs:
                first = branch_vertices[left_index]
                second = branch_vertices[right_index]
                paths = _simple_paths_between(graph, first, second, branch_set)
                if not paths:
                    break
                paths_by_pair[(first, second)] = paths
            else:
                ordered_pairs = tuple(paths_by_pair)
                if _can_choose_disjoint_paths(paths_by_pair, ordered_pairs):
                    return "K3,3 subdivision"
    return None


def is_planar(graph: Graph, max_vertices: int = 12) -> bool:
    for component_vertices in graph.connected_components():
        component = graph.induced_subgraph(component_vertices)
        vertex_count = len(component.vertices)
        if vertex_count > max_vertices:
            raise ValueError(
                f"Planarity search supports at most {max_vertices} vertices "
                "per connected component"
            )
        if vertex_count >= 3 and len(component.edges) > 3 * vertex_count - 6:
            return False
        if _find_kuratowski_subdivision(component) is not None:
            return False
    return True


def visualize_planar_graph(
    graph: Graph,
    output_path: str = "planar_graph.png",
    show: bool = False,
) -> None:
    output_path = "task6/" + output_path
    if not is_planar(graph):
        raise ValueError("Only planar graphs can be visualized")

    try:
        import matplotlib.pyplot as plt
    except ImportError as error:
        raise RuntimeError("Install Matplotlib with: python -m pip install matplotlib") from error

    positions = _planar_layout(graph)

    figure, axes = plt.subplots(figsize=(6, 6))
    for first, second in graph.edges:
        x_values = (positions[first][0], positions[second][0])
        y_values = (positions[first][1], positions[second][1])
        axes.plot(x_values, y_values, color="steelblue", linewidth=1.5, zorder=1)
    for vertex, (x_position, y_position) in positions.items():
        axes.scatter(x_position, y_position, color="tomato", s=500, zorder=2)
        axes.text(x_position, y_position, str(vertex), ha="center", va="center", zorder=3)
    axes.set_title("Planar graph")
    axes.set_aspect("equal")
    axes.axis("off")
    figure.savefig(output_path, bbox_inches="tight")
    if show:
        plt.show()
    plt.close(figure)


def _rotation_systems(graph: Graph):
    vertices = graph.vertices
    choices = []
    for vertex in vertices:
        neighbors = tuple(graph.neighbors(vertex))
        if len(neighbors) <= 2:
            choices.append((neighbors,))
        else:
            first_neighbor = neighbors[0]
            choices.append(
                tuple((first_neighbor, *rest) for rest in permutations(neighbors[1:]))
            )
    for orders in product(*choices):
        yield dict(zip(vertices, orders))


def _faces_from_rotation(graph: Graph, rotation: dict[Vertex, tuple[Vertex, ...]]):
    visited: set[tuple[Vertex, Vertex]] = set()
    faces: list[tuple[Vertex, ...]] = []
    for first, second in graph.edges:
        for start in ((first, second), (second, first)):
            if start in visited:
                continue
            face: list[Vertex] = []
            current = start
            while current not in visited:
                visited.add(current)
                vertex, neighbor = current
                face.append(vertex)
                neighbor_order = rotation[neighbor]
                previous_index = neighbor_order.index(vertex) - 1
                current = (neighbor, neighbor_order[previous_index % len(neighbor_order)])
            faces.append(tuple(face))
    return faces


def _find_planar_embedding(graph: Graph):
    vertex_count = len(graph.vertices)
    edge_count = len(graph.edges)
    for rotation in _rotation_systems(graph):
        faces = _faces_from_rotation(graph, rotation)
        if len(faces) == edge_count - vertex_count + 2:
            return rotation, faces
    raise ValueError("Could not construct a planar embedding")


def _has_unique_vertices(face: tuple[Vertex, ...]) -> bool:
    return len(face) == len(set(face)) and len(face) >= 3


def _barycentric_layout(
    graph: Graph,
    outer_face: tuple[Vertex, ...],
) -> dict[Vertex, tuple[float, float]]:
    positions: dict[Vertex, tuple[float, float]] = {}
    outer_vertices = set(outer_face)
    for index, vertex in enumerate(outer_face):
        angle = 2 * math.pi * index / len(outer_face)
        positions[vertex] = (math.cos(angle), math.sin(angle))

    interior_vertices = tuple(vertex for vertex in graph.vertices if vertex not in outer_vertices)
    for vertex in interior_vertices:
        positions[vertex] = (0.0, 0.0)

    for _ in range(2000):
        next_positions = positions.copy()
        largest_change = 0.0
        for vertex in interior_vertices:
            neighbors = graph.neighbors(vertex)
            average_x = sum(positions[neighbor][0] for neighbor in neighbors) / len(neighbors)
            average_y = sum(positions[neighbor][1] for neighbor in neighbors) / len(neighbors)
            next_positions[vertex] = (average_x, average_y)
            largest_change = max(
                largest_change,
                abs(average_x - positions[vertex][0]),
                abs(average_y - positions[vertex][1]),
            )
        positions = next_positions
        if largest_change < 1e-8:
            break
    return positions


def _orientation(
    first: tuple[float, float],
    second: tuple[float, float],
    third: tuple[float, float],
) -> float:
    return (
        (second[0] - first[0]) * (third[1] - first[1])
        - (second[1] - first[1]) * (third[0] - first[0])
    )


def _segments_cross(
    first_start: tuple[float, float],
    first_end: tuple[float, float],
    second_start: tuple[float, float],
    second_end: tuple[float, float],
) -> bool:
    epsilon = 1e-8
    first_a = _orientation(first_start, first_end, second_start)
    first_b = _orientation(first_start, first_end, second_end)
    second_a = _orientation(second_start, second_end, first_start)
    second_b = _orientation(second_start, second_end, first_end)
    return (first_a * first_b < -epsilon) and (second_a * second_b < -epsilon)


def _has_crossing(graph: Graph, positions: dict[Vertex, tuple[float, float]]) -> bool:
    for first_edge, second_edge in combinations(graph.edges, 2):
        if set(first_edge) & set(second_edge):
            continue
        first_start, first_end = (positions[first_edge[0]], positions[first_edge[1]])
        second_start, second_end = (positions[second_edge[0]], positions[second_edge[1]])
        if _segments_cross(first_start, first_end, second_start, second_end):
            return True
    return False


def _planar_layout(graph: Graph) -> dict[Vertex, tuple[float, float]]:
    positions: dict[Vertex, tuple[float, float]] = {}
    components = graph.connected_components()
    for component_index, component_vertices in enumerate(components):
        component = graph.induced_subgraph(component_vertices)
        if len(component.vertices) <= 2:
            angle_offset = component_index * math.pi / 2
            for vertex_index, vertex in enumerate(component.vertices):
                positions[vertex] = (
                    2.5 * component_index + math.cos(angle_offset + vertex_index * math.pi),
                    math.sin(angle_offset + vertex_index * math.pi),
                )
            continue

        _, faces = _find_planar_embedding(component)
        for face in faces:
            if not _has_unique_vertices(face):
                continue
            component_positions = _barycentric_layout(component, face)
            if not _has_crossing(component, component_positions):
                for vertex, (x_position, y_position) in component_positions.items():
                    positions[vertex] = (x_position + 3.0 * component_index, y_position)
                break
        else:
            raise ValueError("Could not find crossing-free coordinates")
    return positions


def main() -> None:
    planar_graph = Graph(
        vertices=(1, 2, 3, 4),
        edges=((1, 2), (2, 3), (3, 4), (4, 1), (1, 3)),
    )
    cube_graph = Graph(
        vertices=range(1, 9),
        edges=(
            (1, 2), (2, 3), (3, 4), (4, 1),
            (5, 6), (6, 7), (7, 8), (8, 5),
            (1, 5), (2, 6), (3, 7), (4, 8),
        ),
    )
    octahedral_graph = Graph(
        vertices=range(1, 7),
        edges=(
            (1, 3), (1, 4), (1, 5), (1, 6),
            (2, 3), (2, 4), (2, 5), (2, 6),
            (3, 5), (5, 4), (4, 6), (6, 3),
        ),
    )
    non_planar_graph = Graph(
        vertices=(1, 2, 3, 4, 5),
        edges=combinations((1, 2, 3, 4, 5), 2),
    )

    print(f"Planar example: {is_planar(planar_graph)}")
    visualize_planar_graph(planar_graph)
    print("Saved planar graph visualization to planar_graph.png")
    print(f"Cube graph: {is_planar(cube_graph)}")
    visualize_planar_graph(cube_graph, "cube_graph.png")
    print("Saved cube graph visualization to cube_graph.png")
    print(f"Octahedral graph: {is_planar(octahedral_graph)}")
    visualize_planar_graph(octahedral_graph, "octahedral_graph.png")
    print("Saved octahedral graph visualization to octahedral_graph.png")
    print(f"K5 example: {is_planar(non_planar_graph)}")


if __name__ == "__main__":
    main()