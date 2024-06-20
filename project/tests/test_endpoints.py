def test_list_blocks_by_producer(test_app):
    producer_id = "60c9fce42cff1c36042ffd2c"
    params = {
        'farm_id': '60d0b7cc3e6abce02d29b901',
        'block_name': 'ta'
    }
    url = f"/blocks/producers/{producer_id}"
    response = test_app.get(url)
    content = response.json()
    assert response.status_code == 200
    assert type(content["data"]) == list
    assert content["filters"]["producer"] == True
    assert content["filters"]["farm"] == False
    assert content["filters"]["block"] == False
    
    url = "{}?farm_id={}&block_name={}".format(url, params['farm_id'], params['block_name'])
    response = test_app.get(url)
    content = response.json()
    assert response.status_code == 200
    assert type(content["data"]) == list
    assert content["filters"]["producer"] == True
    assert content["filters"]["farm"] == True
    assert content["filters"]["block"] == True


def test_list_farms_by_producer(test_app):
    producer_id = "61390c83098d98f43a5d52ed"
    params = {
        'farm_name': 'test'
    }
    url = f"/farms/producers/{producer_id}"
    response = test_app.get(url)
    content = response.json()
    assert response.status_code == 200
    assert type(content["data"]) == list
    assert content["filters"]["producer"] == True
    assert content["filters"]["farm"] == False

    url = "{}?farm_name={}".format(url, params['farm_name'])
    response = test_app.get(url)
    content = response.json()
    assert response.status_code == 200
    assert type(content["data"]) == list
    assert content["filters"]["producer"] == True
    assert content["filters"]["farm"] == True


def test_list_producer_apps_data(test_app):
    identity = '1230987654321'
    identifier_name = 'populationIdentifier'
    url = f"/producers/apps?identifier={identity}&identifier_name={identifier_name}"
    response = test_app.get(url)
    content = response.json()
    assert response.status_code == 200
    assert type(content["data"]) == dict
    assert content["filters"]["identifier"] == True
    assert content["filters"]["email"] == False
    assert content["filters"]["phone"] == False


def test_list_farms_apps_data_by_producer(test_app):
    identity = '2155434346615'
    identifier_name = 'RTN'
    url = f"/farms/apps?identifier={identity}&identifier_name={identifier_name}"
    response = test_app.get(url)
    content = response.json()
    assert response.status_code == 200
    assert type(content["data"]) == list
    assert content["filters"]["identifier"] == True
    assert content["filters"]["email"] == False
    assert content["filters"]["phone"] == False


def test_list_blocks_apps_data_by_producer(test_app):
    identity = '09882308823000'
    identifier_name = 'RTN'
    url = f"/blocks/apps?identifier={identity}&identifier_name={identifier_name}"
    response = test_app.get(url)
    content = response.json()
    assert response.status_code == 200
    assert type(content["data"]) == list
    assert content["filters"]["identifier"] == True
    assert content["filters"]["email"] == False
    assert content["filters"]["phone"] == False
