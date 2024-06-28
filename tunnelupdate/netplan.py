from yaml import safe_load, safe_dump

def render_addresses(addrlist: list[str]) -> str:
    res = []
    for addr in addrlist:
        res.append(f"Address={addr}")
    return "\n".join(res)

def render_routes(routes: list[dict[str, str]]) -> str:
    res = ""
    for route in routes:
        res += f"""[Route]
Destination={route["to"]}
Gateway={route["via"]}
"""
    return res

def convert_netplan(data) -> None:
    tunnels = data["network"]["tunnels"]
    for name, cfg in tunnels.items():
        netdev = f"""[NetDev]
Name={name}
MTUBytes={cfg["mtu"]}
Kind={cfg["mode"]}

[Tunnel]
Independent=true
Local={cfg["local"]}
Remote={cfg["remote"]}
"""
        
        network = f"""[Match]
Name={name}

[Link]
MTUBytes={cfg["mtu"]}

[Network]
LinkLocalAddressing=ipv6
{render_addresses(cfg["addresses"])}
ConfigureWithoutCarrier=yes

{render_routes(cfg["routes"])}
"""
        # 10-netplan-router-a-ipv6.netdev
        # 10-netplan-router-a-ipv6.network
        with open(f"/etc/systemd/network/10-netplan-{name}.netdev", "w") as f:
            f.write(netdev)

        with open(f"/etc/systemd/network/10-netplan-{name}.network", "w") as f:
            f.write(network)

if __name__ == "__main__":
    with open("tunnels-base.yaml", "r") as f:
        src = f.read()
    data = safe_load(src)
    convert_netplan(data)
