"""Unit tests for repository classes — verify structure and contract without DB."""

import inspect
import uuid

from app.repositories.config_repository import ConfigRepository
from app.repositories.investment_repository import InvestmentRepository
from app.repositories.region_repository import RegionRepository
from app.repositories.weather_repository import WeatherRepository


class TestConfigRepositoryContract:
    def test_has_get_all(self) -> None:
        assert inspect.iscoroutinefunction(ConfigRepository.get_all)

    def test_has_get_by_condition(self) -> None:
        assert inspect.iscoroutinefunction(ConfigRepository.get_by_condition)

    def test_has_update_by_condition(self) -> None:
        assert inspect.iscoroutinefunction(ConfigRepository.update_by_condition)


class TestInvestmentRepositoryContract:
    def test_has_save_evaluation(self) -> None:
        assert inspect.iscoroutinefunction(InvestmentRepository.save_evaluation)

    def test_has_get_history(self) -> None:
        assert inspect.iscoroutinefunction(InvestmentRepository.get_history)

    def test_get_history_accepts_region_filter(self) -> None:
        sig = inspect.signature(InvestmentRepository.get_history)
        assert "region_id" in sig.parameters


class TestWeatherRepositoryContract:
    def test_has_save_snapshot(self) -> None:
        assert inspect.iscoroutinefunction(WeatherRepository.save_snapshot)

    def test_has_get_latest_snapshot(self) -> None:
        assert inspect.iscoroutinefunction(WeatherRepository.get_latest_snapshot)

    def test_has_get_by_region(self) -> None:
        assert inspect.iscoroutinefunction(WeatherRepository.get_by_region)


class TestRegionRepositoryContract:
    def test_has_create(self) -> None:
        assert inspect.iscoroutinefunction(RegionRepository.create)

    def test_has_get_by_id(self) -> None:
        assert inspect.iscoroutinefunction(RegionRepository.get_by_id)

    def test_has_get_by_name(self) -> None:
        assert inspect.iscoroutinefunction(RegionRepository.get_by_name)

    def test_has_get_all(self) -> None:
        assert inspect.iscoroutinefunction(RegionRepository.get_all)
