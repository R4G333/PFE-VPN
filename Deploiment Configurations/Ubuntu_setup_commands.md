# OpenVPN + Active Directory Server Setup

## 1. Update System

```bash
sudo apt update -y
sudo apt upgrade -y
```

---

## 2. Install Packages

```bash
sudo apt install -y \
openvpn \
easy-rsa \
ufw \
iptables-persistent \
netfilter-persistent \
realmd \
sssd \
sssd-tools \
libnss-sss \
libpam-sss \
adcli \
oddjob \
oddjob-mkhomedir \
packagekit \
krb5-user
```

---

## 3. Create Local VPN Users (Optional)

```bash
sudo adduser user1
sudo adduser user2
```

---

## 4. Create PKI

```bash
mkdir ~/easy-rsa

cp -r /usr/share/easy-rsa/* ~/easy-rsa/

cd ~/easy-rsa

./easyrsa init-pki

./easyrsa build-ca nopass

./easyrsa build-server-full server nopass

./easyrsa gen-dh

openvpn --genkey secret ta.key
```

---

## 5. Copy Certificates

```bash
sudo mkdir -p /etc/openvpn/server

sudo cp pki/ca.crt /etc/openvpn/server/

sudo cp pki/issued/server.crt /etc/openvpn/server/

sudo cp pki/private/server.key /etc/openvpn/server/

sudo cp pki/dh.pem /etc/openvpn/server/

sudo cp ta.key /etc/openvpn/server/
```

---

## 6. Enable IP Forwarding

Edit:

```bash
sudo nano /etc/sysctl.conf
```

Uncomment or add

```text
net.ipv4.ip_forward=1
```

Apply

```bash
sudo sysctl -p
```

---

## 7. Configure NAT

Replace **ens33** with your network interface if different.

```bash
sudo iptables -t nat -A POSTROUTING \
-s 10.8.0.0/24 \
-o ens33 \
-j MASQUERADE

sudo netfilter-persistent save
```

---

## 8. Configure Firewall

```bash
sudo ufw allow OpenSSH

sudo ufw allow 1194/udp

sudo ufw enable
```

---

## 9. OpenVPN Configuration

Create

```bash
sudo nano /etc/openvpn/server/server.conf
```

Contents

```text
port 1194
proto udp
dev tun

ca ca.crt
cert server.crt
key server.key
dh dh.pem

topology subnet

server 10.8.0.0 255.255.255.0

ifconfig-pool-persist ipp.txt

push "redirect-gateway def1"

push "dhcp-option DNS 8.8.8.8"

keepalive 10 120

cipher AES-256-GCM
data-ciphers AES-256-GCM

auth SHA256

tls-crypt ta.key

verify-client-cert none

plugin /usr/lib/x86_64-linux-gnu/openvpn/plugins/openvpn-plugin-auth-pam.so login

username-as-common-name

user nobody
group nogroup

persist-key
persist-tun

status /var/log/openvpn-status.log
log-append /var/log/openvpn.log

verb 3
```

---

## 10. Start OpenVPN

```bash
sudo systemctl enable openvpn-server@server

sudo systemctl restart openvpn-server@server
```

---

# Active Directory Integration

## Configure DNS

Point DNS to the Domain Controller.

Example

```text
192.168.182.130
```

---

## Join Domain

Discover domain

```bash
realm discover hightech.local
```

Join

```bash
sudo realm join -U Administrator hightech.local
```

Verify

```bash
realm list
```

---

## Configure SSSD

Edit

```bash
sudo nano /etc/sssd/sssd.conf
```

Adjust your domain configuration as needed.

Protect file

```bash
sudo chmod 600 /etc/sssd/sssd.conf
```

Restart

```bash
sudo systemctl restart sssd

sudo sss_cache -E
```

---

## Test AD Users

```bash
id ysf@hightech.local

id student1@hightech.local

getent passwd ysf@hightech.local
```

---

# OpenVPN Authentication

Authentication uses PAM

```text
plugin /usr/lib/x86_64-linux-gnu/openvpn/plugins/openvpn-plugin-auth-pam.so login
```

OpenVPN will authenticate against local accounts or Active Directory through PAM/SSSD.

---

# Services

Restart

```bash
sudo systemctl restart openvpn-server@server

sudo systemctl restart sssd
```

Enable

```bash
sudo systemctl enable openvpn-server@server

sudo systemctl enable sssd
```

---

# Summary

- Ubuntu Server
- OpenVPN Server
- AES-256-GCM encryption
- TLS Crypt enabled
- PAM Authentication
- Active Directory authentication
- SSSD integration
- NAT enabled
- IP forwarding enabled
- UFW firewall configured
