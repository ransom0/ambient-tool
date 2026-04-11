from ambient_tool.client import build_client


def main():
    client = build_client()
    devices = client.get_devices()

    print(f"Devices returned: {len(devices)}")
    print(devices)


if __name__ == "__main__":
    main()
