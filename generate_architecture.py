import os
import ast
from collections import defaultdict, Counter
from pathlib import Path

PROJECT_ROOT = Path(".")
OUTPUT_FILE = "ARCHITECTURE.md"

EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    ".idea",
    ".vscode",
    "dist",
    "build",
    "tests",
}

LAYER_HINTS = {
    "api": ["api", "routes", "controllers"],
    "services": ["service", "services"],
    "domain": ["domain", "models", "entities"],
    "infrastructure": ["infra", "infrastructure", "db", "database"],
    "utils": ["utils", "helpers", "common"],
    "tests": ["test", "tests"],
}

MAX_HUB_IMPORTS = 15


def is_excluded(path: Path) -> bool:
    return any(part in EXCLUDE_DIRS for part in path.parts)


def find_python_files():
    for root, dirs, files in os.walk(PROJECT_ROOT):
        root_path = Path(root)
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        if is_excluded(root_path):
            continue
        for f in files:
            if f.endswith(".py"):
                yield root_path / f


# AST helpers
def parse_imports(file_path: Path):
    imports = set()
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
    except Exception:
        return imports
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                imports.add(n.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split(".")[0])
    return imports


def add_parents(tree):
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            child.parent = node


def extract_signatures_and_calls(file_path: Path):
    """Retourne dict avec classes/methods/fonctions + dépendances internes"""
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
        add_parents(tree)
    except Exception:
        return {}, [], {}

    classes = {}
    functions = []
    calls_map = defaultdict(list)  # fonction/méthode -> modules appelés

    for node in ast.walk(tree):
        # classes
        if isinstance(node, ast.ClassDef):
            methods = []
            method_calls = {}
            for n in node.body:
                if isinstance(n, ast.FunctionDef):
                    args = [a.arg for a in n.args.args]
                    sig = f"def {n.name}({', '.join(args)})"
                    doc = ast.get_docstring(n)
                    if doc:
                        sig += f"  # {doc.splitlines()[0]}"
                    methods.append(sig)

                    # détecter appels internes
                    calls = set()
                    for cnode in ast.walk(n):
                        if isinstance(cnode, ast.Call):
                            if isinstance(cnode.func, ast.Name):
                                calls.add(cnode.func.id)
                            elif isinstance(cnode.func, ast.Attribute):
                                calls.add(cnode.func.attr)
                    method_calls[n.name] = sorted(calls)
            doc_cls = ast.get_docstring(node)
            classes[node.name] = {
                "doc": doc_cls.splitlines()[0] if doc_cls else "",
                "methods": methods,
                "calls": method_calls,
            }

        # fonctions globales
        elif isinstance(node, ast.FunctionDef):
            if not isinstance(getattr(node, "parent", None), ast.ClassDef):
                args = [a.arg for a in node.args.args]
                sig = f"def {node.name}({', '.join(args)})"
                doc = ast.get_docstring(node)
                if doc:
                    sig += f"  # {doc.splitlines()[0]}"
                functions.append(sig)

                calls = set()
                for cnode in ast.walk(node):
                    if isinstance(cnode, ast.Call):
                        if isinstance(cnode.func, ast.Name):
                            calls.add(cnode.func.id)
                        elif isinstance(cnode.func, ast.Attribute):
                            calls.add(cnode.func.attr)
                calls_map[node.name] = sorted(calls)

    return classes, functions, calls_map


def detect_layer(path: Path):
    lower = str(path).lower()
    for layer, hints in LAYER_HINTS.items():
        if any(h in lower for h in hints):
            return layer
    return "unclassified"


def has_main(file_path: Path):
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
    except Exception:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "main":
            return True
    return False


