class BaseAppException(Exception):
    """Базовое исключение приложения"""
    pass


class ValidationError(BaseAppException):
    """Ошибка валидации данных"""
    pass


class BusinessError(BaseAppException):
    """Ошибка бизнес-логики"""
    pass


class DatabaseError(BaseAppException):
    """Ошибка базы данных"""
    pass


class RepositoryError(BaseAppException):
    """Ошибка репозитория"""
    pass


class ServiceError(BaseAppException):
    """Ошибка сервиса"""
    pass


class NotFoundError(BaseAppException):
    """"Ошибка если редмет или инвентарь не найден"""
    pass


class NotAdminError(BaseAppException):
    """ошибка если пользователь не администратор"""


class InventoryAlreadyExistsError(BaseAppException):
    """Ошибка если инвентарь для пользователя уже существует"""
    pass


class ItemAlreadyExistsError(BaseAppException):
    """Ошибка если предмет уже существует"""
    pass
