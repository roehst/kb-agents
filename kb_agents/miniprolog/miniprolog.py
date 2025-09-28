"""
Miniprolog class - A PySwip-compatible interface for the miniprolog engine.

This class provides a high-level interface that mimics PySwip's API while using
the internal miniprolog engine for Prolog operations. It maintains separate
storage for program rules (loaded via consult) and dynamically asserted facts.
"""

import json
from typing import Iterator, Dict, Any, List
from pathlib import Path

from .kb import KB
from .syntax import Rule, Predicate, Var
from .parser import parse_kb, parse_rule, parse_query
from .sld import sld_resolution
from .subst import Subst
from .unify import unify


class Miniprolog:
    """
    A PySwip-compatible Prolog interface using the miniprolog engine.
    
    This class maintains two separate knowledge bases:
    - program_rules: Rules loaded via consult() operations
    - asserted_facts: Facts dynamically added via assertz() operations
    
    This separation allows for independent serialization and management
    of the static program logic versus dynamic runtime facts.
    """
    
    def __init__(self):
        """Initialize an empty Miniprolog instance."""
        self.program_rules: List[Rule] = []
        self.asserted_facts: List[Rule] = []
    
    def _get_combined_kb(self) -> KB:
        """Get a combined knowledge base with both program rules and asserted facts."""
        return KB(self.program_rules + self.asserted_facts)
    
    def _remove_ending_periods(self, text: str) -> str:
        """Remove trailing periods from Prolog text, similar to main.py."""
        while text.endswith("."):
            text = text[:-1]
        return text
    
    def consult(self, source: str) -> None:
        """
        Load Prolog rules from a file or string into the program knowledge base.
        
        Args:
            source: Either a file path or Prolog source code string
        """
        # Check if it's a file path - be more strict about what constitutes a file
        if '/' in source or source.endswith('.pl') or source.endswith('.pro'):
            path = Path(source)
            if not path.exists():
                raise FileNotFoundError(f"Prolog file not found: {source}")
            self.consult_file(source)
        else:
            # It's Prolog source code
            rules = parse_kb(source)
            self.program_rules.extend(rules)
    
    def consult_file(self, filename: str) -> None:
        """
        Load Prolog rules from a file into the program knowledge base.
        
        Args:
            filename: Path to the Prolog file to load
        """
        path = Path(filename)
        if not path.exists():
            raise FileNotFoundError(f"Prolog file not found: {filename}")
        
        content = path.read_text(encoding='utf-8')
        rules = parse_kb(content)
        self.program_rules.extend(rules)
    
    def assertz(self, fact: str) -> None:
        """
        Assert a fact or rule into the dynamic knowledge base.
        
        Args:
            fact: Prolog fact or rule as a string (period optional)
        """
        fact = self._remove_ending_periods(fact.strip())
        rule = parse_rule(fact)
        if rule is None:
            raise ValueError(f"Invalid Prolog syntax: {fact}")
        self.asserted_facts.append(rule)
    
    def retract(self, fact: str) -> None:
        """
        Retract the first matching fact from the dynamic knowledge base.
        
        Args:
            fact: Prolog fact pattern to retract (period optional)
        """
        fact = self._remove_ending_periods(fact.strip())
        target_rule = parse_rule(fact)
        if target_rule is None:
            raise ValueError(f"Invalid Prolog syntax: {fact}")
        
        # Find and remove the first matching rule
        for i, rule in enumerate(self.asserted_facts):
            if self._rules_match(rule, target_rule):
                del self.asserted_facts[i]
                return
    
    def retractall(self, pattern: str) -> None:
        """
        Retract all matching facts from the dynamic knowledge base.
        
        Args:
            pattern: Prolog fact pattern to retract (period optional)
        """
        pattern = self._remove_ending_periods(pattern.strip())
        target_rule = parse_rule(pattern)
        if target_rule is None:
            raise ValueError(f"Invalid Prolog syntax: {pattern}")
        
        # Remove all matching rules
        self.asserted_facts = [
            rule for rule in self.asserted_facts 
            if not self._rules_match(rule, target_rule)
        ]
    
    def _rules_match(self, rule1: Rule, rule2: Rule) -> bool:
        """
        Check if two rules match for retraction purposes using unification.
        This handles wildcards and proper pattern matching.
        """
        # For retraction, we only care about the head matching
        # (facts have empty body, rules need head matching for retraction)
        try:
            result = unify(rule1.head, rule2.head, Subst({}))
            return result is not None
        except Exception:
            # Fallback to string comparison if unification fails
            return str(rule1) == str(rule2)
    
    def _predicates_match(self, pred1: Predicate, pred2: Predicate) -> bool:
        """
        Check if two predicates match, with pred2 potentially containing wildcards (_).
        """
        if pred1.name != pred2.name:
            return False
        
        if len(pred1.args) != len(pred2.args):
            return False
        
        # Check each argument
        for arg1, arg2 in zip(pred1.args, pred2.args):
            # If arg2 is a variable named '_', it's a wildcard that matches anything
            if hasattr(arg2, 'name') and arg2.name == '_':
                continue
            # Otherwise, they must be equal
            if str(arg1) != str(arg2):
                return False
        
        return True
    
    def query(self, query: str) -> Iterator[Dict[str, Any]]:
        """
        Query the combined knowledge base and return an iterator of variable bindings.
        
        Args:
            query: Prolog query as a string (period optional)
            
        Yields:
            Dictionary of variable bindings for each solution
        """
        query = self._remove_ending_periods(query.strip())
        query_predicate = parse_query(query)
        if query_predicate is None:
            raise ValueError(f"Invalid query syntax: {query}")
        
        # Create combined knowledge base
        kb = self._get_combined_kb()
        
        # Use SLD resolution to find solutions
        query_goals = [query_predicate]
        results = sld_resolution(kb, query_goals, Subst({}))
        
        # Convert results to PySwip-compatible format
        for subst, _constraint_store in results:
            # Extract variable bindings from the original query
            bindings = {}
            
            # Get all variables from the original query predicate
            def collect_query_vars(predicate):
                vars_in_query = set()
                def collect_vars_from_term(term):
                    if isinstance(term, Var):
                        vars_in_query.add(term.name)
                    elif hasattr(term, 'args'):
                        for arg in term.args:
                            collect_vars_from_term(arg)
                
                collect_vars_from_term(predicate)
                return vars_in_query
            
            query_var_names = collect_query_vars(query_predicate)
            
            # For each variable in the original query, follow the substitution chain
            for var_name in query_var_names:
                # Find the variable object in the substitution
                query_var = None
                for var in subst.mapping:
                    if isinstance(var, Var) and var.name == var_name:
                        query_var = var
                        break
                
                if query_var is not None:
                    # Follow the substitution chain to get the final ground term
                    final_term = subst.apply(query_var)
                    # Convert to string representation
                    if hasattr(final_term, 'name'):
                        bindings[var_name] = final_term.name
                    else:
                        bindings[var_name] = str(final_term)
                else:
                    # Variable not found in substitution, might be unbound
                    bindings[var_name] = var_name
            
            yield bindings
    
    def save(self, filename: str, program: bool = True, facts: bool = True) -> None:
        """
        Save the knowledge base to a JSON file.
        
        Args:
            filename: Path where to save the knowledge base
            program: Whether to save program rules (from consult)
            facts: Whether to save asserted facts
        """
        data = {}
        
        if program:
            # Convert program rules to serializable format using Pydantic
            data['program_rules'] = [rule.model_dump() for rule in self.program_rules]
        
        if facts:
            # Convert asserted facts to serializable format using Pydantic
            data['asserted_facts'] = [rule.model_dump() for rule in self.asserted_facts]
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    def load(self, filename: str, program: bool = True, facts: bool = True) -> None:
        """
        Load a knowledge base from a JSON file.
        
        Args:
            filename: Path to the JSON file to load
            program: Whether to load program rules
            facts: Whether to load asserted facts
        """
        path = Path(filename)
        if not path.exists():
            raise FileNotFoundError(f"Save file not found: {filename}")
        
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if program and 'program_rules' in data:
            self.program_rules = [Rule.model_validate(rule_dict) for rule_dict in data['program_rules']]
        
        if facts and 'asserted_facts' in data:
            self.asserted_facts = [Rule.model_validate(rule_dict) for rule_dict in data['asserted_facts']]