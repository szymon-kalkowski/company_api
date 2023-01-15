# company_api

Company REST API created using Flask and Neo4j

https://company-api.onrender.com/departments

Endpoints:
\
\
'/employees', methods=['GET', 'POST']

POST:
{
name: '',
position: '',
department: '',
relation: ''
}
\
\
'/employees/:id', methods=['PUT', 'DELETE']

PUT:
{
name: '',
position: '',
department: '',
relation: ''
}
\
\
'/employees/:id/subordinates', methods=['GET']
\
\
'/employees/:id/department', methods=['GET']
\
\
'/departments', methods=['GET']
\
\
'/departments/:id/employees', methods=['GET']
