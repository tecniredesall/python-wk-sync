APP_FEDERATION = "federation"
APP_TRANSFORMATIONS = "transformations"
APP_TRUMMODITY = "trummodity"
IDENTIDAD = {"populationIdentifier": "IDENTIDAD",
             "population_identifier": "IDENTIDAD"}
GENDER = {
    "masculino": "male",
    "m": "male",
    "famenino": "female",
    "f": "female",
    "otro": "other"
}
ID_INTEGERS_EXTRAS = ["scholarship_id",
                      "marital_status_id", "profession_id", "producer_type_id"]
CONF_TRUMODITY = {
    "task": "worker.trumodity.tasks.change_settle_process_status",
    "routing_key": "trummodity",
    "queue": "trummodity_services",
    "exchange": "default",
    "type_exchange": "direct"
}
CONF_PENDING = {
    "task": "worker.pendingactions.tasks.consume_pending_actions",
    "routing_key": "pending",
    "queue": "pending_actions",
    "exchange": "default",
    "type_exchange": "direct",
}
CONF_FEDERATION = {
    "task": "worker.federation.tasks.get_updates_federation",
    "routing_key": "federation",
    "queue": "federation_services",
    "exchange": "default",
    "type_exchange": "direct",
}
EXTRAS_PRODUCERS = {
    "ihcafe_carnet": {"type": "string", "key": "ihcafeCarnet", "label": "Carnet IHCAFE"},
    "productor_type": {"type": "string", "key": "producerType", "label": "Tipo de productor"},
    "contact":  {"type": "string", "key": "contact", "label": "Nombre de contacto"},
    "phone_contact":  {"type": "string", "key": "phoneContact", "label": "Celular de contacto"},
    "phone_contact_code":  {"type": "string", "key": "phoneContactCode", "label": "Código numérico del contacto"},
    "age":  {"type": "integer", "key": "age", "label": "Edad"},
    "scholarship":  {"type": "string", "key": "scolarship", "label": "Escolaridad"},
    "marital_status":  {"type": "string", "key": "maritalStatus", "label": "Estado civil"},
    "profession":  {"type": "string", "key": "profession", "label": "Profesión"},
    "association_date":  {"type": "date", "key": "associationDate", "label": "Fecha de asociación"},
    "gender":  {"type": "string", "key": "gender", "label": "Género"}
}
EXTRAS_FARMS = {
    "country": {"type": "string", "key": "country", "label": "Pais"},
    "state": {"type": "string", "key": "state", "label": "Departamento"},
    "city": {"type": "string", "key": "city", "label": "Municipio"},
    "village": {"type": "string", "key": "village", "label": "Villa"},
    "wasteland_area": {"type": "float", "key": "wastelandArea", "label": "Área de terreno baldío"},
    "productive_area": {"type": "float", "key": "productiveArea", "label": "Área productiva"},
    "unit_wasteland_area": {"type": "string", "key": "unitWastelandArea", "label": "Unidad del área de terreno baldío"},
    "unit_productive_area": {"type": "string", "key": "unitProductiveArea", "label": "Unidad del área productiva"}
}
EXTRAS_BLOCKS = {
    "country": {"type": "string", "key": "country", "label": "Pais"},
    "state": {"type": "string", "key": "state", "label": "Departamento"},
    "city": {"type": "string", "key": "city", "label": "Municipio"},
    "village": {"type": "string", "key": "village", "label": "Villa"},
    "shade_variety": {"type": "array", "key": "shadeVariety", "label": "Variedades de sombra"},
    "soil_type": {"type": "array", "key": "soilType", "label": "Tipos de suelo"},
    "variety_coffee": {"type": "array", "key": "varietyCoffee", "label": "Variedad de cafe"}
}
PURCHASE_ORDER_STATUS = {
    "settled": "settled",
    "cancelled": "cancelled"
}
