from ldap3 import Server, Connection, Tls
import ssl

tls = Tls(validate=ssl.CERT_NONE)

server = Server("192.168.182.130", port=636, use_ssl=True, tls=tls)

conn = Connection(
    server,
    user="ysf@hightech.local",
    password="13371337",
    auto_bind=True
)

print(conn.bound)
