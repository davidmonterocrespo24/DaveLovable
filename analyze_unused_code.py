#!/usr/bin/env python3
"""
Frontend Unused Code Analyzer
Analyzes the React/TypeScript frontend to detect:
- Unused files (not imported anywhere)
- Unused exports (functions, classes, components)
- Unused imports
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict
import json


class FrontendAnalyzer:
    def __init__(self, frontend_path: str, debug: bool = False):
        self.frontend_path = Path(frontend_path).resolve()  # Resolve to absolute path
        self.src_path = self.frontend_path / "src"
        self.debug = debug

        # Storage for analysis
        self.all_files: List[Path] = []
        self.imports_map: Dict[str, Set[str]] = defaultdict(set)  # file -> imported files
        self.exports_map: Dict[str, Set[str]] = defaultdict(set)  # file -> exported items
        self.import_usage: Dict[str, Set[str]] = defaultdict(set)  # file -> used imports

    def scan_files(self) -> None:
        """Scan all TypeScript/TSX files in src directory."""
        print(f"Scanning files in {self.src_path}...")

        extensions = ('.ts', '.tsx')
        self.all_files = [
            f for f in self.src_path.rglob('*')
            if f.is_file() and f.suffix in extensions
        ]

        print(f"Found {len(self.all_files)} TypeScript/TSX files")

    def resolve_import_path(self, import_path: str, current_file: Path) -> str:
        """Resolve import path to absolute file path."""
        # Skip non-local imports (node_modules)
        if not import_path.startswith('@/') and not import_path.startswith('.'):
            return None

        # Handle @ alias (maps to src/)
        if import_path.startswith('@/'):
            import_path = import_path.replace('@/', '')
            resolved = (self.src_path / import_path)
        # Handle relative imports
        elif import_path.startswith('.'):
            current_dir = current_file.parent
            resolved = (current_dir / import_path)
        else:
            # Absolute from src (shouldn't happen often)
            resolved = (self.src_path / import_path)

        # Normalize the path
        try:
            resolved = resolved.resolve()
        except:
            if self.debug:
                print(f"    ERROR: Could not resolve path: {resolved}")
            return None

        # Try with different extensions
        for ext in ['', '.ts', '.tsx', '.js', '.jsx', '/index.ts', '/index.tsx']:
            candidate = Path(str(resolved) + ext)
            if self.debug and current_file.name == 'Index.tsx':
                print(f"    Trying: {candidate} (exists: {candidate.exists()})")
            if candidate.exists():
                # Convert to relative path from frontend root
                try:
                    rel_path = candidate.relative_to(self.frontend_path)
                    # Normalize path separators to forward slashes for consistency
                    result = str(rel_path).replace('\\', '/')
                    if self.debug and current_file.name == 'Index.tsx':
                        print(f"    SUCCESS: Resolved to {result}")
                    return result
                except ValueError:
                    # Path is outside frontend_path
                    if self.debug:
                        print(f"    ERROR: Path outside frontend_path")
                    continue

        if self.debug and current_file.name == 'Index.tsx':
            print(f"    FAILED: Could not find file for {import_path}")
        return None

    def analyze_imports(self, file_path: Path) -> Tuple[Set[str], Set[str]]:
        """
        Analyze imports in a file.
        Returns: (imported_files, imported_items)
        """
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return set(), set()

        imported_files = set()
        imported_items = set()

        # Match various import patterns
        import_patterns = [
            # import X from "path"
            r'import\s+(\w+)\s+from\s+["\']([^"\']+)["\']',
            # import { X, Y } from "path"
            r'import\s+\{([^}]+)\}\s+from\s+["\']([^"\']+)["\']',
            # import * as X from "path"
            r'import\s+\*\s+as\s+(\w+)\s+from\s+["\']([^"\']+)["\']',
            # import "path" (side effects)
            r'import\s+["\']([^"\']+)["\']',
        ]

        for pattern in import_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                if len(match.groups()) == 2:
                    items_str, path = match.groups()
                    if '{' in pattern:
                        # Named imports
                        items = [item.strip().split(' as ')[0].strip()
                                for item in items_str.split(',')]
                        imported_items.update(items)
                    else:
                        # Default import
                        imported_items.add(items_str.strip())

                    resolved = self.resolve_import_path(path, file_path)
                    if self.debug and file_path.name == 'Index.tsx':
                        print(f"  Import: {path} -> Resolved: {resolved}")
                    if resolved:
                        imported_files.add(resolved)
                elif len(match.groups()) == 1:
                    # Side effect import only
                    path = match.groups()[0]
                    resolved = self.resolve_import_path(path, file_path)
                    if resolved:
                        imported_files.add(resolved)

        if self.debug and file_path.name == 'Index.tsx':
            print(f"File: {file_path}")
            print(f"Imported files: {imported_files}")

        return imported_files, imported_items

    def analyze_exports(self, file_path: Path) -> Set[str]:
        """Analyze exports in a file."""
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return set()

        exported_items = set()

        # Export patterns
        export_patterns = [
            # export default X
            r'export\s+default\s+(\w+)',
            # export const/let/var X
            r'export\s+(?:const|let|var)\s+(\w+)',
            # export function X
            r'export\s+function\s+(\w+)',
            # export class X
            r'export\s+class\s+(\w+)',
            # export { X, Y }
            r'export\s+\{([^}]+)\}',
            # export type/interface X
            r'export\s+(?:type|interface)\s+(\w+)',
        ]

        for pattern in export_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                items_str = match.group(1)
                if '{' in pattern:
                    # Multiple exports
                    items = [item.strip().split(' as ')[0].strip()
                            for item in items_str.split(',')]
                    exported_items.update(items)
                else:
                    exported_items.add(items_str)

        return exported_items

    def analyze_all_files(self) -> None:
        """Analyze imports and exports for all files."""
        print("\nAnalyzing imports and exports...")

        for file_path in self.all_files:
            # Normalize path separators to forward slashes
            rel_path = str(file_path.relative_to(self.frontend_path)).replace('\\', '/')

            # Analyze imports
            imported_files, imported_items = self.analyze_imports(file_path)
            self.imports_map[rel_path] = imported_files
            self.import_usage[rel_path] = imported_items

            # Analyze exports
            exported_items = self.analyze_exports(file_path)
            self.exports_map[rel_path] = exported_items

    def find_unused_files(self) -> List[str]:
        """Find files that are never imported."""
        # Entry points that don't need to be imported
        entry_points = {
            'src/main.tsx',
            'src/App.tsx',
            'src/vite-env.d.ts',
        }

        # Also consider page components as entry points
        pages = [str(f.relative_to(self.frontend_path)).replace('\\', '/')
                for f in self.all_files if 'pages/' in str(f)]
        entry_points.update(pages)

        # Files that are imported
        imported_files = set()
        for imports in self.imports_map.values():
            imported_files.update(imports)

        # Find unused
        unused = []
        for file_path in self.all_files:
            rel_path = str(file_path.relative_to(self.frontend_path)).replace('\\', '/')
            if rel_path not in imported_files and rel_path not in entry_points:
                unused.append(rel_path)

        return sorted(unused)

    def find_unused_exports(self) -> Dict[str, List[str]]:
        """Find exported items that are never imported."""
        # Collect all imported items with their source files
        imported_items_by_file: Dict[str, Set[str]] = defaultdict(set)

        for file_path in self.all_files:
            rel_path = str(file_path.relative_to(self.frontend_path)).replace('\\', '/')
            try:
                content = file_path.read_text(encoding='utf-8')
            except:
                continue

            # Find imports and their sources
            import_pattern = r'import\s+(?:\{([^}]+)\}|(\w+))\s+from\s+["\']([^"\']+)["\']'
            matches = re.finditer(import_pattern, content)

            for match in matches:
                named_imports, default_import, source = match.groups()
                resolved_source = self.resolve_import_path(source, file_path)

                if resolved_source:
                    if named_imports:
                        items = [item.strip().split(' as ')[0].strip()
                                for item in named_imports.split(',')]
                        imported_items_by_file[resolved_source].update(items)
                    if default_import:
                        # Default imports match default exports or component names
                        imported_items_by_file[resolved_source].add('default')
                        imported_items_by_file[resolved_source].add(default_import)

        # Find unused exports
        unused_exports = {}
        for file_path, exports in self.exports_map.items():
            if exports:
                imported = imported_items_by_file.get(file_path, set())
                unused = exports - imported
                if unused:
                    unused_exports[file_path] = sorted(unused)

        return unused_exports

    def generate_report(self) -> str:
        """Generate a comprehensive report."""
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("FRONTEND UNUSED CODE ANALYSIS REPORT")
        report_lines.append("=" * 80)
        report_lines.append("")

        # Summary
        report_lines.append(f"Total files analyzed: {len(self.all_files)}")
        report_lines.append("")

        # Unused files
        unused_files = self.find_unused_files()
        report_lines.append(f"\n{'=' * 80}")
        report_lines.append(f"UNUSED FILES ({len(unused_files)})")
        report_lines.append(f"{'=' * 80}")
        report_lines.append("\nThese files are not imported anywhere:\n")

        if unused_files:
            for file_path in unused_files:
                report_lines.append(f"  - {file_path}")
        else:
            report_lines.append("  ✓ No unused files found!")

        # Unused exports
        unused_exports = self.find_unused_exports()
        report_lines.append(f"\n{'=' * 80}")
        report_lines.append(f"UNUSED EXPORTS ({len(unused_exports)} files with unused exports)")
        report_lines.append(f"{'=' * 80}")
        report_lines.append("\nThese exported functions/classes/components are not used:\n")

        if unused_exports:
            for file_path, exports in sorted(unused_exports.items()):
                report_lines.append(f"\n  {file_path}:")
                for export in exports:
                    report_lines.append(f"    - {export}")
        else:
            report_lines.append("  ✓ No unused exports found!")

        # UI Components analysis (special section for shadcn/ui)
        report_lines.append(f"\n{'=' * 80}")
        report_lines.append("UI COMPONENTS USAGE (shadcn/ui)")
        report_lines.append(f"{'=' * 80}")

        ui_components = [f for f in unused_files if 'components/ui/' in f]
        if ui_components:
            report_lines.append(f"\nUnused UI components ({len(ui_components)}):\n")
            for comp in ui_components:
                comp_name = Path(comp).stem
                report_lines.append(f"  - {comp_name}")
        else:
            report_lines.append("\n  ✓ All UI components are in use!")

        # Import dependency graph
        report_lines.append(f"\n{'=' * 80}")
        report_lines.append("MOST IMPORTED FILES (Top 10)")
        report_lines.append(f"{'=' * 80}")
        report_lines.append("")

        import_counts = defaultdict(int)
        for imports in self.imports_map.values():
            for imported_file in imports:
                import_counts[imported_file] += 1

        top_imports = sorted(import_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        for file_path, count in top_imports:
            report_lines.append(f"  {count:3d} imports  - {file_path}")

        report_lines.append(f"\n{'=' * 80}")
        report_lines.append("END OF REPORT")
        report_lines.append(f"{'=' * 80}")

        return '\n'.join(report_lines)

    def export_json_report(self, output_file: str) -> None:
        """Export detailed report as JSON."""
        unused_files = self.find_unused_files()
        unused_exports = self.find_unused_exports()

        report_data = {
            "summary": {
                "total_files": len(self.all_files),
                "unused_files_count": len(unused_files),
                "files_with_unused_exports": len(unused_exports)
            },
            "unused_files": unused_files,
            "unused_exports": unused_exports,
            "all_exports": {k: list(v) for k, v in self.exports_map.items()},
            "all_imports": {k: list(v) for k, v in self.imports_map.items()}
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2)

        print(f"\nJSON report exported to: {output_file}")


def main():
    """Main execution function."""
    import sys

    # Fix encoding for Windows console
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    frontend_path = "front"

    if not os.path.exists(frontend_path):
        print(f"Error: Frontend path '{frontend_path}' not found!")
        print("Please run this script from the project root directory.")
        return

    print("Starting Frontend Code Analysis...")
    print(f"Frontend path: {os.path.abspath(frontend_path)}")
    print()

    analyzer = FrontendAnalyzer(frontend_path, debug=False)

    # Run analysis
    analyzer.scan_files()
    analyzer.analyze_all_files()

    # Generate and print report
    report = analyzer.generate_report()
    print("\n" + report)

    # Export JSON report
    json_output = "frontend_analysis_report.json"
    analyzer.export_json_report(json_output)

    # Save text report
    txt_output = "frontend_analysis_report.txt"
    with open(txt_output, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"Text report saved to: {txt_output}")


if __name__ == "__main__":
    main()
