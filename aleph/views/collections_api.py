from flask import Blueprint, request
from werkzeug.exceptions import BadRequest
from followthemoney import model
from followthemoney.exc import InvalidMapping

from aleph.core import db
from aleph.model import Collection
from aleph.search import CollectionsQuery
from aleph.logic.collections import delete_collection, update_collection
from aleph.logic.collections import process_collection
from aleph.logic.entities import bulk_load_query
from aleph.serializers import CollectionSchema
from aleph.views.util import get_db_collection, get_index_collection
from aleph.views.util import require, jsonify, parse_request
from aleph.util import dict_list

blueprint = Blueprint('collections_api', __name__)


@blueprint.route('/api/2/collections', methods=['GET'])
def index():
    result = CollectionsQuery.handle(request, schema=CollectionSchema)
    return jsonify(result)


@blueprint.route('/api/2/collections', methods=['POST', 'PUT'])
def create():
    require(request.authz.logged_in)
    data = parse_request(CollectionSchema)
    collection = Collection.create(data, request.authz.role)
    db.session.commit()
    update_collection(collection)
    return view(collection.id)


@blueprint.route('/api/2/collections/<int:id>', methods=['GET'])
def view(id):
    collection = get_index_collection(id)
    return jsonify(collection, schema=CollectionSchema)


@blueprint.route('/api/2/collections/<int:id>', methods=['POST', 'PUT'])
def update(id):
    collection = get_db_collection(id, request.authz.WRITE)
    data = parse_request(CollectionSchema)
    collection.update(data)
    db.session.commit()
    update_collection(collection)
    return view(id)


@blueprint.route('/api/2/collections/<int:id>/process', methods=['POST', 'PUT'])  # noqa
def process(id):
    collection = get_db_collection(id, request.authz.WRITE)
    process_collection.apply_async([collection.id], priority=2)
    return jsonify({'status': 'accepted'}, status=202)


@blueprint.route('/api/2/collections/<int:id>/mapping', methods=['POST', 'PUT'])  # noqa
def mapping_process(id):
    collection = get_db_collection(id, request.authz.WRITE)
    require(request.authz.is_admin)
    if not request.is_json:
        raise BadRequest()
    data = request.get_json().get(collection.foreign_id)
    for query in dict_list(data, 'queries', 'query'):
        try:
            model.make_mapping(query)
            bulk_load_query.apply_async([collection.id, query], priority=6)
        except InvalidMapping as invalid:
            raise BadRequest(invalid)
    return jsonify({'status': 'accepted'}, status=202)


@blueprint.route('/api/2/collections/<int:id>', methods=['DELETE'])
def delete(id):
    collection = get_db_collection(id, request.authz.WRITE)
    delete_collection.apply_async([collection.id], priority=7)
    return jsonify({'status': 'accepted'}, status=202)
