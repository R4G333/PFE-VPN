from ldap3 import Server, Connection

server = Server(
    "192.168.182.130",
    port=389,
    use_ssl=False
)

try:
    conn = Connection(
        server,
        user="ysf@hightech.local",
        password="13371337",
        auto_bind=True
    )

    print("SUCCESS")

except Exception as e:
    print(type(e).__name__)
    print(e)
