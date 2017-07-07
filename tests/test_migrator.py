def test_migrator():
    import peewee as pw
    from playhouse.db_url import connect
    from peewee_migrate import Migrator

    database = connect('sqlite:///:memory:')
    migrator = Migrator(database)

    @migrator.create_table
    class Customer(pw.Model):
        name = pw.CharField()

    assert Customer == migrator.orm['customer']

    @migrator.create_table
    class Order(pw.Model):
        number = pw.CharField()
        uid = pw.CharField(unique=True)

        customer_id = pw.ForeignKeyField(Customer, db_column='customer_id')

    assert Order == migrator.orm['order']
    migrator.run()

    migrator.add_columns(Order, finished=pw.BooleanField(default=False))
    assert 'finished' in Order._meta.fields
    migrator.run()

    migrator.drop_columns('order', 'finished', 'customer_id', 'uid')
    assert 'finished' not in Order._meta.fields
    assert not hasattr(Order, 'customer_id')
    assert not hasattr(Order, 'customer_id_id')
    migrator.run()

    migrator.add_columns(Order, customer=pw.ForeignKeyField(Customer, null=True))
    assert 'customer' in Order._meta.fields
    assert Order.customer.name == 'customer'
    migrator.run()
    assert Order.customer.name == 'customer'

    migrator.rename_column(Order, 'number', 'identifier')
    assert 'identifier' in Order._meta.fields
    migrator.run()

    migrator.drop_not_null(Order, 'identifier')
    assert Order._meta.fields['identifier'].null
    assert Order._meta.columns['identifier'].null
    migrator.run()

    migrator.add_default(Order, 'identifier', 11)
    assert Order._meta.fields['identifier'].default == 11
    migrator.run()

    migrator.change_columns(Order, identifier=pw.IntegerField(default=0))
    assert Order.identifier.db_field == 'int'
    migrator.run()

    Order.create(identifier=55)
    migrator.sql('UPDATE "order" SET identifier = 77;')
    migrator.run()
    order = Order.get()
    assert order.identifier == 77

    migrator.add_index(Order, 'identifier', 'customer')
    migrator.run()
    assert Order._meta.indexes
    assert not Order.identifier.index

    migrator.drop_index(Order, 'identifier', 'customer')
    assert not Order._meta.indexes

    migrator.remove_fields(Order, 'customer')
    assert not hasattr(Order, 'customer')

    migrator.add_index(Order, 'identifier', unique=True)
    migrator.run()
    assert not Order.identifier.index
    assert Order.identifier.unique
    assert Order._meta.indexes

    migrator.change_columns(Order, identifier=pw.IntegerField(default=0))
    assert not Order._meta.indexes
