from __init__ import *

def main():
    threads = []

    # Build threads.
    threads.append(irc.IRCClientThread())
    threads.append(metaupdate.MetaUpdateThread())
    threads.append(stream.AFKStreamThread())

    # Start threads.
    [ thread.start() for thread in threads ]
    # Wait for threads to finish.
    [ thread.join() for thread in threads ]

if __name__ == '__main__':
    main()
