from flask import Flask, jsonify, request
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os  # provides ways to access the Operating System and allows us to read the environment variables

load_dotenv()

app = Flask(__name__)

uri = os.getenv('URI')
user = os.getenv("USERNAMENEO")
password = os.getenv("PASSWORD")
driver = GraphDatabase.driver(uri, auth=(user, password), database="neo4j")


def get_employees(tx):
    args = request.args.to_dict()
    query = f"MATCH (e:Employee) RETURN e"
    if 'sort' in args.keys() and 'search' in args.keys():
        query = f"MATCH (e:Employee) WHERE e.name CONTAINS '{args['search']}' OR e.position CONTAINS '{args['search']}' RETURN e"
        if args['sort'] in ['position', 'name']:
            query += f" ORDER BY e.{args['sort']}"
    elif 'sort' in args.keys():
        if args['sort'] in ['position', 'name']:
            query += f" ORDER BY e.{args['sort']}"
    elif 'search' in args.keys():
        query = f"MATCH (e:Employee) WHERE e.name CONTAINS '{args['search']}' OR e.position CONTAINS '{args['search']}' RETURN e"
    results = tx.run(query).data()
    employees = [{'name': result['e']['name'],
                  'position': result['e']['position']} for result in results]
    return employees


def add_employee(tx):
    name = request.json['name']
    position = request.json['position']
    department = request.json['department']
    relation = request.json['relation']

    res = tx.run(f"MATCH (e:Employee{{ name: '{name}' }}) RETURN e;").data()
    if len(res) == 0:
        query = f"MATCH (d:Department{{ name: '{department}' }}) CREATE (e:Employee{{ name: '{name}', position: '{position}'}}) -[:{relation}]-> (d) RETURN e;"
        tx.run(query)


def update_employee(tx, id):
    query = f"MATCH (e:Employee) WHERE e.id={id}"
    result = tx.run(query).data()

    if not result:
        return None
    else:
        query = ""


@app.route('/employees', methods=['GET', 'POST'])
def get_post_employees_route():
    if request.method == 'GET':
        with driver.session() as session:
            employees = session.execute_read(get_employees)

        response = {'employees': employees}
        return jsonify(response)
    elif request.method == 'POST':
        with driver.session() as session:
            session.execute_write(add_employee)
        response = {'status': 'success'}
        return jsonify(response)


@app.route('/employees/<id>', methods=['PUT', 'DELETE'])
def put_delete_employee_route(id):
    if request.method == 'PUT':
        with driver.session() as session:
            employee = session.execute_write(update_employee, id)
        if not employee:
            response = {'message': 'Movie not found'}
            return jsonify(response), 404
        else:
            response = {'status': 'success'}
            return jsonify(response)


if __name__ == '__main__':
    app.run()
