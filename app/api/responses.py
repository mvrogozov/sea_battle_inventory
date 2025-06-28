from fastapi import status

NOT_FOUND_RESPONSE = {
    status.HTTP_404_NOT_FOUND: {
        "description": "Предмет или инвентарь не найден",
        "content": {
            "application/json": {
                "example": {"detail": "Предмет с ID {item_id} не найден"}
            }
        }
    }
}

ALREADY_EXISTS = {
status.HTTP_409_CONFLICT: {
        "description": "Запись уже существует",
        "content": {
            "application/json": {
                "example": {"detail": "Inventory for this user already exists"}
            }
        }
    }
}

SERVICE_ERROR= {
    status.HTTP_503_SERVICE_UNAVAILABLE: {
        "description": "Ошибка в процессе работы сервиса",
        "content": {
            "application/json": {
                "example": {"detail": "Service unavailable"}
            }
        }
    }
}

UNEXPECTED_ERROR = {
    status.HTTP_500_INTERNAL_SERVER_ERROR: {
        "description": "Неизвестная ошибка",
        "content": {
            "application/json": {
                "example": {"detail": "Internal error"}
            }
        }
    }
}
