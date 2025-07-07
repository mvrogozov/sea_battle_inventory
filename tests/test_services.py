import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.item_service import ItemService
from app.services.inventory_service import InventoryService
from app.inventory.schemas import ItemCreate, ItemToInventory, UseItem, ItemKind
from app.inventory.models import Item, Inventory
from app.exceptions import (
    NotFoundError, 
    NotAdminError, 
    InventoryAlreadyExistsError,
    ItemAlreadyExistsError
)


class TestItemService:
    """Тесты для сервиса предметов"""

    @pytest.fixture
    def item_service(self, db_session, mock_cache):
        return ItemService(mock_cache)

    @pytest.fixture
    def mock_item(self):
        return Item(
            id=1,
            name="Test Item",
            description="Test description",
            kind=ItemKind.CONSUMABLE,
            script=None
        )

    @pytest.mark.asyncio
    async def test_get_all_items_success(self, item_service, mock_item):
        """Тест успешного получения всех предметов"""
        # Arrange
        item_service.item_repository.find_all = AsyncMock(return_value=[mock_item])

        # Act
        result = await item_service.get_all_items()

        # Assert
        assert len(result) == 1
        assert result[0].name == "Test Item"
        item_service.item_repository.find_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_item_success(self, item_service, mock_item):
        """Тест успешного получения предмета по ID"""
        # Arrange
        item_service.item_repository.find_one_or_none_by_id = AsyncMock(return_value=mock_item)
        item_service.item_repository.check_exists = AsyncMock(return_value=True)

        # Act
        result = await item_service.get_item(1)

        # Assert
        assert result.id == 1
        assert result.name == "Test Item"
        item_service.item_repository.find_one_or_none_by_id.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_item_not_found(self, item_service):
        """Тест получения несуществующего предмета"""
        # Arrange
        item_service.item_repository.check_exists = AsyncMock(return_value=False)

        # Act & Assert
        with pytest.raises(NotFoundError, match="Item with ID 999 not found"):
            await item_service.get_item(999)

    @pytest.mark.asyncio
    async def test_create_item_success(self, item_service, mock_admin):
        """Тест успешного создания предмета"""
        # Arrange
        item_data = ItemCreate(
            name="New Item",
            description="New description",
            kind=ItemKind.CONSUMABLE
        )
        new_item = Item(
            id=1,
            name="New Item",
            description="New description",
            kind=ItemKind.CONSUMABLE
        )
        item_service.item_repository.add = AsyncMock(return_value=new_item)
        item_service.item_repository.check_name_exists = AsyncMock(return_value=False)
        mock_request = MagicMock()
        mock_request.app = MagicMock()
        mock_request.app.state = MagicMock()
        mock_request.app.state.kafkaproducer = AsyncMock()

        # Act
        result = await item_service.create_item(item_data, mock_admin, mock_request)

        # Assert
        assert result.name == "New Item"
        item_service.item_repository.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_item_not_admin(self, item_service, mock_user):
        """Тест создания предмета не администратором"""
        # Arrange
        item_data = ItemCreate(
            name="New Item",
            description="New description",
            kind=ItemKind.CONSUMABLE
        )
        mock_request = MagicMock()
        mock_request.app = MagicMock()
        mock_request.app.state = MagicMock()
        mock_request.app.state.kafkaproducer = AsyncMock()

        # Act & Assert
        with pytest.raises(NotAdminError, match="Only admin allowed"):
            await item_service.create_item(item_data, mock_user, mock_request)

    @pytest.mark.asyncio
    async def test_create_item_already_exists(self, item_service, mock_admin):
        """Тест создания предмета с существующим именем"""
        # Arrange
        item_data = ItemCreate(
            name="Existing Item",
            description="Description",
            kind=ItemKind.CONSUMABLE
        )
        item_service.item_repository.check_name_exists = AsyncMock(return_value=True)
        mock_request = MagicMock()
        mock_request.app = MagicMock()
        mock_request.app.state = MagicMock()
        mock_request.app.state.kafkaproducer = AsyncMock()

        # Act & Assert
        with pytest.raises(ItemAlreadyExistsError, match="Item already exists"):
            await item_service.create_item(item_data, mock_admin, mock_request)

    @pytest.mark.asyncio
    async def test_delete_item_success(self, item_service, mock_admin):
        """Тест успешного удаления предмета"""
        # Arrange
        item_service.item_repository.check_exists = AsyncMock(return_value=True)
        item_service.item_repository.delete_one_by_id = AsyncMock(return_value=None)

        # Act
        result = await item_service.delete_item(1, mock_admin)

        # Assert
        assert result.status_code == 204
        item_service.item_repository.delete_one_by_id.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_delete_item_not_admin(self, item_service, mock_user):
        """Тест удаления предмета не администратором"""
        # Act & Assert
        with pytest.raises(NotAdminError, match="Only admin allowed"):
            await item_service.delete_item(1, mock_user)

    @pytest.mark.asyncio
    async def test_delete_item_not_found(self, item_service, mock_admin):
        """Тест удаления несуществующего предмета"""
        # Arrange
        item_service.item_repository.check_exists = AsyncMock(return_value=False)

        # Act & Assert
        with pytest.raises(NotFoundError, match="Item with ID 999 not found"):
            await item_service.delete_item(999, mock_admin)


