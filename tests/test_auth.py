import pytest
import jwt
from unittest.mock import patch, AsyncMock
from fastapi import status, HTTPException
import asyncio

from app.inventory.common import get_current_user
from app.inventory.schemas import UserInfo


class TestAuthentication:
    """Тесты для аутентификации и авторизации"""

    @pytest.mark.asyncio
    async def test_valid_jwt_token(self):
        """Тест валидного JWT токена"""
        # Arrange
        valid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJyb2xlIjoidXNlciIsImV4cCI6MTc1MTQwODU5MX0.test_signature"
        
        with patch('app.inventory.common.HTTPAuthorizationCredentials') as mock_credentials:
            mock_credentials.return_value.credentials = valid_token
            
            with patch('jwt.decode') as mock_decode:
                mock_decode.return_value = {
                    'user_id': 1,
                    'role': 'user',
                    'exp': 1751408591
                }

                # Act
                result = await get_current_user(mock_credentials())

                # Assert
                assert isinstance(result, UserInfo)
                assert result.user_id == 1
                assert result.role == 'user'

    @pytest.mark.asyncio
    async def test_invalid_jwt_token(self):
        """Тест невалидного JWT токена"""
        # Arrange
        invalid_token = "invalid.token.here"
        
        with patch('app.inventory.common.HTTPAuthorizationCredentials') as mock_credentials:
            mock_credentials.return_value.credentials = invalid_token
            
            with patch('jwt.decode') as mock_decode:
                mock_decode.side_effect = jwt.InvalidTokenError("Invalid token")

                # Act & Assert
                with pytest.raises(HTTPException) as exc_info:
                    await get_current_user(mock_credentials())
                
                assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
                assert exc_info.value.detail == 'Wrong token'

    @pytest.mark.asyncio
    async def test_jwt_token_missing_user_id(self):
        """Тест JWT токена без user_id"""
        # Arrange
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test_signature"
        
        with patch('app.inventory.common.HTTPAuthorizationCredentials') as mock_credentials:
            mock_credentials.return_value.credentials = token
            
            with patch('jwt.decode') as mock_decode:
                mock_decode.return_value = {
                    'role': 'user',
                    'exp': 1751408591
                }

                # Act & Assert
                with pytest.raises(HTTPException) as exc_info:
                    await get_current_user(mock_credentials())
                
                assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
                assert exc_info.value.detail == 'Token must contains user_id and role'

    @pytest.mark.asyncio
    async def test_jwt_token_missing_role(self):
        """Тест JWT токена без role"""
        # Arrange
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test_signature"
        
        with patch('app.inventory.common.HTTPAuthorizationCredentials') as mock_credentials:
            mock_credentials.return_value.credentials = token
            
            with patch('jwt.decode') as mock_decode:
                mock_decode.return_value = {
                    'user_id': 1,
                    'exp': 1751408591
                }

                # Act & Assert
                with pytest.raises(HTTPException) as exc_info:
                    await get_current_user(mock_credentials())
                
                assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
                assert exc_info.value.detail == 'Token must contains user_id and role'

    @pytest.mark.asyncio
    async def test_jwt_token_empty_user_id(self):
        """Тест JWT токена с пустым user_id"""
        # Arrange
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test_signature"
        
        with patch('app.inventory.common.HTTPAuthorizationCredentials') as mock_credentials:
            mock_credentials.return_value.credentials = token
            
            with patch('jwt.decode') as mock_decode:
                mock_decode.return_value = {
                    'user_id': None,
                    'role': 'user',
                    'exp': 1751408591
                }

                # Act & Assert
                with pytest.raises(HTTPException) as exc_info:
                    await get_current_user(mock_credentials())
                
                assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
                assert exc_info.value.detail == 'Token must contains user_id and role'

    @pytest.mark.asyncio
    async def test_jwt_token_empty_role(self):
        """Тест JWT токена с пустой role"""
        # Arrange
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test_signature"
        
        with patch('app.inventory.common.HTTPAuthorizationCredentials') as mock_credentials:
            mock_credentials.return_value.credentials = token
            
            with patch('jwt.decode') as mock_decode:
                mock_decode.return_value = {
                    'user_id': 1,
                    'role': '',
                    'exp': 1751408591
                }

                # Act & Assert
                with pytest.raises(HTTPException) as exc_info:
                    await get_current_user(mock_credentials())
                
                assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
                assert exc_info.value.detail == 'Token must contains user_id and role'

    @pytest.mark.asyncio
    async def test_admin_token(self):
        """Тест токена администратора"""
        # Arrange
        admin_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJyb2xlIjoiYWRtaW4iLCJleHAiOjE3NTE0MDg1OTF9.test_signature"
        
        with patch('app.inventory.common.HTTPAuthorizationCredentials') as mock_credentials:
            mock_credentials.return_value.credentials = admin_token
            
            with patch('jwt.decode') as mock_decode:
                mock_decode.return_value = {
                    'user_id': 1,
                    'role': 'admin',
                    'exp': 1751408591
                }

                # Act
                result = await get_current_user(mock_credentials())

                # Assert
                assert isinstance(result, UserInfo)
                assert result.user_id == 1
                assert result.role == 'admin'

    @pytest.mark.asyncio
    async def test_jwt_decode_error_handling(self):
        """Тест обработки ошибок декодирования JWT"""
        # Arrange
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test_signature"
        
        with patch('app.inventory.common.HTTPAuthorizationCredentials') as mock_credentials:
            mock_credentials.return_value.credentials = token
            
            with patch('jwt.decode') as mock_decode:
                mock_decode.side_effect = jwt.InvalidTokenError("Invalid token")

                # Act & Assert
                with pytest.raises(HTTPException) as exc_info:
                    await get_current_user(mock_credentials())
                
                assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
                assert exc_info.value.detail == 'Wrong token'

    @pytest.mark.asyncio
    async def test_jwt_token_with_user_id(self):
        """Тест JWT токена с user_id"""
        token = "token_with_user_id"
        with patch('app.inventory.common.HTTPAuthorizationCredentials') as mock_credentials:
            mock_credentials.return_value.credentials = token
            with patch('jwt.decode') as mock_decode:
                mock_decode.return_value = {
                    'user_id': 123,
                    'role': 'user',
                    'exp': 1751408591
                }
                user = await get_current_user(mock_credentials())
                assert user.user_id == 123
                assert user.role == 'user'

    @pytest.mark.asyncio
    async def test_jwt_token_with_sub(self):
        """Тест JWT токена с sub вместо user_id"""
        token = "token_with_sub"
        with patch('app.inventory.common.HTTPAuthorizationCredentials') as mock_credentials:
            mock_credentials.return_value.credentials = token
            with patch('jwt.decode') as mock_decode:
                mock_decode.return_value = {
                    'sub': 456,
                    'role': 'user',
                    'exp': 1751408591
                }
                user = await get_current_user(mock_credentials())
                assert user.user_id == 456
                assert user.role == 'user'

    @pytest.mark.asyncio
    async def test_jwt_token_missing_user_id_and_sub(self):
        """Тест JWT токена без user_id и sub"""
        token = "token_missing_user_id_and_sub"
        with patch('app.inventory.common.HTTPAuthorizationCredentials') as mock_credentials:
            mock_credentials.return_value.credentials = token
            with patch('jwt.decode') as mock_decode:
                mock_decode.return_value = {
                    'role': 'user',
                    'exp': 1751408591
                }
                with pytest.raises(HTTPException) as exc_info:
                    await get_current_user(mock_credentials())
                assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
                assert exc_info.value.detail == 'Token must contains user_id and role'


class TestAuthorization:
    """Тесты для проверки ролей и разрешений"""

    def test_admin_role_check(self, mock_admin):
        """Тест проверки роли администратора"""
        assert mock_admin.role == "admin"
        assert mock_admin.user_id == 1

    def test_user_role_check(self, mock_user):
        """Тест проверки роли пользователя"""
        assert mock_user.role == "user"
        assert mock_user.user_id == 1

    def test_role_comparison(self, mock_admin, mock_user):
        """Тест сравнения ролей"""
        assert mock_admin.role != mock_user.role
        assert mock_admin.user_id == mock_user.user_id

    def test_user_info_creation(self):
        """Тест создания объекта UserInfo"""
        user_info = UserInfo(user_id=123, role="moderator")
        assert user_info.user_id == 123
        assert user_info.role == "moderator"

    def test_user_info_validation(self,):
        """Тест валидации UserInfo"""
        # Должно работать с корректными данными
        user_info = UserInfo(user_id=1, role="user")
        assert user_info.user_id > 0
        assert len(user_info.role) > 0 