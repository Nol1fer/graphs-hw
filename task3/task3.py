class Node:
    def __init__(self, node_id, parent=None):
        self.id = node_id
        self.parent = parent
        self.children = []

def parse_code(code: str) -> Node:
    root = Node(0)
    current = root
    next_id = 1

    for i, ch in enumerate(code):
        if ch == '0':
            child = Node(next_id, parent=current)
            next_id += 1
            current.children.append(child)
            current = child

        elif ch == '1':
            if current.parent is None:
                raise ValueError(f"Некорректная '1' в позиции {i}: уже в корне")
            current = current.parent

        else:
            raise ValueError(f"Некорректный символ '{ch}' в позиции {i}")

    if current is not root:
        print("Warning: code does not end back at root")

    return root

def is_complete_code(code: str) -> bool:
    depth = 0

    for i, ch in enumerate(code):
        if ch == '0':
            depth += 1
        elif ch == '1':
            if depth == 0:
                raise ValueError(f"Некорректная '1' в позиции {i}: уже в корне")
            depth -= 1
        else:
            raise ValueError(f"Некорректный символ '{ch}' в позиции {i}")

    return depth == 0

def parse_to_dot(root: Node) -> str:
    lines = [
        "digraph Tree {",
    ]

    def visit(node: Node):
        for child in node.children:
            lines.append(f'    {node.id} -> {child.id};')
            visit(child)

    visit(root)
    lines.append("}")
    return "\n".join(lines) + "\n"

def write_dot(root: Node, filename: str) -> None:
    with open(filename, "w", encoding="utf-8") as f:
        f.write(parse_to_dot(root))

def main():
    code = "0101001101010100010111"
    if is_complete_code(code) == False:
        print("Проверьте последовательность двоичного кода")
        return
    root = parse_code(code)

    print(root.id, [item.id for item in root.children])

    write_dot(root, "tree.dot")

if __name__ == "__main__":
    main()
    