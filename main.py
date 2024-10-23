#!/usr/bin/env python3


from cfdns import CFdns

with CFdns() as cf:
    cf.update_record_ifchanged()
