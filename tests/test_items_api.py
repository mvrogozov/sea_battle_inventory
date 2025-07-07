import pytest
from fastapi import status
from unittest.mock import AsyncMock

from app.inventory.models import Item
from app.inventory.schemas import ItemResponse, ItemKind


@pytest.mark.api
class TestItemsAPI:
    """Тесты для API эндпоинтов предметов"""

    def test_get_items_success(self, client, mock_item_service):
        """Тест успешного получения списка предметов"""
        mock_items = [
            ItemResponse(
                id=1,
                name="Test Item",
                kind=ItemKind.CONSUMABLE,
                description="Test description",
                script="",
                shop_item_id=None
            )
        ]
        mock_item_service.get_all_items.return_value = mock_items

        response = client.get("/items/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Test Item"
        mock_item_service.get_all_items.assert_called_once()

    def test_get_item_by_id_success(self, client, mock_item_service):
        """Тест успешного получения предмета по ID"""
        # Arrange
        mock_item = ItemResponse(
            id=1,
            name="Test Item",
            kind=ItemKind.CONSUMABLE,
            description="Test description",
            script="",
            shop_item_id=None
        )
        mock_item_service.get_item.return_value = mock_item

        # Act
        response = client.get("/items/1")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "Test Item"
        mock_item_service.get_item.assert_called_once_with(1)

    def test_get_item_by_id_not_found(self, client, mock_item_service):
        """Тест получения несуществующего предмета"""
        # Arrange
        from app.exceptions import NotFoundError
        mock_item_service.get_item.side_effect = NotFoundError("Item not found")

        # Act
        response = client.get("/items/999")

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Item not found" in response.json()["detail"]

    def test_create_item_success(self, client, mock_item_service, mock_admin_jwt_token):
        """Тест успешного создания предмета администратором"""
        # Arrange
        item_data = {
            "name": "New Item",
            "description": "New description",
            "kind": "расходник",
            "script": "",
            "promotion_id": None
        }
        mock_item = ItemResponse(
            id=1,
            name="New Item",
            kind=ItemKind.CONSUMABLE,
            description="New description",
            script="",
            shop_item_id=None
        )
        mock_item_service.create_item.return_value = mock_item

        # Act
        response = client.post(
            "/items/create",
            json=item_data,
            headers={"Authorization": f"Bearer {mock_admin_jwt_token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "New Item"
        mock_item_service.create_item.assert_called_once()

    def test_create_item_unauthorized(self, client, mock_item_service):
        """Тест создания предмета без авторизации"""
        # Arrange
        item_data = {
            "name": "New Item",
            "description": "New description",
            "kind": "расходник",
            "script": "",
            "promotion_id": None
        }

        # Act
        response = client.post("/items/create", json=item_data)

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_item_not_admin(self, client, mock_item_service, mock_jwt_token):
        """Тест создания предмета обычным пользователем"""
        # Arrange
        item_data = {
            "name": "New Item",
            "description": "New description",
            "kind": "расходник",
            "script": "",
            "promotion_id": None
        }
        from app.exceptions import NotAdminError
        mock_item_service.create_item.side_effect = NotAdminError("Not admin")

        # Act
        response = client.post(
            "/items/create",
            json=item_data,
            headers={"Authorization": f"Bearer {mock_jwt_token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_item_success(self, client, mock_item_service, mock_admin_jwt_token):
        """Тест успешного удаления предмета администратором"""
        # Arrange
        from fastapi.responses import Response
        mock_response = Response(status_code=status.HTTP_204_NO_CONTENT)
        mock_item_service.delete_item.return_value = mock_response

        # Act
        response = client.delete(
            "/items/1",
            headers={"Authorization": f"Bearer {mock_admin_jwt_token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT
        mock_item_service.delete_item.assert_called_once()

    def test_delete_item_unauthorized(self, client, mock_item_service):
        """Тест удаления предмета без авторизации"""
        # Act
        response = client.delete("/items/1")

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_item_not_found(self, client, mock_item_service, mock_admin_jwt_token):
        """Тест удаления несуществующего предмета"""
        # Arrange
        from app.exceptions import NotFoundError
        mock_item_service.delete_item.side_effect = NotFoundError("Item not found")

        # Act
        response = client.delete(
            "/items/999",
            headers={"Authorization": f"Bearer {mock_admin_jwt_token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_invalid_item_id(self, client):
        """Тест с некорректным ID предмета"""
        # Act
        response = client.get("/items/0")

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_service_error(self, client, mock_item_service):
        """Тест обработки ошибки сервиса"""
        # Arrange
        from app.exceptions import ServiceError
        mock_item_service.get_all_items.side_effect = ServiceError("Service error")

        # Act
        response = client.get("/items/")

        # Assert
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE 