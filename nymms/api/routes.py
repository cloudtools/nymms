import logging
import arrow

from flask import request
from flask.ext.api import FlaskAPI
from flask.ext.api import status

from schematics.exceptions import ValidationError

from nymms.state import sdb_state
from nymms.suppress import sdb_suppress
from nymms.config import config
from nymms import schemas
from nymms.providers.sdb import SimpleDBBackend


logger = logging.getLogger(__name__)

nymms_api = FlaskAPI(__name__)


DEFAULT_RESULT_LIMIT = 1000
DEFAULT_SUPPRESSION_LIMIT = 1000
DEFAULT_STATE_LIMIT = 1000


@nymms_api.route('/state', methods=['GET'])
def state():
    """
    List current states.

    Query Params:
    - limit (default 1000)
    """
    region = config.settings['region']
    domain = config.settings['state_domain']

    state = sdb_state.SDBStateManager(region, domain,
                                      schema_class=schemas.APIStateRecord)
    args = request.args.to_dict(flat=True)
    limit = int(args.get('limit', DEFAULT_STATE_LIMIT))
    states, _ = state.filter(
        filters=request.args,
        max_items=limit)
    return [s.to_primitive() for s in states]


# Disabling for now- need a way of adding optional API endpoints
# For example, this end point would only work if the SDB results handler
# was enabled
# @nymms_api.route('/result', methods=['GET'])
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
    limit = int(args.pop('limit', DEFAULT_RESULT_LIMIT))
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
    return [schemas.APIResult(r).to_primitive() for r in results]


@nymms_api.route('/suppress', methods=['GET', 'POST'])
def suppress():
    """
    List or create suppressions.

    Query Params:
    - limit (default 1000)
    - show_inactive (default False)
    """
    region = config.settings['region']
    cache_timeout = config.settings['suppress']['cache_timeout']
    domain = config.settings['suppress']['domain']

    mgr = sdb_suppress.SDBSuppressionManager(
        region, cache_timeout, domain, schema_class=schemas.APISuppression)

    if request.method == 'POST':
        data = request.data

        suppress_obj = schemas.APISuppression(data)
        try:
            suppress_obj.validate()
        except ValidationError as e:
            return e.messages, status.HTTP_400_BAD_REQUEST

        now = arrow.get()
        if suppress_obj.expires <= now:
            return (
                {'expires': 'expires must be in the future'},
                status.HTTP_400_BAD_REQUEST
            )
        mgr.add_suppression(suppress_obj)
        return suppress_obj.to_primitive(), status.HTTP_201_CREATED

    # request.method == 'GET'
    args = request.args.to_dict(flat=True)
    limit = int(args.get('limit', DEFAULT_SUPPRESSION_LIMIT))
    filters = ["`expires` > '0'"]
    if not args.get('show_inactive', False):
        filters.append("`disabled` is null")

    suppressions, _ = mgr.filter(
        filters=filters, max_items=limit)
    return [s.to_primitive() for s in suppressions]


@nymms_api.route("/suppress/<string:key>/", methods=['GET', 'DELETE'])
def suppress_detail(key):
    """
    View, Edit, Deactivate suppressions.

    Query Params:
    - hard_delete (default False)
    """
    region = config.settings['region']
    cache_timeout = config.settings['suppress']['cache_timeout']
    domain = config.settings['suppress']['domain']

    mgr = sdb_suppress.SDBSuppressionManager(
        region, cache_timeout, domain, schema_class=schemas.APISuppression)

    item = mgr.get(key)
    if request.method == 'DELETE':
        if request.args.get('hard_delete', False):
            mgr.backend.purge(item)
        else:
            mgr.deactivate_suppression(key)
    return item.to_primitive()
