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