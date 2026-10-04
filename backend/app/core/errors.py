class AppError(Exception):
    def __init__(self, status: int, code: str, message: str):
        self.status, self.code, self.message = status, code, message


def missing():
    raise AppError(404, "NOT_FOUND", "Record not found")


def invalid(message: str):
    raise AppError(422, "VALIDATION_ERROR", message)
