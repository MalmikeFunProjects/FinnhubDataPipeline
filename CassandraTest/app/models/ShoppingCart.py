import datetime
from cassandra.cqlengine.models import Model
from cassandra.cqlengine import columns

class ShoppingCart(Model):
    __keyspace__ = "market"
    __table_name__ = "shopping_cart"
    userid = columns.Text(primary_key=True)
    item_count = columns.Integer()
    last_updated = columns.DateTime(default=datetime.datetime.now)
    # items = columns.List(columns.Text)
