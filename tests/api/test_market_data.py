def test_corrupted_data(corrupted_price_data):
    # corrupted_price_data: {"bidPrice": 100, "askPrice": 90}
    corrupted_bidPrice = corrupted_price_data["bidPrice"] 
    corrupted_askPrice = corrupted_price_data["askPrice"]

    assert corrupted_askPrice > 0
    assert corrupted_bidPrice > 0
    
    assert corrupted_bidPrice < corrupted_askPrice 
    
    assert corrupted_askPrice != corrupted_bidPrice


def test_live_data(live_price_data):

    live_bidPrice = float(live_price_data["bidPrice"])
    live_askPrice = float(live_price_data["askPrice"])

    assert live_bidPrice > 0
    assert live_askPrice > 0
 
    assert live_askPrice > live_bidPrice
    
    assert live_askPrice != live_bidPrice

    print("Live data is validated")