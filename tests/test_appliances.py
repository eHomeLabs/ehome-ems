"""Exercise new wizard sections without changing existing IDs or device controls."""
from test_config_flow import WizardTests, state
from unittest import IsolatedAsyncioTestCase


class ApplianceTests(IsolatedAsyncioTestCase):
    setUp = WizardTests.setUp
    async def test_appliance_can_be_added_updated_removed_and_cost_settings_preserved(self):
        await self.flow.async_step_user()
        self.states.update({'sensor.fridge': state('85'), 'sensor.fridge_day': state('0.8', 'kWh')})
        form = await self.flow.async_step_add_appliance()
        self.assertNotIn('kind', [k.schema for k in form['data_schema'].schema])
        data = {'name': 'Fridge', 'power': 'sensor.fridge', 'energy': 'sensor.fridge_day',
                'energy_period': 'today', 'included_in_home': True}
        result = await self.flow.async_step_add_appliance(data)
        self.assertEqual(result['step_id'], 'appliances')
        identifier, saved = next(iter(self.flow._draft['usages'].items()))
        self.assertEqual(saved['kind'], 'appliance')
        await self.flow.async_step_edit_appliance({'usage_id': identifier})
        await self.flow.async_step_appliance_details({**data, 'name': 'Fridge renamed'})
        self.assertEqual(list(self.flow._draft['usages']), [identifier])
        await self.flow.async_step_daily({'tariff_eur_kwh': .215, 'home': 'sensor.fridge_day'})
        self.assertEqual(self.flow._draft['tariff_eur_kwh'], .215)
        self.assertFalse(self.flow._errors(self.flow._draft))
        draft = self.flow._draft
        self.flow._start(draft)
        self.assertEqual(self.flow._draft['daily'], {'home': 'sensor.fridge_day'})
        self.assertEqual(self.flow._draft['usages'][identifier]['name'], 'Fridge renamed')
        await self.flow.async_step_remove_appliance({'usage_id': identifier})
        self.assertFalse(self.flow._draft['usages'])

    async def test_daily_rejects_invalid_price_and_wrong_unit(self):
        await self.flow.async_step_user()
        for tariff in [float('nan'), float('inf'), -1, 11, True]:
            result = await self.flow.async_step_daily({'tariff_eur_kwh': tariff})
            self.assertIn('tariff_eur_kwh', result['errors'])
        result = await self.flow.async_step_daily({'home': 'sensor.home'})
        self.assertEqual(result['errors']['home'], 'unsupported_unit')
        await self.flow.async_step_daily({'tariff_eur_kwh': 0})
        self.assertEqual(self.flow._draft['tariff_eur_kwh'], 0)
        await self.flow.async_step_daily({})
        self.assertIsNone(self.flow._draft['tariff_eur_kwh'])
