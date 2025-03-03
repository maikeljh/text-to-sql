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
        Calculates execution accuracy by counting matching rows over total true rows,
        ignoring column names and considering only values. A row is considered a match if
        it is a subset or superset of an expected row.

        :param expected: The expected list of dictionaries (true result set).
        :param actual: The actual list of dictionaries (query output).
        :return: Accuracy as a float (0.0 - 1.0).
        """
        expected_set = [set(row.values()) for row in expected]
        actual_set = [set(row.values()) for row in actual]

        if not expected_set:
            return 1.0 if not actual_set else 0.0

        correct_matches = sum(
            any(actual_row.issubset(exp_row) or exp_row.issubset(actual_row) for exp_row in expected_set)
            for actual_row in actual_set
        )

        return correct_matches / len(expected_set)
