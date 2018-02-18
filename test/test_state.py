"""Test for VehicleState."""

import unittest
from unittest import mock
import datetime
from test import load_response_json, TEST_COUNTRY, TEST_PASSWORD, TEST_USERNAME, BackendMock, G31_VIN
from bimmer_connected.account import ConnectedDriveAccount
from bimmer_connected.state import VehicleState, LidState, LockState

TEST_DATA = load_response_json('G31_NBTevo/dynamic.json')


class TestState(unittest.TestCase):
    """Test for VehicleState."""

    # pylint: disable=protected-access

    def test_parse(self):
        """Test if the parsing of the attributes is working."""
        account = unittest.mock.MagicMock(ConnectedDriveAccount)
        state = VehicleState(account, None)
        state._attributes = TEST_DATA['attributesMap']

        self.assertEqual(2201, state.mileage)
        self.assertEqual('km', state.unit_of_length)

        self.assertEqual(datetime.datetime(2018, 2, 17, 12, 15, 36), state.timestamp)

        self.assertAlmostEqual(-34.4, state.gps_position[0])
        self.assertAlmostEqual(25.26, state.gps_position[1])

        self.assertAlmostEqual(19, state.remaining_fuel)
        self.assertEqual('l', state.unit_of_volume)

        self.assertAlmostEqual(202, state.remaining_range_fuel)

    def test_missing_attribute(self):
        """Test if error handling is working correctly."""
        account = unittest.mock.MagicMock(ConnectedDriveAccount)
        state = VehicleState(account, None)
        state._attributes = dict()
        with self.assertRaises(ValueError):
            state.mileage  # pylint: disable = pointless-statement

    @mock.patch('bimmer_connected.vehicle.VehicleState.update_data')
    def test_no_attributes(self, _):
        """Test if error handling is working correctly."""
        account = unittest.mock.MagicMock(ConnectedDriveAccount)
        state = VehicleState(account, None)
        with self.assertRaises(ValueError):
            state.mileage  # pylint: disable = pointless-statement

    def test_update_data(self):
        """Test update_data method."""
        backend_mock = BackendMock()
        with mock.patch('bimmer_connected.account.requests', new=backend_mock):
            account = ConnectedDriveAccount(TEST_USERNAME, TEST_PASSWORD, TEST_COUNTRY)
            vehicle = account.get_vehicle(G31_VIN)
            with self.assertRaises(IOError):
                vehicle.state.update_data()

            backend_mock.add_response('.*/api/vehicle/dynamic/v1/{vin}'.format(vin=G31_VIN),
                                      data_file='G31_NBTevo/dynamic.json')
            vehicle.state.update_data()
            self.assertEqual(2201, vehicle.state.mileage)

    def test_lids(self):
        """Test features around lids."""
        account = unittest.mock.MagicMock(ConnectedDriveAccount)
        state = VehicleState(account, None)
        state._attributes = TEST_DATA['attributesMap']

        for lid in state.lids:
            self.assertEqual(LidState.CLOSED, lid.state)

        self.assertEqual(0, len(list(state.open_lids)))
        self.assertTrue(state.all_lids_closed)

        state._attributes['door_driver_front'] = LidState.OPEN
        self.assertFalse(state.all_lids_closed)

    def test_windows(self):
        """Test features around lids."""
        account = unittest.mock.MagicMock(ConnectedDriveAccount)
        state = VehicleState(account, None)
        state._attributes = TEST_DATA['attributesMap']

        for window in state.windows:
            self.assertEqual(LidState.CLOSED, window.state)

        self.assertEqual(0, len(list(state.open_windows)))
        self.assertTrue(state.all_windows_closed)

        state._attributes['window_driver_front'] = LidState.INTERMEDIATE
        self.assertFalse(state.all_windows_closed)

    def test_door_locks(self):
        """Test the door locks."""
        account = unittest.mock.MagicMock(ConnectedDriveAccount)
        state = VehicleState(account, None)
        state._attributes = TEST_DATA['attributesMap']

        self.assertEqual(LockState.SECURED, state.door_lock_state)
