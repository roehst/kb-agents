from z3 import *
import coverage

# Algorithm
# - Load a coverage file
# - Map each test to the lines it covers
# - Create a boolean variable for each test
# - Create a boolean variable for each line
# - For each line, create a clause that is the OR of all tests that cover that line
# - Solve the SAT problem to find tests that can be discarded without losing coverage
# - No need to pass `test_functions`, consider all tests in the coverage file

from coverage import Coverage
import z3

cov = Coverage(data_file=".coverage")
cov.load()
data = cov.get_data()

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
    print("Tests to exclude:")
    excluded_tests = [
        ctx
        for ctx, var in _mapping_ctxs.items()
        if not model.evaluate(var, model_completion=True)
    ]
    for test in excluded_tests:
        print(f"- {test}")
else:
    print("No solution found.")

# Show the lines that are covered most repeatedly
line_coverage_count = {line: len(contexts) for line, contexts in mapping.items()}
sorted_lines = sorted(line_coverage_count.items(), key=lambda x: x[1], reverse=True)
print("\nTop 10 most covered lines:")
for (filename, line), count in sorted_lines[:10]:
    print(f"{filename}:{line} covered by {count} tests")
# Show the lines that are covered least repeatedly
print("\nTop 10 least covered lines:")
for (filename, line), count in sorted_lines[-10:]:
    print(f"{filename}:{line} covered by {count} tests")
