from jacked import easy_client

def main():
    with easy_client(name="captest", channels_in=2, channels_out=2) as client:
        captured = client.capture(sec=3)
        client.play(captured)

if __name__ == '__main__':
    main()
