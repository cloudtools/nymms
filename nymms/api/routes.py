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


nymms_api = FlaskAPI(__name__)


@nymms_api.route('/state', methods=['GET'])
def state():
    """
    List current states.
    """
    region = config.settings['region']
    domain = config.settings['state_domain']

    state = sdb_state.SDBStateBackend(region, domain)
    states = state.get_all_states(
        filters=request.args,
        model_cls=APIStateRecord)
    return [s.to_primitive() for s in states]


def get_domain(region, domain_name):
    conn = aws_helper.ConnectionManager(region).sdb
    domain = conn.create_domain(domain_name)
    return domain


def get_results(domain, filters=None, order_by='timestamp', limit=1000):

    query = "select * from %s" % (domain.name)
    where_clause = ""
    where_clause += ' and '.join(filters)
    if order_by:
        if where_clause:
            where_clause += " and "
        where_clause += "%s is not null " % order_by
        where_clause += "order by `%s` desc" % order_by
    if where_clause:
        query += " where " + where_clause
    results = []
    for item in domain.select(query, max_items=limit):
        result = APIResult(item, strict=False, origin=item)
        result.validate()
        results.append(result)
    return results


@nymms_api.route('/result', methods=['GET'])
def result():
    """
    List past results
    """
    region = config.settings['region']
    domain_name = config.settings['result_domain']
    domain = get_domain(region, domain_name)
    args = dict(request.args)
    limit = args.pop('limit', [1000])
    results = get_results(
        domain, filters=args, limit=int(limit[0]))
    return [r.to_primitive() for r in results]


@nymms_api.route('/suppress', methods=['GET', 'POST'])
def suppress():
    """
    List or create suppressions.
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
    filters = suppress.get_suppressions(
        None,
        active=request.args.get('active', True),
        model_cls=APISuppression)
    return [f.to_primitive() for f in filters]


@nymms_api.route("/suppress/<string:key>/", methods=['GET', 'PUT', 'DELETE'])
def suppress_detail(key):
    """
    View, Edit, Deactivate suppressions.
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
        item['disabled'] = arrow.get().timestamp
        item.save()
        disabled_suppression_obj = APISuppression(item)
        return disabled_suppression_obj.to_primitive()
