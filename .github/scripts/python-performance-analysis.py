#!/usr/bin/env python3
"""
Python Code Performance Analyzer
Tracks code metrics and identifies optimization opportunities
"""

import json
import os
from pathlib import Path
from datetime import datetime


class PythonPerformanceAnalyzer:
    def __init__(self, src_dir="src"):
        self.src_dir = src_dir
        self.metrics_file = ".metrics.json"
        self.metrics = self.load_metrics()

    def load_metrics(self):
        """Load existing metrics or create new"""
        if os.path.exists(self.metrics_file):
            with open(self.metrics_file, 'r') as f:
                return json.load(f)
        return {"history": [], "summary": {}}

    def save_metrics(self):
        """Save metrics to file"""
        with open(self.metrics_file, 'w') as f:
            json.dump(self.metrics, f, indent=2)

    def analyze_python_files(self):
        """Analyze all Python files for complexity"""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "total_files": 0,
            "total_lines": 0,
            "avg_lines_per_file": 0,
            "large_files": [],
            "complex_functions": [],
            "imports_analysis": {"unused": [], "circular": []},
        }

        py_files = list(Path(self.src_dir).rglob("*.py"))
        metrics["total_files"] = len(py_files)

        for py_file in py_files:
            with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
                num_lines = len(lines)

                metrics["total_lines"] += num_lines

                # Flag large files
                if num_lines > 500:
                    metrics["large_files"].append({
                        "file": str(py_file),
                        "lines": num_lines
                    })

                # Count functions and estimate complexity
                func_count = content.count('\ndef ')
                class_count = content.count('\nclass ')
                if_count = content.count('\nif ')
                loop_count = content.count('\nfor ') + content.count('\nwhile ')

                # Estimate cyclomatic complexity
                complexity = 1 + if_count + loop_count
                if complexity > 15:  # High complexity threshold
                    metrics["complex_functions"].append({
                        "file": str(py_file),
                        "estimated_complexity": complexity,
                        "functions": func_count,
                        "classes": class_count,
                    })

        if metrics["total_files"] > 0:
            metrics["avg_lines_per_file"] = round(
                metrics["total_lines"] / metrics["total_files"]
            )

        return metrics

    def generate_report(self):
        """Generate and display performance report"""
        print("\n" + "="*50)
        print("Python Code Performance Analysis Report")
        print("="*50 + "\n")

        metrics = self.analyze_python_files()

        print(f"Total Python Files: {metrics['total_files']}")
        print(f"Total Lines of Code: {metrics['total_lines']}")
        print(f"Average Lines per File: {metrics['avg_lines_per_file']}")

        if metrics["large_files"]:
            print(f"\n⚠️  Large Files (>500 lines) - Refactoring Candidates:")
            for file_info in metrics["large_files"]:
                print(f"   - {file_info['file']}: {file_info['lines']} lines")

        if metrics["complex_functions"]:
            print(f"\n⚠️  High Complexity Files (>15 estimated complexity):")
            for func_info in metrics["complex_functions"]:
                print(f"   - {func_info['file']}")
                print(f"     Complexity: {func_info['estimated_complexity']}, "
                      f"Functions: {func_info['functions']}, "
                      f"Classes: {func_info['classes']}")

        print("\n" + "="*50)
        print("Optimization Recommendations")
        print("="*50)
        print("""
1. Break down large files (>500 lines) into smaller modules
2. Reduce function complexity (aim for <10 cyclomatic complexity)
3. Use caching for expensive operations (functools.lru_cache)
4. Implement lazy loading for heavy dependencies
5. Profile hot paths with cProfile before optimizing
6. Consider generator functions for large data processing
7. Use vectorized operations (NumPy) for numerical code
        """)

        # Save metrics
        self.metrics["history"].append(metrics)
        self.metrics["summary"] = metrics
        self.save_metrics()

        print(f"\n✅ Metrics saved to {self.metrics_file}\n")


if __name__ == "__main__":
    analyzer = PythonPerformanceAnalyzer()
    analyzer.generate_report()
