# We need to keep track of substitutions during unification and resolution.
# A substitution is a mapping from variables to terms.
# Since our queries contain variables, what we really want
# is to find substitutions that make the query true.


from kb_agents.miniprolog.syntax import Predicate, Rule


from dataclasses import dataclass


@dataclass
class KB:
    rules: list[Rule]

    # When we begin to resolve a goal, we need to find all rules
    # whose head predicate matches the goal predicate.
    # This is a simple name and arity match.
    def get_rules_for_predicate(self, predicate: Predicate) -> list[Rule]:
        return [
            rule
            for rule in self.rules
            if rule.head.name == predicate.name
            and len(rule.head.args) == len(predicate.args)
        ]