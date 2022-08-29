from domain_modelling import model


def test_orderline_mapper_can_load_lines(session):
    session.execute(
        "INSERT INTO order_lines (sku, qty, orderid) VALUES "
        '("SMALL_TABLE", 2, "order-1"),'
        '("ELEGANT_LAMP", 12, "order-2"),'
        '("BLUE_BED", 13, "order-3")'
    )
    expected = [
        model.OrderLine("order-1", "SMALL_TABLE", 2),
        model.OrderLine("order-2", "ELEGANT_LAMP", 12),
        model.OrderLine("order-3", "BLUE_BED", 13),
    ]
    assert session.query(model.OrderLine).all() == expected


def test_orderline_mapper_can_save_lines(session):
    new_line = model.OrderLine("order1", "DECORATIVE_WIDGET", 12)
    session.add(new_line)
    session.commit()

    rows = list(session.execute('SELECT orderid, sku, qty FROM "order_lines"'))
    assert rows == [("order1", "DECORATIVE_WIDGET", 12)]
