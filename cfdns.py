#!/usr/bin/env python3


from cloudflare import Cloudflare
from clogger import log
import requests
import os
#import __init__


log = log(os.getenv('LOG_LEVEL'))

def debuggo(func):
    def inner_function(*args, **kwargs):
        log.debug(f"__ calling {args[0].__class__.__name__}.{func.__name__}")
        return func(*args, **kwargs)
    return inner_function


class CFdns:
    def __init__(self):
        self.log = log
        self.client = Cloudflare(
            api_email=os.getenv('CF_EMAIL'),
            api_key=os.getenv('CF_API_KEY'),
        )
        self.dns = self.client.dns.records

    def __enter__(self):
        self._check_target_exists()
        return self

    @debuggo
    def update_record_ifchanged(self):
        if self._check_ips() is False:
            self._update()

    @property
    def _public_ip(self):
        resp = requests.get('https://ipinfo.io/ip')
        if resp.status_code == 200:
            return resp.text
        else:
            return False

    @property
    def dns_records(self):
        records = self.dns.list(zone_id=os.getenv('CF_ZONE_ID'))
        return {r.name: r for r in records.result}

    @debuggo
    def _check_target_exists(self):
        if os.getenv('RECORD_NAME') in self.dns_records.keys():
            self.target_record = self.dns_records[os.getenv('RECORD_NAME')]
        else:
            self.log.info(f'DNS record for {os.getenv("RECORD_NAME")} not found')
            self.log.info(f'creating DNS record...')
            self._create_record()
            self.target_record = self.dns_records[os.getenv('RECORD_NAME')]
            self.log.debug(f'target record = {self.target_record.name}')

    def _check_ips(self):
        if self.target_record.content == self._public_ip:
            self.log.debug(f'record IP matches public IP')
            return True
        else:
            self.log.warning(f'record IP does not match public IP')
            return False

    @debuggo
    def _create_record(self):
        self.log.info(f'creating DNS record {os.getenv("RECORD_NAME")}')
        self.dns.create(
            zone_id=os.getenv('CF_ZONE_ID'),
            content=self._public_ip,
            name=os.getenv('RECORD_NAME'),
            type=os.getenv('RECORD_TYPE'),
            proxied=bool(int(os.getenv('RECORD_PROXIED'))),
        )

    @debuggo
    def _update(self):
        self.log.info(f'updating DNS record {os.getenv("RECORD_NAME")}')
        self.dns.update(
            dns_record_id=self.target_record.id,
            zone_id=os.getenv('CF_ZONE_ID'),
            content=self._public_ip,
            name=os.getenv('RECORD_NAME'),
            type=os.getenv('RECORD_TYPE'),
            proxied=bool(int(os.getenv('RECORD_PROXIED'))),
        )

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.log.debug('exiting context manager')
        if exc_type:
            self.log.warning(f'{exc_type}: {exc_val}: {exc_tb}')


if __name__ == '__main__':
    CFdns()
