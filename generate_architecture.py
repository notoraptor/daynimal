import ast
import os
from collections import Counter, defaultdict
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

MAX_HUB_IMPORTS = 15
MAX_CALL_SEGMENTS = 4


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


def _parse_tree(file_path: Path):
    """Parse a Python file into an AST, or return None on error."""
    try:
        return ast.parse(file_path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _parse_imports_from_tree(tree):
    """Extract import paths from an already-parsed AST."""
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)
    return imports


def _extract_known_names(tree):
    """Extract imported names and top-level definitions.

    These are architecturally meaningful prefixes for method calls
    (as opposed to local variables like f, parts, result).
    """
    known = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                known.add(alias.asname or alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                known.add(alias.asname or alias.name)
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            known.add(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            known.add(node.name)
    return known


def resolve_import(imp, internal_modules):
    """Resolve an import path to an internal module name, or None."""
    if imp in internal_modules:
        return imp
    init = imp + ".__init__"
    if init in internal_modules:
        return init
    return None


def _get_dotted_name(node):
    """Reconstruct full dotted name from an AST expression (e.g. self.page.update).

    Returns None for unresolvable nodes (literals, comprehensions, etc.).
    """
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Attribute):
        value = _get_dotted_name(node.value)
        if value:
            return f"{value}.{node.attr}"
        return None
    elif isinstance(node, ast.Call):
        return _get_dotted_name(node.func)
    elif isinstance(node, ast.Subscript):
        return _get_dotted_name(node.value)
    return None


def _extract_calls(node, known_names):
    """Extract architecturally meaningful call names from an AST node.

    Keeps: bare calls (isinstance, Path), self/cls/super chains,
    calls on imported modules (os.walk, ast.parse).
    Drops: calls on local variables (f.endswith, parts.append).
    Truncates long fluent chains to MAX_CALL_SEGMENTS segments.
    """
    calls = set()
    for cnode in ast.walk(node):
        if isinstance(cnode, ast.Call):
            name = _get_dotted_name(cnode.func)
            if name:
                parts = name.split(".")
                root = parts[0]
                if len(parts) > MAX_CALL_SEGMENTS:
                    name = ".".join(parts[:MAX_CALL_SEGMENTS])
                if len(parts) == 1:
                    calls.add(name)
                elif root in ("self", "cls", "super") or root in known_names:
                    calls.add(name)
    return calls


def _get_decorators(node):
    """Extract decorator names from a function/method/class node."""
    decorators = []
    for dec in node.decorator_list:
        name = _get_dotted_name(dec)
        if name:
            decorators.append(f"@{name}")
    return decorators


def _get_bases(node):
    """Extract base class names from a ClassDef node."""
    bases = []
    for base in node.bases:
        name = _get_dotted_name(base)
        if name:
            bases.append(name)
    return bases


def extract_signatures_and_calls(tree, known_names):
    """Extract classes, functions, calls, and entry point info from a parsed AST."""
    classes = {}
    functions = []
    calls_map = {}
    found_main = False

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            methods = []
            method_calls = []
            for n in node.body:
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    decorators = _get_decorators(n)
                    args = [a.arg for a in n.args.args]
                    prefix = (
                        "async def" if isinstance(n, ast.AsyncFunctionDef) else "def"
                    )
                    sig = f"{prefix} {n.name}({', '.join(args)})"
                    doc = ast.get_docstring(n)
                    if doc:
                        sig += f"  # {doc.splitlines()[0]}"
                    methods.append({"signature": sig, "decorators": decorators})
                    calls = _extract_calls(n, known_names)
                    method_calls.append(sorted(calls))
            bases = _get_bases(node)
            class_decorators = _get_decorators(node)
            doc_cls = ast.get_docstring(node)
            classes[node.name] = {
                "bases": bases,
                "decorators": class_decorators,
                "doc": doc_cls.splitlines()[0] if doc_cls else "",
                "methods": methods,
                "calls": method_calls,
            }

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            decorators = _get_decorators(node)
            args = [a.arg for a in node.args.args]
            prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
            sig = f"{prefix} {node.name}({', '.join(args)})"
            doc = ast.get_docstring(node)
            if doc:
                sig += f"  # {doc.splitlines()[0]}"
            functions.append({"signature": sig, "decorators": decorators})
            if node.name == "main":
                found_main = True
            calls = _extract_calls(node, known_names)
            calls_map[node.name] = sorted(calls)

    return classes, functions, calls_map, found_main


def detect_layer(path: Path):
    """Group modules by their actual parent directory."""
    parts = path.parts
    if len(parts) <= 1:
        return "root"
    return "/".join(parts[:-1])


# ---------------- Main generator ----------------
def generate():
    files = list(find_python_files())

    # Build internal module set
    internal_modules = set()
    for f in files:
        module_name = ".".join(f.relative_to(PROJECT_ROOT).with_suffix("").parts)
        internal_modules.add(module_name)

    internal_top_packages = {m.split(".")[0] for m in internal_modules}

    # Analysis
    imports_map = {}
    internal_deps = {}
    external_imports = Counter()
    layers = defaultdict(list)
    entry_points = []
    signatures_map = {}
    module_docs = {}

    for f in files:
        module_name = ".".join(f.relative_to(PROJECT_ROOT).with_suffix("").parts)

        tree = _parse_tree(f)
        if tree is None:
            continue

        # Module docstring (full text)
        doc = ast.get_docstring(tree)
        if doc:
            module_docs[module_name] = doc

        # Imports (from single parse)
        imports = _parse_imports_from_tree(tree)
        imports_map[module_name] = imports

        # Classify imports as internal or external
        internal = set()
        for imp in imports:
            top = imp.split(".")[0]
            if top in internal_top_packages:
                resolved = resolve_import(imp, internal_modules)
                if resolved and resolved != module_name:
                    internal.add(resolved)
            else:
                external_imports[top] += 1
        internal_deps[module_name] = internal

        # Signatures + calls (reuse same tree)
        known_names = _extract_known_names(tree)
        classes, functions, calls_map, found_main = extract_signatures_and_calls(
            tree, known_names
        )
        signatures_map[module_name] = {
            "classes": classes,
            "functions": functions,
            "calls": calls_map,
        }

        if f.name == "__main__.py" or found_main:
            entry_points.append(module_name)

        layers[detect_layer(f)].append(module_name)

    # Hub detection (modules with many internal dependencies)
    hubs = [m for m, deps in internal_deps.items() if len(deps) > MAX_HUB_IMPORTS]

    # Cycle detection (direct A <-> B cycles)
    cycles = set()
    for m, deps in internal_deps.items():
        for dep in deps:
            if dep in internal_deps and m in internal_deps[dep]:
                pair = tuple(sorted([m, dep]))
                cycles.add(pair)

    # ------------------ Write Markdown ------------------
    with open(OUTPUT_FILE, "w", encoding="utf-8") as md:
        md.write("# Architecture Overview\n\n")

        # Structure by directory
        md.write("## 1. Project Structure\n")
        for layer in sorted(layers):
            md.write(f"\n### {layer}\n")
            for m in sorted(layers[layer]):
                doc = module_docs.get(m)
                if doc:
                    md.write(f"- `{m}` — {doc.splitlines()[0]}\n")
                else:
                    md.write(f"- `{m}`\n")

        # Entry points
        md.write("\n## 2. Entry Points\n")
        if entry_points:
            for ep in entry_points:
                md.write(f"- {ep}\n")
        else:
            md.write("- No explicit entry points detected\n")

        # Internal dependencies
        md.write("\n## 3. Internal Dependencies\n")
        for module in sorted(imports_map):
            deps = sorted(internal_deps.get(module, set()))
            if deps:
                md.write(f"\n### {module}\n")
                for d in deps:
                    md.write(f"- depends on `{d}`\n")

        # External dependencies
        md.write("\n## 4. External Dependencies\n")
        for lib, count in sorted(
            external_imports.most_common(), key=lambda c: (-c[1], c[0])
        ):
            md.write(f"- {lib} (used {count} times)\n")

        # Signatures and calls
        md.write("\n## 5. Signatures and Calls\n")
        for module in sorted(signatures_map):
            sigs = signatures_map[module]
            if not sigs["classes"] and not sigs["functions"]:
                continue
            doc = module_docs.get(module)
            if doc:
                quoted = "\n> ".join(doc.splitlines())
                md.write(f"\n### Module: {module}\n> {quoted}\n")
            else:
                md.write(f"\n### Module: {module}\n")
            # classes
            for cls_name, info in sigs["classes"].items():
                md.write("```python\n")
                for dec in info["decorators"]:
                    md.write(f"{dec}\n")
                bases_str = f"({', '.join(info['bases'])})" if info["bases"] else ""
                md.write(f"class {cls_name}{bases_str}")
                if info["doc"]:
                    md.write(f"  # {info['doc']}")
                md.write("\n")
                for method_info, method_calls in zip(info["methods"], info["calls"]):
                    for dec in method_info["decorators"]:
                        md.write(f"    {dec}\n")
                    md.write(f"    {method_info['signature']}\n")
                    if method_calls:
                        md.write(f"    # calls: {', '.join(method_calls)}\n")
                md.write("```\n")
            # functions
            for func_info in sigs["functions"]:
                md.write("```python\n")
                for dec in func_info["decorators"]:
                    md.write(f"{dec}\n")
                md.write(f"{func_info['signature']}\n```\n")
                func_name = func_info["signature"].split("(")[0].split()[-1]
                calls = sigs["calls"].get(func_name, [])
                if calls:
                    md.write(f"- calls: `{'`, `'.join(calls)}`\n")

        # High-coupling modules
        md.write("\n## 6. High-Coupling Modules (Risk Zones)\n")
        if hubs:
            for h in hubs:
                md.write(f"- {h} ({len(internal_deps[h])} internal dependencies)\n")
        else:
            md.write("- No obvious high-coupling modules detected\n")

        # Cycles
        md.write("\n## 7. Dependency Cycles Detected\n")
        if cycles:
            for a, b in sorted(cycles):
                md.write(f"- {a} <-> {b}\n")
        else:
            md.write("- No obvious cycles detected\n")

    print(f"[OK] {OUTPUT_FILE} generated.")


if __name__ == "__main__":
    generate()
