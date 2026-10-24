
import pytest
from pydantic import ValidationError

from src.config import Settings


def test_default_configuration():
    config = Settings(_env_file=None)

    assert config.app_name == "GeoSentinel AI"
    assert config.app_env == "development"
    assert config.app_port == 8000


def test_custom_configuration():
    config = Settings(
        _env_file=None,
        app_env="test",
        app_port=8080,
    )

    assert config.app_env == "test"
    assert config.app_port == 8080


@pytest.mark.parametrize("port", [0, -1, 65536])
def test_invalid_port_is_rejected(port):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, app_port=port)


def test_blank_host_is_rejected():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, app_host="   ")
