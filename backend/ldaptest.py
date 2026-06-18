from ldap3 import Server, Connection

server = Server("192.168.182.130", port=389)

conn = Connection(
    server,
    user="ysf@hightech.local",
    password="YOUR_PASSWORD"
)

conn.open()
print("Connected")

print("Starting TLS...")
conn.start_tls()

print("Binding...")
conn.bind()

print("Success")