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
    query = f"""MATCH (e:Employee) 
                RETURN e
                """
    if 'sort' in args.keys() and 'search' in args.keys():
        query = f"""MATCH (e:Employee) 
                    WHERE e.name CONTAINS '{args['search']}' 
                    OR e.position CONTAINS '{args['search']}' 
                    RETURN e
                    """
        if args['sort'] in ['position', 'name']:
            query += f" ORDER BY e.{args['sort']}"
    elif 'sort' in args.keys():
        if args['sort'] in ['position', 'name']:
            query += f" ORDER BY e.{args['sort']}"
    elif 'search' in args.keys():
        query = f"""MATCH (e:Employee) 
                    WHERE e.name CONTAINS '{args['search']}' 
                    OR e.position CONTAINS '{args['search']}' 
                    RETURN e"""
    results = tx.run(query).data()
    employees = [{'name': result['e']['name'],
                  'position': result['e']['position']} for result in results]
    return employees


def add_employee(tx):
    name = request.json['name']
    position = request.json['position']
    department = request.json['department']
    relation = request.json['relation']

    res = tx.run(f"""MATCH (e:Employee{{ name: '{name}' }}) 
                     RETURN e""").data()
    if len(res) == 0:
        query = f"""MATCH (d:Department{{ name: '{department}' }}) 
                    CREATE (e:Employee{{ name: '{name}', position: '{position}'}}) -[:{relation}]-> (d) 
                    RETURN e"""
        tx.run(query)


def update_employee(tx, id):
    query = f"""MATCH (e:Employee) 
                WHERE id(e)={id}
                RETURN e;"""
    result = tx.run(query).data()

    name = request.json['name']
    position = request.json['position']
    department = request.json['department']
    relation = request.json['relation']

    query = f"""MATCH (e:Employee) 
                WHERE id(e)={id}
                """

    if department and relation:
        query = f"""MATCH (nd:Department{{name: '{department}'}})
                    MATCH (e:Employee) -[r]-> (d:Department) 
                    WHERE id(e)={id}
                    DELETE r
                    CREATE (e) -[:{relation}]-> (nd)
                    """
    if name:
        query += f"""SET e.name = '{name}'
                     """
    if position:
        query += f"""SET e.position = '{position}'
                     """

    query += "RETURN e;"

    if not result:
        return None
    else:
        result = tx.run(query).data()
        return result


def delete_employee(tx, id):
    query = f"""MATCH (e:Employee) 
                WHERE id(e) = {id} 
                RETURN e"""
    result = tx.run(query).data()

    if not result:
        return None
    else:
        query = f"""MATCH (e:Employee) -[r]-> () 
                    WHERE id(e) = {id}
                    DELETE e, r"""
        tx.run(query)
        return {'status': 'success'}


def get_subordinates(tx, id):
    query = f"""MATCH (e:Employee) -[:WORKS_IN]-> (d:Department) <-[:MANAGES]- (m:Employee)
                WHERE id(m) = {id}
                RETURN e"""
    results = tx.run(query).data()
    employees = [{'name': result['e']['name'],
                  'position': result['e']['position']} for result in results]
    return employees


def get_department_info(tx, id):
    query = f"""MATCH (e:Employee) -[r]-> (d:Department) <-[:MANAGES]- (m:Employee)
                WHERE id(e)={id}
                WITH d, m
                MATCH (es:Employee) -[r]-> (d)
                RETURN d, m, count(es) AS ces;
                """
    result = tx.run(query).data()[0]
    department = {'name': result['d']['name'],
                  'manager': result['m']['name'], 'employees': result['ces']}
    return department


def get_departments(tx):
    args = request.args.to_dict()
    query = f"""MATCH (d:Department)
                RETURN d
                """
    if 'sort' in args.keys() and args['sort'] == 'name':
        query += "ORDER BY d.name"
    results = tx.run(query).data()
    departments = [{'name': result['d']['name']} for result in results]
    return departments


def get_department_employees(tx, id):
    query = f"""MATCH (d:Department) 
                WHERE id(d) = {id} 
                RETURN d"""
    result = tx.run(query).data()

    if not result:
        return None
    else:
        query = f"""MATCH (d:Department) <-[r:WORKS_IN]- (e:Employee) 
                    WHERE id(d) = {id}
                    RETURN e"""
        results = tx.run(query).data()
        employees = [{'name': result['e']['name'],
                      'position': result['e']['position']} for result in results]
        return employees


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
            response = {'message': 'Employee not found'}
            return jsonify(response), 404
        else:
            response = {'status': 'success'}
            return jsonify(response)
    elif request.method == 'DELETE':
        with driver.session() as session:
            employee = session.execute_write(delete_employee, id)
        if not employee:
            response = {'message': 'Employee not found'}
            return jsonify(response), 404
        else:
            response = {'status': 'success'}
            return jsonify(response)


@app.route('/employees/<id>/subordinates', methods=['GET'])
def get_subordinates_route(id):
    with driver.session() as session:
        employees = session.execute_read(get_subordinates, id)
    response = {'employees': employees}
    return jsonify(response)


@app.route('/employees/<id>/department', methods=['GET'])
def get_department_info_route(id):
    with driver.session() as session:
        department = session.execute_read(get_department_info, id)
    response = {'department': department}
    return jsonify(response)


@app.route('/departments', methods=['GET'])
def get_departments_route():
    with driver.session() as session:
        departments = session.execute_read(get_departments)
    response = {'departments': departments}
    return jsonify(response)


@app.route('/departments/<id>/employees', methods=['GET'])
def get_department_employees_route(id):
    with driver.session() as session:
        employees = session.execute_read(get_department_employees, id)
    if not employees:
        response = {'message': 'Department not found'}
        return jsonify(response), 404
    else:
        response = {'employees': employees}
        return jsonify(response)


if __name__ == '__main__':
    app.run()
