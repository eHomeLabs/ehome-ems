"""Explicitly configured alerts, persistent deduplication and bounded journal."""
import asyncio
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from math import isfinite
import re
from zoneinfo import ZoneInfo

from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.storage import Store
from .const import DOMAIN

KINDS = {'daily_import', 'import_power', 'entity_unavailable'}


def validate_rules(hass, rules):
    if not isinstance(rules, list) or len(rules) > 20:
        raise ValueError('invalid_alerts')
    clean, seen = [], set()
    for rule in rules:
        if not isinstance(rule, dict) or set(rule)-{'label'} != {'id','kind','entity','threshold','duration_minutes','enabled','notify_service','daily_confirmed'}:
            raise ValueError('invalid_alert')
        identifier, kind, entity = rule['id'], rule['kind'], rule['entity']
        if not isinstance(identifier,str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,64}', identifier) or identifier in seen or kind not in KINDS:
            raise ValueError('invalid_alert')
        label=rule.get("label","")
        if not isinstance(label,str) or len(label.strip())>80 or any(ord(c)<32 for c in label):
            raise ValueError("invalid_alert_label")
        seen.add(identifier)
        if type(rule['enabled']) is not bool or type(rule['daily_confirmed']) is not bool:
            raise ValueError('invalid_alert')
        state = hass.states.get(entity) if isinstance(entity,str) and '.' in entity else None
        if state is None:
            raise ValueError('alert_entity_missing')
        unit = state.attributes.get('unit_of_measurement')
        if kind == 'daily_import' and (unit not in ('Wh','kWh') or not rule['daily_confirmed']):
            raise ValueError('alert_requires_daily_energy')
        if kind == 'import_power' and unit not in ('W','kW'):
            raise ValueError('alert_requires_power')
        for key, low, high in [('threshold',.01,1000000),('duration_minutes',0,1440)]:
            value=rule[key]
            if isinstance(value,bool) or not isinstance(value,(int,float)) or not isfinite(value) or not low <= value <= high:
                raise ValueError('invalid_alert_value')
        target=rule['notify_service']
        if target != 'persistent_notification.create' and (not isinstance(target,str) or not re.fullmatch(r'notify\.[a-z0-9_]+',target) or not hass.services.has_service(*target.split('.'))):
            raise ValueError('alert_notify_service_missing')
        clean.append({**rule,"label":label.strip() or {"daily_import":"Import quotidien","import_power":"Puissance réseau","entity_unavailable":"Entité indisponible"}[kind]})
    return clean


def save_alerts(hass, entry, rules, revision):
    if entry.modified_at.isoformat() != revision:
        raise ValueError('conflict')
    clean=validate_rules(hass,rules)
    mapping=deepcopy(dict(entry.options or entry.data))
    mapping['alerts']=clean
    hass.config_entries.async_update_entry(entry,options=mapping)


def numeric(state, units):
    if state is None or state.attributes.get('unit_of_measurement') not in units:
        return None
    try:
        value=float(state.state)*units[state.attributes['unit_of_measurement']]
    except (ValueError,TypeError,OverflowError):
        return None
    return value if isfinite(value) and value >= 0 else None


