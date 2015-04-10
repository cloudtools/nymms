import logging
import arrow

from flask import request

from nymms import schemas
from nymms.api import routes
from nymms.config import config
from nymms.providers.sdb import SimpleDBBackend


logger = logging.getLogger(__name__)
logger.debug('imported API plugin: %s', __name__)


@routes.nymms_api.route('/result', methods=['GET'])
def result():
    """
    List past results.

    Query Params:
    - limit (default 1000)
    - from_timestamp
    - to_timestamp
    """
    region = config.settings['region']
    domain_name = config.settings['result_domain']
    backend = SimpleDBBackend(region, domain_name)
    args = request.args.to_dict(flat=True)
    limit = int(args.pop('limit', routes.DEFAULT_RESULT_LIMIT))
    from_timestamp = args.pop('from_timestamp', None)
    to_timestamp = args.pop('to_timestamp', None)
    filters = []
    if from_timestamp:
        filters.append(
            'timestamp >= "%s"' % arrow.get(from_timestamp))
    if to_timestamp:
        filters.append(
            'timestamp <= "%s"' % arrow.get(to_timestamp).timestamp)
    results, _ = backend.filter(filters=filters, max_items=limit)
    return [schemas.APIResult(r).to_primitive(role='sdb') for r in results]
