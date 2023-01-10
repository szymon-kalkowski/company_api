from flask import Flask, jsonify, request
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os  # provides ways to access the Operating System and allows us to read the environment variables

load_dotenv()

app = Flask(__name__)

uri = os.getenv('URI')
user = os.getenv("USERNAME")
password = os.getenv("PASSWORD")
driver = GraphDatabase.driver(uri, auth=(user, password), database="neo4j")


def get_employees(tx):
    query = "MATCH (e:Employee) RETURN e"
    results = tx.run(query).data()
    employees = [{'name': result['e']['name'],
                  'position': result['e']['position']} for result in results]
    return employees


@app.route('/employees', methods=['GET'])
def get_employees_route():
    with driver.session() as session:
        employees = session.execute_read(get_employees)

    response = {'employees': employees}
    return jsonify(response)


if __name__ == '__main__':
    app.run()
