from typing import Dict, List, Any


class QueryEvaluator:
    """
    A class for evaluating SQL query results by comparing them to expected results.
    """

    @staticmethod
    def calculate_accuracy(
        expected: List[Dict[str, Any]], actual: List[Dict[str, Any]]
    ) -> float:
        """
        Calculates execution accuracy by counting matching rows over total true rows.

        :param expected: The expected list of dictionaries (true result set).
        :param actual: The actual list of dictionaries (query output).
        :return: Accuracy as a float (0.0 - 1.0).
        """
        expected_set = {frozenset(row.items()) for row in expected}
        actual_set = {frozenset(row.items()) for row in actual}

        if not expected_set:
            return 1.0 if not actual_set else 0.0

        correct_matches = len(expected_set.intersection(actual_set))
        return correct_matches / len(expected_set)
