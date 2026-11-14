import {test} from 'node:test';
import assert from 'node:assert/strict';
import {isMeteringEntity,meteringOptions,applianceAvailability,powerFill,pvSunshineEstimate} from '../custom_components/ehome_ems/frontend/ehome-panel.mjs';
test('metering uses HA units or classes independently of transport',()=>{
  for(const unit of ['W','kW','kWh','Wh','A','mA','V'])assert.ok(isMeteringEntity({attributes:{unit_of_measurement:unit}}));
  assert.ok(isMeteringEntity({attributes:{device_class:'energy'}}));
  assert.equal(isMeteringEntity({attributes:{unit_of_measurement:'°C'}}),false);
  const states={'sensor.z2m_power':{attributes:{unit_of_measurement:'W'}},'sensor.linkquality':{attributes:{}},'sensor.shelly_voltage':{attributes:{unit_of_measurement:'V'}},'sensor.weather':{attributes:{unit_of_measurement:'°C'}}};
  const options=Object.keys(states).map(id=>[id,id]);
  assert.deepEqual(meteringOptions(options,states).map(([id])=>id),['sensor.z2m_power','sensor.shelly_voltage']);
  assert.deepEqual(meteringOptions(options,states,{},true),options);
  assert.deepEqual(meteringOptions([['sensor.weather','Weather']],states),[]);
  assert.deepEqual(meteringOptions(options,states,{'sensor.z2m_power':'plug','sensor.linkquality':'plug'}).map(([id])=>id),['sensor.z2m_power','sensor.shelly_voltage']);
});
test('HA availability distinguishes off, zero, unknown and unavailable',()=>{
  const config={power:'sensor.mirror',control_entity:'switch.plug'},bindings={'sensor.mirror':{source:'sensor.real'}};
  const states={'sensor.real':{state:'0'},'switch.plug':{state:'off'}};
  assert.equal(applianceAvailability(config,states,bindings),'available');
  states['switch.plug'].state='unknown';assert.equal(applianceAvailability(config,states,bindings),'unknown');
  states['sensor.real'].state='unavailable';assert.equal(applianceAvailability(config,states,bindings),'unavailable');
  assert.equal(applianceAvailability({},states),'unknown');
});
test('power gauge is bounded and never invents a maximum',()=>{
  assert.equal(powerFill(500,1000),50);assert.equal(powerFill(2000,1000),100);assert.equal(powerFill(0,1000),0);
  for(const value of [null,undefined,0,NaN,-100])assert.equal(powerFill(50,value),null);
  assert.equal(powerFill(null,1000),null);assert.equal(powerFill(-1,1000),null);
});
test('invalid cloud coverage never becomes sunshine',()=>{
  const rows=Array.from({length:9},(_,i)=>({datetime:`2026-11-13T${String(i+8).padStart(2,'0')}:00:00Z`,cloud_coverage:''}));
  assert.equal(pvSunshineEstimate(rows,'UTC',new Date('2026-11-13T12:00:00Z')),null);
});
