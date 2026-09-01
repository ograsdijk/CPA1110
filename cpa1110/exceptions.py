class CPA1110Error(Exception):
    """Base exception for the cpa1110 package."""


class CPAConnectionError(ConnectionError, CPA1110Error):
    """Connection or connection-state error."""


class CPAProtocolError(CPA1110Error):
    """Protocol/response validation error when communicating with the device."""


class CPATransactionMismatchError(CPAProtocolError):
    """A Modbus response carried a different transaction ID than its request."""

    def __init__(self, expected_transaction_id: int, received_transaction_id: int):
        self.expected_transaction_id = expected_transaction_id
        self.received_transaction_id = received_transaction_id
        super().__init__(
            "Modbus transaction ID mismatch: "
            f"expected {expected_transaction_id}, received {received_transaction_id}"
        )
