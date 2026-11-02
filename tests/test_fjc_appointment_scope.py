"""Prevent non-presidential FJC assignments from being attributed to presidents."""
import json
import unittest
from pathlib import Path
from scripts.collect_fjc_judges import appointment_mechanism

ROOT = Path(__file__).resolve().parents[1]


class FJCAppointmentScopeTests(unittest.TestCase):
    def test_assignment_categories_are_not_presidential(self):
        self.assertEqual(appointment_mechanism('None (assignment)'), 'non_presidential_assignment')
        self.assertEqual(appointment_mechanism('None (reassignment)'), 'non_presidential_reassignment')
        self.assertEqual(appointment_mechanism('Joseph R. Biden'), 'presidential_appointment')
        with self.assertRaises(ValueError):
            appointment_mechanism('None (unknown)')
        with self.assertRaises(ValueError):
            appointment_mechanism('')

    def test_persisted_index_reconciles_without_fabricated_presidents(self):
        index = json.loads((ROOT / 'data/judiciary/fjc-appointment-index.json').read_text(encoding='utf-8'))
        self.assertGreater(index['appointmentRecords'], 4000)
        if 'presidentialAppointmentRecords' in index:
            presidential = index['presidentialAppointmentRecords']
            nonpresidential = index['nonPresidentialServiceRecords']
            self.assertEqual(presidential + nonpresidential, index['appointmentRecords'])
            self.assertEqual(presidential, sum(r['appointments'] for r in index['presidents']))
            self.assertEqual(nonpresidential, sum(r['records'] for r in index['nonPresidentialServiceTypes']))
            self.assertFalse(any(r['name'].startswith('None') for r in index['presidents']))
        else:
            # Prior index remains valid until the official FJC collector publishes its refresh.
            self.assertEqual(index['appointmentRecords'], sum(r['appointments'] for r in index['presidents']))


if __name__ == '__main__':
    unittest.main()
