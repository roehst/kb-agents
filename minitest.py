#!/usr/bin/env python3
"""
Improved minitest script that identifies truly redundant test cases.
This version analyzes coverage patterns to find tests that cover identical sets of lines,
generates a minimal test set, runs it, and validates that coverage hasn't dropped.
"""

from coverage import Coverage
import z3
import subprocess
import sys
import tempfile
import os
from collections import defaultdict

def run_minimal_tests_and_validate_coverage(selected_tests, original_coverage_lines):
    """Run the minimal test set and validate that coverage hasn't dropped."""
    
    print("\n" + "="*80)
    print("RUNNING MINIMAL TEST SET AND VALIDATING COVERAGE")
    print("="*80)
    
    # Convert test context names to pytest-compatible format
    pytest_args = []
    for test in sorted(selected_tests):
        # Convert from "tests.module.Class.method" to "tests/module.py::Class::method"
        parts = test.split('.')
        if len(parts) >= 4 and parts[0] == 'tests':  # tests.module.class.method
            module_path = '/'.join(parts[:2]) + '.py'  # tests/module.py
            class_method = '::'.join(parts[2:])         # Class::method
            pytest_args.append(f"{module_path}::{class_method}")
        elif len(parts) >= 3 and parts[0] == 'tests':  # tests.module.function
            module_path = '/'.join(parts[:2]) + '.py'  # tests/module.py
            function_name = parts[2]
            pytest_args.append(f"{module_path}::{function_name}")
    
    if not pytest_args:
        print("ERROR: No valid pytest arguments could be generated.")
        return False
    
    # Filter out any invalid test formats
    valid_args = [arg for arg in pytest_args if not arg.startswith('#')]
    
    if not valid_args:
        print("ERROR: No valid test arguments after filtering.")
        return False
    
    print(f"Running {len(valid_args)} minimal tests...")
    print("Command: uv run pytest --cov=kb_agents --cov-report=term " + " ".join(f'"{arg}"' for arg in valid_args))
    print()
    
    # Run the minimal test set with coverage
    cmd = ["uv", "run", "pytest", "--cov=kb_agents", "--cov-report=term"] + valid_args
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=".")
        
        print("STDOUT:")
        print(result.stdout)
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        if result.returncode != 0:
            print(f"ERROR: Tests failed with return code {result.returncode}")
            return False
        
        print("✅ All minimal tests passed!")
        
        # Load the new coverage data to compare
        try:
            new_cov = Coverage(data_file=".coverage")
            new_cov.load()
            new_data = new_cov.get_data()
            
            # Count coverage lines
            new_coverage_lines = 0
            for filename in new_data.measured_files():
                if new_data.lines(filename):
                    new_coverage_lines += len(new_data.lines(filename))
            
            print(f"\nCoverage comparison:")
            print(f"Original coverage: {original_coverage_lines} lines")
            print(f"Minimal set coverage: {new_coverage_lines} lines")
            
            if new_coverage_lines >= original_coverage_lines:
                print("✅ Coverage maintained or improved!")
                coverage_percentage = (new_coverage_lines / original_coverage_lines) * 100 if original_coverage_lines > 0 else 100
                print(f"Coverage retention: {coverage_percentage:.1f}%")
                return True
            else:
                lost_lines = original_coverage_lines - new_coverage_lines
                coverage_percentage = (new_coverage_lines / original_coverage_lines) * 100 if original_coverage_lines > 0 else 0
                print(f"❌ Coverage dropped by {lost_lines} lines ({coverage_percentage:.1f}% retained)")
                return False
                
        except Exception as e:
            print(f"ERROR: Could not load new coverage data: {e}")
            return False
            
    except Exception as e:
        print(f"ERROR: Failed to run tests: {e}")
        return False

