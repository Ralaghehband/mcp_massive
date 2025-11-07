from mcp_massive.options_utils import (
    parse_occ_strike,
    build_occ_option_ticker,
    build_occ_option_list,
    generate_strike_ladder,
)


def test_parse_occ_strike() -> None:
    assert parse_occ_strike("O:RZLV251107C00009500") == 9.5
    assert parse_occ_strike("O:RZLV251107P00000500") == 0.5


def test_build_occ_option_ticker_round_trip() -> None:
    ticker = build_occ_option_ticker("RZLV", "2025-11-07", "call", 6.0)
    assert ticker == "O:RZLV251107C00006000"
    assert parse_occ_strike(ticker) == 6.0


def test_build_occ_option_list() -> None:
    lst = build_occ_option_list("RZLV", "2025-11-07", "call", [0.5, 1.0])
    assert lst == ["O:RZLV251107C00000500", "O:RZLV251107C00001000"]


def test_generate_strike_ladder_defaults() -> None:
    strikes = generate_strike_ladder(None, None, None)
    assert strikes[0] == 0.5
    assert strikes[-1] == 10.0
    assert len(strikes) == ((10 - 0.5) / 0.5) + 1


def test_generate_strike_ladder_with_bounds() -> None:
    strikes = generate_strike_ladder(None, 2.0, 3.0)
    assert strikes == [2.0, 2.5, 3.0]


def test_generate_strike_ladder_single() -> None:
    assert generate_strike_ladder(6.5, None, None) == [6.5]
