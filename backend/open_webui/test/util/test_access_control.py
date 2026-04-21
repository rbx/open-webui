from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from open_webui.utils.access_control import get_permission_value, get_permissions


def _group(permissions: dict):
    return SimpleNamespace(permissions=permissions)


GROUPS_PATH = 'open_webui.utils.access_control.Groups.get_groups_by_member_id'


class TestCombinePermissionsIntegers:
    """get_permissions merges integer-valued permissions using most-permissive semantics."""

    @pytest.mark.anyio
    @patch(GROUPS_PATH, new_callable=AsyncMock)
    async def test_single_group_integer_limit(self, mock_groups):
        mock_groups.return_value = [_group({'workspace': {'knowledge_max_count': 10}})]
        result = await get_permissions('user1', {'workspace': {'knowledge_max_count': None}})
        assert result['workspace']['knowledge_max_count'] == 10

    @pytest.mark.anyio
    @patch(GROUPS_PATH, new_callable=AsyncMock)
    async def test_most_permissive_takes_higher_limit(self, mock_groups):
        mock_groups.return_value = [
            _group({'workspace': {'knowledge_max_count': 10}}),
            _group({'workspace': {'knowledge_max_count': 25}}),
        ]
        result = await get_permissions('user1', {'workspace': {'knowledge_max_count': None}})
        assert result['workspace']['knowledge_max_count'] == 25

    @pytest.mark.anyio
    @patch(GROUPS_PATH, new_callable=AsyncMock)
    async def test_zero_means_unlimited_always_wins(self, mock_groups):
        mock_groups.return_value = [
            _group({'workspace': {'knowledge_max_count': 10}}),
            _group({'workspace': {'knowledge_max_count': 0}}),
        ]
        result = await get_permissions('user1', {'workspace': {'knowledge_max_count': None}})
        assert result['workspace']['knowledge_max_count'] == 0

    @pytest.mark.anyio
    @patch(GROUPS_PATH, new_callable=AsyncMock)
    async def test_none_group_value_is_skipped(self, mock_groups):
        mock_groups.return_value = [
            _group({'workspace': {'knowledge_max_count': None}}),
            _group({'workspace': {'knowledge_max_count': 15}}),
        ]
        result = await get_permissions('user1', {'workspace': {'knowledge_max_count': None}})
        assert result['workspace']['knowledge_max_count'] == 15

    @pytest.mark.anyio
    @patch(GROUPS_PATH, new_callable=AsyncMock)
    async def test_boolean_permissions_unaffected(self, mock_groups):
        mock_groups.return_value = [
            _group({'workspace': {'knowledge': True, 'knowledge_max_count': 10}}),
            _group({'workspace': {'knowledge': False, 'knowledge_max_count': 5}}),
        ]
        result = await get_permissions('user1', {'workspace': {'knowledge': False, 'knowledge_max_count': None}})
        assert result['workspace']['knowledge'] is True
        assert result['workspace']['knowledge_max_count'] == 10


class TestGetPermissionValue:
    """get_permission_value returns the raw resolved value for a permission key."""

    @pytest.mark.anyio
    @patch(GROUPS_PATH, new_callable=AsyncMock)
    async def test_returns_none_when_no_groups_and_no_default(self, mock_groups):
        mock_groups.return_value = []
        assert await get_permission_value('user1', 'workspace.knowledge_max_count') is None

    @pytest.mark.anyio
    @patch(GROUPS_PATH, new_callable=AsyncMock)
    async def test_falls_back_to_default_permissions(self, mock_groups):
        mock_groups.return_value = []
        result = await get_permission_value(
            'user1', 'workspace.knowledge_max_count',
            {'workspace': {'knowledge_max_count': 20}},
        )
        assert result == 20

    @pytest.mark.anyio
    @patch(GROUPS_PATH, new_callable=AsyncMock)
    async def test_group_value_overrides_default(self, mock_groups):
        mock_groups.return_value = [_group({'workspace': {'knowledge_max_count': 5}})]
        result = await get_permission_value(
            'user1', 'workspace.knowledge_max_count',
            {'workspace': {'knowledge_max_count': 20}},
        )
        assert result == 5

    @pytest.mark.anyio
    @patch(GROUPS_PATH, new_callable=AsyncMock)
    async def test_most_permissive_across_groups(self, mock_groups):
        mock_groups.return_value = [
            _group({'workspace': {'knowledge_max_count': 5}}),
            _group({'workspace': {'knowledge_max_count': 30}}),
        ]
        assert await get_permission_value('user1', 'workspace.knowledge_max_count') == 30

    @pytest.mark.anyio
    @patch(GROUPS_PATH, new_callable=AsyncMock)
    async def test_zero_unlimited_wins_over_any_limit(self, mock_groups):
        mock_groups.return_value = [
            _group({'workspace': {'knowledge_max_count': 5}}),
            _group({'workspace': {'knowledge_max_count': 0}}),
        ]
        assert await get_permission_value('user1', 'workspace.knowledge_max_count') == 0

    @pytest.mark.anyio
    @patch(GROUPS_PATH, new_callable=AsyncMock)
    async def test_missing_key_returns_none(self, mock_groups):
        mock_groups.return_value = [_group({'workspace': {'knowledge': True}})]
        assert await get_permission_value('user1', 'workspace.knowledge_max_count') is None

    @pytest.mark.anyio
    @patch(GROUPS_PATH, new_callable=AsyncMock)
    async def test_size_limit_key(self, mock_groups):
        mock_groups.return_value = [_group({'workspace': {'knowledge_max_size': 50}})]
        assert await get_permission_value('user1', 'workspace.knowledge_max_size') == 50
