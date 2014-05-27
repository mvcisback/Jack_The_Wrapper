from jacked import get_client

def main():
    with get_client(name="captest", in_channels=2, out_channels=2) as client:
        captured = client.capture(sec=3)
        client.play(captured)

if __name__ == '__main__':
    main()
