from docuflow.features.parts.order_cart import OrderCart


def test_add_item():
    cart = OrderCart()
    cart.add("BASE-001", name="Base Plate", qty=2)
    assert len(cart.get_items()) == 1
    assert cart.get_items()[0].qty == 2


def test_update_qty():
    cart = OrderCart()
    cart.add("BASE-001", qty=2)
    cart.update_qty("BASE-001", 5)
    assert cart.get_items()[0].qty == 5


def test_remove_item():
    cart = OrderCart()
    cart.add("BASE-001")
    cart.remove("BASE-001")
    assert cart.is_empty()
