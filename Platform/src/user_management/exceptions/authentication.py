class AuthenticationFailedException(Exception):
    def __init__(self, message="Authentication failed"):
        self.message = message
        super().__init__(self.message)

class PermissionDeniedException(Exception):
    def __init__(self, message: str = "Permission denied."):
        self.message = message
        super().__init__(self.message)