import netl_triga_fuel_loader


def test_package_imports_and_has_version():
    assert isinstance(netl_triga_fuel_loader.__version__, str)
    assert netl_triga_fuel_loader.__version__
