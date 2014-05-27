from jacked import get_client

INPUTS = [('in_1', 'system:capture_1'), ('in_2', 'system:capture_2')]
OUTPUTS = [('out_1', 'system:playback_1'), ('out_2', 'system:playback_2')]

def main():
    with get_client(name="captest", inputs=INPUTS, outputs=OUTPUTS) as client:
        captured = client.capture(sec=3)
        client.play(captured)

if __name__ == '__main__':
    main()
