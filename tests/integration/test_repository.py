from domain_modelling import model, repository


def test_repository_can_save_a_batch(session):
    batch = model.Batch("batch-001", "SMALL_TABLE", qty=20, eta=None)

    repo = repository.SqlAlchemyRepository(session)
    repo.add(batch)
    session.commit()

    rows = list(
        session.execute("SELECT reference, sku, _purchased_quantity, eta FROM batches")
    )

    assert rows == [("batch-001", "SMALL_TABLE", 20, None)]


def insert_order_lines(session):
    session.execute(
        "INSERT INTO order_lines (sku, qty, orderid) VALUES "
        '("SMALL_TABLE", 2, "order-1")'
    )

    [[orderline_id]] = session.execute(
        'SELECT id FROM "order_lines" WHERE sku = :sku AND orderid=:orderid',
        dict(orderid="order-1", sku="SMALL_TABLE"),
    )
    return orderline_id


def insert_batch(session, batch_id):
    session.execute(
        "INSERT INTO batches (reference, sku, _purchased_quantity, eta) VALUES "
        ' (:batch_id, "SMALL_TABLE", 20, NULL)',
        dict(batch_id=batch_id),
    )
    [[batch_id]] = session.execute(
        "SELECT id FROM batches WHERE reference = :batch_id AND sku='SMALL_TABLE'",
        dict(batch_id=batch_id),
    )
    return batch_id


def insert_allocation(session, orderline_id, batch_id):
    session.execute(
        "INSERT INTO allocations (orderline_id, batch_id) VALUES "
        "(:orderline_id, :batch_id)",
        dict(orderline_id=orderline_id, batch_id=batch_id),
    )


def test_repository_can_retrieve_a_batch_with_allocations(session):
    orderline_id = insert_order_lines(session)
    batch1_id = insert_batch(session, "batch1")
    insert_batch(session, "batch2")
    insert_allocation(session, orderline_id, batch1_id)

    repo = repository.SqlAlchemyRepository(session)
    retrieved = repo.get("batch1")

    expected = model.Batch("batch1", "SMALL_TABLE", qty=20, eta=None)
    assert retrieved == expected
    assert retrieved.sku == expected.sku
    assert retrieved._purchased_quantity == expected._purchased_quantity
    assert retrieved._allocations == {model.OrderLine("order-1", "SMALL_TABLE", 2)}
