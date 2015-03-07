import logging

logger = logging.getLogger(__name__)

from nymms.utils.aws_helper import ConnectionManager
from nymms.schemas import OriginModel


class BaseBackend(object):
    def __init__(self, schema_class):
        self.schema = schema_class

    def deserialize(self, item, strict=False):
        try:
            item_obj = self.schema(item, strict=strict, origin=item)
            item_obj.validate()
            return item_obj
        except Exception:
            logger.exception("Problem deserializing item:")
            logger.error("Data: %s", str(item))
            return None


class SimpleDBBackend(BaseBackend):
    OPERATOR_MAP = {
        'lt': '<',
        'gt': '>',
        'eq': '=',
        'ne': '!=',
        'gte': '>=',
        'lte': '<=',
        'like': 'like',
        'notlike': 'not like'}

    def __init__(self, region, domain_name, schema_class):
        self.region = region
        self.domain_name = domain_name

        self._conn = None
        self._domain = None

        super(SimpleDBBackend, self).__init__(schema_class)

    @property
    def conn(self):
        if not self._conn:
            self._conn = ConnectionManager(self.region)
        return self._conn

    @property
    def domain(self):
        if not self._domain:
            self._domain = self.conn.sdb.create_domain(self.domain_name)
        return self._domain

    def get(self, item_id, consistent_read=True):
        logger.debug("getting item '%s'", item_id)
        item = self.domain.get_item(item_id, consistent_read=consistent_read)
        if not item:
            logger.debug("Item %s not found.", item_id)
            return None
        return self.deserialize(item)

    def filter(self, filters=None, order_by=None, consistent_read=True,
               max_items=None, next_token=None):
        order_by = order_by or getattr(self.schema, 'default_sort_order')

        query = "select * from %s" % self.domain_name
        if filters:
            query += " where "
            query += ' and '.join(filters)

        # TODO: This is kind of a weak way of dealing with the fact that in
        # order to order by something it has to be specified in the where
        # field.
        if order_by and order_by in query:
            query += " order by `%s`" % order_by

        results = []

        if max_items:
            max_items = int(max_items)
            query += " limit %s" % max_items

        logger.debug("Executing query: %s", query)
        query_results = self.domain.select(query,
                                           consistent_read=consistent_read,
                                           max_items=max_items,
                                           next_token=next_token)
        for item in query_results:
            results.append(self.deserialize(item))

        _next_token = query_results.next_token
        if _next_token:
            _next_token = _next_token.replace('\n', '')
        return (results, _next_token)

    def web_filter(self, filters=None, order_by=None, consistent_read=True,
                   max_items=None, next_token=None):
        new_filters = []
        for (field, value) in filters:
            try:
                field, operator = field.split('__')
            except ValueError:
                operator = 'eq'
            operator = self.OPERATOR_MAP[operator]
            if field not in self.schema._fields:
                logger.debug("Invalid field in query string.")
                continue
            new_filters.append("`%s` %s '%s'" % (field, operator, value))
        logging.debug(new_filters)
        return self.filter(filters=new_filters, order_by=order_by,
                           consistent_read=consistent_read,
                           max_items=max_items, next_token=next_token)

    def purge(self, item_or_key):
        """ Deletes from the datastore entirely. Shouldn't be used in most
        cases. """
        if isinstance(item_or_key, OriginModel):
            return item_or_key._origin.delete()
        return self.domain.delete_attributes(item_or_key)

    def put(self, item, context=None):
        key = getattr(item, item.pk)
        logger.debug("Added %s to %s.", key, self.domain_name)
        return self.domain.put_attributes(key,
                                          item.to_primitive(context=context))
