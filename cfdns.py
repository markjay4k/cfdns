#!/usr/bin/env python3


import cloudflare as cf
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
        self.client = cf.Cloudflare(
            api_email=os.getenv('CF_EMAIL'),
            api_key=os.getenv('CF_API_KEY'),
        )
        self.dns = self.client.dns.records
        self.ipurls = [
            'https://ipinfo.io/ip',
            'https://ifconfig.me',
        ]

    def __enter__(self):
        self.public_ip = self._public_ip()
        if self.public_ip is False:
            raise ValueError('could not get public IP')
        self.dns_records = self._dns_records()
        if self.dns_records is False:
            raise ValueError('Connection issue with cloudflar')
        else:
            self._check_target_exists()
            return self

    @debuggo
    def update_record_ifchanged(self):
        try:
            if self._check_ips() is False:
                self._update()
        except ValueError as err:
            self.log.warning(f'{err = }')

    def _public_ip(self):
        for url in self.ipurls:
            try:
                resp = requests.get(url)
                if resp.status_code == 200:
                    self.log.debug(f'used {url}')
                    return resp.text 
                else:
                    self.log.warning(f'{url = } {resp.status_code = }')
                    continue
            except requests.exceptions.ReadTimeout as err:
                self.log.warning(f'{err = }')
                continue
            except requests.exceptions.ConnectionError as err:
                self.log.warning(f'{err = }')
                continue
        else:
            self.log.warning('could not get public IP')
            return False

    def _check_ips(self):
        if self.target_record.content == self.public_ip:
            self.log.debug(f'record IP matches public IP')
            return True
        else:
            self.log.warning(f'record IP does not match public IP')
            return False

    def _dns_records(self):
        try:
            records = self.dns.list(zone_id=os.getenv('CF_ZONE_ID'))
            return {r.name: r for r in records.result}
        except cf.InternalServerError as err:
            self.log.warning(f'{err = }')
            raise ValueError('could not get records from cloudflar')

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

    @debuggo
    def _create_record(self):
        self.log.info(f'creating DNS record {os.getenv("RECORD_NAME")}')
        self.dns.create(
            zone_id=os.getenv('CF_ZONE_ID'),
            content=self.public_ip,
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
            content=self.public_ip,
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
