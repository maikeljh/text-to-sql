from typing import Dict, List, Any


class QueryEvaluator:
    """
    A class for evaluating SQL query results by comparing them to expected results,
    ignoring column names and focusing on values.
    """

    @staticmethod
    def calculate_accuracy(
        expected: List[Dict[str, Any]], actual: List[Dict[str, Any]]
    ) -> float:
        """
        Calculates accuracy by matching expected rows to actual rows using value subsets.
        Each expected row is considered correct if its set of values is a subset of
        any unmatched actual row's values. Column names are ignored.
        
        Row count must be equal.

        :param expected: List of dicts representing expected result rows.
        :param actual: List of dicts representing actual result rows.
        :return: Accuracy score (0.0 - 1.0).
        """
        if len(expected) != len(actual):
            return 0.0

        expected_sets = [set(row.values()) for row in expected]
        actual_sets = [set(row.values()) for row in actual]

        correct = 0

        for exp in expected_sets:
            for i, act in enumerate(actual_sets):
                if exp.issubset(act):
                    correct += 1
                    break

        return correct / len(expected) if expected else 1.0