def analyze_test_redundancy():
    """Analyze test coverage to identify redundant test cases."""
    
    # Load coverage data
    cov = Coverage(data_file=".coverage")
    cov.load()
    data = cov.get_data()

    # Map each test to the lines it covers
    test_to_lines = defaultdict(set)
    line_to_tests = defaultdict(set)
    
    for filename in data.measured_files():
        for line in data.lines(filename):
            contexts = list(data.contexts_by_lineno(filename)[line])
            for ctx in contexts:
                test_to_lines[ctx].add((filename, line))
                line_to_tests[(filename, line)].add(ctx)
    
    print(f"Found {len(test_to_lines)} test contexts covering {len(line_to_tests)} lines")
    
    # Find tests with identical coverage patterns
    coverage_groups = defaultdict(list)
    for test, lines in test_to_lines.items():
        # Convert set to frozenset for hashing
        coverage_signature = frozenset(lines)
        coverage_groups[coverage_signature].append(test)
    
    print(f"\nFound {len(coverage_groups)} unique coverage patterns")
    
    # Report duplicate tests
    duplicate_groups = {sig: tests for sig, tests in coverage_groups.items() if len(tests) > 1}
    
    if duplicate_groups:
        print(f"\nFound {len(duplicate_groups)} groups of tests with identical coverage:")
        for i, (signature, tests) in enumerate(duplicate_groups.items(), 1):
            print(f"\nGroup {i}: {len(tests)} tests covering {len(signature)} lines identically")
            for test in tests:
                print(f"  - {test}")
            
            # Show a few example lines they cover
            example_lines = list(signature)[:5]
            if example_lines:
                print("  Example lines covered:")
                for filename, line in example_lines:
                    short_filename = filename.split('/')[-1]
                    print(f"    {short_filename}:{line}")
                if len(signature) > 5:
                    print(f"    ... and {len(signature) - 5} more lines")
    else:
        print("\nNo tests with identical coverage patterns found.")
    
    # Now run the original SAT-based optimization
    print("\n" + "="*80)
    print("Running SAT-based test minimization:")
    
    mapping = {}
    for filename in data.measured_files():
        for line in data.lines(filename):
            contexts = list(data.contexts_by_lineno(filename)[line])
            mapping.setdefault((filename, line), contexts)

    _mapping_targets = {}
    _mapping_ctxs = {}

    solver = z3.Solver()

    for (filename, line), contexts in mapping.items():
        # Create a variable for this filename and line (target)
        line_var = z3.Bool(f"line_{filename}_{line}")
        _mapping_targets[(filename, line)] = line_var
        # Create a clause that is the OR of all contexts (tests) that cover this line
        clause = []
        for ctx in contexts:
            if ctx not in _mapping_ctxs:
                ctx_var = z3.Bool(f"ctx_{ctx}")
                _mapping_ctxs[ctx] = ctx_var
            else:
                ctx_var = _mapping_ctxs[ctx]
            clause.append(ctx_var)
        if clause:
            solver.add(z3.Implies(line_var, z3.Or(clause)))

    # Sum of all line variables
    covered_lines = z3.Sum([z3.If(var, 1, 0) for var in _mapping_targets.values()])
    # Sum of all context variables
    selected_contexts = z3.Sum([z3.If(var, 1, 0) for var in _mapping_ctxs.values()])

    current_coverage = len(_mapping_targets)

    solver.add(covered_lines >= current_coverage)

    # Minimize the number of selected contexts
    opt = z3.Optimize()
    opt.add(solver.assertions())
    h = opt.minimize(selected_contexts)
    if opt.check() == z3.sat:
        model = opt.model()
        selected_tests = [
            ctx
            for ctx, var in _mapping_ctxs.items()
            if model.evaluate(var, model_completion=True)
        ]
        print(
            f"Selected {len(selected_tests)} tests out of {len(_mapping_ctxs)} to maintain coverage of {current_coverage} lines."
        )
        excluded_tests = [
            ctx
            for ctx, var in _mapping_ctxs.items()
            if not model.evaluate(var, model_completion=True)
        ]
        if excluded_tests:
            print("Tests that can be excluded without losing coverage:")
            for test in excluded_tests:
                print(f"- {test}")
        else:
            print("No tests can be excluded without losing coverage.")
        
        # Generate shell command to run minimal test set
        print("\n" + "="*80)
        print("Shell command to run minimal test set:")
        print("="*80)
        
        # Convert test context names to pytest-compatible format
        pytest_args = []
        for test in sorted(selected_tests):
            # Convert from "tests.module.Class.method" to "tests/module.py::Class::method"
            parts = test.split('.')
            if len(parts) >= 4 and parts[0] == 'tests':  # tests.module.class.method
                module_path = '/'.join(parts[:2]) + '.py'  # tests/module.py
                class_method = '::'.join(parts[2:])         # Class::method
                pytest_args.append(f"{module_path}::{class_method}")
            elif len(parts) >= 3 and parts[0] == 'tests':  # tests.module.function
                module_path = '/'.join(parts[:2]) + '.py'  # tests/module.py
                function_name = parts[2]
                pytest_args.append(f"{module_path}::{function_name}")
            else:
                # Fallback: just use the original test name as a comment
                pytest_args.append(f"# Unhandled test format: {test}")
        
        if pytest_args:
            # Filter out any unhandled formats for the actual command
            valid_args = [arg for arg in pytest_args if not arg.startswith('#')]
            
            # Format the command nicely
            command = "uv run pytest " + " ".join(f'"{arg}"' for arg in valid_args)
            print(command)
            print()
            print("Or for better readability:")
            print("uv run pytest \\")
            for i, arg in enumerate(valid_args):
                if i < len(valid_args) - 1:
                    print(f'  "{arg}" \\')
                else:
                    print(f'  "{arg}"')
            
            # Show any unhandled formats as comments
            unhandled = [arg for arg in pytest_args if arg.startswith('#')]
            if unhandled:
                print("\nNote: Some test formats couldn't be converted:")
                for comment in unhandled:
                    print(f"  {comment}")
        else:
            print("No valid pytest arguments could be generated.")
        
        # Actually run the minimal test set and validate coverage
        success = run_minimal_tests_and_validate_coverage(selected_tests, current_coverage)
        
        if success:
            print("\n🎉 SUCCESS: Minimal test set maintains full coverage!")
            print(f"Reduced from {len(_mapping_ctxs)} tests to {len(selected_tests)} tests")
            reduction_percentage = ((len(_mapping_ctxs) - len(selected_tests)) / len(_mapping_ctxs)) * 100
            print(f"Test reduction: {reduction_percentage:.1f}%")
        else:
            print("\n❌ FAILURE: Minimal test set does not maintain coverage or failed to run.")
            print("You may need to review the test selection algorithm.")
    else:
        print("No solution found.")

    # Show the lines that are covered most repeatedly
    line_coverage_count = {line: len(contexts) for line, contexts in mapping.items()}
    sorted_lines = sorted(line_coverage_count.items(), key=lambda x: x[1], reverse=True)
    print("\nTop 10 most covered lines:")
    for (filename, line), count in sorted_lines[:10]:
        short_filename = filename.split('/')[-1]
        print(f"{short_filename}:{line} covered by {count} tests")

if __name__ == "__main__":
    analyze_test_redundancy()