from app.domain.enums import InvestmentLevel, WeatherCondition


class TestWeatherCondition:
    def test_has_all_expected_conditions(self) -> None:
        expected = {"CLEAR", "CLOUDS", "DRIZZLE", "RAIN", "THUNDERSTORM", "SNOW", "EXTREME"}
        actual = {c.value for c in WeatherCondition}
        assert actual == expected

    def test_values_are_uppercase_strings(self) -> None:
        for condition in WeatherCondition:
            assert condition.value == condition.value.upper()


class TestInvestmentLevel:
    def test_has_all_expected_levels(self) -> None:
        expected = {"NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL"}
        actual = {level.value for level in InvestmentLevel}
        assert actual == expected

    def test_ordering_by_severity(self) -> None:
        ordered = [
            InvestmentLevel.NONE,
            InvestmentLevel.LOW,
            InvestmentLevel.MEDIUM,
            InvestmentLevel.HIGH,
            InvestmentLevel.CRITICAL,
        ]
        assert len(ordered) == len(InvestmentLevel)
