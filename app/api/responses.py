from fastapi import status

ITEM_NOT_FOUND_RESPONSE = {
    status.HTTP_404_NOT_FOUND: {
        "description": "Предмет не найден",
        "content": {
            "application/json": {
                "example": {"detail": "Item with ID {item_id} not found"}
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