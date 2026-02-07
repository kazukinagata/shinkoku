"""Custom assertion helpers for tests."""


def assert_amount_is_integer_yen(amount: object, label: str = "amount") -> None:
    """Assert that an amount is an integer (yen, no decimal).

    Raises AssertionError with a descriptive message if the value is not int.
    """
    assert isinstance(amount, int), (
        f"{label} must be an integer (yen), got {type(amount).__name__}: {amount}"
    )
