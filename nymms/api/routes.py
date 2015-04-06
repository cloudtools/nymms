import logging
import arrow

from flask import request
from flask.ext.api import FlaskAPI
from flask.ext.api import status

from schematics.exceptions import ValidationError

from nymms.state import sdb_state
from nymms.suppress import sdb_suppress
from nymms.schemas import APIResult, APISuppression, APIStateRecord
from nymms.config import config
from nymms.utils import aws_helper
from nymms import schemas


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

    state = sdb_state.SDBStateBackend(region, domain)
    args = request.args.to_dict(flat=True)
    limit = int(args.get('limit', DEFAULT_STATE_LIMIT))
    states = state.get_all_states(
        filters=request.args,
        model_cls=APIStateRecord,
        limit=limit)
    return [s.to_primitive() for s in states]


def get_domain(region, domain_name):
    conn = aws_helper.ConnectionManager(region).sdb
    domain = conn.create_domain(domain_name)
    return domain


def get_results(domain, order_by='timestamp desc', limit=DEFAULT_RESULT_LIMIT,
                from_timestamp=None, to_timestamp=None):

    query = "select * from %s" % (domain.name)
    filters = []
    if not order_by:
        order_by = 'timestamp'
    parts = order_by.split(' ')
    if len(parts) == 2:
        direction = parts[1]
    else:
        direction = 'desc'
    order_by = parts[0]

    if from_timestamp:
        filters.append(
            'timestamp >= "%s"' % arrow.get(from_timestamp).timestamp)
    if to_timestamp:
        filters.append(
            'timestamp <= "%s"' % arrow.get(to_timestamp).timestamp)
    filters.append('%s is not null' % order_by)
    order_by_clause = 'order by `%s` %s' % (order_by, direction)
    query += ' where ' + ' and '.join(filters) + ' ' + order_by_clause
    results = []
    for item in domain.select(query, max_items=limit):
        result = APIResult(item, strict=False, origin=item)
        result.validate()
        results.append(result)
    return results


@nymms_api.route('/result', methods=['GET'])
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
    domain = get_domain(region, domain_name)
    args = request.args.to_dict(flat=True)
    limit = int(args.pop('limit', DEFAULT_RESULT_LIMIT))
    from_timestamp = args.pop('from_timestamp', None)
    to_timestamp = args.pop('to_timestamp', None)
    results = get_results(
        domain, limit=limit,
        from_timestamp=from_timestamp, to_timestamp=to_timestamp)
    return [r.to_primitive() for r in results]


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

    suppress = sdb_suppress.SDBSuppressFilterBackend(
        region, cache_timeout, domain)

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
        suppress.add_suppression(suppress_obj)
        return suppress_obj.to_primitive(), status.HTTP_201_CREATED

    # request.method == 'GET'
    args = request.args.to_dict(flat=True)
    limit = int(args.get('limit', DEFAULT_SUPPRESSION_LIMIT))
    active = (not args.get('show_inactive', False))
    filters = suppress.get_suppressions(
        None,
        active=active,
        model_cls=APISuppression,
        limit=limit)
    return [f.to_primitive() for f in filters]


@nymms_api.route("/suppress/<string:key>/", methods=['GET', 'PUT', 'DELETE'])
def suppress_detail(key):
    """
    View, Edit, Deactivate suppressions.

    Query Params:
    - hard_delete (default False)
    """
    region = config.settings['region']
    domain_name = config.settings['suppress']['domain']
    domain = get_domain(region, domain_name)
    item = domain.get_item(key)
    suppression_obj = APISuppression(item)
    if request.method == 'GET':
        return suppression_obj.to_primitive()
    if request.method == 'PUT':
        api_data = suppression_obj.to_primitive()
        api_data.update(request.data)
        edited_suppression_obj = APISuppression(api_data)
        try:
            edited_suppression_obj.validate()
        except ValidationError as e:
            return e.messages, status.HTTP_400_BAD_REQUEST
        for key in request.data:
            item[key] = getattr(edited_suppression_obj, key)
        item.save()
        return edited_suppression_obj.to_primitive()
    if request.method == 'DELETE':
        if request.args.get('hard_delete', False):
            domain.delete_item(item)
        else:
            item['disabled'] = arrow.get().timestamp
            item.save()
        disabled_suppression_obj = APISuppression(item)
        return disabled_suppression_obj.to_primitive()
