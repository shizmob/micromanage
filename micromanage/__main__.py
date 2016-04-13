from __init__ import *

def main():
    threads = []

    # Build threads.
    threads.append(irc.IRCClientThread())
    threads.append(metaupdater.MetaUpdateThread())
    threads.append(afkstreamer.AFKStreamThread())
    threads.append(recorder.StreamRecordThread())
    threads.append(fallback.FallbackStreamThread())

    # Start threads.
    [ thread.start() for thread in threads ]
    # Wait for threads to finish.
    [ thread.join() for thread in threads ]

if __name__ == '__main__':
    main()