class AlertRuntime:
    def __init__(self,hass,entry,now=None):
        self.hass,self.entry=hass,entry
        self.rules=(entry.options or entry.data).get('alerts',[])
        self.now=now or (lambda:datetime.now(timezone.utc))
        self.store=Store(hass,1,f'{DOMAIN}_alerts_{entry.entry_id}')
        self.records,self.journal={},[]
        self.busy,self.stopped=False,False
        self.task=None
        self._persisted=None

    async def async_start(self):
        data=await self.store.async_load() or {}
        # Only preserve latches for exactly the same rule after configuration reload.
        self.records={r['id']:data.get('records',{}).get(r['id'],{}) for r in self.rules}
        self.journal=data.get('journal',[])[-50:]
        self.unsubscribe=async_track_time_interval(self.hass,self.async_tick,timedelta(seconds=30)) if any(r.get("enabled") for r in self.rules) else lambda:None
        self.entry.async_on_unload(self.async_stop)
        await self.async_tick()

    async def async_stop(self):
        self.stopped=True
        if hasattr(self,'unsubscribe'):self.unsubscribe()
        self.hass.data.get(DOMAIN,{}).get('alerts_runtime',{}).pop(self.entry.entry_id,None)

    async def persist(self):
        data={'records':self.records,'journal':self.journal[-50:]}
        if data != self._persisted:
            await self.store.async_save(data)
            self._persisted=deepcopy(data)

    async def async_tick(self,_now=None):
        if self.stopped or self.busy:return
        self.busy=True
        self.task=asyncio.current_task()
        try:
            now=self.now()
            day=now.astimezone(ZoneInfo(self.hass.config.time_zone)).date().isoformat()
            for rule in self.rules:
                if self.stopped or not rule.get('enabled'):continue
                record=self.records.setdefault(rule['id'],{})
                definition={key:value for key,value in rule.items() if key!='label'}
                stored={key:value for key,value in record.get('rule',{}).items() if key!='label'}
                if stored != definition:
                    record.clear();record['rule']=definition
                state=self.hass.states.get(rule['entity'])
                kind=rule['kind']
                if kind=='entity_unavailable':
                    active=state is None or state.state in ('unknown','unavailable')
                    message=f"L’entité {rule['entity']} est indisponible depuis au moins {rule['duration_minutes']:g} minute(s)."
                else:
                    value=numeric(state,{'Wh':.001,'kWh':1} if kind=='daily_import' else {'W':1,'kW':1000})
                    if value is None:
                        # Missing energy never resets a daily latch or produces a zero.
                        record.pop('since',None)
                        continue
                    if kind=='daily_import':
                        updated=getattr(state,'last_updated',None)
                        if updated is None or updated.astimezone(ZoneInfo(self.hass.config.time_zone)).date().isoformat() != day:
                            record.pop('since',None)
                            continue
                    active=value > rule['threshold']
                    message=(f"Votre consommation réseau est élevée. Vous avez importé plus de {rule['threshold']:g} kWh aujourd’hui."
                             if kind=='daily_import' else f"Votre puissance d’import réseau dépasse {rule['threshold']:g} W.")
                if kind=='daily_import' and record.get('day') != day:
                    record.update(day=day,notified=False);record.pop('since',None)
                if not active:
                    record.pop('since',None)
                    if kind!='daily_import':record['notified']=False
                    continue
                record.setdefault('since',now.isoformat())
                if record.get('notified') or (now-datetime.fromisoformat(record['since'])).total_seconds() < rule['duration_minutes']*60:continue
                record['notified']=True
                event={'time':now.isoformat(),'rule_id':rule['id'],'label':rule.get('label',rule['id']),'message':message,'status':'pending'}
                self.journal.append(event);self.journal=self.journal[-50:]
                # Persist before dispatch: no repeated sends after a reload/crash.
                await self.persist()
                try:
                    domain,service=rule['notify_service'].split('.')
                    payload={'title':'eHome EMS · '+rule.get('label',rule['id']),'message':message}
                    if domain=='persistent_notification':payload['notification_id']=f'ehome_ems_{self.entry.entry_id}_{rule["id"]}'
                    async with asyncio.timeout(10):
                        await self.hass.services.async_call(domain,service,payload,blocking=True)
                    event['status']='sent'
                except Exception:
                    event['status']='failed'
                await self.persist()
            await self.persist()
        finally:
            self.busy=False
            self.task=None


async def async_setup_alerts(hass,entry):
    runtime=AlertRuntime(hass,entry)
    hass.data.setdefault(DOMAIN,{}).setdefault('alerts_runtime',{})[entry.entry_id]=runtime
    await runtime.async_start()