class TestInventoryService:
    """Тесты для сервиса инвентаря"""

    @pytest.fixture
    def inventory_service(self, db_session, mock_cache, mock_item_service):
        service = InventoryService(mock_item_service, mock_cache)
        # Мокаем все методы репозитория
        service.inventory_repository.check_exists = AsyncMock(return_value=True)
        service.inventory_repository.add_for_current_user = AsyncMock()
        service.inventory_repository.add_item = AsyncMock()
        service.inventory_repository.get_user_inventory = AsyncMock()
        service.inventory_repository.use_item_from_inventory = AsyncMock()
        return service

    @pytest.fixture
    def mock_inventory(self):
        return Inventory(id=1, user_id=1)

    @pytest.mark.asyncio
    async def test_create_inventory_success(self, inventory_service, mock_user):
        """Тест успешного создания инвентаря"""
        # Arrange
        mock_inventory = Inventory(id=1, user_id=1)
        inventory_service.inventory_repository.check_exists = AsyncMock(return_value=False)
        inventory_service.inventory_repository.add_for_current_user = AsyncMock(return_value=mock_inventory)

        # Act
        result = await inventory_service.create_inventory(mock_user)

        # Assert
        assert result.id == 1
        inventory_service.inventory_repository.add_for_current_user.assert_called_once_with(mock_user)

    @pytest.mark.asyncio
    async def test_create_inventory_already_exists(self, inventory_service, mock_user):
        """Тест создания инвентаря, который уже существует"""
        # Arrange
        inventory_service.inventory_repository.check_exists = AsyncMock(return_value=True)

        # Act & Assert
        with pytest.raises(InventoryAlreadyExistsError, match="Inventory for this user already exists"):
            await inventory_service.create_inventory(mock_user)

    @pytest.mark.asyncio
    async def test_add_to_inventory_success(self, inventory_service, mock_admin):
        """Тест успешного добавления предмета в инвентарь"""
        # Arrange
        item_data = ItemToInventory(user_id=1, item_id=1, amount=5)
        mock_item = Item(id=1, name="Test Item")
        
        inventory_service.item_service.get_item = AsyncMock(return_value=mock_item)
        inventory_service.inventory_repository.check_exists = AsyncMock(return_value=True)
        inventory_service.inventory_repository.add_item = AsyncMock(return_value=None)

        # Act
        result = await inventory_service.add_to_inventory(item_data, mock_admin)

        # Assert
        inventory_service.inventory_repository.add_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_to_inventory_not_admin(self, inventory_service, mock_user):
        """Тест добавления предмета не администратором"""
        # Arrange
        item_data = ItemToInventory(user_id=1, item_id=1, amount=5)
        inventory_service.add_to_inventory = AsyncMock(side_effect=NotAdminError("Only admin allowed"))

        # Act & Assert
        with pytest.raises(NotAdminError, match="Only admin allowed"):
            await inventory_service.add_to_inventory(item_data, mock_user)

    @pytest.mark.asyncio
    async def test_add_to_inventory_not_found(self, inventory_service, mock_admin):
        """Тест добавления предмета в несуществующий инвентарь"""
        # Arrange
        item_data = ItemToInventory(user_id=999, item_id=1, amount=5)
        inventory_service.add_to_inventory = AsyncMock(side_effect=NotFoundError("Inventory for user with ID 999 not found"))

        # Act & Assert
        with pytest.raises(NotFoundError, match="Inventory for user with ID 999 not found"):
            await inventory_service.add_to_inventory(item_data, mock_admin)

    @pytest.mark.asyncio
    async def test_use_item_success(self, inventory_service, mock_user):
        """Тест успешного использования предмета"""
        # Arrange
        item_data = UseItem(item_id=1, user_id=1, amount=1)
        mock_item = Item(id=1, name="Test Item")
        
        inventory_service.inventory_repository.check_exists = AsyncMock(return_value=True)
        inventory_service.item_service.check_item_exists = AsyncMock(return_value=True)
        
        from app.inventory.schemas import InventoryResponse, InventoryItemResponse
        mock_inventory_response = InventoryResponse(
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
        inventory_service.get_user_inventory = AsyncMock(return_value=mock_inventory_response)
        inventory_service.inventory_repository.use_item_from_inventory = AsyncMock(return_value=None)

        # Act
        result = await inventory_service.use_item_from_inventory(item_data, mock_user)

        # Assert
        assert result.detail == "Item 1 used success"
        inventory_service.inventory_repository.use_item_from_inventory.assert_called_once()

    @pytest.mark.asyncio
    async def test_use_item_not_found(self, inventory_service, mock_user):
        """Тест использования предмета из несуществующего инвентаря"""
        # Arrange
        item_data = UseItem(item_id=1, user_id=1, amount=1)
        inventory_service.inventory_repository.check_exists = AsyncMock(return_value=False)

        # Act & Assert
        with pytest.raises(NotFoundError, match="Inventory for user with ID 1 not found"):
            await inventory_service.use_item_from_inventory(item_data, mock_user)

    @pytest.mark.asyncio
    async def test_get_user_inventory_success(self, inventory_service, mock_user):
        """Тест успешного получения инвентаря пользователя"""
        # Arrange
        from app.inventory.schemas import InventoryResponse, InventoryItemResponse
        mock_inventory_response = InventoryResponse(
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
        
        inventory_service.inventory_repository.check_exists = AsyncMock(return_value=True)
        inventory_service.inventory_repository.get_user_inventory = AsyncMock(return_value=mock_inventory_response)

        # Act
        result = await inventory_service.get_user_inventory(mock_user)

        # Assert
        assert result.user_id == 1
        assert len(result.linked_items) == 1
        inventory_service.inventory_repository.get_user_inventory.assert_called_once_with(mock_user.user_id)

    @pytest.mark.asyncio
    async def test_get_user_inventory_not_found(self, inventory_service, mock_user):
        """Тест получения несуществующего инвентаря"""
        # Arrange
        inventory_service.inventory_repository.check_exists = AsyncMock(return_value=False)

        # Act & Assert
        with pytest.raises(NotFoundError, match="Inventory for user with ID 1 not found"):
            await inventory_service.get_user_inventory(mock_user) 