class UserExistsException(Exception):
    def __init__(self, message="User with provided details already exists"):
        self.message = message
        super().__init__(self.message)

class UserNotFoundException(Exception):
    def __init__(self, message="User not found"):
        self.message = message
        super().__init__(self.message)