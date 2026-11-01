"""Unit tests for input backend abstraction and mock behavior."""

from lanpad.modules.input.factory import MockInputBackend, get_input_backend


def test_mock_backend_movement():
    mock = MockInputBackend(1000, 1000)
    mock.x, mock.y = 500, 500
    mock.apply([["m", 50, -30]])
    assert mock.get_pointer_pos() == (550, 470)

    # Clamping
    mock.apply([["m", 1000, 1000]])
    assert mock.get_pointer_pos() == (999, 999)


def test_mock_backend_keys_and_release():
    mock = MockInputBackend()
    mock.apply([["k", "Shift_L", True]])
    assert "Shift_L" in mock.held
    mock.apply([["k", "Control_L", True]])
    assert "Control_L" in mock.held
    mock.release_all()
    assert len(mock.held) == 0


def test_factory_returns_backend():
    backend = get_input_backend(force_mock=True)
    assert backend is not None
    backend.selftest()


if __name__ == "__main__":
    test_mock_backend_movement()
    test_mock_backend_keys_and_release()
    test_factory_returns_backend()
    print("input tests OK")
