from adaptive_calendar_agent.models import CommandType
from adaptive_calendar_agent.parser import parse_command


def test_chinese_skip_command() -> None:
    parsed = parse_command("这周先不上 gym 的课了")
    assert parsed.command_type == CommandType.SKIP_EVENT
    assert parsed.target == "gym"


def test_english_skip_command() -> None:
    parsed = parse_command("skip gym this week")
    assert parsed.command_type == CommandType.SKIP_EVENT
    assert parsed.target == "gym"


def test_replan_days() -> None:
    parsed = parse_command("重新安排未来14天")
    assert parsed.command_type == CommandType.REPLAN
    assert parsed.horizon_days == 14


def test_unknown_does_not_guess() -> None:
    parsed = parse_command("make my life better")
    assert parsed.command_type == CommandType.UNKNOWN
    assert parsed.confidence < 0.5
