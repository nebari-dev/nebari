import os
import logging

import CloudFlare


logger = logging.getLogger(__name__)


def update_record(zone_name, record_name, record_type, record_address):
    for variable in {'CLOUDFLARE_TOKEN'}:
        if variable not in os.environ:
            raise ValueError(f'Cloudflare required environment variable={variable} not defined')

    cf = CloudFlare.CloudFlare(token=os.environ['CLOUDFLARE_API_TOKEN'])

    record = {
        "name": record_name,
        "type": record_type,
        "content": record_address,
        "ttl": 1,
        "proxied": False,
    }

    zone_id = None
    for zone in cf.zones.get():
        if zone["name"] == zone_name:
            zone_id = zone["id"]
            break
    else:
        raise ValueError(f"Cloudflare zone {zone_name} not found")

    for _record in cf.zones.dns_records.get(zone_id):
        if _record["name"] == record_name:
            logger.info(
                f"record name={record_name} type={record_type} address={record_address} already exists updating"
            )
            cf.zones.dns_records.put(zone_id, _record["id"], data=_record)
            break
    else:
        logger.info(
            f"record name={record_name} type={record_type} address={record_address} does not exists creating"
        )
        cf.zones.dns_records.post(zone_id, data=record)
