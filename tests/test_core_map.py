from netl_triga_fuel_loader import core_map


def test_ring_sizes_and_totals():
    assert core_map.RINGS["A"] == ["A-01"]
    assert [len(core_map.RINGS[letter]) for letter in core_map.RING_LETTERS] == [1, 6, 12, 18, 24, 30, 36]
    assert len(core_map.ALL_LOCATIONS) == 127
    assert len(set(core_map.ALL_LOCATIONS)) == 127


def test_reserved_and_fuel_partition():
    reserved = core_map.RESERVED_LOCATIONS
    fuel = core_map.FUEL_LOCATIONS
    all_locs = set(core_map.ALL_LOCATIONS)

    assert len(reserved) == 11
    assert len(fuel) == 110
    assert reserved <= all_locs
    assert fuel <= all_locs
    assert reserved.isdisjoint(fuel)

    # Non-fuel, non-reserved positions: graphite, source holder, empty holes.
    non_fuel_loaded = {"D-03", "G-32", "E-11", "F-13", "F-14", "G-34"}
    assert all_locs == fuel | reserved | non_fuel_loaded
    assert non_fuel_loaded.isdisjoint(fuel)


def test_predicates():
    assert core_map.is_fuel_location("B-01")
    assert not core_map.is_fuel_location("A-01")  # central thimble (reserved)
    assert not core_map.is_fuel_location("D-03")  # graphite
    assert not core_map.is_fuel_location("G-32")  # source holder
    assert core_map.is_reserved("C-01")  # transient rod
    assert not core_map.is_reserved("B-01")
    assert core_map.ring_of("F-15") == "F"


def test_ring_of_rejects_unknown():
    import pytest

    with pytest.raises(KeyError):
        core_map.ring_of("Z-99")


def test_hex_coordinates():
    coords = core_map.hex_coordinates()
    assert len(coords) == 127
    assert coords["A-01"] == (0.0, 0.0)
    # Every location has a distinct point.
    assert len(set(coords.values())) == 127

    # Outer rings sit farther from the center than inner rings.
    def max_radius(letter):
        return max((x * x + y * y) ** 0.5 for loc, (x, y) in coords.items() if loc.startswith(letter))

    assert max_radius("B") < max_radius("D") < max_radius("G")
