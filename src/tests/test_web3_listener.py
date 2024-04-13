from unittest.mock import patch

from hexbytes import HexBytes
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.db import engine
from models.user_portfolio import PositionStatus, UserPortfolio
from web3_listener import handle_event


@pytest.fixture(scope="module")
def db_session():
    session = Session(engine)
    yield session


@pytest.fixture
def event_data():
    return {
        "removed": False,
        "logIndex": 1,
        "transactionIndex": 0,
        "transactionHash": "0xcf7fd3f78a02f233cd7bbb64aec516997aad6212cf86d0599d7db5021aa38f6c",
        "blockHash": "0x4874e743d6e778c5b4af1c0547f7bf5f8d6bcfae8541022d9b1959ce7d41da9f",
        "blockNumber": 192713205,
        "address": "0x55c4c840F9Ac2e62eFa3f12BaBa1B57A1208B6F5",
        "data": HexBytes("0x0000000000000000000000000000000000000000000000000000000001312d000000000000000000000000000000000000000000000000000000000001312d00"),
        "topics": [
            HexBytes("0x73a19dd210f1a7f902193214c0ee91dd35ee5b4d920cba8d519eca65a7b488ca"),
            HexBytes("0x00000000000000000000000020f89ba1b0fc1e83f9aef0a134095cd63f7e8cc7"),
        ],
    }


@pytest.fixture(autouse=True)
def clean_user_portfolio(db_session: Session):
    db_session.query(UserPortfolio).delete()
    db_session.commit()


@patch("web3_listener._extract_stablecoin_event")
def test_handle_event_deposit(mock_extract_event, event_data, db_session: Session):
    mock_extract_event.return_value = (
        100,
        "0x20f89ba1b0fc1e83f9aef0a134095cd63f7e8cc7",
    )  # amount, from_address
    amount = 20_000000
    shares = 20_000000
    event_data['data'] = HexBytes("0x{:064x}".format(amount) + "{:064x}".format(shares))
    handle_event("0x55c4c840F9Ac2e62eFa3f12BaBa1B57A1208B6F5", event_data, "Deposit")
    user_portfolio = db_session.query(UserPortfolio).filter(
        UserPortfolio.user_address == "0x20f89ba1b0fc1e83f9aef0a134095cd63f7e8cc7"
    ).first()
    assert user_portfolio is not None
    assert user_portfolio.total_balance == 20


# @patch("web3_listener._extract_stablecoin_event")
def test_handle_event_deposit_then_init_withdraw(event_data, db_session: Session):
    # mock_extract_event.return_value = (
    #     100,
    #     100,
    #     "0x20f89ba1b0fc1e83f9aef0a134095cd63f7e8cc7",
    # )  # amount, from_address
    amount = 200_000000
    shares = 200_000000
    event_data['data'] = HexBytes("0x{:064x}".format(amount) + "{:064x}".format(shares))
    handle_event("0x55c4c840F9Ac2e62eFa3f12BaBa1B57A1208B6F5", event_data, "Deposit")
    user_portfolio = db_session.query(UserPortfolio).filter(
        UserPortfolio.user_address == "0x20f89ba1b0fc1e83f9aef0a134095cd63f7e8cc7"
    ).first()
    assert user_portfolio is not None
    assert user_portfolio.total_balance == 200

    amount = 200_000000
    shares = 200_000000
    event_data['data'] = HexBytes("0x{:064x}".format(amount) + "{:064x}".format(shares))
    handle_event("0x55c4c840F9Ac2e62eFa3f12BaBa1B57A1208B6F5", event_data, "InitiateWithdraw")
    db_session.commit()
    user_portfolio = db_session.query(UserPortfolio).filter(
        UserPortfolio.user_address == "0x20f89ba1b0fc1e83f9aef0a134095cd63f7e8cc7"
    ).first()
    assert user_portfolio is not None
    assert user_portfolio.pending_withdrawal == 200

    amount = 200_000000
    shares = 200_000000
    event_data['data'] = HexBytes("0x{:064x}".format(amount) + "{:064x}".format(shares))
    handle_event("0x55c4c840F9Ac2e62eFa3f12BaBa1B57A1208B6F5", event_data, "Withdrawn")
    db_session.commit()
    user_portfolio = db_session.query(UserPortfolio).filter(
        UserPortfolio.user_address == "0x20f89ba1b0fc1e83f9aef0a134095cd63f7e8cc7"
    ).first()
    assert user_portfolio is not None
    assert user_portfolio.total_balance == 0
    assert user_portfolio.status == PositionStatus.CLOSED
