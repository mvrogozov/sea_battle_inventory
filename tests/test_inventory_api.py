import pytest
from fastapi import status
from unittest.mock import AsyncMock

from app.inventory.models import Inventory, InventoryItem, Item
from app.inventory.schemas import (
    InventoryResponse, 
    ItemToInventory, 
    UseItem,
    InventoryItemResponse,
    SuccessResponse
)


@pytest.mark.api
class TestInventoryAPI:
    """Тесты для API эндпоинтов инвентаря"""

    def test_create_inventory_success(self, client, mock_inventory_service, mock_jwt_token):
        """Тест успешного создания инвентаря"""
        # Arrange
        mock_inventory_service.create_inventory.return_value = None

        # Act
        response = client.post(
            "/inventory/",
            json={"user_id": 1},
            headers={"Authorization": f"Bearer {mock_jwt_token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["detail"] == "Inventory created"
        mock_inventory_service.create_inventory.assert_called_once()

    def test_create_inventory_unauthorized(self, client, mock_inventory_service):
        """Тест создания инвентаря без авторизации"""
        # Act
        response = client.post("/inventory/", json={"user_id": 1})

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_inventory_already_exists(self, client, mock_inventory_service, mock_jwt_token):
        """Тест создания инвентаря, который уже существует"""
        # Arrange
        from app.exceptions import InventoryAlreadyExistsError
        mock_inventory_service.create_inventory.side_effect = InventoryAlreadyExistsError("Already exists")

        # Act
        response = client.post(
            "/inventory/",
            json={"user_id": 1},
            headers={"Authorization": f"Bearer {mock_jwt_token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_409_CONFLICT

    def test_add_item_to_inventory_success(self, client, mock_inventory_service, mock_admin_jwt_token):
        """Тест успешного добавления предмета в инвентарь"""
        # Arrange
        item_data = {
            "item_id": 1,
            "amount": 5
        }
        mock_inventory_service.add_to_inventory.return_value = None

        # Act
        response = client.patch(
            "/inventory/add_item",
            json=item_data,
            headers={"Authorization": f"Bearer {mock_admin_jwt_token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["detail"] == "Item added"
        mock_inventory_service.add_to_inventory.assert_called_once()

    def test_add_item_to_inventory_unauthorized(self, client, mock_inventory_service):
        """Тест добавления предмета без авторизации"""
        # Arrange
        item_data = {
            "item_id": 1,
            "amount": 5
        }

        # Act
        response = client.patch("/inventory/add_item", json=item_data)

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_add_item_to_inventory_not_admin(self, client, mock_inventory_service, mock_jwt_token):
        """Тест добавления предмета обычным пользователем"""
        # Arrange
        item_data = {
            "item_id": 1,
            "amount": 5
        }
        from app.exceptions import NotAdminError
        mock_inventory_service.add_to_inventory.side_effect = NotAdminError("Not admin")

        # Act
        response = client.patch(
            "/inventory/add_item",
            json=item_data,
            headers={"Authorization": f"Bearer {mock_jwt_token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_use_item_success(self, client, mock_inventory_service, mock_jwt_token):
        """Тест успешного использования предмета"""
        # Arrange
        item_data = {
            "item_id": 1,
            "user_id": 1,
            "amount": 1
        }
        mock_inventory_service.use_item_from_inventory.return_value = SuccessResponse(detail="Item used")

        # Act
        response = client.patch(
            "/inventory/use_item",
            json=item_data,
            headers={"Authorization": f"Bearer {mock_jwt_token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["detail"] == "Item used"
        mock_inventory_service.use_item_from_inventory.assert_called_once()

    def test_use_item_unauthorized(self, client, mock_inventory_service):
        """Тест использования предмета без авторизации"""
        # Arrange
        item_data = {
            "item_id": 1,
            "user_id": 1,
            "amount": 1
        }

        # Act
        response = client.patch("/inventory/use_item", json=item_data)

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_use_item_not_found(self, client, mock_inventory_service, mock_jwt_token):
        """Тест использования несуществующего предмета"""
        # Arrange
        item_data = {
            "item_id": 999,
            "user_id": 1,
            "amount": 1
        }
        from app.exceptions import NotFoundError
        mock_inventory_service.use_item_from_inventory.side_effect = NotFoundError("Item not found")

        # Act
        response = client.patch(
            "/inventory/use_item",
            json=item_data,
            headers={"Authorization": f"Bearer {mock_jwt_token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_user_inventory_success(self, client, mock_inventory_service, mock_jwt_token):
        """Тест успешного получения инвентаря пользователя"""
        # Arrange
        mock_inventory = InventoryResponse(
            user_id=1,
            linked_items=[
                InventoryItemResponse(
                    item_id=1,
                    name="Test Item",
                    amount=5,
                    script="",
                    promotion_id=None
                )
            ]
        )
        mock_inventory_service.get_user_inventory.return_value = mock_inventory

        # Act
        response = client.get(
            "/inventory/user_inventory",
            headers={"Authorization": f"Bearer {mock_jwt_token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["user_id"] == 1
        assert len(data["linked_items"]) == 1
        assert data["linked_items"][0]["name"] == "Test Item"
        mock_inventory_service.get_user_inventory.assert_called_once()

    def test_get_user_inventory_unauthorized(self, client, mock_inventory_service):
        """Тест получения инвентаря без авторизации"""
        # Act
        response = client.get("/inventory/user_inventory")

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_user_inventory_not_found(self, client, mock_inventory_service, mock_jwt_token):
        """Тест получения несуществующего инвентаря"""
        # Arrange
        from app.exceptions import NotFoundError
        mock_inventory_service.get_user_inventory.side_effect = NotFoundError("Inventory not found")

        # Act
        response = client.get(
            "/inventory/user_inventory",
            headers={"Authorization": f"Bearer {mock_jwt_token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_invalid_user_id(self, client, mock_inventory_service, mock_jwt_token):
        """Тест с некорректным количеством предметов (amount = 0)"""
        # Arrange
        item_data = {
            "item_id": 1,
            "amount": 0  # Должно быть больше 0
        }

        # Act
        response = client.patch(
            "/inventory/add_item",
            json=item_data,
            headers={"Authorization": f"Bearer {mock_jwt_token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY 