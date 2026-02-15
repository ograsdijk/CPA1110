class CPA1110Error(Exception):
    """Base exception for the cpa1110 package."""


class CPAConnectionError(ConnectionError, CPA1110Error):
    """Connection or connection-state error."""


class CPAProtocolError(CPA1110Error):
    """Protocol/response validation error when communicating with the device."""