# ---------------- Main generator ----------------
def generate():
    files = list(find_python_files())
    imports_map = {}
    internal_modules = set()
    external_imports = Counter()
    layers = defaultdict(list)
    entry_points = []
    import_count = Counter()
    signatures_map = {}
    calls_map_global = defaultdict(list)

    # modules internes
    for f in files:
        module_name = ".".join(f.relative_to(PROJECT_ROOT).with_suffix("").parts)
        internal_modules.add(module_name)

    # analyse fichiers
    for f in files:
        module_name = ".".join(f.relative_to(PROJECT_ROOT).with_suffix("").parts)
        imports = parse_imports(f)
        imports_map[module_name] = imports

        for imp in imports:
            if imp not in internal_modules:
                external_imports[imp] += 1
            import_count[module_name] += 1

        if f.name == "__main__.py" or has_main(f):
            entry_points.append(module_name)

        layer = detect_layer(f)
        layers[layer].append(module_name)

        classes, functions, calls_map = extract_signatures_and_calls(f)
        signatures_map[module_name] = {"classes": classes, "functions": functions}
        calls_map_global[module_name] = calls_map

    # identifier les hubs / modules critiques
    hubs = [m for m, c in import_count.items() if c > MAX_HUB_IMPORTS]

    # détecter cycles simples
    cycles = []
    for m, imps in imports_map.items():
        for i in imps:
            if i in imports_map and m in imports_map[i]:
                cycles.append((m, i))

    # ------------------ Write Markdown ------------------
    with open(OUTPUT_FILE, "w", encoding="utf-8") as md:
        md.write("# Architecture Overview\n\n")

        # Structure par couche
        md.write("## 1. Project Structure\n")
        for layer, mods in layers.items():
            md.write(f"\n### {layer.capitalize()}\n")
            for m in sorted(mods):
                md.write(f"- {m}\n")

        # Entry points
        md.write("\n## 2. Entry Points\n")
        if entry_points:
            for ep in entry_points:
                md.write(f"- {ep}\n")
        else:
            md.write("- No explicit entry points detected\n")

        # Dépendances internes
        md.write("\n## 3. Internal Dependencies\n")
        for module, imps in imports_map.items():
            internal = sorted(i for i in imps if i in internal_modules)
            if internal:
                md.write(f"\n### {module}\n")
                for i in internal:
                    md.write(f"- depends on `{i}`\n")

        # Dépendances externes
        md.write("\n## 4. External Dependencies\n")
        for lib, count in external_imports.most_common():
            md.write(f"- {lib} (used {count} times)\n")

        # Signatures et appels
        md.write("\n## 5. Signatures and Calls\n")
        for module, sigs in signatures_map.items():
            md.write(f"\n### Module: {module}\n")
            # classes
            for cls, info in sigs["classes"].items():
                md.write(f"```python\nclass {cls}")
                if info["doc"]:
                    md.write(f"  # {info['doc']}")
                md.write("\n")
                for method in info["methods"]:
                    md.write(f"    {method}\n")
                # appels internes
                for method, calls in info["calls"].items():
                    if calls:
                        md.write(f"    # calls: {', '.join(calls)}\n")
                md.write("```\n")
            # fonctions
            for func in sigs["functions"]:
                md.write(f"```python\n{func}\n```\n")
                if calls_map_global[module].get(func.split("(")[0]):
                    calls = calls_map_global[module][func.split("(")[0]]
                    if calls:
                        md.write(f"- calls: {', '.join(calls)}\n")

        # Modules critiques / hubs
        md.write("\n## 6. High-Coupling Modules (Risk Zones)\n")
        if hubs:
            for h in hubs:
                md.write(f"- {h} (many imports)\n")
        else:
            md.write("- No obvious high-coupling modules detected\n")

        # Cycles
        md.write("\n## 7. Dependency Cycles Detected\n")
        if cycles:
            for a, b in cycles:
                md.write(f"- {a} <-> {b}\n")
        else:
            md.write("- No obvious cycles detected\n")

        # Observations
        md.write("\n## 8. Observations\n")
        md.write("- Architecture inferred statically from source code\n")
        md.write("- Layers are heuristic-based and may require validation\n")
        md.write(
            "- Signatures include classes, methods, functions, and short docstrings\n"
        )
        md.write("- Internal calls between functions/methods are listed\n")
        md.write(
            "- This document is intended as canonical project memory for Claude Code\n"
        )

    print(f"[OK] {OUTPUT_FILE} generated.")


if __name__ == "__main__":
    generate()
