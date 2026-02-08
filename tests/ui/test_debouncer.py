"""Tests for Debouncer utility."""

import asyncio

import pytest

from daynimal.ui.utils.debounce import Debouncer


@pytest.mark.asyncio
async def test_debouncer_delays_execution():
    """Test debouncer delays function execution."""
    called = []

    async def test_func(value):
        called.append(value)

    debouncer = Debouncer(delay=0.1)

    # Call debounced function
    await debouncer.debounce(test_func, "test1")

    # Should not be called yet
    assert len(called) == 0

    # Wait for delay
    await asyncio.sleep(0.15)

    # Should be called now
    assert len(called) == 1
    assert called[0] == "test1"


@pytest.mark.asyncio
async def test_debouncer_cancels_previous_calls():
    """Test debouncer cancels previous pending calls."""
    called = []

    async def test_func(value):
        called.append(value)

    debouncer = Debouncer(delay=0.1)

    # Rapid calls (simulating user typing)
    await debouncer.debounce(test_func, "a")
    await asyncio.sleep(0.05)  # Wait less than delay
    await debouncer.debounce(test_func, "ab")
    await asyncio.sleep(0.05)
    await debouncer.debounce(test_func, "abc")

    # Wait for final delay
    await asyncio.sleep(0.15)

    # Only last call should execute
    assert len(called) == 1
    assert called[0] == "abc"


@pytest.mark.asyncio
async def test_debouncer_multiple_sequential_calls():
    """Test debouncer handles multiple sequential calls correctly."""
    called = []

    async def test_func(value):
        called.append(value)

    debouncer = Debouncer(delay=0.05)

    # First call
    await debouncer.debounce(test_func, "first")
    await asyncio.sleep(0.1)

    # Second call (after first completed)
    await debouncer.debounce(test_func, "second")
    await asyncio.sleep(0.1)

    # Both should execute
    assert len(called) == 2
    assert called[0] == "first"
    assert called[1] == "second"


@pytest.mark.asyncio
async def test_debouncer_with_kwargs():
    """Test debouncer works with keyword arguments."""
    called = []

    async def test_func(value, suffix=""):
        called.append(f"{value}{suffix}")

    debouncer = Debouncer(delay=0.05)

    await debouncer.debounce(test_func, "test", suffix="!")
    await asyncio.sleep(0.1)

    assert len(called) == 1
    assert called[0] == "test!"


@pytest.mark.asyncio
async def test_debouncer_custom_delay():
    """Test debouncer respects custom delay."""
    called = []

    async def test_func():
        called.append(True)

    debouncer = Debouncer(delay=0.2)

    await debouncer.debounce(test_func)

    # Should not be called after 0.1s
    await asyncio.sleep(0.1)
    assert len(called) == 0

    # Should be called after 0.25s
    await asyncio.sleep(0.15)
    assert len(called) == 1
