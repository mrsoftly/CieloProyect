import mysql.connector
database = mysql.connector.connect(
    host='localhost',
    user='usercrm',
    passwd='12345678',
    auth_plugin='mysql_native_password'
)
cursor = database.cursor()
cursor.execute('CREATE DATABASE crmdb')
print('OK')