from fastapi import HTTPException, status


class BadRequestError(HTTPException):
    def __init__(self, detail: str = "Petición no válida") -> None:
        super().__init__(status.HTTP_400_BAD_REQUEST, detail)


class UnauthorizedError(HTTPException):
    def __init__(self, detail: str = "No autenticado") -> None:
        super().__init__(
            status.HTTP_401_UNAUTHORIZED, detail, headers={"WWW-Authenticate": "Bearer"}
        )


class ForbiddenError(HTTPException):
    def __init__(self, detail: str = "No tienes permiso para realizar esta acción") -> None:
        super().__init__(status.HTTP_403_FORBIDDEN, detail)


class NotFoundError(HTTPException):
    def __init__(self, detail: str = "No encontrado") -> None:
        super().__init__(status.HTTP_404_NOT_FOUND, detail)


class ConflictError(HTTPException):
    def __init__(self, detail: str = "Conflicto con el estado actual") -> None:
        super().__init__(status.HTTP_409_CONFLICT, detail)
